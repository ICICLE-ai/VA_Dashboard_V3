import json
from tqdm import tqdm
from pangu.environment.examples.KB.PPODSparqlCache import PPODSparqlCache

if __name__ == '__main__':
    # read a list from a txt file
    entities = json.load(open('data/entities.json', 'r'))

    sparql_cache = PPODSparqlCache()
    for e in tqdm(entities):
        e = e.strip()
        in_relations = sparql_cache.get_entity_in_relations(e)
        out_relations = sparql_cache.get_entity_out_relations(e)

    sparql_cache.save_cache('data/ppod_cache.json')
