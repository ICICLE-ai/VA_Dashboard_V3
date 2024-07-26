import argparse
import json

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=str, default="exp/sample_queries_with_R/schema_graph.json")
    args = parser.parse_args()

    data = json.load(open(args.data, 'r'))
    predicate_to_entity = set()
    predicate_to_literal = set()
    for t in data:
        for p in data[t]:
            if len(data[t][p]) == 1 and data[t][p][0] == 'literal':
                predicate_to_literal.add(p)
            else:
                predicate_to_entity.add(p)

    with open('data/predicate_entity.json', 'w') as f:
        json.dump(list(predicate_to_entity), f)
    with open('data/predicate_literal.json', 'w') as f:
        json.dump(list(predicate_to_literal), f)

    print(len(predicate_to_entity), len(predicate_to_literal))
