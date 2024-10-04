import argparse
import json
import os
import re

from rdflib import Graph, URIRef

ppod_predicate_to_label = {
    "http://poderopedia.com/vocab/hasURL": "has URL",
    "http://purl.obolibrary.org/obo/BFO_0000066": "occurs in",
    "http://www.w3.org/ns/org#memberOf": "is member of",
    "http://vivoweb.org/ontology/core#fundingAgentFor": "funding organization",
    "https://raw.githubusercontent.com/adhollander/FSLschemas/main/fsisupp.owl#orgOwner": "organization owner",
    "http://purl.org/cerif/frapo/isFundedBy": "is funded by",
    "https://raw.githubusercontent.com/adhollander/FSLschemas/main/fsisupp.owl#inWatershed": "in watershed",
    "https://raw.githubusercontent.com/adhollander/FSLschemas/main/fsisupp.owl#projType": "project type",
    "https://raw.githubusercontent.com/adhollander/FSLschemas/main/fsisupp.owl#projDetails": "project details",
    "https://raw.githubusercontent.com/adhollander/FSLschemas/main/fsisupp.owl#FSI_000239": "related sustainability issue",
    "https://raw.githubusercontent.com/adhollander/FSLschemas/main/fsisupp.owl#infrastructureAdjacent": "adjacent infrastructure",
    "https://raw.githubusercontent.com/adhollander/FSLschemas/main/fsisupp.owl#taxa": "taxa",
    "http://xmlns.com/foaf/0.1/lastName": "last name",
    "https://raw.githubusercontent.com/adhollander/FSLschemas/main/fsisupp.owl#habitatType": "habitat type",
    "https://raw.githubusercontent.com/adhollander/FSLschemas/main/fsisupp.owl#issuesOther": "related issue",
    "http://vivoweb.org/ontology/core#hasFundingVehicle": "funding provided via",
    "https://raw.githubusercontent.com/adhollander/FSLschemas/main/fsisupp.owl#leadIndividual": "lead individual",
    "http://www.w3.org/ns/org#classification": "organization type",
    "http://purl.org/dc/terms/isPartOf": "is part of",
    "http://vivoweb.org/ontology/core#contactInformation": "contact",
    "https://raw.githubusercontent.com/adhollander/FSLschemas/main/fsisupp.owl#mandatedBy": "mandated by",
    "http://iflastandards.info/ns/fr/frbr/frbrer/P2007": "was created by",
    "http://dbpedia.org/ontology/endYear": "endYear",
    "http://purl.obolibrary.org/obo/RO_0001025": "located in",
    "https://raw.githubusercontent.com/adhollander/FSLschemas/main/fsisupp.owl#positionType": "position type",
    "https://raw.githubusercontent.com/adhollander/FSLschemas/main/fsisupp.owl#gmType": "guideline/mandate type",
    "https://raw.githubusercontent.com/adhollander/FSLschemas/main/fsisupp.owl#hasCapacity": "capacity",
    "https://raw.githubusercontent.com/adhollander/FSLschemas/main/fsisupp.owl#infrastructureIntersect": "intersecting infrastructure",
    "http://dbpedia.org/ontology/startYear": "startYear",
    "http://purl.obolibrary.org/obo/RO_0000087": "has role",
    "http://purl.obolibrary.org/obo/RO_0002331": "involved in",
    "https://raw.githubusercontent.com/adhollander/FSLschemas/main/fsisupp.owl#issuesPurpose": "purpose of infrastructure",
    "http://vivoweb.org/ontology/core#affiliatedOrganization": "partner organization",
    "https://raw.githubusercontent.com/adhollander/FSLschemas/main/fsisupp.owl#govLevel": "government level",
    "http://purl.obolibrary.org/obo/RO_0000056": "participates in",
    "https://raw.githubusercontent.com/adhollander/FSLschemas/main/fsisupp.owl#infrastructureType": "infrastructure type",
    "https://raw.githubusercontent.com/adhollander/FSLschemas/main/fsisupp.owl#inCounty": "in county",
    "http://purl.org/dc/terms/title": "title",
    "https://raw.githubusercontent.com/adhollander/FSLschemas/main/fsisupp.owl#orgManager": "organization manager",
    "http://xmlns.com/foaf/0.1/mbox": "email",
    "https://raw.githubusercontent.com/adhollander/FSLschemas/main/fsisupp.owl#FSI_000243": "note",
    "http://purl.obolibrary.org/obo/RO_0000081": "role of",
    "https://raw.githubusercontent.com/adhollander/FSLschemas/main/fsisupp.owl#orgUser": "organization user",
    "https://raw.githubusercontent.com/adhollander/FSLschemas/main/fsisupp.owl#inEcoregion": "in ecoregion",
    "http://xmlns.com/foaf/0.1/firstName": "first name",
    "https://raw.githubusercontent.com/adhollander/FSLschemas/main/fsisupp.owl#isPartOfInfra": "is part of",
    "http://purl.org/dc/terms/date": "date",
    "http://xmlns.com/foaf/0.1/phone": "phone",
    "http://vivoweb.org/ontology/core#hasCollaborator": "has partner",
    "https://raw.githubusercontent.com/adhollander/FSLschemas/main/fsisupp.owl#GM_Name": "guideline/mandate name",
    "https://raw.githubusercontent.com/adhollander/FSLschemas/main/fsisupp.owl#progType": "program type",
    "https://raw.githubusercontent.com/adhollander/FSLschemas/main/fsisupp.owl#ecologicalProcess": "ecological process",
    "https://raw.githubusercontent.com/adhollander/FSLschemas/main/fsisupp.owl#commodity": "commodity",
    "http://purl.obolibrary.org/obo/RO_0000057": "has participant",
    "https://raw.githubusercontent.com/adhollander/FSLschemas/main/fsisupp.owl#infrastructureDownstream": "downstream infrastructure",
    "http://xmlns.com/foaf/0.1/name": "full name",
    "http://purl.org/dc/terms/references": "references",
    "https://raw.githubusercontent.com/adhollander/FSLschemas/main/fsisupp.owl#leadOrg": "lead organization",
    "https://raw.githubusercontent.com/adhollander/FSLschemas/main/fsisupp.owl#infrastructureUpstream": "upstream infrastructure",
    "http://purl.obolibrary.org/obo/RO_0002353": "output of",
    "http://www.w3.org/2004/02/skos/core#altLabel": "alias",
    "https://raw.githubusercontent.com/adhollander/FSLschemas/main/fsisupp.owl#hasStrategy": "has strategy",
    "https://raw.githubusercontent.com/adhollander/FSLschemas/main/fsisupp.owl#assocGeo": "associated geography",
    "https://raw.githubusercontent.com/adhollander/FSLschemas/main/fsisupp.owl#FSLdoc": "FSL doc"
}


