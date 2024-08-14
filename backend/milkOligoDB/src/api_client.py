import uuid
from typing import List

import requests
import logging

from backend.milkOligoDB.config.settings import API_URL_CREATE_CONCEPT, API_URL_CREATE_INSTANCE, API_URL_CREATE_RELATION, ICFOODS_API_URL_GET_CONCEPT, \
    ICFOODS_PROPOSITIONS_SEARCH_URL, ICFOODS_API_URL_GET_RELATION, ICFOODS_API_URL_GET_INSTANCE, ICFOODS_API_URL_GET_PROPOSITION


def create_concept(concept_name: str, iri: str = None) -> str:
    """
    Create a concept with the given name.

    Args:
        concept_name: The name of the concept.
        iri: The IRI of the concept.

    Returns:
        The UUID of the created concept, or None if creation failed.
    """
    iri = iri if iri else f"http://example.com/{uuid.uuid4()}"
    data = {"title": concept_name, "iri": iri}
    try:
        response = requests.post(API_URL_CREATE_CONCEPT, json=data)
        response.raise_for_status()
        return response.json().get("uuid")
    except requests.RequestException as e:
        logging.error(f"Concept creation failed: {e}")
        return None


def create_instance(concept_uuid: str, instance_title: str, item_type: str) -> dict:
    """
    Create an instance with the given concept UUID, instance title, and item type.

    Args:
        concept_uuid: The UUID of the concept.
        instance_title: The title of the instance.
        item_type: The type of the instance.

    Returns:
        The JSON response of the instance creation, or None if creation failed.
    """
    data = {"title": instance_title, "concept": concept_uuid, "item_type": item_type}
    try:
        response = requests.post(API_URL_CREATE_INSTANCE, json=data)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logging.error(f"Instance creation failed: {e}")
        return None


def create_relation(title: str, definition: str, iri: str = None) -> bool:
    """
    Send a request to the API to create a relation.

    Args:
        title: The title of the relation.
        definition: The definition of the relation.
        iri (optional): The IRI from OLS.

    Returns:
        True if the relation was created successfully, False otherwise.
    """
    iri = iri if iri else f"http://example.com/{uuid.uuid4()}"
    data = {"title": title, "definition": definition, "inverse": None, "iri": iri}
    try:
        response = requests.post(API_URL_CREATE_RELATION, json=data)
        response.raise_for_status()
        return True
    except requests.RequestException as e:
        logging.error(f"Failed to create relation: {title} - {e}")
        return False


def get_article_title_by_doi(doi: str) -> str:
    """
    Fetches the article title from the CrossRef API using the provided DOI.

    Args:
        doi (str): The DOI of the article.

    Returns:
        str: The title of the article or None if an error occurs.
    """
    url = f"https://api.crossref.org/works/{doi}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        return data.get("message", {}).get("title", [None])[0]
    except requests.RequestException as e:
        logging.error(f"Failed to fetch data for DOI {doi}: {e}")
        return None
    except IndexError:
        logging.error(f"No title found for DOI {doi}")
        return None


def get_all_concepts():
    url = ICFOODS_API_URL_GET_CONCEPT
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logging.error(f"Failed to fetch concepts: {e}")
        return None


def get_all_relations():
    url = ICFOODS_API_URL_GET_RELATION
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logging.error(f"Failed to fetch relations: {e}")
        return None


def get_all_instances():
    url = ICFOODS_API_URL_GET_INSTANCE
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logging.error(f"Failed to fetch instances: {e}")
        return None


def get_all_propositions():
    url = ICFOODS_API_URL_GET_PROPOSITION
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logging.error(f"Failed to fetch propositions: {e}")
        return None


def search_subjects(object: str, predicate: str) -> List[str]:
    """
    Search for propositions based on the given object and predicate.

    Args:
        object: The object of the propositions.
        predicate: The predicate of the propositions.

    Returns:
        A list of subject labels from the search results.
    """
    url = f"{ICFOODS_PROPOSITIONS_SEARCH_URL}/object/{object}/predicate/{predicate}/"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        subjects = []
        for obj in data:
            subjects.append(obj.get("subject_label"))
        return subjects
    except requests.RequestException as e:
        logging.error(f"Failed to search propositions: {e}")
        return []


