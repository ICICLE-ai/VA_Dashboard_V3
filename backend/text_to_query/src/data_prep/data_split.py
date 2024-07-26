import argparse
import json
import random

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=str, default='exp/sample_queries_with_questions.json')
    args = parser.parse_args()

    data = json.load(open(args.data, 'r'))
    print('#sample', len(data))

    # randomly sample 0.6 of the data for training, 0.2 for validation and 0.2 for testing
    random.seed(1)
    random.shuffle(data)
    len_train = int(len(data) * 0.6)
    len_valid = int(len(data) * 0.2)
    len_test = len(data) - len_train - len_valid
    train_data = data[:len_train]
    valid_data = data[len_train:len_train + len_valid]
    test_data = data[len_train + len_valid:]

    json.dump(train_data, open(f'exp/sample_queries_train_{len_train}.json', 'w'))
    json.dump(valid_data, open(f'exp/sample_queries_valid_{len_valid}.json', 'w'))
    json.dump(test_data, open(f'exp/sample_queries_test_{len_test}.json', 'w'))
