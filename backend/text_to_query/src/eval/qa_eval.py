import sys
from pathlib import Path

sys.path.append('.')
sys.path.append('src')

import os
from pangu.ppod_api import PanguForPPOD
from src.enumeration.graph_query import get_num_node
from src.enumeration.graph_query import get_num_edge
import argparse
import json
from collections import defaultdict

from tqdm import tqdm

from pangu.environment.examples.KB.PPODSparqlService import execute_query

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--eval', type=str, help='path to eval data', default='exp/sample_queries_valid_98.json')
    parser.add_argument('--llm', type=str, default='gpt-4o')
    parser.add_argument('--kg_api', action='store_true', help='use KG API to obtain data')
    args = parser.parse_args()

    data = json.load(open(args.eval))
    pangu = PanguForPPOD(api_key=os.getenv('OPENAI_API_KEY'), llm_name=args.llm, use_kg_api=args.kg_api)
    proj_root = str(Path(__file__).parent.absolute()) + '/../..'
    entity_to_label = json.load(open(os.path.join(proj_root, 'data/entity_to_label.json'), 'r'))

    results = []
    metrics = defaultdict(float)
    max_steps = 3 if not args.kg_api else 1
    for sample in tqdm(data):
        question = sample['question']
        gold_s_expr = sample['s-expression']
        gold_s_expr_repr = sample['s-expression_str']
        gold_sparql = sample['sparql']
        gold_ans = execute_query(gold_sparql)
        gold_ans_label = []
        for ans in gold_ans:
            gold_ans_label.append(entity_to_label[ans[0]] if ans[0] in entity_to_label else ans[0])
        gold_graph_query = sample['graph_query']
        num_node = get_num_node(gold_graph_query)
        num_edge = get_num_edge(gold_graph_query)

        predictions = pangu.text_to_query(question, max_steps=max_steps)
        pred_s_expr = None
        pred_s_expr_repr = None
        pred_sparql = None
        pred_ans = None
        pred_ans_label = None
        em = precision = recall = f1 = 0.0

        for prediction in predictions:
            if len(prediction['results']) == 0:
                print('[WARN] Empty result:', question, prediction['sparql'])
                continue
            pred_s_expr = prediction['s-expression']
            pred_s_expr_repr = prediction['s-expression_repr']
            pred_sparql = prediction['sparql']
            pred_ans = prediction['results']
            pred_ans_label = [pangu.entity_to_label[ans] if ans in pangu.entity_to_label else ans for ans in pred_ans]
            if set(pred_ans) == set(gold_ans):
                em = precision = recall = f1 = 1.0
            else:  # calculate F1
                precision = len(set(pred_ans) & set(gold_ans)) / len(set(pred_ans)) if len(set(pred_ans)) > 0 else 0.0
                recall = len(set(pred_ans) & set(gold_ans)) / len(set(gold_ans)) if len(set(gold_ans)) > 0 else 0.0
                f1 = 2 * precision * recall / (precision + recall) if precision + recall > 0 else 0.0
            break

        log = {'question': question, 'num_node': num_node, 'num_edge': num_edge,
               'gold_s_expr': gold_s_expr, 'pred_s_expr': pred_s_expr,
               'gold_s_expr_repr': gold_s_expr_repr, 'pred_s_expr_repr': pred_s_expr_repr,
               'gold_sparql': gold_sparql, 'pred_sparql': pred_sparql,
               'gold_ans': gold_ans, 'pred_ans': pred_ans,
               'gold_ans_label': gold_ans_label, 'pred_ans_label': pred_ans_label,
               'em': em, 'f1': f1, 'precision': precision, 'recall': recall}
        print(log)
        results.append(log)
        metrics['em'] += em
        metrics['f1'] += f1
        metrics['precision'] += precision
        metrics['recall'] += recall
        metrics[f"{num_edge}_hop_em"] += em
        metrics[f"{num_edge}_hop_f1"] += f1
        metrics[f"{num_edge}_hop_precision"] += precision
        metrics[f"{num_edge}_hop_recall"] += recall
        metrics[f"{num_edge}_hop"] += 1

    llm_label = args.llm.split('/')[-1]
    qa_eval_log_path = f'exp/qa_eval_results_{llm_label}.json'
    with open(qa_eval_log_path, 'w') as f:
        json.dump(results, f, indent=4)
        print(f'QA eval results saved to {qa_eval_log_path}')

    for key in metrics:
        if 'hop' in key:
            metrics[key] /= metrics[f"{key.split('_')[0]}_hop"]
        else:
            metrics[key] /= len(data)
        print(f'{key}: {round(metrics[key], 4)}')
