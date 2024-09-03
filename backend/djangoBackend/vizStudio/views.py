import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.absolute()) + '/../..')
from pandas import json_normalize
from datetime import datetime

# Create your views here.
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
import json
from vizStudio.helper import node_retrieval_bm25_api
import sys 
import os
import pandas as pd
from SPARQLWrapper import SPARQLWrapper

from . import pangu
from .speechframework.models import ConformerModel
sys.path.append(os.path.abspath(os.path.join(os.getcwd(), '../')))


# import AutoVega.visualize as autovis
from vega_helper.visualize import AutoVega
#speech 2 text imports
from django.http import HttpResponse
from django.template import loader
# from whisperX import whisperx
import whisperx
import pyaudio
import torch
# from speechframework.models import ConformerModel
import numpy as np
from django.shortcuts import render
import torch.nn as nn
# from .speech2text import int2float, model_vad,save_file, model_asr,whisperx_align, metadata, process_frame, work_method
# from speechframework.models import ConformerModel
from .speech2text import start_wake_detection, transcribe_audio


FORMAT = pyaudio.paInt16
CHANNELS = 1
SAMPLE_RATE = 16000
CHUNK = 1024
class NpEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.int64):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, datetime.datetime):
            return str(obj)
        if isinstance(obj, pd.Timestamp):
            return str(obj)
        return super(NpEncoder, self).default(obj)

@csrf_exempt
@require_http_methods(["POST"])
def calculate_length(request):
    data = json.loads(request.body)
    user_string = data.get('user_string', '')
    response_data = {
        'length': node_retrieval_bm25_api.wrapper(user_string)
    }
    return JsonResponse(response_data)

@csrf_exempt
@require_http_methods(["POST"])
def text2query(request):
    data = json.loads(request.body)
    question = data.get('question', '')
    openai_api = data.get('openai_api','')
    # toy_data = [{'input': 'What downstream infrastructures are connected to adjacent infrastructure in Drakes Estero?', 's-expression': '(JOIN https://raw.githubusercontent.com/adhollander/FSLschemas/main/fsisupp.owl#infrastructureDownstream_inv (JOIN https://raw.githubusercontent.com/adhollander/FSLschemas/main/fsisupp.owl#infrastructureAdjacent https://raw.githubusercontent.com/adhollander/FSLschemas/main/CA_PPODterms.ttl#inf_725827))', 's-expression_repr': '(JOIN [is downstream infrastructure of] (JOIN [adjacent infrastructure] [Drakes Estero]))', 'score': -1.9361265e-07, 'sparql': 'SELECT DISTINCT ?x\nWHERE {\n?x0 <https://raw.githubusercontent.com/adhollander/FSLschemas/main/fsisupp.owl#infrastructureAdjacent> <https://raw.githubusercontent.com/adhollander/FSLschemas/main/CA_PPODterms.ttl#inf_725827> .\n?x0 <https://raw.githubusercontent.com/adhollander/FSLschemas/main/fsisupp.owl#infrastructureDownstream> ?x .\nFILTER (?x != <https://raw.githubusercontent.com/adhollander/FSLschemas/main/CA_PPODterms.ttl#inf_725827>)\n}', 'results': [('https://raw.githubusercontent.com/adhollander/FSLschemas/main/CA_PPODterms.ttl#inf_5f26fd',)], 'labels': ['Drakes Bay']},
    res = pangu.text_to_query(question, openai_api_key=openai_api)
    return JsonResponse({"result": res})

@csrf_exempt
@require_http_methods(['POST'])
def generate_vega(request):
    request_obj = json.loads(request.body)
    data = request_obj['data']
    df_nested_list = pd.json_normalize(data)
    columns = list(df_nested_list.columns)
    rename_dict  = {}
    for col in columns:
        rename_dict[col] = col.split('.')[0]
    df_nested_list = df_nested_list.rename(columns=rename_dict)
    columns = list(rename_dict.values())
    if 'id' in columns and 'state' in columns:
        test = AutoVega(df_nested_list, chart='map')
    else:
        test = AutoVega(df_nested_list)
    
    scripts = test.plot()
    final= {
        'data': scripts, 
        'info': {
            'label_column': test._label_column,
            'numerical_column': test._numerical_column,
            'date_column': test._date_column
        }
    }
    return JsonResponse(final)

@csrf_exempt
@require_http_methods(["POST"])
def sparql_execute(request):
    request_obj = json.loads(request.body)
    endpoint = request_obj.get('endpoint', '')
    sparql_query = request_obj.get('sparql', '')
    print('dddd')
    sparql = SPARQLWrapper(endpoint)
    sparql.setReturnFormat('json')

    sparql.setQuery(sparql_query)
    results = sparql.query().convert()
    output = results["results"]["bindings"]
    if (len(output)>0):
        df =  json_normalize(output)
    else:
        print('no data')
        df =  []
    print(type(df))
    columns = list(df.columns)
    columns_filter = [ele for ele in columns if ".type" not in ele and '.datatype' not in ele]
    df = df.filter(items=columns_filter)
    # output = sparqlQuery.convertJson(df, df.to_dict('records'))
    return JsonResponse(df.to_dict('records'), safe=False)


