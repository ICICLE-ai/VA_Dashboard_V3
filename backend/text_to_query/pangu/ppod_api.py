import string
import sys
from pathlib import Path
from typing import Dict, List

import numpy as np

sys.path.append(str(Path(__file__).parent.absolute()) + '/..')

from langchain_core.messages import SystemMessage, HumanMessage
import json
import os.path
from collections import defaultdict

from langchain_core.prompts import AIMessagePromptTemplate
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain.prompts.chat import ChatPromptTemplate, HumanMessagePromptTemplate
from sentence_transformers import SentenceTransformer

from src.enumeration.schema_generation import lisp_to_repr
from src.linking.node_retrieval_api import SentenceTransformerRetriever, BM25Retriever, Colbertv2Retrieval
from pangu.environment.examples.KB.PPODSparqlCache import execute_query
from pangu.environment.examples.KB.ppod_environment import PPODEnv, lisp_to_sparql
from pangu.language.plan_wrapper import Plan
from pangu.language.ppod_language import PPODLanguage
from pangu.ppod_agent import PPODAgent


class LLMLogitsCache:
    def __init__(self, model_name='gpt-4o'):
        self.set_model_name(model_name)

    def set_model_name(self, model_name):
        self.file_path = f'.llm_logits_{model_name}.pkl'
        self.cache = self.load()

    def load(self):
        import pickle
        if os.path.exists(self.file_path):
            with open(self.file_path, 'rb') as f:
                return pickle.load(f)
        return {}

    def get(self, prompt: str):
        return self.cache.get(prompt, None)

    def set(self, prompt: str, top_logprobs: list):
        self.cache[prompt] = top_logprobs
        self.save()

    def save(self):
        import pickle
        with open(self.file_path, 'wb') as f:
            pickle.dump(self.cache, f)


llm_logits_cache = LLMLogitsCache()


def format_candidates(plans):
    # A list of letters from 'a' to 't' (for at most 20 candidates)
    letters = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', "l", "m", "n", "o", "p", "q", "r", "s", "t"]
    # Using a list comprehension to format the output
    formatted_choices = ["{}. {}".format(letters[i], plan_str) for i, plan_str in enumerate(plans)]
    used_letters = letters[:len(plans)]

    # Combining the formatted choices into a single string
    formatted_string = "Candidate actions:\n" + "\n".join(formatted_choices)
    return formatted_string


def score_pairs(question: str, plans, demo_retriever, demos, llm, beam_size=5):
    if isinstance(llm, ChatOpenAI):
        return score_pairs_chat(question, plans, demo_retriever, demos, llm, beam_size)
    elif isinstance(llm, OpenAIEmbeddings):
        return score_pairs_embeddings(question, plans, demo_retriever, demos, llm, beam_size)


def score_pairs_chat(question: str, plans, demo_retriever, demos, llm: ChatOpenAI, beam_size=5):
    demo_questions = demo_retriever.get_top_k_sentences(question, 5, distinct=True)
    retrieved_demos = []
    for q in demo_questions:
        for d in demos:
            if d['question'] == q:
                retrieved_demos.append(d)
                break

    demo_str = '\n'.join(
        [f"Question: {demo['question']}\nLogical form: {demo['s-expression_str']}" for demo in retrieved_demos])
    system_instruction = f"You're good at understand logical forms given natural language input. Here are some examples of questions and their corresponding logical forms:\n\n{demo_str}\n\nGiven a new question, choose a candidate that is the most close to its corresponding logical form. Please only **output a single-letter option**, e.g., `a`"
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

    logit_bais = {token_id: 100 for token_id in range(64, 64 + 26)}  # 'a' to 'z' tokens
    logit_bais.update({6: -100, 7: -100, 8: -100, 9: -100, 12: -100, 13: -100, 220: -100, 334: -100, 4155: -100, 5454: -100, 12488: -100, 25759: -100})

    chat_completion = llm.invoke(prompt_value.to_messages(), max_tokens=1, seed=1, logprobs=True, top_logprobs=15, logit_bias=logit_bais)
    top_logprobs = chat_completion.response_metadata['logprobs']['content'][0]['top_logprobs']
    top_logprobs = top_logprobs[:len(plans)]
    top_scores = {}  # {plan: score}
    for top_log in top_logprobs[:beam_size]:
        try:
            choice_mark = top_log['token'].lower().strip("-().*' ")
            if len(choice_mark) != 1 or (choice_mark not in string.ascii_lowercase) or (ord(choice_mark) - 96 > len(plans)):
                continue
            top_scores[plans[ord(choice_mark) - 97]] = top_log['logprob']
        except Exception as e:
            # print('score_pairs_chat exception', e, 'TopLogprob token:', top_log['token'])
            continue

    return top_scores


