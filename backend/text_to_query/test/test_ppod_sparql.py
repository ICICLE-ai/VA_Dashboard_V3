import argparse
import sys
from pathlib import Path

from pangu.ppod_api import pangu_for_sparql

sys.path.append(str(Path(__file__).parent.absolute()) + '/../../..')


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--llm', type=str, help='Llama gguf file path')
    parser.add_argument('--api_key', type=str, help='endpoint API key')
    args = parser.parse_args()

    # text-to-query API demo
    res = pangu_for_sparql.text_to_query('What downstream infrastructures are connected to adjacent infrastructure in Drakes Estero?')
    for item in res:
        print(item)
    print()

    question = 'Which infrastructure intersects with San Dieguito Lagoon and involves striped mullet?'  # entity: San Dieguito Lagoon, literal: striped mullet
    # entity retrieval API demo
    entities = pangu_for_sparql.retrieve_entity(question, top_k=10)
    for i, doc in enumerate(entities):
        print(i, doc, pangu_for_sparql.label_to_entity[doc])
    print()

    # literal retrieval API demo
    literals = pangu_for_sparql.retrieve_literal(question, top_k=10)
    for i, doc in enumerate(literals):
        print(i, doc)
    print()

    # relation retrieval API demo
    relations = pangu_for_sparql.retrieve_relation(question, top_k=10)
    for i, doc in enumerate(relations):
        print(i, doc, pangu_for_sparql.label_to_predicate[doc])
    print()
