import json
import re

from pangu.environment.environment import Env
from pangu.environment.examples.KB.PPODSparqlService import PPODSparqlService, QueryAPI
from pangu.language.util import lisp_to_nested_expression, linearize_lisp_expression


def is_valid_uuid(uuid_str):
    uuid_regex = re.compile(r'^[a-fA-F0-9]{8}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{12}$')
    return bool(uuid_regex.match(uuid_str))


def is_entity(s: str) -> bool:
    if s.startswith('<') and s.endswith('>'):
        s = s[1:-1]
    if (s.startswith('fslp:') or s.startswith('http://www.wikidata.org/entity/')
            or s.startswith('https://raw.githubusercontent.com/adhollander/FSLschemas/main/')):
        return True
    if is_valid_uuid(s):
        return True
    return False


def replace_inv_to_r_func(input_str):
    import re
    # Regex pattern to match 'string_inv' and capture 'string' part
    pattern = re.compile(r"(\S+)_inv")

    # Replacement function to format the matched string
    def replacer(match):
        return "(R {})".format(match.group(1))

    # Replacing in the input string using the pattern and replacer function
    output_str = pattern.sub(replacer, input_str)
    return output_str


def replace_r_func_to_inv(input_str):
    import re
    pattern = re.compile(r"\(R (\S+?)\)")

    def replacer(match):
        return "{}_inv".format(match.group(1))

    output_str = pattern.sub(replacer, input_str)
    return output_str


