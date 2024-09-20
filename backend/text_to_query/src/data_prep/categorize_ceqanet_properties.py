import json

from pangu.environment.examples.KB.PPODSparqlService import execute_query

if __name__ == '__main__':
    predicates = json.load(open("backend/text_to_query/ceqanet_data/predicates.json"))
    for predicate in predicates:
        query = 'SELECT * WHERE {?s <' + str(predicate) + '> ?o} LIMIT 100'
        res = execute_query(query, 'http://localhost:3003/sparql')
        print(predicate)
        print(res)
        print()
