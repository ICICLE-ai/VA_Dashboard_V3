import sys

sys.path.append("src")

from src.enumeration.schema_generation import replace_inv_relations
import argparse
import json
import random

from openai import OpenAI
from tqdm import tqdm

from src.llm_util import openai_chat_completion

question_generation_instruction = """You possess the ability to interpret formal language effectively. Your task is to generate a natural language query that accurately conveys the process and underlying intention of a given structured LISP expression. The LISP expressions include specific entities or relations, which are denoted by square brackets, such as [city].

Here are functions you'll encounter in the LISP expressions and what they represent:

- JOIN(relation, entities) returns entities: establishes a connection between an entity (or a set of entities) and a relation, resulting in another entity (or set of entities).
- AND(entities, entities) returns entities: identifies the intersection between two sets of entities.
- COUNT(entities) returns an integer: the total number of entities within a set.

It's important to note that each relation is directed. The suffix `_inv` (inverse) may be appended to the relation name to represent an inverse relation, e.g., 
- (JOIN [is part of] [A]): `what is part of A?`
- (JOIN [is part of]_inv [A]): `what does A belong to?` or `what contains A?`"""

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=str, default="exp/sample_queries_with_questions.json")
    parser.add_argument("--api_key", type=str, help="OpenAI API key")
    parser.add_argument("--llm", type=str, help="OpenAI model name", default='gpt-4-turbo')
    args = parser.parse_args()

    output_path = "exp/debug_sample_queries_with_questions.json"
    data = json.load(open(args.data, "r"))
    inv_label = json.load(open("data/inverse_predicate.json", "r"))
    client = OpenAI(api_key=args.api_key)

    random.seed(1)
    sampled_data = random.sample(data, min(len(data), 500))
    print("Sampled data size:", len(sampled_data))

    results = []
    for idx, sample in tqdm(enumerate(sampled_data)):
        s_expr_str = sample["s-expression_str"]
        s_expr_str = replace_inv_relations(s_expr_str, inv_label)
        sample["s-expression_str"] = s_expr_str
        messages = [{'role': 'system', 'content': question_generation_instruction},
                    {'role': 'user',
                     'content': 'LISP: (AND foaf:Organization (JOIN [has member] (JOIN [associated geography] [Santiago Creek])))\nQuestion: '},
                    {'role': 'assistant', 'content': 'Which organization has a member that is associated with Santiago Creek?'},

                    {'role': 'user',
                     'content': 'LISP: (AND foaf:Organization (AND (JOIN [own] [Helendale Bluffs Recharge Site]) (JOIN [participates in] [Management])))\nQuestion: '},
                    {'role': 'assistant',
                     'content': 'Which organization owns the Helendale Bluffs Recharge Site and participate in Management?'},

                    {'role': 'user',
                     'content': 'LISP: (AND foaf:Organization (JOIN [create] [Nitrate Groundwater Pollution Hazard Index]))\nQuestion: '},
                    {'role': 'assistant', 'content': 'Which organization creates Nitrate Groundwater Pollution Hazard Index?'},

                    {'role': 'user', 'content': 'LISP: ' + s_expr_str + '\nQuestion: '}]
        response = openai_chat_completion(messages, client, model=args.llm, json_mode=False)
        print(s_expr_str, response.strip())
        sample['question'] = response.strip()
        results.append(sample)

        if idx % 10 == 0:
            with open(output_path, "w") as f:
                json.dump(results, f, indent=4)

    with open(output_path, "w") as f:
        json.dump(results, f, indent=4)
