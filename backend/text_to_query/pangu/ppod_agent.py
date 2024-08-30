import itertools
import json
import os.path
from collections import defaultdict
from typing import List, Dict, Set

from pangu.environment.environment import Env
from pangu.environment.examples.KB.PPODSparqlService import execute_query
from pangu.environment.examples.KB.ppod_environment import PPODEnv, lisp_to_sparql

from pangu.language.domain_language import DomainLanguage
from pangu.language.plan_wrapper import Plan
from pangu.language.ppod_language import PPODLanguage

proj_root = os.path.dirname(os.path.abspath(__file__)) + '/..'
with open(os.path.join(proj_root, "data/types.json")) as f:
    ppod_classes = set(json.load(f))
with open(os.path.join(proj_root, "data/predicates.json")) as f:
    ppod_relations = set(json.load(f))
with open(os.path.join(proj_root, "data/entities.json")) as f:
    ppod_entities = set(json.load(f))
with open(os.path.join(proj_root, "data/entity_to_label.json")) as f:
    ppod_entity_label = json.load(f)
with open(os.path.join(proj_root, "data/predicate_to_label.json")) as f:
    ppod_relation_label = json.load(f)


def lisp_to_label(lisp: str, entity_to_label, relation_to_label):
    lisp_split = lisp.split(' ')
    res = []
    for item in lisp_split:
        r_par_count = item.count(')')
        item = item.rstrip(')')
        r_par = r_par_count > 0

        inv = False
        if item.endswith('_inv'):
            inv = True
            item = item.replace('_inv', '')

        if item in entity_to_label:
            res.append('[' + entity_to_label[item] + ']')
        elif item in relation_to_label:
            res.append('[' + relation_to_label[item] + ']')
        else:
            res.append(item)

        if inv:
            res[-1] += '_inv'

        if r_par:
            res[-1] += ')' * r_par_count

    return ' '.join(res)


