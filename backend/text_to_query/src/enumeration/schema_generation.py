import sys

sys.path.append('src')
sys.path.append('.')
from pangu.ppod_agent import lisp_to_label

import copy
import json
import random
from collections import defaultdict

import igraph as ig
from tqdm import tqdm

from src.enumeration.graph_query import add_node, add_edge, clone_graph_query, get_relations, get_entity_label_list, is_terminal_node, is_question_node
from src.enumeration.logical_form_util import get_lisp_from_graph_query
from pangu.environment.examples.KB.PPODSparqlCache import execute_query
from pangu.environment.examples.KB.ppod_environment import lisp_to_sparql

relation_black_list = {'http://www.w3.org/2000/01/rdf-schema#label', 'http://www.w3.org/1999/02/22-rdf-syntax-ns#type', 'http://schema.org/identifier',
                       'http://purl.org/dc/terms/title'}
cvt_nodes = {'http://purl.obolibrary.org/obo/BFO_0000023'}
entity_black_list = {'https://raw.githubusercontent.com/adhollander/FSLschemas/main/fsisupp.owl#Container'}
numerical_relations = {'http://purl.org/dc/terms/date', 'http://dbpedia.org/ontology/startYear', 'http://dbpedia.org/ontology/endYear'}
function_map = {'le': '<=', 'lt': '<', 'ge': '>=', 'gt': '>', 'ARGMIN': 'argmin', 'ARGMAX': 'argmax', 'COUNT': 'count'}
function_probability = {'le': 0.05, 'lt': 0.05, 'ge': 0.05, 'gt': 0.05, 'ARGMIN': 0.1, 'ARGMAX': 0.1}


def simplify_with_prefixes(lisp: str, prefixes: dict):
    for prefix in prefixes:
        full = prefixes[prefix]
        lisp = lisp.replace(full, f"{prefix}:")
    return lisp


def replace_inv_relations(lisp: str, inv_label: dict):
    for inv in inv_label:
        lisp = lisp.replace(inv, inv_label[inv])
    return lisp


def lisp_to_repr(lisp, prefixes, inv_label):
    lisp = lisp_to_label(lisp)
    if prefixes:
        lisp = simplify_with_prefixes(lisp, prefixes)
    if inv_label:
        lisp = replace_inv_relations(lisp, inv_label)
    return lisp


def graph_query_to_sparql(graph_query: dict):
    clauses = ['SELECT DISTINCT ', 'WHERE {']

    # find question node first
    # for nid in range(len(graph_query['nodes'])):
    #     if graph_query['nodes'][nid]['question_node'] == 1:
    #         clauses[0] += '?n' + str(nid) + ' '
    #         # maybe extend to queries with multiple question nodes

    for nid in range(len(graph_query['nodes'])):
        clauses[0] += '?n' + str(nid) + ' '
        node = graph_query['nodes'][nid]
        if node['node_type'] == 'class':
            clauses.append(f"?n{nid} a <{node['id']}> . ")
        elif node['node_type'] == 'entity':
            clauses.append(f"?n{nid} <http://schema.org/identifier> <{node['id']}> . ")
        elif node['node_type'] == 'literal' and node['friendly_name'] is not None:
            clauses.append(f"?n{nid} rdfs:label \"{node['friendly_name']}\" . ")

    for edge in graph_query['edges']:
        clauses.append(f"?n{edge['start']} <{edge['relation']}> ?n{edge['end']} . ")

    return ' '.join(clauses) + '}'


def sample_connected_subgraph(graph, start_vertex, min_edges=1, max_edges=4):
    if graph.ecount() == 0 or max_edges < min_edges:
        return None

    visited_vertices = {start_vertex}
    visited_edges = set()

    while len(visited_edges) < max_edges:
        # get current out edges
        edges = [e.index for e in graph.es.select(_source=start_vertex) if e.index not in visited_edges]
        if not edges:
            break  # no more edges to explore

        # choose a random edge
        # numerical_relations_id = [graph.es[e].index for e in range(len(graph.es)) if graph.es[e]['label'] in numerical_relations]
        chosen_edge = random.choice(edges)
        visited_edges.add(chosen_edge)

        # if the next vertex is not literal, move to the next vertex; if it is literal, stay at the current vertex and continue to explore
        if graph.es[chosen_edge].target == 'literal':
            continue

        edge_data = graph.es[chosen_edge]
        next_vertex = edge_data.target
        if next_vertex == start_vertex:
            next_vertex = edge_data.source
        visited_vertices.add(next_vertex)

        # update start vertex
        start_vertex = next_vertex

    if min_edges <= len(visited_edges) <= max_edges:
        subgraph_vertices = list(visited_vertices)
        return graph.subgraph_edges(visited_edges, delete_vertices=True)
    else:
        return None


