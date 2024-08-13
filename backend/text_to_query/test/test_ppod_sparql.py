import os
import argparse

from pangu.ppod_api import PanguForPPOD

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--llm', type=str, help='Llama gguf file path')
    args = parser.parse_args()

    pangu = PanguForPPOD(openai_api_key=os.getenv('OPENAI_API_KEY'), llm_name=args.llm)

    # text-to-query API demo
    res = pangu.text_to_query('What downstream infrastructures are connected to adjacent infrastructure in Drakes Estero?')
    for item in res:
        print(item)
    print()

    question = 'Which infrastructure intersects with San Dieguito Lagoon and involves striped mullet?'  # entity: San Dieguito Lagoon, literal: striped mullet
    # entity retrieval API demo
    entities = pangu.retrieve_entity(question, top_k=10)
    for i, doc in enumerate(entities):
        print(i, doc, pangu.label_to_entity[doc])
    print()

    # literal retrieval API demo
    literals = pangu.retrieve_literal(question, top_k=10)
    for i, doc in enumerate(literals):
        print(i, doc)
    print()

    # relation retrieval API demo
    relations = pangu.retrieve_relation(question, top_k=10)
    for i, doc in enumerate(relations):
        print(i, doc, pangu.label_to_predicate[doc])
    print()