def lisp_to_sparql(lisp: str) -> str:
    """
    Convert a lisp expression to a SPARQL query
    :param lisp: lisp expression
    :return: SPARQL query
    """
    lisp = replace_inv_to_r_func(lisp)

    clauses = []
    order_clauses = []
    entities = set()  # collect entites for filtering
    # identical_variables = {}   # key should be smaller than value, we will use small variable to replace large variable
    identical_variables_r = {}  # key should be larger than value
    expression = lisp_to_nested_expression(lisp)
    superlative = False
    if expression[0] in ['ARGMAX', 'ARGMIN']:
        superlative = True
        # remove all joins in relation chain of an arg function. In another word, we will not use arg function as
        # binary function here, instead, the arity depends on the number of relations in the second argument in the
        # original function
        if isinstance(expression[2], list):
            def retrieve_relations(exp: list):
                rtn = []
                for element in exp:
                    if element == 'JOIN':
                        continue
                    elif isinstance(element, str):
                        rtn.append(element)
                    elif isinstance(element, list) and element[0] == 'R':
                        rtn.append(element)
                    elif isinstance(element, list) and element[0] == 'JOIN':
                        rtn.extend(retrieve_relations(element))
                return rtn

            relations = retrieve_relations(expression[2])
            expression = expression[:2]
            expression.extend(relations)

    sub_programs = linearize_lisp_expression(expression, [0])
    question_var = len(sub_programs) - 1
    count = False

    def get_root(var: int):
        while var in identical_variables_r:
            var = identical_variables_r[var]

        return var

    for i, subp in enumerate(sub_programs):
        i = str(i)
        if subp[0] == 'JOIN':
            if isinstance(subp[1], list):  # R relation
                if is_entity(subp[2]):  # entity
                    clauses.append(" <" + subp[2] + "> <" + subp[1][1] + "> ?x" + i + " .")
                    entities.add(subp[2])
                elif subp[2][0] == '#':  # variable
                    clauses.append("?x" + subp[2][1:] + " <" + subp[1][1] + "> ?x" + i + " .")
                else:  # literal   (actually I think literal can only be object)
                    subp[2] = ' '.join(subp[2:])
                    clauses.append(f"\"{subp[2]}\" <{subp[1][1]}> ?x{i} .")
            else:
                if is_entity(subp[2]):  # entity
                    clauses.append("?x" + i + " <" + subp[1] + "> <" + subp[2] + "> .")
                    entities.add(subp[2])
                elif subp[2][0] == '#':  # variable
                    clauses.append("?x" + i + " <" + subp[1] + "> ?x" + subp[2][1:] + " .")
                else:  # literal
                    subp[2] = ' '.join(subp[2:])
                    clauses.append(f"?x{i} <{subp[1]}> \"{subp[2]}\" .")
        elif subp[0] == 'AND':
            var1 = int(subp[2][1:])
            rooti = get_root(int(i))
            root1 = get_root(var1)
            if rooti > root1:
                identical_variables_r[rooti] = root1
            else:
                identical_variables_r[root1] = rooti
                root1 = rooti
            # identical_variables[var1] = int(i)
            if subp[1][0] == "#":
                var2 = int(subp[1][1:])
                root2 = get_root(var2)
                # identical_variables[var2] = int(i)
                if root1 > root2:
                    # identical_variables[var2] = var1
                    identical_variables_r[root1] = root2
                else:
                    # identical_variables[var1] = var2
                    identical_variables_r[root2] = root1
            else:  # 2nd argument is a class
                clauses.append("?x" + i + " a <" + subp[1] + "> .")
        elif subp[0] in ['le', 'lt', 'ge', 'gt']:  # the 2nd can only be numerical value
            clauses.append("?x" + i + " <" + subp[1] + "> ?y" + i + " .")
            if subp[0] == 'le':
                op = "<="
            elif subp[0] == 'lt':
                op = "<"
            elif subp[0] == 'ge':
                op = ">="
            else:
                op = ">"
            if subp[2].__contains__('^^'):
                data_type = subp[2].split("^^")[1].split("#")[1]
                if data_type not in ['integer', 'float', 'dateTime', 'double']:
                    subp[2] = f'"{subp[2].split("^^")[0] + "-08:00"}"^^<{subp[2].split("^^")[1]}>'
                else:
                    subp[2] = f'"{subp[2].split("^^")[0]}"^^<{subp[2].split("^^")[1]}>'
            clauses.append(f"FILTER (?y{i} {op} <{subp[2]}>)")
        elif subp[0] == 'TC':
            var = int(subp[1][1:])
            # identical_variables[var] = int(i)
            rooti = get_root(int(i))
            root_var = get_root(var)
            if rooti > root_var:
                identical_variables_r[rooti] = root_var
            else:
                identical_variables_r[root_var] = rooti

            year = subp[3]
            from_para = f'"{year}-12-31"^^xsd:dateTime'
            to_para = f'"{year}-01-01"^^xsd:dateTime'

            clauses.append(f'FILTER(NOT EXISTS {{?x{i} <{subp[2]}> ?sk0}} || ')
            clauses.append(f'EXISTS {{?x{i} <{subp[2]}> ?sk1 . ')
            clauses.append(f'FILTER(xsd:datetime(?sk1) <= {from_para}) }})')
            if subp[2][-4:] == "from":
                clauses.append(f'FILTER(NOT EXISTS {{?x{i} {subp[2][:-4] + "to"} ?sk2}} || ')
                clauses.append(f'EXISTS {{?x{i} <{subp[2][:-4] + "to"}> ?sk3 . ')
            else:  # from_date -> to_date
                clauses.append(f'FILTER(NOT EXISTS {{?x{i} {subp[2][:-9] + "to_date"} ?sk2}} || ')
                clauses.append(f'EXISTS {{?x{i} <{subp[2][:-9] + "to_date"}> ?sk3 . ')
            clauses.append(f'FILTER(xsd:datetime(?sk3) >= {to_para}) }})')

        elif subp[0] in ["ARGMIN", "ARGMAX"]:
            superlative = True
            if subp[1][0] == '#':
                var = int(subp[1][1:])
                rooti = get_root(int(i))
                root_var = get_root(var)
                # identical_variables[var] = int(i)
                if rooti > root_var:
                    identical_variables_r[rooti] = root_var
                else:
                    identical_variables_r[root_var] = rooti
            else:  # arg1 is class
                clauses.append(f'?x{i} a <{subp[1]}> .')

            if len(subp) == 3:
                clauses.append(f'?x{i} <{subp[2]}> ?sk0 .')
            elif len(subp) > 3:
                for j, relation in enumerate(subp[2:-1]):
                    if j == 0:
                        var0 = f'x{i}'
                    else:
                        var0 = f'c{j - 1}'
                    var1 = f'c{j}'
                    if isinstance(relation, list) and relation[0] == 'R':
                        clauses.append(f'?{var1} <{relation[1]}> ?{var0} .')
                    else:
                        clauses.append(f'?{var0} <{relation}> ?{var1} .')

                clauses.append(f'?c{j} <{subp[-1]}> ?sk0 .')

            if subp[0] == 'ARGMIN':
                order_clauses.append("ORDER BY ?sk0")
            elif subp[0] == 'ARGMAX':
                order_clauses.append("ORDER BY DESC(?sk0)")
            order_clauses.append("LIMIT 1")


        elif subp[0] == 'COUNT':  # this is easy, since it can only be applied to the quesiton node
            var = int(subp[1][1:])
            root_var = get_root(var)
            identical_variables_r[int(i)] = root_var  # COUNT can only be the outtermost
            count = True
    #  Merge identical variables
    for i in range(len(clauses)):
        for k in identical_variables_r:
            clauses[i] = clauses[i].replace(f'?x{k} ', f'?x{get_root(k)} ')

    question_var = get_root(question_var)

    for i in range(len(clauses)):
        clauses[i] = clauses[i].replace(f'?x{question_var} ', f'?x ')

    if superlative:
        arg_clauses = clauses[:]

    for entity in entities:
        clauses.append(f'FILTER (?x != <{entity}>)')
    clauses.insert(0, "WHERE {")
    if count:
        # clauses.insert(0, f"SELECT COUNT DISTINCT ?x")
        clauses.insert(0, f"SELECT (COUNT(DISTINCT ?x) AS ?count)")
    elif superlative:
        clauses.insert(0, "{SELECT ?sk0")
        clauses = arg_clauses + clauses
        clauses.insert(0, "WHERE {")
        clauses.insert(0, f"SELECT DISTINCT ?x")
    else:
        clauses.insert(0, f"SELECT DISTINCT ?x")

    clauses.append('}')
    clauses.extend(order_clauses)
    if superlative:
        clauses.append('}')
        clauses.append('}')

    # for clause in clauses:
    #     print(clause)

    return '\n'.join(clauses)


