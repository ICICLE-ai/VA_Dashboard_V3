import json
import os
from rank_bm25 import BM25Okapi


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
        query_tokens = query_string.split(" ")
        doc_scores = self.bm25.get_scores(query_tokens)
        top_docs_scores = sorted(((score, self.corpus[i]) for i, score in enumerate(doc_scores)), reverse=True, key=lambda x: x[0])[:top_k]
        return [(entity, self.label_to_entity[entity], score) for score, entity in top_docs_scores]


def node_retrieval(query, index, top_k=10):
    return index.query(query, top_k)

def wrapper(query):
    # Get the absolute path to the directory where func.py is located
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # Construct the path to the data file relative to the current script's location
    path1  = os.path.join(current_dir, '..', 'data', 'entity_to_label.json')
    path2  = os.path.join(current_dir, '..', 'data', 'label_to_entity.json')
    index = BM25Index(path1, path2)
    results = node_retrieval(query, index, top_k=5)
    return results

# if __name__ == '__main__':
#     # note the relative path
#     index = BM25Index('data/entity_to_label.json', 'data/label_to_entity.json')

#     query = 'Dry Creek Conservancy belongs to which county?'  # Dry Creek Conservancy
#     results = node_retrieval(query, index, top_k=5)
#     print(results)
#     print()

#     query = 'Mid-Peninsula Water District belongs to which ecoregion?'  # Mid-Peninsula Water District
#     results = node_retrieval(query, index, top_k=5)
#     print(results)
