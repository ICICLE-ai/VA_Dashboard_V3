import json
import os.path
from abc import ABC, abstractmethod
from pathlib import Path

import numpy as np
import torch
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer, util, CrossEncoder
from sklearn.feature_extraction.text import TfidfVectorizer


class TextRetriever(ABC):
    def __init__(self, corpus):
        self.corpus = corpus

    @abstractmethod
    def _preprocess(self):
        pass

    @abstractmethod
    def scores_on_corpus(self, query):
        pass

    def get_top_k_sentences(self, query, k=10, distinct=True):
        if len(self.corpus) == 0:
            return []
        top_k_indices = self.get_top_k_indices(query, k, distinct)
        top_k_sentences = [self.corpus[i] for i in top_k_indices]
        return top_k_sentences

    def get_top_k_indices(self, query, k=10, distinct=True):
        scores = self.scores_on_corpus(query)

        # Get the top k indices with the highest scores
        if distinct is False:
            top_k_indices = np.argsort(scores)[::-1][:k]
            return top_k_indices
        else:
            top_k_indices = np.argsort(scores)[::-1][:5 * k]

            # Remove duplicates by storing seen sentences in a set
            seen_sentences = set()
            unique_top_k_indices = []
            for i in top_k_indices:
                if self.corpus[i] not in seen_sentences:
                    unique_top_k_indices.append(i)
                    seen_sentences.add(self.corpus[i])

                    if len(unique_top_k_indices) == k:
                        break

            return unique_top_k_indices


class BM25Retriever(TextRetriever):
    def __init__(self, corpus, split=' '):
        super().__init__(corpus)
        self.bm25 = None
        self.split_char = split
        self._preprocess()

    def _preprocess(self):
        tokenized_corpus = [doc.split(self.split_char) for doc in self.corpus]
        self.bm25 = BM25Okapi(tokenized_corpus)

    def scores_on_corpus(self, query):
        tokenized_query = query.split(" ")
        scores = self.bm25.get_scores(tokenized_query)
        return scores


class TfidfRetriever(TextRetriever):
    def __init__(self, corpus):
        super().__init__(corpus)
        self.vectorizer = None
        self.tfidf_matrix = None
        self._preprocess()

    def _preprocess(self):
        self.vectorizer = TfidfVectorizer()
        self.tfidf_matrix = self.vectorizer.fit_transform(self.corpus)

    def scores_on_corpus(self, query):
        query_vec = self.vectorizer.transform([query])
        scores = np.dot(self.tfidf_matrix, query_vec.T).toarray().flatten()
        return scores


class SentenceTransformerRetriever(TextRetriever):
    def __init__(self, corpus, model_name=None, model=None, device='cuda'):
        super().__init__(corpus)
        assert model_name is not None or model is not None, "Either model_name or model should be provided"
        if model is None:
            self.model = SentenceTransformer(model_name).to(device)
        else:
            self.model = model
        self.embeddings = None
        self._preprocess()

    def _preprocess(self):
        if len(self.corpus) > 0:
            with torch.no_grad():
                self.embeddings = self.model.encode(self.corpus)
        else:
            self.embeddings = []

    def scores_on_corpus(self, query):
        with torch.no_grad():
            query_embedding = self.model.encode([query])[0]
            scores = util.pytorch_cos_sim(query_embedding, self.embeddings)[0]
            return scores.cpu().numpy()


class GritLMRetriever(TextRetriever):

    def __init__(self, corpus, model_name='GritLM/GritLM-7B', model=None, instruction=''):
        from gritlm import GritLM

        super().__init__(corpus)
        assert model_name is not None or model is not None, "Either model_name or model should be provided"
        if model is None:
            self.model = GritLM(model_name, torch_dtype='auto')
        else:
            self.model = model
        self.instruction = instruction
        self.embeddings = None
        self._preprocess()

    def gritlm_instruction(self, instruction):
        return "<|user|>\n" + instruction + "\n<|embed|>\n" if instruction else "<|embed|>\n"

    def _preprocess(self):
        with torch.no_grad():
            self.embeddings = self.model.encode(self.corpus, instruction=self.gritlm_instruction(""))

    def scores_on_corpus(self, query):
        if isinstance(query, str):
            query = [query]
        with torch.no_grad():
            query_embedding = self.model.encode(query, instruction=self.gritlm_instruction(self.instruction))[0]
            scores = util.pytorch_cos_sim(query_embedding, self.embeddings)[0]
            return scores.cpu().numpy()