def convert_to_iso8601(date_str):
    # Match MM/DD/YYYY format and convert to YYYY-MM-DD
    match = re.match(r'(\d{1,2})/(\d{1,2})/(\d{4})', date_str)
    if match:
        month, day, year = match.groups()
        return f"{year}-{int(month):02d}-{int(day):02d}"
    return date_str


def convert_camel_label_to_words(s: str) -> str:
    last_part = s.split('#')[-1]

    # full uppercase word: convert continuous uppercase to lowercase
    last_part = re.sub(r'^[A-Z]+(?=[A-Z][a-z])', lambda m: m.group().lower(), last_part)

    # convert camel case string to lowercase and separate with space
    # use re.sub() to insert space between lower and upper case
    converted_string = re.sub(r'([a-z])([A-Z])', r'\1 \2', last_part)

    # convert the whole string to lowercase
    converted_string = converted_string.lower()

    return converted_string


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--nt", type=str, default="backend/data/CEQAnet2019onB.nt")
    args = parser.parse_args()

    with open(args.nt, "r") as f:
        nt = f.read()

    # Convert date strings to ISO 8601 format
    nt = re.sub(r'(\d{1,2}/\d{1,2}/\d{4})', lambda m: convert_to_iso8601(m.group(0)), nt)

    g = Graph()
    g.parse(data=nt, format="nt", publicID='http:/')

    os.makedirs("backend/text_to_query/ceqanet_data", exist_ok=True)
    predicate_set = set(g.predicates())

    print("Number of triples: {}".format(len(g)))
    print("Number of unique predicates: {}".format(len(predicate_set)))

    # Filter subjects and objects to ensure they are not literals or predicates
    filtered_subjects = {s for s in g.subjects() if isinstance(s, URIRef) and s not in predicate_set}
    filtered_objects = {o for o in g.objects() if isinstance(o, URIRef) and o not in predicate_set}
    both_subjects_and_objects = filtered_subjects & filtered_objects

    print("Number of unique subjects: {}".format(len(filtered_subjects)))
    print("Number of unique objects: {}".format(len(filtered_objects)))

    with open("backend/text_to_query/ceqanet_data/predicates.json", "w") as f:
        json.dump(list(predicate_set), f, indent=4)
    with open("backend/text_to_query/ceqanet_data/subjects.json", "w") as f:
        json.dump(list(filtered_subjects), f, indent=4)
    with open("backend/text_to_query/ceqanet_data/objects.json", "w") as f:
        json.dump(list(filtered_objects), f, indent=4)

    entity_set = filtered_subjects | filtered_objects
    print("Number of unique entities: {}".format(len(entity_set)))
    with open("backend/text_to_query/ceqanet_data/entities.json", "w") as f:
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
        predicate_has_label = False
        for row in g.query(label_query, initBindings={"entity": str(predicate)}):
            if row[0].strip() == "":
                continue
            predicate_to_label[predicate] = row[0].value
            predicate_has_label = True
            break
        if predicate_has_label is False:
            if predicate not in ppod_predicate_to_label:
                predicate_to_label[str(predicate)] = convert_camel_label_to_words(str(predicate).split('/')[-1].split('#')[-1])
            else:
                predicate_to_label[str(predicate)] = ppod_predicate_to_label[str(predicate)]

    with open("backend/text_to_query/ceqanet_data/entity_to_label.json", "w") as f:
        json.dump(entity_to_label, f, indent=4)
    print("Number of entities with labels: {}".format(len(entity_to_label)))
    with open("backend/text_to_query/ceqanet_data/predicate_to_label.json", "w") as f:
        json.dump(predicate_to_label, f, indent=4)
    print("Number of predicates with labels: {}".format(len(predicate_to_label)))

    # v -> k list from entity_to_label and predicate_to_label
    label_to_entity = {}
    for entity, label in entity_to_label.items():
        if label not in label_to_entity:
            label_to_entity[label] = []
        label_to_entity[label].append(entity)
    with open("backend/text_to_query/ceqanet_data/label_to_entity.json", "w") as f:
        json.dump(label_to_entity, f, indent=4)

    label_to_predicate = {}
    for predicate, label in predicate_to_label.items():
        if label not in label_to_predicate:
            label_to_predicate[label] = []
        label_to_predicate[label].append(predicate)
    with open("backend/text_to_query/ceqanet_data/label_to_predicate.json", "w") as f:
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
    with open("backend/text_to_query/ceqanet_data/entity_to_type.json", "w") as f:
        json.dump(entity_to_type, f, indent=4)

    type_set = set()
    for type_list in entity_to_type.values():
        type_set.update(type_list)
    print("Number of unique types: {}".format(len(type_set)))
    with open("backend/text_to_query/ceqanet_data/types.json", "w") as f:
        json.dump(list(type_set), f, indent=4)

    prefixes = {}
    for prefix, namespace in g.namespaces():
        prefixes[prefix] = namespace
    with open("backend/text_to_query/ceqanet_data/prefix.json", "w") as f:
        json.dump(prefixes, f, indent=4)
    print("Number of prefixes: {}".format(len(prefixes)))

    literal_set = {o for o in g.objects() if not isinstance(o, URIRef)} | {s for s in g.subjects() if not isinstance(s, URIRef)}
    literal_set = set([str(literal) for literal in literal_set])
    literal_set = literal_set - set(list(label_to_entity.keys()))
    literal_set = literal_set - set(list(label_to_predicate.keys()))
    print("Number of unique literals: {}".format(len(literal_set)))
    with open("backend/text_to_query/ceqanet_data/literals.json", "w") as f:
        json.dump(list(literal_set), f, indent=4)

    # Number of triples: 1468432
    # Number of unique predicates: 53
    # Number of unique subjects: 66977
    # Number of unique objects: 13714
    # Number of unique entities: 66980
    # Number of entities with labels: 66977
    # Number of predicates with labels: 0
    # Number of unique types: 4
    # Number of prefixes: 29
    # Number of unique literals: 373348
