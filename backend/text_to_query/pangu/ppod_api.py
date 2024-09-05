import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.absolute()) + '/../../..')
from backend.milkOligoDB.src.api_client import get_all_concepts, get_all_relations, get_all_instances, get_uuid_concept_maps, get_uuid_relation_maps, get_uuid_instance_maps

from backend.llama_service import LlamaCppWrapper, OllamaWrapper
from langchain_core.messages import SystemMessage, HumanMessage
import json
import os.path
from collections import defaultdict

from langchain_core.prompts import AIMessagePromptTemplate
from langchain_openai import ChatOpenAI
from langchain.prompts.chat import ChatPromptTemplate, HumanMessagePromptTemplate
from sentence_transformers import SentenceTransformer

from backend.text_to_query.src.enumeration.schema_generation import lisp_to_repr
from backend.text_to_query.src.linking.node_retrieval_api import SentenceTransformerRetriever, BM25Retriever, Colbertv2Retrieval, GritLMRetriever
from backend.text_to_query.pangu.environment.examples.KB.PPODSparqlService import execute_query
from backend.text_to_query.pangu.environment.examples.KB.ppod_environment import PPODEnv, lisp_to_sparql, execute_lisp_by_kg_api
from backend.text_to_query.pangu.language.plan_wrapper import Plan
from backend.text_to_query.pangu.language.ppod_language import PPODLanguage
from backend.text_to_query.pangu.ppod_agent import PPODAgent


def format_candidates(plans):
    # A list of letters from 'a' to 't' (for at most 20 candidates)
    letters = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', "l", "m", "n", "o", "p", "q", "r", "s", "t"]
    # Using a list comprehension to format the output
    formatted_choices = ["{}. {}".format(letters[i], plan_str) for i, plan_str in enumerate(plans)]
    used_letters = letters[:len(plans)]

    # Combining the formatted choices into a single string
    formatted_string = "Candidate actions:\n" + "\n".join(formatted_choices)
    return formatted_string


system_instruction_template = f"""You're good at understand logical forms given natural language input. Now, let's classify the most relevant logical form for a given natural language query.

Here are functions you'll encounter in the LISP expressions and what they represent:

- JOIN(relation, entities) returns entities: establishes a connection between an entity (or a set of entities) and a relation, resulting in another entity (or set of entities).
- AND(entities, entities) returns entities: identifies the intersection between two sets of entities.
- COUNT(entities) returns an integer: the total number of entities within a set.

It's important to note that each relation is directed. The suffix `_inv` (inverse) may be appended to the relation name to represent an inverse relation, e.g., 
- (JOIN [is part of] [A]): `what is part of A?`
- (JOIN [is part of]_inv [A]): `what does A belong to?` or `what contains A?`

Here are some examples of questions and their corresponding logical forms:

{{demo_str}}

Given a new question, choose a candidate that is the most close to its corresponding logical form. Please only **output a single-letter option**, e.g., `a`."""


def score_pairs_chat(question: str, plans, demo_retriever, demos, llm, beam_size=5):
    demo_questions = demo_retriever.get_top_k_sentences(question, 5, distinct=True)
    retrieved_demos = []
    for q in demo_questions:
        for d in demos:
            if d['question'] == q:
                retrieved_demos.append(d)
                break

    demo_str = '\n\n'.join(
        [f"Question: {demo['question']}\nLogical form: {demo['s-expression_str']}" for demo in retrieved_demos])
    system_instruction = system_instruction_template.replace("{demo_str}", demo_str)

    demo_input1 = ["Question: Which programs are partnered with organizations of the academic type?",
                   "Candidate actions:",
                   "a. (AND core:Program (JOIN [partner organization] (JOIN [organization type] [Industry])))",
                   "b. (AND core:Program (JOIN [partner organization] (JOIN [organization type] [Academic])))",
                   "c. (AND core:Organization (JOIN [parent organization] (JOIN [organization type] [Academic])))",
                   "d. (AND core:Project (JOIN [lead organization] (JOIN [organization type] [Academic])))",
                   "e. (AND core:Project (JOIN [lead organization] (JOIN [organization type] [Academic])))",
                   "Choice: "]
    demo_output1 = 'b'

    system_message_prompt = SystemMessage(system_instruction)
    human_message_prompt1 = HumanMessage('\n'.join(demo_input1))
    human_message_prompt2 = HumanMessagePromptTemplate.from_template(f"Question: {{question}}\n{{format_candidates}}\nChoice: ")

    chat_prompt = ChatPromptTemplate.from_messages([system_message_prompt, human_message_prompt1, AIMessagePromptTemplate.from_template(demo_output1), human_message_prompt2])

    prompt_value = chat_prompt.format_prompt(question=question, format_candidates=format_candidates(plans))

    if isinstance(llm, ChatOpenAI) or isinstance(llm, LlamaCppWrapper) or isinstance(llm, OllamaWrapper):
        completion = llm.invoke(prompt_value.to_messages(), max_tokens=1, seed=1, logprobs=True, top_logprobs=20, temperature=0.5,
                                logit_bias={token_id: 99 for token_id in range(64, 64 + 26)})
        top_logprobs = completion.response_metadata['logprobs']['content'][0]['top_logprobs']
        # [{token: 'a', logprob: -0.1}, ...]
    else:
        raise NotImplementedError(f'LLM {llm} is not implemented for logprobs')
    top_logprobs = top_logprobs[:len(plans)]
    top_scores = {}
    for top_log in top_logprobs[:beam_size]:
        try:
            top_scores[plans[ord(top_log['token'].lower()) - 97]] = top_log['logprob']
        except Exception as e:
            print('score_pairs_chat exception', e, 'TopLogprob token:', top_log['token'])
    return top_scores