def get_uuid_concept_maps(all_concepts: List):
    uuid_to_concept_map = {}
    concept_to_uuid_map = {}
    for concept in all_concepts:
        uuid = concept.get("uuid")
        label = concept.get("label")
        uuid_to_concept_map[uuid] = label
        if label not in concept_to_uuid_map:
            concept_to_uuid_map[label] = []
        concept_to_uuid_map[label].append(uuid)
    return uuid_to_concept_map, concept_to_uuid_map


def get_uuid_relation_maps(all_relations: List):
    uuid_to_relation_map = {}
    relation_to_uuid_map = {}
    for relation in all_relations:
        uuid = relation.get("uuid")
        label = relation.get("label")
        uuid_to_relation_map[uuid] = label
        if label not in relation_to_uuid_map:
            relation_to_uuid_map[label] = []
        relation_to_uuid_map[label].append(uuid)
    return uuid_to_relation_map, relation_to_uuid_map


def get_uuid_instance_maps(all_instances: List):
    uuid_to_instance_map = {}
    instance_to_uuid_map = {}
    for instance in all_instances:
        uuid = instance.get("uuid")
        label = instance.get("label")
        uuid_to_instance_map[uuid] = label
        if label not in instance_to_uuid_map:
            instance_to_uuid_map[label] = []
        instance_to_uuid_map[label].append(uuid)
    return uuid_to_instance_map, instance_to_uuid_map


def get_adjacent_relations_by_subject(uuid: str):
    url = f"{ICFOODS_PROPOSITIONS_SEARCH_URL}/subject/{uuid}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logging.error(f"Failed to fetch adjacent relations by subject: {e}")
        return None


def get_adjacent_relations_by_object(uuid: str):
    url = f"{ICFOODS_PROPOSITIONS_SEARCH_URL}/object/{uuid}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logging.error(f"Failed to fetch adjacent relations by object: {e}")
        return None


def get_object_by_subject_and_relation(subject_uuid: str, relation_uuid: str):
    url = f"{ICFOODS_PROPOSITIONS_SEARCH_URL}/subject/{subject_uuid}/predicate/{relation_uuid}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logging.error(f"Failed to fetch object by subject and relation: {e}")
        return None


def get_subject_by_object_and_relation(object_uuid: str, relation_uuid: str):
    url = f"{ICFOODS_PROPOSITIONS_SEARCH_URL}/object/{object_uuid}/predicate/{relation_uuid}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logging.error(f"Failed to fetch subject by object and relation: {e}")
        return None


if __name__ == '__main__':
    all_concepts = get_all_concepts()
    all_relations = get_all_relations()
    all_instances = get_all_instances()
    all_propositions = get_all_propositions()

    print('len all_concepts:', len(all_concepts))
    print('len all_relations:', len(all_relations))
    print('len all_instances:', len(all_instances))
    print('len all_propositions:', len(all_propositions))

    uuid_to_concept_map, concept_to_uuid_map = get_uuid_concept_maps(all_concepts)
    uuid_to_relation_map, relation_to_uuid_map = get_uuid_relation_maps(all_relations)
    uuid_to_instance_map, instance_to_uuid_map = get_uuid_instance_maps(all_instances)

    print('len uuid_to_concept_map:', len(uuid_to_concept_map))
    print('len concept_to_uuid_map:', len(concept_to_uuid_map))
    print('len uuid_to_relation_map:', len(uuid_to_relation_map))
    print('len relation_to_uuid_map:', len(relation_to_uuid_map))
    print('len uuid_to_instance_map:', len(uuid_to_instance_map))
    print('len instance_to_uuid_map:', len(instance_to_uuid_map))

    triples = get_adjacent_relations_by_subject(list(uuid_to_instance_map.keys())[0])
    if len(triples):
        print(triples)
        object = get_object_by_subject_and_relation(list(uuid_to_instance_map.keys())[0], triples[0].get('predicate'))
        print(object)

    triples = get_adjacent_relations_by_object(list(uuid_to_instance_map.keys())[0])
    if len(triples):
        print(triples)
        subject = get_subject_by_object_and_relation(list(uuid_to_instance_map.keys())[0], triples[0].get('predicate'))
        print(subject)

    print('Test done')
