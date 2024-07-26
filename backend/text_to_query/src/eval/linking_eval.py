import sys

sys.path.append('.')

import argparse
import json
import os
from collections import defaultdict
from tqdm import tqdm
from pangu.ppod_api import PanguForPPOD
from src.enumeration.graph_query import get_entity_id_set, get_literals, get_num_edge

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--data', type=str, help='path to eval data', default='exp/sample_queries_valid_98.json')
    parser.add_argument('--retriever', type=str, default='sentence-transformers/gtr-t5-base')
    parser.add_argument('--llm', type=str, default='gpt-4o')
    args = parser.parse_args()

    # load data
    verbose = True
    data = json.load(open(args.data, 'r'))
    pangu = PanguForPPOD(openai_api_key=os.getenv('OPENAI_API_KEY'), llm_name=args.llm, retriever=args.retriever)

    k_list = [1, 2, 3, 5, 10, 15, 20, 30, 50]
    metrics = defaultdict(float)
    for sample in tqdm(data):
        question = sample['question']
        graph_query = sample['graph_query']
        num_relation = get_num_edge(graph_query)
        gold_entities = get_entity_id_set(graph_query)
        gold_entity_labels = [pangu.entity_to_label.get(e, None) for e in gold_entities]
        gold_literals = get_literals(graph_query)

        pred_entity_labels = pangu.retrieve_entity(question, 50)
        pred_entity_ids = []
        for e in pred_entity_labels:
            pred_entity_ids.append(pangu.label_to_entity.get(e, None)[0])
        pred_literals = pangu.retrieve_literal(question, 50)

        # evaluate linking results
        if len(gold_entities):
            metrics['entity'] += 1
        if len(gold_literals):
            metrics['literal'] += 1
        for k in k_list:
            pred_entities_k = set(pred_entity_ids[:k])
            intersection = gold_entities.intersection(pred_entities_k)
            recall = len(intersection) / len(gold_entities) if len(gold_entities) > 0 else 0
            metrics['recall_entity@{}'.format(k)] += recall
        for k in k_list:
            pred_literals_k = set(pred_literals[:k])
            intersection = gold_literals.intersection(pred_literals_k)
            recall = len(intersection) / len(gold_literals) if len(gold_literals) > 0 else 0
            # print(f"k={k}, pred_literals[:k]={pred_literals[:k]}, gold_literals={gold_literals}, intersection={intersection}, recall={recall}")
            metrics['recall_literal@{}'.format(k)] += recall

            if verbose:
                if k == 10 and recall < 1:
                    print('Question:', question)
                    print('Gold entities:', list(gold_entity_labels)[:10])
                    print('Gold literals:', gold_literals)
                    print('Pred entities:', list(pred_entity_labels)[:10])
                    print('Pred literals:', list(pred_literals_k)[:10])
                    print()

    for k in k_list:
        metrics['recall_entity@{}'.format(k)] /= metrics['entity']
        metrics['recall_literal@{}'.format(k)] /= metrics['literal']
        print('Recall@{}: entity={:.4f}, literal={:.4f}'.format(k, metrics['recall_entity@{}'.format(k)], metrics['recall_literal@{}'.format(k)]))
