import sys
from pathlib import Path

from pangu.ppod_api import pangu_for_kg_api

sys.path.append(str(Path(__file__).parent.absolute()) + '/../../..')

import argparse
import os

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--api_key', type=str)
    parser.add_argument('--llm', type=str, help='Llama gguf file path')
    args = parser.parse_args()

    api_key = os.getenv('OPENAI_API_KEY') if args.api_key is None else args.api_key

    # text-to-query API demo
    res = pangu_for_kg_api.text_to_query('Which infrastructures are adjacent to Drakes Estero?')
    for item in res:
        print(item)
