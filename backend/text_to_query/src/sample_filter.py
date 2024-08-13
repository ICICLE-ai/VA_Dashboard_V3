import argparse
import json

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--data', type=str, default='/research/nfs_su_809/workspace/shu.251/GUI_/backend/text_to_query/exp/qa_eval_results_gpt-4o.json')
    args = parser.parse_args()

    data = json.load(open(args.data))

    sampled_data = []
    for sample in data:
        if sample['em'] == 1.0 and sample['num_node'] <= 2:
            sampled_data.append(sample)

    output_path = args.data.replace('.json', '_1_hop_em_1.json')
    with open(output_path, 'w') as f:
        json.dump(sampled_data, f, indent=4)
