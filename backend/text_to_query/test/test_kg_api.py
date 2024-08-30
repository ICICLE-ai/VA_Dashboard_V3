import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.absolute()) + '/../../..')

import argparse
import os

from backend.text_to_query.pangu.ppod_api import PanguForPPOD

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--api_key', type=str)
    parser.add_argument('--llm', type=str, help='Llama gguf file path')
    args = parser.parse_args()

    api_key = os.getenv('OPENAI_API_KEY') if args.api_key is None else args.api_key
    pangu = PanguForPPOD(api_key=api_key, llm_name=args.llm, use_kg_api=True)

    # text-to-query API demo
    res = pangu.text_to_query('What downstream infrastructures are connected to adjacent infrastructure in Drakes Estero?')
    for item in res:
        print(item)
