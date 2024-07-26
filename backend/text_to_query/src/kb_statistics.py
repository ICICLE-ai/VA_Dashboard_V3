import argparse
import json

from rdflib import Graph, URIRef

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--ttl", type=str, default="data/PPOD_CA.ttl")
    args = parser.parse_args()

    with open(args.ttl, "r") as f:
        ttl = f.read()

    g = Graph()
    g.parse(data=ttl, format="ttl", publicID='http:/')

    predicate_set = set(g.predicates())

    print("Number of triples: {}".format(len(g)))
    print("Number of unique predicates: {}".format(len(predicate_set)))

    # Filter subjects and objects to ensure they are not literals or predicates
    filtered_subjects = {s for s in g.subjects() if isinstance(s, URIRef) and s not in predicate_set}
    filtered_objects = {o for o in g.objects() if isinstance(o, URIRef) and o not in predicate_set}
    both_subjects_and_objects = filtered_subjects & filtered_objects

    print("Number of unique subjects: {}".format(len(filtered_subjects)))
    print("Number of unique objects: {}".format(len(filtered_objects)))

    with open("data/predicates.json", "w") as f:
        json.dump(list(predicate_set), f, indent=4)
    with open("data/subjects.json", "w") as f:
        json.dump(list(filtered_subjects), f, indent=4)
    with open("data/objects.json", "w") as f:
        json.dump(list(filtered_objects), f, indent=4)

    entity_set = filtered_subjects | filtered_objects
    print("Number of unique entities: {}".format(len(entity_set)))
    with open("data/entities.json", "w") as f:
        json.dump(list(entity_set), f, indent=4)

    entity_to_label = {}
    predicate_to_label = {}
    label_query = """
        SELECT ?label
        WHERE {
            ?entity rdfs:label ?label .
        }
    """
    for entity in entity_set:
        for row in g.query(label_query, initBindings={"entity": entity}):
            if row[0].strip() == "":
                continue
            entity_to_label[entity] = row[0].value
            break
    for predicate in predicate_set:
        for row in g.query(label_query, initBindings={"entity": predicate}):
            if row[0].strip() == "":
                continue
            predicate_to_label[predicate] = row[0].value
            break
    with open("data/entity_to_label.json", "w") as f:
        json.dump(entity_to_label, f, indent=4)
    print("Number of entities with labels: {}".format(len(entity_to_label)))
    with open("data/predicate_to_label.json", "w") as f:
        json.dump(predicate_to_label, f, indent=4)
    print("Number of predicates with labels: {}".format(len(predicate_to_label)))

    # v -> k list from entity_to_label and predicate_to_label
    label_to_entity = {}
    for entity, label in entity_to_label.items():
        if label not in label_to_entity:
            label_to_entity[label] = []
        label_to_entity[label].append(entity)
    with open("data/label_to_entity.json", "w") as f:
        json.dump(label_to_entity, f, indent=4)

    label_to_predicate = {}
    for predicate, label in predicate_to_label.items():
        if label not in label_to_predicate:
            label_to_predicate[label] = []
        label_to_predicate[label].append(predicate)
    with open("data/label_to_predicate.json", "w") as f:
        json.dump(label_to_predicate, f, indent=4)

    entity_to_type = {}
    type_query = """
        SELECT ?class
        WHERE {
            ?entity a ?class .
        }
    """
    for entity in entity_set:
        type_list = []
        for row in g.query(type_query, initBindings={"entity": entity}):
            type_list.append(row[0])
        entity_to_type[entity] = type_list
    with open("data/entity_to_type.json", "w") as f:
        json.dump(entity_to_type, f, indent=4)

    type_set = set()
    for type_list in entity_to_type.values():
        type_set.update(type_list)
    print("Number of unique types: {}".format(len(type_set)))
    with open("data/types.json", "w") as f:
        json.dump(list(type_set), f, indent=4)

    prefixes = {}
    for prefix, namespace in g.namespaces():
        prefixes[prefix] = namespace
    with open("data/prefix.json", "w") as f:
        json.dump(prefixes, f, indent=4)
    print("Number of prefixes: {}".format(len(prefixes)))

    literal_set = {o for o in g.objects() if not isinstance(o, URIRef)} | {s for s in g.subjects() if not isinstance(s, URIRef)}
    literal_set = set([str(literal) for literal in literal_set])
    literal_set = literal_set - set(list(label_to_entity.keys()))
    literal_set = literal_set - set(list(label_to_predicate.keys()))
    print("Number of unique literals: {}".format(len(literal_set)))
    with open("data/literals.json", "w") as f:
        json.dump(list(literal_set), f, indent=4)


    # Number of triples: 158575
    # Number of unique predicates: 77
    # Number of unique subjects: 7605
    # Number of unique objects: 11626
    # Number of unique entities: 11841
    # Number of entities with labels: 7520
    # Number of predicates with labels: 64
    # Number of unique types: 10
    # Number of prefixes: 39
    # Number of unique literals: 3848
