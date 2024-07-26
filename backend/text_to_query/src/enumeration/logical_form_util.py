import networkx as nx
from typing import List, Union
from collections import defaultdict
from pathlib import Path

REVERSE = True  # if REVERSE, then reverse relations are also taken into account for semantic EM

path = str(Path(__file__).parent.absolute())

function_map = {'le': '<=', 'ge': '>=', 'lt': '<', 'gt': '>'}


def lisp_to_nested_expression(lisp_string):
    """
    Takes a logical form as a lisp string and returns a nested list representation of the lisp.
    For example, "(count (division first))" would get mapped to ['count', ['division', 'first']].
    """
    stack: List = []
    current_expression: List = []
    tokens = lisp_string.split()
    for token in tokens:
        while token[0] == '(':
            nested_expression: List = []
            current_expression.append(nested_expression)
            stack.append(current_expression)
            current_expression = nested_expression
            token = token[1:]
        current_expression.append(token.replace(')', ''))
        while token[-1] == ')':
            current_expression = stack.pop()
            token = token[:-1]
    return current_expression[0]


def get_symbol_type(symbol: str) -> int:
    if symbol.__contains__('^^'):
        return 2
    elif symbol in types:
        return 3
    elif symbol in relations:
        return 4
    elif symbol:
        return 1


def same_logical_form(form1: str, form2: str) -> bool:
    if form1.__contains__("@@UNKNOWN@@") or form2.__contains__("@@UNKNOWN@@"):
        return False
    try:
        G1 = logical_form_to_graph(lisp_to_nested_expression(form1))
    except Exception:
        return False
    try:
        G2 = logical_form_to_graph(lisp_to_nested_expression(form2))
    except Exception:
        return False

    def node_match(n1, n2):
        if n1['id'] == n2['id'] and n1['type'] == n2['type']:
            func1 = n1.pop('function', 'none')
            func2 = n2.pop('function', 'none')
            tc1 = n1.pop('tc', 'none')
            tc2 = n2.pop('tc', 'none')

            if func1 == func2 and tc1 == tc2:
                return True
            else:
                return False
            # if 'function' in n1 and 'function' in n2 and n1['function'] == n2['function']:
            #     return True
            # elif 'function' not in n1 and 'function' not in n2:
            #     return True
            # else:
            #     return False
        else:
            return False

    def multi_edge_match(e1, e2):
        if len(e1) != len(e2):
            return False
        values1 = []
        values2 = []
        for v in e1.values():
            values1.append(v['relation'])
        for v in e2.values():
            values2.append(v['relation'])
        return sorted(values1) == sorted(values2)

    return nx.is_isomorphic(G1, G2, node_match=node_match, edge_match=multi_edge_match)


def logical_form_to_graph(expression: List) -> nx.MultiGraph:
    G = _get_graph(expression)
    G.nodes[len(G.nodes())]['question_node'] = 1
    return G