def normalize_vector(v: list) -> np.ndarray:
    norm = np.linalg.norm(v)
    if norm == 0:
        return np.array(v)
    return np.array(v) / norm


def score_pairs_embeddings(question: str, plans: List[str], demo_retriever, demos, llm: OpenAIEmbeddings, beam_size: int) -> Dict[str, float]:
    """
    Embed and normalize question and plans to get top_beam_size plans
    """
    question_embedding = llm.embed_query(question)
    question_embedding = normalize_vector(question_embedding)

    plans_embeddings = llm.embed_documents(plans)
    plans_embeddings = [normalize_vector(embedding) for embedding in plans_embeddings]

    scores = {}
    for i, plan_embedding in enumerate(plans_embeddings):
        score = np.dot(question_embedding, plan_embedding)
        scores[plans[i]] = score

    # Sort the dictionary by scores and keep only the top beam_size entries
    top_scores = dict(sorted(scores.items(), key=lambda item: item[1], reverse=True)[:beam_size])

    return top_scores


class PanguForPPOD:
    def __init__(self, proj_root: str = None, openai_api_key: str = None, llm_name: str = 'gpt-4o', retriever: str = 'sentence-transformers/gtr-t5-base'):
        if proj_root is None:
            proj_root = str(Path(__file__).parent.absolute()) + '/..'
        if openai_api_key is not None:
            assert openai_api_key.startswith("sk-")
            os.environ['OPENAI_API_KEY'] = openai_api_key
        else:
            assert 'OPENAI_API_KEY' in os.environ

        # load data
        self.entity_to_label = json.load(open(os.path.join(proj_root, 'data/entity_to_label.json'), 'r'))
        self.label_to_entity = json.load(open(os.path.join(proj_root, "data/label_to_entity.json"), 'r'))
        self.predicate_to_label = json.load(open(os.path.join(proj_root, "data/predicate_to_label.json"), 'r'))
        self.label_to_predicate = json.load(open(os.path.join(proj_root, "data/label_to_predicate.json"), 'r'))
        self.ppod_relations = json.load(open(os.path.join(proj_root, "data/predicates.json"), 'r'))
        self.ppod_classes = json.load(open(os.path.join(proj_root, "data/types.json"), 'r'))
        self.literals = json.load(open(os.path.join(proj_root, "data/literals.json"), 'r'))
        self.property_to_entity = json.load(open(os.path.join(proj_root, "data/predicate_entity.json"), 'r'))
        self.property_to_literal = json.load(open(os.path.join(proj_root, "data/predicate_literal.json"), 'r'))
        self.prefixes = json.load(open(os.path.join(proj_root, "data/prefix.json"), 'r'))
        self.inv_label = json.load(open(os.path.join(proj_root, "data/inverse_predicate.json"), 'r'))
        self.demos = json.load(open(os.path.join(proj_root, "exp/sample_queries_train_294.json"), 'r'))  # in-context demo

        # load Pangu components
        language = PPODLanguage()
        environment = PPODEnv(set(self.ppod_relations), set(self.ppod_classes),
                              set(self.property_to_entity), set(self.property_to_literal))
        self.agent = PPODAgent(language=language, environment=environment, find_new_elements=True)

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
        else:
            raise NotImplementedError(f'Retriever {retriever} is not implemented')

        self.llm_name = llm_name
        if llm_name.startswith('gpt'):
            self.llm = ChatOpenAI(api_key=openai_api_key, model=self.llm_name, temperature=0, max_retries=5, timeout=60)
        elif llm_name.startswith('text-embedding-'):
            self.llm = OpenAIEmbeddings(api_key=openai_api_key, model=self.llm_name, max_retries=5, timeout=60)

        else:
            raise NotImplementedError(f'LLM {llm_name} is not implemented yet, check LangChain to implement this.')

    def text_to_query(self, question: str, top_k: int = 10, max_steps: int = 4, verbose: bool = False):
        """

        :param question: natural language question
        :param top_k: the number of results
        :param max_steps: the max number of beam search steps
        :param verbose: for debugging
        :return: a list of plans
        """
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
        self.agent.initialize_plans(init_plans)

        cur_step = 1  # 1 to max_steps
        final_step = cur_step  # final step maybe less than the max cur_step because of determination strategy
        searched_plans = defaultdict(list)  # {step (int, starting from 1): [plan objects]}
        while cur_step <= max_steps:
            new_plans = self.agent.propose_new_plans(use_all_previous=True)
            if len(new_plans) == 0:
                final_step = cur_step - 1
                break

            # filter plans using retrieval model:
            cur_plans = []
            for rtn_type in new_plans:
                # convert plan to plan_str
                for p in new_plans[rtn_type]:
                    p.plan_str = lisp_to_repr(p.plan, self.prefixes, self.inv_label)
                cur_plans.extend(new_plans[rtn_type])
            # recall using SentenceTransformerRetriever
            plan_ranker = SentenceTransformerRetriever([p.plan_str for p in cur_plans], model=self.retrieval_model)
            top_plans = plan_ranker.get_top_k_sentences(question, 20, distinct=True)
            # ranking using LLM
            plan_str_to_scores = score_pairs(question, top_plans, self.demo_retriever, self.demos, self.llm)
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
            self.agent.update_current_plans(filtered_plans)
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
        for plan in final_plans[:top_k]:
            sparql = lisp_to_sparql(plan.plan)
            rows = execute_query(sparql)

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

        return res

    def retrieve_entity(self, question: str, top_k: int = 10, distinct: bool = True):
        return self.entity_retriever.get_top_k_sentences(question, top_k, distinct)

    def retrieve_relation(self, question: str, top_k: int = 10, distinct: bool = True):
        return self.relation_retriever.get_top_k_sentences(question, top_k, distinct)

    def retrieve_literal(self, question: str, top_k: int = 10, distinct: bool = True):
        return self.literal_retriever.get_top_k_sentences(question, top_k, distinct)


if __name__ == "__main__":
    pangu = PanguForPPOD(openai_api_key=os.getenv('OPENAI_API_KEY'), llm_name='gpt-4o')

    # text-to-query API demo
    res = pangu.text_to_query('What downstream infrastructures are connected to adjacent infrastructure in Drakes Estero?')
    for item in res:
        print(item)
    print()

    question = 'Which infrastructure intersects with San Dieguito Lagoon and involves striped mullet?'  # entity: San Dieguito Lagoon, literal: striped mullet
    # entity retrieval API demo
    entities = pangu.retrieve_entity(question, top_k=10)
    for i, doc in enumerate(entities):
        print(i, doc, pangu.label_to_entity[doc])
    print()

    # literal retrieval API demo
    literals = pangu.retrieve_literal(question, top_k=10)
    for i, doc in enumerate(literals):
        print(i, doc)
    print()

    # relation retrieval API demo
    relations = pangu.retrieve_relation(question, top_k=10)
    for i, doc in enumerate(relations):
        print(i, doc, pangu.label_to_predicate[doc])
    print()
