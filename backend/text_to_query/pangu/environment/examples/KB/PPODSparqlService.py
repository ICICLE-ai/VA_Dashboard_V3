import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.absolute()) + '/../../../../../..')

import json
import os.path
from typing import List
import logging

from backend.milkOligoDB.src.api_client import get_adjacent_relations_by_object, get_adjacent_relations_by_subject

proj_root = os.path.dirname(os.path.abspath(__file__)) + '/../../../../'
from rdflib import Graph
from rdflib.plugins.sparql.processor import SPARQLResult

rdf_file_path = os.path.join(proj_root, 'data/PPOD_CA.ttl')
g = Graph()
with open(rdf_file_path, "r") as f:
    ttl = f.read()
g.parse(data=ttl, format="ttl", publicID='http:/')


def execute_query(query: str, endpoint='https://jupyter002-second.pods.tacc.develop.tapis.io/sparql'):
    if endpoint == 'rdflib':
        return execute_query_with_rdflib(query)
    return execute_query_with_virtuoso(query, endpoint)


def execute_query_with_rdflib(query: str) -> List[str]:
    try:
        result = g.query(query)
    except Exception as e:
        print(f"Failed to execute query: {query}")
        print(e)
        return []
    else:
        if isinstance(result, SPARQLResult):
            res = []
            for row in result:
                res.append(tuple([str(item) for item in row]))
            return res
        return list(result)


def execute_query_with_virtuoso(query: str, endpoint='https://jupyter002-second.pods.tacc.develop.tapis.io/sparql'):
    """
    Using SPARQLWrapper to execute the query
    :param query:
    :param endpoint:
    :return:
    """
    from SPARQLWrapper import SPARQLWrapper, JSON
    sparql = SPARQLWrapper(endpoint)
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    response = sparql.query().convert()
    rows = []
    for result in response["results"]["bindings"]:
        cur_row = []
        skip = False  # skip the results from openlinksw
        for key in result:
            if result[key]["value"].startswith('http://www.openlinksw.com/') or result[key]["value"].startswith("http://localuriqaserver"):
                skip = True
                break
            cur_row.append(result[key]["value"])
        if not skip:
            rows.append(tuple(cur_row))
    return rows


class PPODSparqlService:

    def __init__(self, cache_path: str = os.path.join(proj_root, 'data/ppod_cache.json')):
        self.cache_path = cache_path
        if os.path.isfile(cache_path):
            print(f"Loading cache from {cache_path}")
            self.load_cache(cache_path)
        else:
            print(f"Cache file {cache_path} not found, creating a new one")
            self.cache = {"types": {}, "in_relations": {}, "out_relations": {}, "in_entities": {},
                          "out_entities": {},
                          "cmp_entities": {},
                          "is_reachable": {},
                          "is_intersectant": {},
                          "sparql_execution": {}}

    def get_sparql_execution(self, sparql_query: str):
        try:
            if sparql_query not in self.cache["sparql_execution"]:
                rows = execute_query(sparql_query)
                self.cache["sparql_execution"][sparql_query] = rows
            return self.cache["sparql_execution"][sparql_query]
        except Exception as e:
            print(f"get_sparql_execution: {sparql_query}")
            print(e)
            return []

    def get_entity_in_relations(self, entity: str):
        if entity not in self.cache["in_relations"]:
            rows = execute_query(f"SELECT DISTINCT ?p WHERE {{ ?s ?p <{entity}> }}")
            self.cache["in_relations"][entity] = [row[0] for row in rows]
        return self.cache["in_relations"][entity]

    def get_literal_in_relations(self, literal: str):
        if len(literal) > 50:
            return []
        if literal not in self.cache["in_relations"]:
            rows = execute_query(f"SELECT DISTINCT ?p WHERE {{ ?s ?p \"{literal}\" }}")
            self.cache["in_relations"][literal] = [row[0] for row in rows]
        return self.cache["in_relations"][literal]

    def get_entity_out_relations(self, entity: str):
        if entity not in self.cache["out_relations"]:
            rows = execute_query(f"SELECT DISTINCT ?p WHERE {{ <{entity}> ?p ?o }}")
            self.cache["out_relations"][entity] = [row[0] for row in rows]
        return self.cache["out_relations"][entity]

    def load_cache(self, path: str):
        with open(path, 'r') as f:
            self.cache = json.load(f)

    def save_cache(self, path: str):
        try:
            # Ensure the directory exists
            os.makedirs(os.path.dirname(path), exist_ok=True)

            # Use an absolute path for the temporary file
            temp_file_path = os.path.abspath(os.path.join(os.path.dirname(path), 'ppod_cache_temp.json'))

            # Write to the temporary file
            logging.info(f"Writing to temporary file: {temp_file_path}")
            with open(temp_file_path, 'w') as f:
                json.dump(self.cache, f)

            # Check if the temporary file was created successfully
            if os.path.isfile(temp_file_path):
                # Try to replace the existing file (if it exists) with the new one
                logging.info(f"Replacing {path} with {temp_file_path}")
                os.replace(temp_file_path, path)
                logging.info("Cache saved successfully")
            else:
                raise FileNotFoundError(f"Temporary file {temp_file_path} was not created")

        except Exception as e:
            logging.error(f"Error saving cache: {str(e)}")
            # If an error occurs, try to remove the temporary file
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
            raise


class QueryAPI(PPODSparqlService):
    def __init__(self):
        super().__init__()

    def get_entity_in_relations(self, entity: str):
        return get_adjacent_relations_by_object(entity)

    def get_literal_in_relations(self, literal: str):
        return get_adjacent_relations_by_object(literal)

    def get_entity_out_relations(self, entity: str):
        return get_adjacent_relations_by_subject(entity)


if __name__ == '__main__':
    sparql = 'SELECT ?s WHERE { ?s ?p ?o } LIMIT 300'
    results = execute_query(sparql)
    print(results)
    print(len(results))

    results = execute_query(sparql)
    print(results)
    print(len(results))

    # Who are the owners of organizations that work on fragmentation in the Great Valley ecoregion?
    sparql = """
    select ?node_variable_2 where
{ ?node_variable_1 rdf:type foaf:Organization ;
                   <https://raw.githubusercontent.com/adhollander/FSLschemas/main/fsisupp.owl#inEcoregion> <https://raw.githubusercontent.com/adhollander/FSLschemas/main/CA_PPODterms.ttl#eco_7dfa16> ;
                   <https://raw.githubusercontent.com/adhollander/FSLschemas/main/fsisupp.owl#FSI_000239> <https://raw.githubusercontent.com/adhollander/FSLschemas/main/sustsourceindiv.rdf#CI0167> .
  ?node_variable_2 rdf:type foaf:Person .
  ?node_variable_3 rdf:type <http://purl.obolibrary.org/obo/BFO_0000023> ;
                   <http://purl.obolibrary.org/obo/RO_0000057> ?node_variable_2 ;
                   <http://purl.obolibrary.org/obo/RO_0000081> ?node_variable_1 ;
                   <https://raw.githubusercontent.com/adhollander/FSLschemas/main/fsisupp.owl#positionType> <https://raw.githubusercontent.com/adhollander/FSLschemas/main/CA_PPODterms.ttl#positiontypedict_ea1c97> . }

limit 32"""
    results = execute_query_with_rdflib(sparql)
    print(results)
    print(len(results))

    results = execute_query(sparql)
    print(results)
    print(len(results))