def _get_graph(
        expression: List) -> nx.MultiGraph:  # The id of question node is always the same as the size of the graph
    if isinstance(expression, str):
        G = nx.MultiDiGraph()
        if get_symbol_type(expression) == 1:
            G.add_node(1, id=expression, type='entity')
        elif get_symbol_type(expression) == 2:
            G.add_node(1, id=expression, type='literal')
        elif get_symbol_type(expression) == 3:
            G.add_node(1, id=expression, type='class')
            # G.add_node(1, id="common.topic", type='class')
        elif get_symbol_type(expression) == 4:  # relation or attribute
            domain, rang = relation_dr[expression]
            G.add_node(1, id=rang, type='class')  # if it's an attribute, the type will be changed to literal in arg
            G.add_node(2, id=domain, type='class')
            G.add_edge(2, 1, relation=expression)

            if REVERSE:
                if expression in reverse_properties:
                    G.add_edge(1, 2, relation=reverse_properties[expression])

        return G

    if expression[0] == 'R':
        G = _get_graph(expression[1])
        size = len(G.nodes())
        mapping = {}
        for n in G.nodes():
            mapping[n] = size - n + 1
        G = nx.relabel_nodes(G, mapping)
        return G

    elif expression[0] in ['JOIN', 'le', 'ge', 'lt', 'gt']:
        G1 = _get_graph(expression=expression[1])
        G2 = _get_graph(expression=expression[2])

        size = len(G2.nodes())
        qn_id = size
        if G1.nodes[1]['type'] == G2.nodes[qn_id]['type'] == 'class':
            if G2.nodes[qn_id]['id'] in upper_types[G1.nodes[1]['id']]:
                G2.nodes[qn_id]['id'] = G1.nodes[1]['id']
            # G2.nodes[qn_id]['id'] = G1.nodes[1]['id']
        mapping = {}
        for n in G1.nodes():
            mapping[n] = n + size - 1
        G1 = nx.relabel_nodes(G1, mapping)
        G = nx.compose(G1, G2)

        if expression[0] != 'JOIN':
            G.nodes[1]['function'] = function_map[expression[0]]

        return G

    elif expression[0] == 'AND':
        G1 = _get_graph(expression[1])
        G2 = _get_graph(expression[2])

        size1 = len(G1.nodes())
        size2 = len(G2.nodes())
        if G1.nodes[size1]['type'] == G2.nodes[size2]['type'] == 'class':
            # if G2.nodes[size2]['id'] in upper_types[G1.nodes[size1]['id']]:
            G2.nodes[size2]['id'] = G1.nodes[size1]['id']
            # IIRC, in nx.compose, for the same node, its information can be overwritten by its info in the second graph
            # So here for the AND function we force it to choose the type explicitly provided in the logical form
        mapping = {}
        for n in G1.nodes():
            mapping[n] = n + size2 - 1
        G1 = nx.relabel_nodes(G1, mapping)
        G2 = nx.relabel_nodes(G2, {size2: size1 + size2 - 1})
        G = nx.compose(G1, G2)

        return G

    elif expression[0] == 'COUNT':
        G = _get_graph(expression[1])
        size = len(G.nodes())
        G.nodes[size]['function'] = 'count'

        return G

    elif expression[0].__contains__('ARG'):
        G1 = _get_graph(expression[1])
        size1 = len(G1.nodes())
        G2 = _get_graph(expression[2])
        size2 = len(G2.nodes())
        # G2.nodes[1]['class'] = G2.nodes[1]['id']   # not sure whether this is needed for sparql
        G2.nodes[1]['id'] = 0
        G2.nodes[1]['type'] = 'literal'
        G2.nodes[1]['function'] = expression[0].lower()
        if G1.nodes[size1]['type'] == G2.nodes[size2]['type'] == 'class':
            # if G2.nodes[size2]['id'] in upper_types[G1.nodes[size1]['id']]:
            G2.nodes[size2]['id'] = G1.nodes[size1]['id']

        mapping = {}
        for n in G1.nodes():
            mapping[n] = n + size2 - 1
        G1 = nx.relabel_nodes(G1, mapping)
        G2 = nx.relabel_nodes(G2, {size2: size1 + size2 - 1})
        G = nx.compose(G1, G2)

        return G

    elif expression[0] == 'TC':
        G = _get_graph(expression[1])
        size = len(G.nodes())
        G.nodes[size]['tc'] = (expression[2], expression[3])

        return G


def graph_to_logical_form(G, start, count: bool = False):
    if count:
        return '(COUNT ' + none_function(G, start) + ')'
    else:
        return none_function(G, start)


def get_end_num(G, s):
    end_num = defaultdict(lambda: 0)
    for edge in list(G.edges(s)):  # for directed graph G.edges is the same as G.out_edges, not including G.in_edges
        end_num[list(edge)[1]] += 1
    return end_num


def set_visited(G, s, e, relation):
    end_num = get_end_num(G, s)
    for i in range(0, end_num[e]):
        if G.edges[s, e, i]['relation'] == relation:
            G.edges[s, e, i]['visited'] = True


def binary_nesting(function: str, elements: List[str], types_along_path=None) -> str:
    if len(elements) < 2:
        print("error: binary function should have 2 parameters!")
    if not types_along_path:
        if len(elements) == 2:
            return '(' + function + ' ' + elements[0] + ' ' + elements[1] + ')'
        else:
            return '(' + function + ' ' + elements[0] + ' ' + binary_nesting(function, elements[1:]) + ')'
    else:
        if len(elements) == 2:
            return '(' + function + ' ' + types_along_path[0] + ' ' + elements[0] + ' ' + elements[1] + ')'
        else:
            return '(' + function + ' ' + types_along_path[0] + ' ' + elements[0] + ' ' \
                + binary_nesting(function, elements[1:], types_along_path[1:]) + ')'


def count_function(G, start):
    return '(COUNT ' + none_function(G, start) + ')'


