import argparse
import json

from enumeration.schema_generation import simplify_with_prefixes
from pangu.environment.examples.KB.PPODSparqlService import execute_query
from pangu.environment.examples.KB.ppod_environment import replace_r_func_to_inv, lisp_to_sparql
from pangu.ppod_agent import lisp_to_label

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', type=str, help='path to input file', default='exp/sample_queries_with_R/sample_queries_with_questions.json')
    parser.add_argument('--output', type=str, help='path to output file', default='exp/sample_queries_with_questions.json')
    args = parser.parse_args()

    data = json.load(open(args.input, 'r'))
    prefixes = json.load(open('data/prefix.json', 'r'))
    for sample in data:
        sample['s-expression'] = replace_r_func_to_inv(sample['s-expression'])
        sample['s-expression_simplified'] = simplify_with_prefixes(sample['s-expression'], prefixes)
        sample['s-expression_str'] = simplify_with_prefixes(lisp_to_label(sample['s-expression']), prefixes)

        sparql = lisp_to_sparql(sample['s-expression'])
        rows = execute_query(sample['sparql'])
        if len(rows) == 0:
            print('invalid lisp/sparql:', sample['s-expression'], sample['sparql'])

    json.dump(data, open(args.output, 'w'), indent=4)
    print('File saved to', args.output)