class PPODEnv(Env):
    def __init__(self, relations: set, classes: set, relations_to_entity=None, relations_to_literal=None, use_kg_api=False):
        """

        :param relations:
        :param classes:
        :param relations_to_entity: a part of relations that is connected to entities
        :param relations_to_literal: a part of relations that is connected to literals
        """
        super().__init__()
        if use_kg_api:
            self.cache = QueryAPI()
        else:
            self.cache = PPODSparqlService()
        self.relations = relations - {'http://www.w3.org/1999/02/22-rdf-syntax-ns#type', 'http://www.w3.org/2000/01/rdf-schema#label',
                                      'http://www.w3.org/2004/02/skos/core#altLabel', 'http://purl.org/dc/terms/title', 'http://schema.org/identifier',
                                      'http://poderopedia.com/vocab/hasURL'}
        self.relations_inv = set([r + '_inv' for r in self.relations])
        self.classes = classes

        if relations_to_entity is None:
            self.properties = self.relations.union(self.relations_inv)
        else:
            p_inv = set([r + '_inv' for r in relations_to_entity])
            self.properties = relations_to_entity.union(p_inv)

        self.literal_properties = set()
        if relations_to_literal is not None:
            self.literal_properties = relations_to_literal

    def step(self, action: str):
        """
        Interact with the KB to get possible expansions for a given subprogram
        :param action: simply a subprogram
        :return: admissible classes and relations from this subprogram
        """
        if action[0] == '(' and action[-1] == ')':  # for subprogram
            sparql_query = lisp_to_sparql(action)
            clauses = sparql_query.split("\n")

            # query relations
            relations = set()  # in and out relations
            new_clauses = ["SELECT DISTINCT ?rel\nWHERE {\n?sub ?rel ?x .\n{"]
            new_clauses.extend(clauses)
            new_clauses.append("}\n}")
            new_query = '\n'.join(new_clauses)
            try:
                rows = self.execute_SPARQL(new_query)
            except Exception as e:
                print('in_relation query exception:', e)
                print('action:', action)
                print(new_query)
            else:
                in_relations = [r[0] for r in rows]
                relations = set(in_relations)

            # query inverse relations
            new_clauses = ["SELECT DISTINCT ?rel\nWHERE {\n?x ?rel ?obj .\n{"]
            new_clauses.extend(clauses)
            new_clauses.append("}\n}")
            new_query = '\n'.join(new_clauses)
            try:
                rows = self.execute_SPARQL(new_query)
            except Exception as e:
                print('out_relation query exception:', e)
                print('action:', action)
                print(new_query)
            else:
                out_relations = [r[0] for r in rows]
                out_relations = [r + '_inv' for r in out_relations]
                relations = relations.union(set(out_relations))

            # query classes
            new_clauses = ["SELECT DISTINCT ?cls\nWHERE {\n?x a ?cls .\n{"]
            new_clauses.extend(clauses)
            new_clauses.append("}\n}")
            new_query = '\n'.join(new_clauses)
            try:
                rows = self.execute_SPARQL(new_query)
                classes = set([r[0] for r in rows])
            except Exception as e:
                print('class query Exception:', e)
                print('action:', action)
                print(new_query)
                classes = set()
        else:
            if is_entity(action):
                in_relations = self.cache.get_entity_in_relations(action)
                out_relations = self.cache.get_entity_out_relations(action)
                out_relations = [r + '_inv' for r in out_relations]
                relations = set(in_relations).union(set(out_relations))
                classes = set()
            else:
                in_relations = self.cache.get_literal_in_relations(action)
                relations = set(in_relations)
                classes = set()

        # return {"relations": relations, "classes": classes}
        self.cache.save_cache(self.cache.cache_path)
        return {"Property": relations.intersection(self.properties), "Classes": classes.intersection(self.classes),
                "LiteralProperty": self.literal_properties}

    def execute_SPARQL(self, sparql_query):
        try:
            rtn = self.cache.get_sparql_execution(sparql_query)
            return set(tuple(item) if isinstance(item, list) else item for item in rtn)
        except Exception as e:
            print('execute_SPARQL:', e)
            return set()
