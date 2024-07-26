import json

from rank_bm25 import BM25Okapi

from backend.src.ner import ner


class BM25Index:
    def __init__(self, entity_to_label_path, label_to_entity_path):
        self.entity_to_label = json.load(open(entity_to_label_path, 'r'))
        self.label_to_entity = json.load(open(label_to_entity_path, 'r'))
        self.corpus = list(self.label_to_entity.keys())
        self.bm25 = self._build_index()

    def _build_index(self):
        tokenized_corpus = [doc.split(" ") for doc in self.corpus]
        bm25 = BM25Okapi(tokenized_corpus)
        return bm25

    def query(self, query_string, top_k=10):
        entities = ner(query_string)
        if len(entities) == 0:
            entities = query_string
        results = []
        for e in entities:
            query_tokens = e.split(" ")
            retrieved = self.bm25.get_top_n(query_tokens, self.corpus, n=top_k)
            results.extend(retrieved)
        return [(entity, self.label_to_entity[entity]) for entity in results]


def node_retrieval(query, index, top_k=10):
    return index.query(query, top_k)


def wrapper(query):
    index = BM25Index('backend/djangoBackend/vizStudio/data/entity_to_label.json', 'backend/djangoBackend/vizStudio/data/label_to_entity.json')
    results = node_retrieval(query, index, top_k=5)
    return results


if __name__ == '__main__':
    # note the relative path
    index = BM25Index('backend/djangoBackend/vizStudio/data/entity_to_label.json', 'backend/djangoBackend/vizStudio/data/label_to_entity.json')

    query = 'Dry Creek Conservancy belongs to which county?'  # Dry Creek Conservancy
    results = node_retrieval(query, index, top_k=5)
    print(results)
    print()

    query = 'Mid-Peninsula Water District belongs to which ecoregion?'  # Mid-Peninsula Water District
    results = node_retrieval(query, index, top_k=5)
    print(results)