class DPR(TextRetriever):
    def __init__(self, corpus, passage_encoder='facebook-dpr-ctx_encoder-single-nq-base', query_encoder='facebook-dpr-question_encoder-single-nq-base'):
        super().__init__(corpus)
        # Initialize the encoders
        self.passage_encoder = SentenceTransformer(passage_encoder)
        self.query_encoder = SentenceTransformer(query_encoder)
        self.passage_embeddings = self._preprocess()

    def _preprocess(self):
        return self.passage_encoder.encode(self.corpus)

    def scores_on_corpus(self, query):
        query_embedding = self.query_encoder.encode(query)
        scores = util.dot_score(query_embedding, self.passage_embeddings)[0]
        return scores.cpu().numpy()


class CrossEncoderRetrieval(TextRetriever):
    def __init__(self, corpus, model_name_or_path='cross-encoder/nli-deberta-v3-base'):
        super().__init__(corpus)
        self.model = CrossEncoder(model_name_or_path)

    def _preprocess(self):
        pass

    def scores_on_corpus(self, query):
        sentence_combinations = [[query, corpus_sentence] for corpus_sentence in self.corpus]
        scores = self.model.predict(sentence_combinations)[:, 1]
        return scores


class Colbertv2Retrieval(TextRetriever):
    def __init__(self, corpus: list, root: str, index_name: str):
        self.root = root
        self.index_name = index_name
        self.corpus = corpus
        proj_root = str(Path(__file__).parent.absolute()) + '/../..'
        self.checkpoint_path = os.path.join(proj_root, 'exp/colbertv2.0')

        from colbert.infra import Run
        from colbert.infra import RunConfig
        from colbert import Searcher
        from colbert.infra import ColBERTConfig

        self._preprocess()

        with Run().context(RunConfig(nranks=1, experiment="colbert", root=self.root)):
            config = ColBERTConfig(
                root=self.root.rstrip('/') + '/colbert',
            )
            self.searcher = Searcher(index=self.index_name, config=config)

    def _preprocess(self, overwrite='reuse'):
        """
        :param overwrite: one value from [True, 'reuse', 'resume', "force_silent_overwrite"]
        """
        from colbert.infra import Run
        from colbert.infra import RunConfig
        from colbert.infra import ColBERTConfig

        with Run().context(RunConfig(nranks=1, experiment="colbert", root=self.root)):
            config = ColBERTConfig(
                nbits=2,
                root=self.root,
            )
            from colbert import Indexer
            indexer = Indexer(checkpoint=self.checkpoint_path, config=config)
            indexer.index(name=self.index_name, collection=self.corpus, overwrite=overwrite)

    def scores_on_corpus(self, query):
        pass

    def get_top_k_sentences(self, query, k=100, distinct=True):
        from colbert.data import Queries
        query = Queries(path=None, data={0: query})
        ranking = self.searcher.search_all(query, k)
        res = []
        for item in list(ranking.data.values())[0]:
            res.append(self.corpus[item[0]])
        return res

    def get_top_k_indices(self, query, k=100, distinct=True):
        from colbert.data import Queries
        query = Queries(path=None, data={0: query})
        ranking = self.searcher.search_all(query, k)
        res = []
        for item in list(ranking.data.values())[0]:
            res.append(item[0])
        return res


if __name__ == "__main__":
    entity_to_label = json.load(open("data/entity_to_label.json", 'r'))
    label_to_entity = json.load(open("data/label_to_entity.json", 'r'))
    predicate_to_label = json.load(open("data/predicate_to_label.json", 'r'))
    label_to_predicate = json.load(open("data/label_to_predicate.json", 'r'))
    literals = json.load(open("data/literals.json", 'r'))

    model = SentenceTransformer('sentence-transformers/gtr-t5-base')
    entity_retriever = SentenceTransformerRetriever(list(label_to_entity.keys()), model=model)
    literal_retriever = SentenceTransformerRetriever(literals, model=model)
    relation_retriever = SentenceTransformerRetriever(list(label_to_predicate.keys()), model=model)

    question = 'Which infrastructure intersects with San Dieguito Lagoon and involves striped mullet?'  # entity: San Dieguito Lagoon, literal: striped mullet
    entities = entity_retriever.get_top_k_sentences(question, k=10, distinct=True)
    for i, doc in enumerate(entities):
        print(i, doc, label_to_entity[doc])
    print()

    literals = literal_retriever.get_top_k_sentences(question, k=10, distinct=True)
    for i, doc in enumerate(literals):
        print(i, doc)
    print()

    relations = relation_retriever.get_top_k_sentences(question, k=10, distinct=True)
    for i, doc in enumerate(relations):
        print(i, doc, label_to_predicate[doc])
    print()
