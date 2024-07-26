from transformers import AutoTokenizer, AutoModelForTokenClassification
from transformers import pipeline

tokenizer = AutoTokenizer.from_pretrained("dslim/bert-base-NER")
model = AutoModelForTokenClassification.from_pretrained("dslim/bert-base-NER")

ner_pipeline = pipeline("ner", model=model, tokenizer=tokenizer)


def ner(sentence, return_type=False):
    ner_results = ner_pipeline(sentence)
    entities = decode_entities(ner_results, sentence)
    if return_type:
        return entities
    else:
        return [entity[1] for entity in entities]


def decode_entities(output, text):
    entities = []
    current_entity = []
    current_label = None
    for item in output:
        if item['entity'].startswith('B'):
            if current_entity:
                entities.append((current_label, text[current_entity[0]:current_entity[-1]]))
            current_entity = [item['start'], item['end']]
            current_label = item['entity'][2:]
        elif item['entity'].startswith('I') and current_entity:
            current_entity[-1] = item['end']
    if current_entity:
        entities.append((current_label, text[current_entity[0]:current_entity[-1]]))
    return entities


if __name__ == '__main__':
    example = "Apple Inc. is an American multinational technology company headquartered in Cupertino, California, founded by Steve Jobs, Steve Wozniak, and Ronald Wayne in April 1976."
    print(ner(example))