class PPODAgent:
    def __init__(self, language: DomainLanguage,
                 environment: Env = None,
                 find_new_elements=False):
        self.language = language
        # signature -> a list of function names
        self.function_signatures: Dict[str, List] = defaultdict(lambda: [])
        # function name -> return type
        self.return_type: Dict[str, str] = {}
        self.environment = environment
        # programs of all previous steps; each step has its own dict of programs, indexed by return types
        self.current_plans: List[Dict[str, Set]] = []
        self.find_new_elements = find_new_elements

        self.productions = []
        for rule in self.language.all_possible_productions():
            two_sides = rule.split(" -> ")
            if two_sides[0][0] == '<' and two_sides[0][-1] == '>':
                self.function_signatures[two_sides[0]].append(two_sides[1])
                self.return_type[two_sides[1]] = two_sides[0].split(':')[-1][:-1]
            elif two_sides[0] != "@start@":
                self.productions.append(rule)

        self.combinations = []
        for rule in self.productions:
            two_sides = rule.split(" -> ")
            assert two_sides[1][0] == '['
            rtn_type = two_sides[0]
            two_sides[1] = two_sides[1][1:-1]
            # a list of argument types
            elements = two_sides[1].split(", ")
            functions = self.function_signatures[elements[0]]
            # start from 1 because the first element is the function signature
            arguments = elements[1:]

            self.combinations.append((rtn_type, functions, arguments))

    def get_action_from_plan(self, plan: Plan):
        # derive an action to take from a plan. this is something to customize for each task.
        return plan.plan

    def initialize_plans(self, initial_plans: Dict[str, Set]):
        self.current_plans = [initial_plans]

        return initial_plans

    def check_validity(self, plan: Plan):
        # check the validity of a newly proposed candidate plan in a postprocessing fashion
        if plan.plan.startswith('(COUNT') and len(plan.plan.split(' ')) == 2:
            return False
        return True

    def propose_new_plans(self,
                          allow_reuse: bool = False,
                          # if use_all_previous is enabled, then there is no need for KEEP
                          use_all_previous: bool = False):
        """
        :param allow_reuse: whether a subplan can be used for multiple times in a more complicated plan
        :param use_all_previous: when composing plan of height k, whether to consider all programs of height < k
        or only consider k-1
        :return:
        """
        new_plans = defaultdict(lambda: set())

        previous_step_plans = self.current_plans[-1]
        if self.find_new_elements:
            # this will be True for tasks like KBQA, embodied AI, or web surfing
            # get all elements from the environment
            for arg_type in previous_step_plans:
                for rtn_type, functions, arguments in self.combinations:
                    if arg_type in arguments:
                        indices = [index for index, argument in enumerate(arguments) if argument == arg_type]
                        for plan in previous_step_plans[arg_type]:
                            action = self.get_action_from_plan(plan)
                            # fetching new elements from the target environment
                            observations = self.environment.step(action)
                            # print("Observed: ", [len(observations[k]) for k in observations])
                            iterators = []
                            try:
                                for index in indices:
                                    iterator = list(
                                        itertools.product(*([observations[argument] for argument in arguments[0:index]]
                                                            + [[plan.plan]]
                                                            + [observations[argument] for argument in
                                                               arguments[index + 1:]])))
                            except KeyError as e:
                                # print('propose_new_plans KeyError:', e)  # some arguments are missing for this rule, then just skip
                                pass
                            else:
                                iterators.append(iterator)

                            new_plans[rtn_type].update(
                                self._synthesize_new_plans(iterators, functions, allow_reuse, rtn_type))


        else:
            combined_previous_plans = defaultdict(lambda: set())
            for plans in self.current_plans:
                for rtn in plans:
                    combined_previous_plans[rtn].update(plans[rtn])

            # Get new plans by applying the production rules to current plans and new elements
            for rtn_type, functions, arguments in self.combinations:
                try:
                    if not use_all_previous:
                        iterators = [
                            list(itertools.product(*[previous_step_plans[argument] for argument in arguments]))]
                    else:
                        iterators = []
                        for i in range(len(arguments)):
                            iterator = list(
                                itertools.product(*([combined_previous_plans[argument] for argument in arguments[0:i]]
                                                    + [previous_step_plans[arguments[i]]]
                                                    + [combined_previous_plans[argument] for argument in
                                                       arguments[i + 1:]])))
                            iterators.append(iterator)

                    new_plans[rtn_type].update(self._synthesize_new_plans(iterators, functions, allow_reuse, rtn_type))

                except KeyError:
                    pass  # some arguments are missing for this rule, then just skip

        # self.current_plans.append(new_plans)

        return new_plans

    def update_current_plans(self, new_plans):  # used to update with the top-k plans returned by the LM
        self.current_plans.append(new_plans)

    def get_return_type(self, plan: Plan):
        # this is a bit ad-hoc, but should work
        function_name = plan.plan.split(' ')[0][1:]
        return self.return_type[function_name]

    def _check_finalized(self, plan: Plan):
        # check whether a plan is finalized. this is something to customize for each task.
        return True

    def _execute(self, plan: Plan):
        # execute a plan. this is something to customize for each task.
        # the real execution logic should be implemented in the environment
        return set()

    def _get_surface_form(self, plan: Plan):
        # get the surface form of a plan for LM scoring. this is something to customize for each task.
        # (e.g., we may want to use the mention of an entity rather than its ID when scoring a KBQA plan)
        return plan

    def _synthesize_new_plans(self, iterators, functions, allow_reuse=False, rtn_type=None):
        plans = set()
        for iterator in iterators:
            for combo in iterator:  # a combination of elements
                combo = list(combo)
                if not allow_reuse:  # each subplan can only be used once
                    # todo: now the equivalence is determined only by surface forms.
                    #  May consider more advanced properties like symmetry
                    if len(combo) > len(set(combo)):
                        continue
                for i, elemen in enumerate(combo):
                    if isinstance(elemen, Plan):
                        combo[i] = elemen.plan
                for func in functions:
                    new_plan = f"({func} {' '.join(combo)})"
                    new_plan = Plan(new_plan,
                                    plan_str=self._get_surface_form(new_plan),
                                    height=len(self.current_plans),
                                    rtn_type=rtn_type,
                                    function=func,
                                    denotation=self._execute(new_plan),
                                    finalized=self._check_finalized(new_plan))
                    if self.check_validity(new_plan):
                        plans.add(new_plan)

        return plans

    def add_class_to_action(self, action):
        if not action.startswith('('):
            return action
        sparql = lisp_to_sparql(action)
        # write a sparql to query the class of the entity
        new_clauses = ["SELECT DISTINCT ?cls\nWHERE {\n?x a ?cls .\n{"]
        new_clauses.extend(sparql.split("\n"))
        new_clauses.append("}\n}")
        new_query = '\n'.join(new_clauses)
        try:
            rows = execute_query(new_query)
            classes = set([r[0] for r in rows])
        except Exception as e:
            print('add_class_to_action:', e)
            print('action:', action)
            print(new_query)
            classes = set()

        res = []  # todo
        for c in classes:
            res.append(f"(AND {c} {action})")
        return res


if __name__ == '__main__':
    language = PPODLanguage()
    environment = PPODEnv(ppod_relations, ppod_classes)
    agent = PPODAgent(language=language, environment=environment, find_new_elements=True)

    agent.initialize_plans({"Entities": {
        Plan("https://raw.githubusercontent.com/adhollander/FSLschemas/main/CA_PPODterms.ttl#org_aa0d38")}})
    step = 1
    while step <= 4:
        new_plans = agent.propose_new_plans(use_all_previous=True)
        for rtn_type in new_plans:
            print('Step', step, rtn_type)
            for plan in new_plans[rtn_type]:
                print({'plan': plan, 'plan_str': lisp_to_label(plan.plan, ppod_entity_label, ppod_relation_label)})
            print()
        agent.update_current_plans(new_plans)
        step += 1