# # speech2text
# @csrf_exempt
# @require_http_methods(["POST"])
# def page_method(request):
#     """
#     This method load on the page.html template
#     :param request: The request object
#     :return: The rendered template
#     :description: Record the incoming audio, till 5 second of silence is detected, then transcribe the audio and align the transcription with the audio

#     """
#     wake_word_detector = True if request.method == 'POST' else False
#     audio = pyaudio.PyAudio()
#     stream = audio.open(format=FORMAT,
#                         channels=CHANNELS,
#                         rate=SAMPLE_RATE,
#                         input=True,
#                         frames_per_buffer=1024)
#     continue_recording = True if wake_word_detector else False
#     if wake_word_detector:
#         print("Connected to the server")
#         data = []
#         count = 0
#     while continue_recording:
#         audio_chunk = stream.read(1024, exception_on_overflow=False)
#         data.append(audio_chunk)
#         if len(audio_chunk) == 0:
#             break
#         audio_int16 = np.frombuffer(audio_chunk, np.int16)
#         audio_float32 = int2float(audio_int16)
#         temp = torch.from_numpy(audio_float32)
#         a = int(temp.size()[0])
#         if a < 512:
#             m = nn.ConstantPad1d((0, 512-a), 0.0000000)
#             temp = m(temp)
#         try:
#             new_confidence = model_vad(temp, 16000).item()
#         except Exception:
#             save_file()
#         value = round(new_confidence)
#         if value == 0:
#             count += 1
#             print('.', sep=' ', end='', flush=True)
#         else:
#             count = 0  # Reset the count if the value is not 0
#         if count == 80:
#             print(str(count) + " milliseconds elapsed during waiting")
#             res = save_file(data)
#             continue_recording = False
#             audio = whisperx.load_audio(res)
#             result = model_asr.transcribe(audio, 2)
#             result2 = whisperx.align(result["segments"], whisperx_align, metadata, audio, 'cpu', return_char_alignments=False)
#             print(result["segments"][0]["text"]) if result["segments"] else print("No speech detected")
#             print(result2["word_segments"])
#             continue_recording = False
#             stream.stop_stream()
#             stream.close()
#             results = result2["word_segments"]
#             print(results)
#             return JsonResponse({'result':results}) 


# @csrf_exempt
# @require_http_methods(["POST"])
# def audio_main(request):
#     """
#     The initial method for the audio processing on IKLE mode from the home page
#     :param request: The request object
#     :return: The rendered template
#     :description: This method opens the audio stream, loads the wake word model and waits for the wake word to start the recording, once detected, it renders the page.html template

#     """
#     audio = pyaudio.PyAudio()
#     stream = audio.open(format=FORMAT,
#                         channels=CHANNELS,
#                         rate=SAMPLE_RATE,
#                         input=True,
#                         frames_per_buffer=1024)
#     device = torch.device('cpu')
#     checkpoint_path = "word_level_train_015_256_bert1_st00_2fc_conf_16_sig_bce_rop_80.pt"
#     # checkpoint_path = ""
#     pretrained_model = torch.load(checkpoint_path, map_location=device)
#     model_state_dict = pretrained_model["model_state_dict"]
#     model_params = {'num_classes': pretrained_model['model_params']['num_classes'],
#                     'feature_size': pretrained_model['model_params']['feature_size'],
#                     'hidden_size': pretrained_model['model_params']['hidden_size'],
#                     'num_layers': pretrained_model['model_params']['num_layers'],
#                     'dropout': pretrained_model['model_params']['dropout'],
#                     'bidirectional': pretrained_model['model_params']['bidirectional'],
#                     'device': device}
#     model = ConformerModel(**model_params)
#     model.load_state_dict(model_state_dict)
#     model.eval()
#     print("Waiting for the wake word to start the recording (Wake word detector):")
#     result = work_method(stream, model, request)
#     return JsonResponse({'result':result})

    


@csrf_exempt
@require_http_methods(["POST"])
def wake_and_asr(request):
    """
    Wait for wake word and then transcribe the audio
    :param request: The request object
    :return: The transcription of the audio
    """
    start_wake_detection(request)
    results = transcribe_audio(request)
    return results

@require_http_methods(["GET"])
def healthcheck(request):
    """
    Simple healthcheck
    :param request: The request object
    """
    return JsonResponse({200: "Healthy"})
