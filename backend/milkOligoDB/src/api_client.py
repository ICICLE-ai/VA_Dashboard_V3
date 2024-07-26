import uuid
import requests
import logging

from backend.milkOligoDB.config.settings import API_URL_CREATE_CONCEPT, API_URL_CREATE_INSTANCE, API_URL_CREATE_RELATION, ICFOODS_API_URL_GET_CONCEPT


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


if __name__ == '__main__':
    get_all_concepts()
