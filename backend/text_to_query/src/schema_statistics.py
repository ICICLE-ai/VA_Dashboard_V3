import argparse

from rdflib import Graph

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--ttl", type=str, default="data/PPOD_CA.ttl")
    args = parser.parse_args()

    with open(args.ttl, "r") as f:
        ttl = f.read()

    g = Graph()
    g.parse(data=ttl, format="ttl", publicID='http:/')

    # calculate the frequency of predicates and types in this KG; types are entity types in the format of (?entity a ?type)
    predicate_freq = {}
    type_freq = {}
    for s, p, o in g:
        if p not in predicate_freq:
            predicate_freq[p] = 0
        predicate_freq[p] += 1
        if str(p) == 'http://www.w3.org/1999/02/22-rdf-syntax-ns#type' or str(p) == 'a':
            if o not in type_freq:
                type_freq[o] = 0
            type_freq[o] += 1

    # sort the predicates and types by frequency
    sorted_predicate_freq = sorted(predicate_freq.items(), key=lambda x: x[1], reverse=True)
    sorted_type_freq = sorted(type_freq.items(), key=lambda x: x[1], reverse=True)

    # print
    print("predicates by frequency:")
    for p, freq in sorted_predicate_freq:
        print(f"{p}: {freq}")
    print("types by frequency:")
    for t, freq in sorted_type_freq:
        print(f"{t}: {freq}")