import requests
from backend.milkOligoDB.config.settings import API_URL_CREATE_CONCEPT, API_URL_CREATE_INSTANCE, API_URL_CREATE_RELATION, \
    ICFOODS_API_URL_GET_CONCEPT, ICFOODS_PROPOSITIONS_SEARCH_URL, ICFOODS_API_URL_GET_RELATION, ICFOODS_API_URL_GET_INSTANCE, \
    ICFOODS_API_URL_GET_PROPOSITION, ICFOODS_API_HOST, ICFOODS_PROPOSITION_LABELS_FROM_SUBJECT
    
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
import json

@csrf_exempt
@require_http_methods(["POST"])
def get_concepts(request):
    url = ICFOODS_API_URL_GET_INSTANCE

    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise error if the request fails
        result = response.json()  # Assume the response is a list

        # Collect labels and UUIDs
        concepts = [
            {'label': item['label'], 'uuid': item['uuid']} 
            for item in result if 'label' in item and 'uuid' in item
        ]  # Ensure both 'label' and 'uuid' keys exist

        # Return the concepts as a JSON response
        return JsonResponse(concepts, safe=False)  # safe=False for list responses

    except requests.RequestException as e:
        return JsonResponse({'error': str(e)}, status=500)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)



@csrf_exempt
@require_http_methods(["POST"])
def get_predicates(request):
    # Extract UUID from the request body
    try:
        body = json.loads(request.body)
        uuid_to_match = body.get('uuid')  # Get the UUID from the request body
        if not uuid_to_match:
            return JsonResponse({'error': 'UUID not provided'}, status=400)

        # Build the URL with the UUID at the end
        url = f"{ICFOODS_PROPOSITION_LABELS_FROM_SUBJECT}/{uuid_to_match}"

        response = requests.get(url)
        response.raise_for_status()  # Raise error if the request fails
        result = response.json()  # Assume the response is a list

        # Collect predicates where UUID matches either subject or object
        predicates = [
            {'predicate': item['predicate_label'], 'subject': item['subject_label'], 'object': item['object_label']}
            for item in result 
            if ('subject' in item and item['subject'] == uuid_to_match) or 
               ('object' in item and item['object'] == uuid_to_match)
        ]

        # Return the predicates as a JSON response
        return JsonResponse(predicates, safe=False)  # safe=False for list responses

    except requests.RequestException as e:
        return JsonResponse({'error': str(e)}, status=500)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON in request body'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