class PanguForPPOD:
    def __init__(self, proj_root: str = None, api_key: str = None, llm_name: str = 'gpt-4o', retriever: str = 'sentence-transformers/gtr-t5-base', use_kg_api=False):
        if proj_root is None:
            proj_root = str(Path(__file__).parent.absolute()) + '/..'
        if api_key is not None:
            if llm_name.startswith('gpt-'):
                assert api_key.startswith("sk-")
                os.environ['OPENAI_API_KEY'] = api_key

        if use_kg_api:
            self.use_kg_api = True
            all_concepts = get_all_concepts()
            all_relations = get_all_relations()
            all_instances = get_all_instances()
            # all_propositions = get_all_propositions()

            self.class_to_label, self.label_to_class = get_uuid_concept_maps(all_concepts)
            self.predicate_to_label, self.label_to_predicate = get_uuid_relation_maps(all_relations)
            self.entity_to_label, self.label_to_entity = get_uuid_instance_maps(all_instances)
            self.kb_relations = list(self.label_to_predicate.keys())
            self.kb_classes = list(self.label_to_class.keys())
            self.literals = []
            self.property_to_entity = self.kb_relations
            self.property_to_literal = []
        else:
            self.use_kg_api = False
            # load data
            self.entity_to_label = json.load(open(os.path.join(proj_root, 'data/entity_to_label.json'), 'r'))
            self.label_to_entity = json.load(open(os.path.join(proj_root, "data/label_to_entity.json"), 'r'))
            self.predicate_to_label = json.load(open(os.path.join(proj_root, "data/predicate_to_label.json"), 'r'))
            self.label_to_predicate = json.load(open(os.path.join(proj_root, "data/label_to_predicate.json"), 'r'))
            self.kb_relations = json.load(open(os.path.join(proj_root, "data/predicates.json"), 'r'))
            self.kb_classes = json.load(open(os.path.join(proj_root, "data/types.json"), 'r'))
            self.literals = json.load(open(os.path.join(proj_root, "data/literals.json"), 'r'))
            self.property_to_entity = json.load(open(os.path.join(proj_root, "data/predicate_entity.json"), 'r'))
            self.property_to_literal = json.load(open(os.path.join(proj_root, "data/predicate_literal.json"), 'r'))
        self.prefixes = json.load(open(os.path.join(proj_root, "data/prefix.json"), 'r'))
        self.inv_label = json.load(open(os.path.join(proj_root, "data/inverse_predicate.json"), 'r'))
        self.demos = json.load(open(os.path.join(proj_root, "exp/sample_queries_train_294.json"), 'r'))  # in-context demo

        # load Pangu components
        language = PPODLanguage()
        environment = PPODEnv(set(self.kb_relations), set(self.kb_classes),
                              set(self.property_to_entity), set(self.property_to_literal), use_kg_api=use_kg_api)
        self.symbolic_agent = PPODAgent(language=language, environment=environment, find_new_elements=True)

        # load entity/literal retriever
        if retriever.startswith('sentence-transformers/'):
            self.retrieval_model = SentenceTransformer(retriever)
            self.entity_retriever = SentenceTransformerRetriever(list(self.label_to_entity.keys()), model=self.retrieval_model)
            self.relation_retriever = SentenceTransformerRetriever(list(self.label_to_predicate.keys()), model=self.retrieval_model)
            self.literal_retriever = SentenceTransformerRetriever(self.literals, model=self.retrieval_model)
            self.demo_retriever = SentenceTransformerRetriever([d['question'] for d in self.demos], model=self.retrieval_model)
        elif retriever.lower() == 'bm25':
            self.entity_retriever = BM25Retriever(list(self.label_to_entity.keys()))
            self.relation_retriever = BM25Retriever(list(self.label_to_predicate.keys()))
            self.literal_retriever = BM25Retriever(self.literals)
            self.demo_retriever = BM25Retriever([d['question'] for d in self.demos])
        elif retriever.lower() == 'colbertv2':
            self.entity_retriever = Colbertv2Retrieval(list(self.label_to_entity.keys()), os.path.join(proj_root, 'exp/colbert'), 'ppod_entity_index')
            self.relation_retriever = Colbertv2Retrieval(list(self.label_to_predicate.keys()), os.path.join(proj_root, 'exp/colbert'), 'ppod_relation_index')
            self.literal_retriever = Colbertv2Retrieval(self.literals, os.path.join(proj_root, 'exp/colbert'), 'ppod_literal_index')
            self.demo_retriever = Colbertv2Retrieval([d['question'] for d in self.demos], os.path.join(proj_root, 'exp/colbert'), 'ppod_demo_index')
        elif retriever.startswith('GritLM/'):
            from gritlm import GritLM
            self.retrieval_model = GritLM("GritLM/GritLM-7B", torch_dtype="auto")
            self.entity_retriever = GritLMRetriever(list(self.label_to_entity.keys()), model=self.retrieval_model,
                                                    instruction="Given a query, retrieve entities that are mentioned by the query from a knowledge graph.")
            self.relation_retriever = GritLMRetriever(list(self.label_to_predicate.keys()), model=self.retrieval_model,
                                                      instruction="Given a query, retrieve relations that are mentioned by the query from a knowledge graph.")
            self.literal_retriever = GritLMRetriever(self.literals, model=self.retrieval_model,
                                                     instruction="Given a query, retrieve literals that are mentioned by the query from a knowledge graph.")
            self.demo_retriever = GritLMRetriever([d['question'] for d in self.demos], model=self.retrieval_model,
                                                  instruction="Given a query, retrieve the most similar queries.")
        else:
            raise NotImplementedError(f'Retriever {retriever} is not implemented')

        self.llm_name = llm_name
        assert self.llm_name is not None, 'Please set LLM model name or model path'
        if self.llm_name.startswith('gpt-'):
            self.llm = ChatOpenAI(model=self.llm_name, temperature=0, max_retries=5, timeout=60, openai_api_key=api_key)
        elif self.llm_name in ['llama3.1:8b', 'llama3:8b']:
            self.llm = OllamaWrapper(model=self.llm_name, api_key=api_key)
        # elif 'llama' in self.llm_name.lower():
        # self.llm = LlamaCppWrapper(model_path=self.llm_name)

        print('Text-to-query initialized')

    def text_to_query(self, question: str, top_k: int = 10, max_steps: int = 3, verbose: bool = False, openai_api_key: str = None):
        """

        :param question: natural language question
        :param top_k: the number of results
        :param max_steps: the max number of beam search steps
        :param verbose: for debugging
        :return: a list of plans
        """
        if openai_api_key is not None:
            assert openai_api_key.startswith("sk-")
            os.environ['OPENAI_API_KEY'] = openai_api_key
        assert os.environ['OPENAI_API_KEY'] is not None, 'Please set OPENAI_API_KEY in environment variable'

        # from langchain.globals import set_llm_cache
        # from langchain_community.cache import SQLiteCache
        # set_llm_cache(SQLiteCache(database_path="exp/.langchain.db"))  # doesn't support metadata for now

        # linking
        pred_entities = self.entity_retriever.get_top_k_sentences(question, 50, distinct=True)
        pred_entity_ids = []
        for e in pred_entities:
            pred_entity_ids.append(self.label_to_entity.get(e, None)[0])
        pred_literals = self.literal_retriever.get_top_k_sentences(question, 50, distinct=True)

        # initialize plans and start beam search
        init_plans = {'Entities': set(), 'Literals': set()}
        for e in pred_entity_ids[:3]:
            init_plans['Entities'].add(Plan(e, self.entity_to_label.get(e, None)))
        for l in pred_literals[:1]:
            init_plans['Literals'].add(Plan(l, l))
        self.symbolic_agent.initialize_plans(init_plans)

        cur_step = 1  # 1 to max_steps
        final_step = cur_step  # final step maybe less than the max cur_step because of determination strategy
        searched_plans = defaultdict(list)  # {step (int, starting from 1): [plan objects]}
        while cur_step <= max_steps:
            new_plans = self.symbolic_agent.propose_new_plans(use_all_previous=True)
            if len(new_plans) == 0:
                final_step = cur_step - 1
                break

            # filter plans using retrieval model:
            cur_plans = []
            for rtn_type in new_plans:
                # convert plan to plan_str
                for p in new_plans[rtn_type]:
                    p.plan_str = lisp_to_repr(p.plan, self.prefixes, self.inv_label, self.entity_to_label, self.predicate_to_label)
                cur_plans.extend(new_plans[rtn_type])
            # recall using SentenceTransformerRetriever
            plan_ranker = SentenceTransformerRetriever([p.plan_str for p in cur_plans], model=self.retrieval_model)
            top_plans = plan_ranker.get_top_k_sentences(question, 20, distinct=True)
            # ranking using LLM
            plan_str_to_scores = score_pairs_chat(question, top_plans, self.demo_retriever, self.demos, self.llm)
            # add plans from ranked top cur_plans to searched_plans
            for plan_str in plan_str_to_scores:
                for plan in cur_plans:
                    if plan.plan_str == plan_str:
                        plan.score = plan_str_to_scores[plan_str]
                        searched_plans[cur_step].append(plan)
                        break

            if cur_step > 1:
                stop_in_this_step = False
                # check if there exists one plan in the last step that scores higher than all the plans in this step
                for last_plan in searched_plans[cur_step - 1]:
                    last_plan_score = last_plan.score
                    if all([last_plan_score > p.score for p in searched_plans[cur_step]]):
                        stop_in_this_step = True
                        break
                if stop_in_this_step:
                    final_step = cur_step - 1
                    break  # stop searching

            # put top ranked plans back into a plan dict
            filtered_plans = defaultdict(set)
            for plan_str in plan_str_to_scores:
                for plan in cur_plans:
                    if plan.plan_str == plan_str:
                        filtered_plans[plan.rtn_type].add(plan)
                        break
            self.symbolic_agent.update_current_plans(filtered_plans)
            cur_step += 1
            final_step = cur_step

        # get plans <= final_step
        final_plans = []
        for i in range(1, final_step + 1):
            final_plans.extend(searched_plans[i])
        # rank final_plans with their scores
        final_plans = sorted(final_plans, key=lambda x: x.score, reverse=True)

        if verbose:
            print('Question:', question)
            print('Predicted entities:', pred_entities[:3], pred_entity_ids[:3])
            print('Predicted literals:', pred_literals[:1])
            print('Valid step:', final_step, 'Total step:', cur_step)

        # convert plans to SPARQL queries and get their execution results
        res = []
        num_valid_query = 0
        if not self.use_kg_api:
            for plan in final_plans[:30]:
                sparql = lisp_to_sparql(plan.plan)
                rows = execute_query(sparql)
                if len(rows) > 0:
                    num_valid_query += 1

                labels = []  # get labels if the results are entities
                for item in rows:
                    if item[0] in self.entity_to_label:
                        labels.append(self.entity_to_label[item[0]])
                    else:
                        labels.append(item[0])
                assert len(rows) == len(labels)
                res.append(
                    {'input': question, 's-expression': plan.plan, 's-expression_repr': plan.plan_str, 'score': plan.score,
                     'sparql': sparql, 'results': rows, 'labels': labels})

                if num_valid_query >= top_k:
                    break

            res = res[:top_k]
            if num_valid_query:
                res = [r for r in res if len(r['results']) > 0]
            return res
        else:  # use_kg_api
            for plan in final_plans[:30]:
                results = execute_lisp_by_kg_api(plan.plan)
                if len(results) > 0:
                    num_valid_query += 1

                labels = []  # get labels if the results are entities
                for item in results:
                    if item in self.entity_to_label:
                        labels.append(self.entity_to_label[item])
                    else:
                        labels.append(item)
                assert len(results) == len(labels)
                res.append(
                    {'input': question, 's-expression': plan.plan, 's-expression_repr': plan.plan_str, 'score': plan.score,
                     'sparql': None, 'results': list(results), 'labels': labels})

                if num_valid_query >= top_k:
                    break

            res = res[:top_k]
            if num_valid_query:
                res = [r for r in res if len(r['results']) > 0]
            return res

    def retrieve_entity(self, question: str, top_k: int = 10, distinct: bool = True):
        return self.entity_retriever.get_top_k_sentences(question, top_k, distinct)

    def retrieve_relation(self, question: str, top_k: int = 10, distinct: bool = True):
        return self.relation_retriever.get_top_k_sentences(question, top_k, distinct)

    def retrieve_literal(self, question: str, top_k: int = 10, distinct: bool = True):
        return self.literal_retriever.get_top_k_sentences(question, top_k, distinct)