if __name__ == '__main__':
    random.seed(1)
    types = json.load(open('data/types.json', 'r'))

    schema_graph = defaultdict(dict)
    entity_to_label = json.load(open('data/entity_to_label.json', 'r'))
    predicate_to_label = json.load(open('data/predicate_to_label.json', 'r'))

    num_edge = 0
    for i in range(len(types)):
        for j in range(len(types)):
            t1 = types[i]
            t2 = types[j]
            if t1 in entity_black_list or t2 in entity_black_list:
                continue

            # detect all relations between t1 and t2
            sparql = "select distinct ?r where { ?s a <" + t1 + "> . ?o a <" + t2 + "> . ?s ?r ?o . }"
            results = execute_query(sparql)
            for r in results:
                num_edge += 1
                # print(t1, r[0], t2)
                if r[0] in relation_black_list:
                    continue
                schema_graph[t1][r[0]] = schema_graph[t1].get(r[0], set())
                schema_graph[t1][r[0]].add(t2)

        sparql = "select distinct ?r where { ?s a <" + types[i] + "> . ?s ?r ?o . }"
        relations = execute_query(sparql)
        for relation in relations:
            r = relation[0]
            if r in relation_black_list:
                continue
            if r in schema_graph[types[i]]:
                continue
            schema_graph[types[i]][r] = ['literal']

    # converting set to list
    for t in schema_graph:
        for r in schema_graph[t]:
            schema_graph[t][r] = list(schema_graph[t][r])
    print()
    print('num_edge:', num_edge)
    with open('exp/schema_graph.json', 'w') as f:
        json.dump(schema_graph, f, indent=4)

    # store schema graph as igraph
    g = ig.Graph(directed=True)
    g.add_vertex(name='literal')
    for t in schema_graph:
        g.add_vertex(name=t)
    for t in schema_graph:
        for r in schema_graph[t]:
            for t2 in schema_graph[t][r]:
                g.add_edge(t, t2, label=r)
    # print(g)

    # sample connected subgraph with up to 4 edges
    sampled_subgraphs = set()
    sampled_subgraph_list = []
    for vertex_id in range(len(g.vs)):  # start from each vertex
        vertex_name = g.vs[vertex_id]['name']
        if vertex_name == 'literal' or vertex_name in cvt_nodes:
            continue
        for num_edge in range(1, 5):  # the number of edges
            for _ in range(0, int(100)):  # sample multiple subgraphs
                sampled_subgraph = sample_connected_subgraph(g, vertex_id, 1, num_edge)
                question_node_class = g.vs[vertex_id]['name']
                friend_name = entity_to_label.get(question_node_class, None)
                graph_query = {'nodes': [], 'edges': []}
                # add node
                for i in range(len(sampled_subgraph.vs)):
                    entity_name = sampled_subgraph.vs[i]['name']
                    node_type = 'class' if entity_name != 'literal' else 'literal'
                    kb_class = entity_name if entity_name != 'literal' else None
                    friend_name = entity_to_label.get(entity_name, None)
                    id = sampled_subgraph.vs[i]['name']
                    add_node(graph_query, id, kb_class, friend_name, node_type, 0, 'none')
                # add edge
                for i in range(len(sampled_subgraph.es)):
                    edge = sampled_subgraph.es[i]
                    add_edge(graph_query, edge.source, edge.target, edge['label'], predicate_to_label.get(edge['label']))
                # check if any edge starts and ends with the same node, if so, clone this node and take it as the new end
                for edge in graph_query['edges']:
                    if edge['start'] == edge['end']:
                        new_node = copy.deepcopy(graph_query['nodes'][edge['end']])
                        new_node['nid'] = len(graph_query['nodes'])
                        graph_query['nodes'].append(new_node)
                        edge['end'] = new_node['nid']

                # store graph query
                graph_query_repr = json.dumps(graph_query, indent=4, sort_keys=True)
                if graph_query_repr not in sampled_subgraphs:
                    sampled_subgraphs.add(graph_query_repr)
                    sampled_subgraph_list.append(graph_query)

    print('num sampled subgraphs:', len(sampled_subgraphs))
    with open('exp/sample_subgraphs.json', 'w') as f:
        json.dump(sampled_subgraph_list, f, indent=4)
    print('done')

    num_valid = 0
    num_total = 0
    results = []
    for graph_query in tqdm(sampled_subgraph_list):
        num_total += 1
        value_filling_sparql = graph_query_to_sparql(graph_query)

        rows = execute_query(value_filling_sparql)
        if len(rows) == 0:
            print('SPARQL no result:', value_filling_sparql)

        else:
            num_valid += 1
            for row in rows[:100]:
                new_graph_query = clone_graph_query(graph_query)
                for i in range(len(row)):  # for each node, fill the value
                    new_graph_query['nodes'][i]['id'] = row[i]
                    new_graph_query['nodes'][i]['node_type'] = 'entity' if row[i] in entity_to_label else 'literal'
                    if new_graph_query['nodes'][i]['node_type'] == 'entity':
                        new_graph_query['nodes'][i]['friendly_name'] = entity_to_label.get(row[i], None)
                for nid in range(len(new_graph_query['nodes'])):  # for each node, try to turn it into a question node and get a query
                    if new_graph_query['nodes'][nid]['node_type'] == 'literal':  # skip literal as question node
                        continue
                    if new_graph_query['nodes'][nid]['class'] is None:  # skip if the class is None
                        continue
                    new_question_graph_query = clone_graph_query(new_graph_query)
                    # set question node
                    new_question_graph_query['nodes'][nid]['question_node'] = 1
                    new_question_graph_query['nodes'][nid]['id'] = new_question_graph_query['nodes'][nid]['class']
                    new_question_graph_query['nodes'][nid]['friendly_name'] = None
                    new_question_graph_query['nodes'][nid]['node_type'] = 'class'
                    # set non-terminal node
                    for nid1 in range(len(new_question_graph_query['nodes'])):
                        if not is_terminal_node(new_question_graph_query, nid1) and not is_question_node(new_question_graph_query, nid1):
                            # if this non-terminal is an entity, set it to a class
                            if new_question_graph_query['nodes'][nid1]['node_type'] == 'entity':
                                new_question_graph_query['nodes'][nid1]['node_type'] = 'class'
                                new_question_graph_query['nodes'][nid1]['friendly_name'] = None
                                new_question_graph_query['nodes'][nid1]['id'] = new_question_graph_query['nodes'][nid1]['class']

                    lisp = get_lisp_from_graph_query(new_question_graph_query)
                    try:
                        sparql = lisp_to_sparql(lisp)
                    except Exception as e:
                        print('lisp to SPARQL exception', e, lisp)
                        continue

                    question_rows = execute_query(sparql)
                    if len(question_rows) == 0:
                        print('invalid:', lisp)
                    num_entity = len(get_entity_label_list(new_question_graph_query))
                    graph_relations = get_relations(new_question_graph_query)
                    num_relation = len(graph_relations)
                    numerical = True if len(graph_relations.intersection(numerical_relations)) > 0 else False
                    if len(question_rows):
                        results.append({'s-expression': lisp, 'sparql': sparql, 'graph_query': new_question_graph_query,
                                        'num_entity': num_entity, 'num_relation': num_relation, 'numerical': numerical, '#results': len(question_rows)})
                    #     print('valid:', lisp)
        print('Collected queries', len(results))

    print('num_valid:', num_valid, 'num_total:', num_total, 'valid ratio:', num_valid / num_total)

    # add function to some samples
    functions = ['ARGMIN', 'ARGMAX', 'COUNT', 'le', 'lt', 'ge', 'gt']
    for function in functions:
        if function == 'COUNT':
            func_samples = random.sample(results, int(0.1 * len(results)))
            for sample in tqdm(func_samples, desc='collecting COUNT queries'):
                new_sample = copy.deepcopy(sample)
                # find question node and set function for it
                for nid in range(len(new_sample['graph_query']['nodes'])):
                    if new_sample['graph_query']['nodes'][nid]['question_node'] == 1:
                        new_sample['graph_query']['nodes'][nid]['function'] = function_map[function]
                        # break  # may consider multiple question nodes
                new_sample['s-expression'] = get_lisp_from_graph_query(new_sample['graph_query'])
                new_sample['sparql'] = lisp_to_sparql(new_sample['s-expression'])
                new_sample['function'] = function
                rows = execute_query(new_sample['sparql'])
                if rows[0][0] != '0':
                    new_sample['#results'] = len(rows)
                    new_sample['answer'] = rows[0][0]
                    results.append(new_sample)
                else:
                    print('invalid:', new_sample['s-expression'])
        elif function in ['le', 'lt', 'ge', 'gt', 'ARGMIN', 'ARGMAX']:
            for sample in tqdm(results, desc=f'collecting {function} queries'):
                sample_relations = get_relations(sample['graph_query'])
                if len(set(sample_relations).intersection(numerical_relations)) == 0:
                    continue
                # take 5% chance to add function
                if random.random() > function_probability[function]:
                    continue
                new_sample = copy.deepcopy(sample)
                # find literal node (with a numerical relation) and set function for it
                for nid in range(len(new_sample['graph_query']['nodes'])):
                    if new_sample['graph_query']['nodes'][nid]['node_type'] == 'literal':
                        # find if there is a numerical relation
                        is_numerical = False
                        for edge in new_sample['graph_query']['edges']:
                            if nid in [edge['start'], edge['end']] and edge['relation'] in numerical_relations:
                                new_sample['graph_query']['nodes'][nid]['function'] = function_map[function]
                                is_numerical = True
                                break
                        if is_numerical:
                            new_sample['s-expression'] = get_lisp_from_graph_query(new_sample['graph_query'])
                            new_sample['sparql'] = lisp_to_sparql(new_sample['s-expression'])
                            new_sample['function'] = function
                            rows = execute_query(new_sample['sparql'])
                            if len(rows):
                                results.append(new_sample)
                            else:
                                print('invalid:', new_sample['s-expression'])

    # simplify the sampled queries using prefixes
    prefixes = json.load(open('data/prefix.json', 'r'))
    for sample in results:
        sample['s-expression_simplified'] = simplify_with_prefixes(sample['s-expression'], prefixes)
        sample['s-expression_str'] = lisp_to_label(sample['s-expression_simplified'])
    output_path = 'exp/sample_queries.json'
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=4)
    print('Saved', len(results), f'queries to {output_path}')
