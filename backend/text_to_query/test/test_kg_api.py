import argparse
import os

from pangu.ppod_api import PanguForPPOD

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--llm', type=str, help='Llama gguf file path')
    args = parser.parse_args()

    pangu = PanguForPPOD(openai_api_key=os.getenv('OPENAI_API_KEY'), llm_name=args.llm, use_kg_api=True)

    # text-to-query API demo
    res = pangu.text_to_query('What downstream infrastructures are connected to adjacent infrastructure in Drakes Estero?')
    for item in res:
        print(item)
    print()