def none_function(G, start, arg_node=None, type_constraint=True):
    if arg_node is not None:
        arg = G.nodes[arg_node]['function']
        path = list(nx.all_simple_paths(G, start, arg_node))
        assert len(path) == 1
        arg_clause = []
        for i in range(0, len(path[0]) - 1):
            edge = G.edges[path[0][i], path[0][i + 1], 0]
            if edge['reverse']:
                relation = '(R ' + edge['relation'] + ')'
            else:
                relation = edge['relation']
            arg_clause.append(relation)

        # Deleting edges until the first node with out degree > 2 is meet
        # (conceptually it should be 1, but remember that add edges is both directions)
        while i >= 0:
            flag = False
            if G.out_degree[path[0][i]] > 2:
                flag = True
            G.remove_edge(path[0][i], path[0][i + 1], 0)
            i -= 1
            if flag:
                break

        if len(arg_clause) > 1:
            arg_clause = binary_nesting(function='JOIN', elements=arg_clause)
            # arg_clause = ' '.join(arg_clause)
        else:
            arg_clause = arg_clause[0]

        return '(' + arg.upper() + ' ' + none_function(G, start) + ' ' + arg_clause + ')'

    # arg = -1
    # for nei in G[start]:
    #     if G.nodes[nei]['function'].__contains__('arg'):
    #         arg = nei
    #         arg_function = G.nodes[nei]['function']
    # if arg != -1:
    #     edge = G.edges[start, arg, 0]
    #     if edge['reverse']:
    #         relation = '(R ' + edge['relation'] + ')'
    #     else:
    #         relation = edge['relation']
    #     G.remove_edge(start, arg, 0)
    #     return '(' + arg_function.upper() + ' ' + none_function(G, start) + ' ' + relation + ')'

    if G.nodes[start]['type'] != 'class':
        return G.nodes[start]['id']

    end_num = get_end_num(G, start)
    clauses = []

    if G.nodes[start]['question'] and type_constraint:
        clauses.append(G.nodes[start]['id'])
    for key in end_num.keys():
        for i in range(0, end_num[key]):
            if not G.edges[start, key, i]['visited']:
                relation = G.edges[start, key, i]['relation']
                G.edges[start, key, i]['visited'] = True
                set_visited(G, key, start, relation)
                if G.edges[start, key, i]['reverse']:
                    relation = '(R ' + relation + ')'
                if G.nodes[key]['function'].__contains__('<') or G.nodes[key]['function'].__contains__('>'):
                    if G.nodes[key]['function'] == '>':
                        clauses.append('(gt ' + relation + ' ' + none_function(G, key) + ')')
                    if G.nodes[key]['function'] == '>=':
                        clauses.append('(ge ' + relation + ' ' + none_function(G, key) + ')')
                    if G.nodes[key]['function'] == '<':
                        clauses.append('(lt ' + relation + ' ' + none_function(G, key) + ')')
                    if G.nodes[key]['function'] == '<=':
                        clauses.append('(le ' + relation + ' ' + none_function(G, key) + ')')
                else:
                    clauses.append('(JOIN ' + relation + ' ' + none_function(G, key) + ')')

    if len(clauses) == 0:
        return G.nodes[start]['id']

    if len(clauses) == 1:
        return clauses[0]
    else:
        return binary_nesting(function='AND', elements=clauses)


def get_lisp_from_graph_query(graph_query):
    G = nx.MultiDiGraph()
    aggregation = 'none'
    arg_node = None
    for node in graph_query['nodes']:
        #         G.add_node(node['nid'], id=node['id'].replace('.', '/'), type=node['node_type'], question=node['question_node'], function=node['function'])
        G.add_node(node['nid'], id=node['id'], type=node['node_type'], question=node['question_node'],
                   function=node['function'], cla=node['class'])
        if node['question_node'] == 1:
            qid = node['nid']
        if node['function'] != 'none':
            aggregation = node['function']
            if node['function'].__contains__('arg'):
                arg_node = node['nid']
    for edge in graph_query['edges']:
        G.add_edge(edge['start'], edge['end'], relation=edge['relation'], reverse=False, visited=False)
        G.add_edge(edge['end'], edge['start'], relation=edge['relation'], reverse=True, visited=False)
    if 'count' == aggregation:
        # print(count_function(G, qid))
        return count_function(G, qid)
    else:
        # print(none_function(G, qid))
        return none_function(G, qid, arg_node=arg_node)
