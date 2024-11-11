from django.urls import path
# from .views import calculate_length, text2query, page_method, work_method, audio_main
from .views import calculate_length,text2query, wake_and_asr,sparql_execute, generate_vega, healthcheck
from .consumers import QueryConsumer
from .graphFromApi import get_concepts, get_predicates


urlpatterns = [
    path('text2query/', text2query, name='text2query'),
    # path('page_method/', page_method, name='page_method'),
    # path('audio_main/', audio_main, name='audio_main'),
    # path('work_method/', work_method, name='work_method'),
    path('calculate_length/', calculate_length, name='calculate_length'),
    path('wake_and_asr/', wake_and_asr, name='wake_and_asr'),
    path('sparql_execute/', sparql_execute, name = 'sparql_execute'),
    path('generate_vega/', generate_vega, name = 'generate_vega'),
    path('healthcheck/', healthcheck, name='healthcheck'),
    path('get_concepts_for_graph/',get_concepts, name = 'get_concepts_for_graph'),
    path('get_predicates/',get_predicates, name = 'get_predicates')
]
websocket_urlpatterns = [
    path('ws/query/', QueryConsumer.as_asgi()),
]
