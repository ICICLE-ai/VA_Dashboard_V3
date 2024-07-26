
# # for speech2text
# import whisperx
# import pyaudio
# import torch
# from .speechframework.models import ConformerModel
# import numpy as np
# import wave
# from speechbrain.processing.features import STFT, spectral_magnitude, Filterbank
# import torchaudio
# from torch.nn.utils.rnn import pack_sequence
# from transformers import BertTokenizer
# from django.shortcuts import render
# import torch.nn as nn


# TOK = BertTokenizer.from_pretrained('bert-base-uncased')


# model_asr = whisperx.load_model("small", 'cpu', compute_type="int8", language="en")
# whisperx_align, metadata = whisperx.load_align_model(language_code="en", device="cpu")
# model_vad, utils = torch.hub.load(repo_or_dir='snakers4/silero-vad',
#                                 model='silero_vad',
#                                 force_reload=True)
# FORMAT = pyaudio.paInt16
# CHANNELS = 1
# SAMPLE_RATE = 16000
# CHUNK = 1024

# def process_frame(indata, frames, data, model, request):
#     """
#     Process the audio frame
#     :param indata: The current input chunk of audio data
#     :param frames: The list of frames for collecting the audio data
#     :param data: The audio data accumulated so far
#     :param model: The wake word detection model
#     :param request: The request object
#     :return: The presence/absence of the wake word
#     :description:  Audio preprocessing -> feature extraction -> input to the model -> Thresholding the output

#     """
#     indata = np.frombuffer(indata, np.int8)
#     a = int(indata.size)
#     if a < 1024:
#         indata = np.pad(indata, (0, 1024-a), mode='constant', constant_values=0)
#     frames.append(indata)  # Apply windowing function to the input frame
#     num_frames = 16
#     if len(frames) >= num_frames:
#         wav_file = save_file(data)
#         data.pop(0)
#         frames.pop(0)  # Clear the frames list
#         filterbank = Filterbank(n_mels=40)
#         stft = STFT(sample_rate=16000, win_length=25, hop_length=10, n_fft=400)
#         wavform, sr = torchaudio.load(wav_file)
#         wavform = wavform.type('torch.FloatTensor')
#         if sr > 16000:
#             wavform = torchaudio.transforms.Resample(sr, 16000)(wavform)
#         features = stft(wavform)
#         features = spectral_magnitude(features)
#         features = filterbank(features)
#         features = pack_sequence(features, enforce_sorted=False)
#         text = request.body.decode() # The word selected by the user on the front end
#         text = TOK(text).input_ids
#         text = torch.tensor(text)
#         text = [text]
#         text = pack_sequence(text, enforce_sorted=False)
#         with torch.no_grad():
#             output = model(features, text)

#         best = np.where(output < 0.75, 0, 1)
#         if best != 1:
#             print(".................")
#         else:
#             print(output)
#             print("Detected", end='')
#             return True


# def save_file(data):
#     """
#     Saves the audio file to the disk
#     :param data: List of audio data chunks
#     :return: The name of the saved file
    
#     """
#     output_file = "my_voice.wav"
#     sample_width = 2  # 2 bytes for 16-bit audio, 1 byte for 8-bit audio
#     with wave.open(output_file, 'wb') as wf:
#         wf.setnchannels(CHANNELS)
#         wf.setsampwidth(sample_width)
#         wf.setframerate(SAMPLE_RATE)

#         for chunk in data:
#             wf.writeframes(chunk)
#         wf.close()
#     return output_file


# def int2float(sound):
#     """
#     Convert the integer audio data to float
#     :param sound: The audio data
#     :return: The audio data in float format

#     """
#     abs_max = np.abs(sound).max()
#     sound = sound.astype('float32')
#     if abs_max > 0:
#         sound *= 1/32768
#     sound = sound.squeeze()  # depends on the use case
#     return sound



# def work_method(stream, model, request):
#     """
#     The main method for the audio processing
#     :param stream: The open stream object
#     :param model: Wake word detection model
#     :param request: The request object
#     :return: The presence/absence of the wake word after double checking the transcription
#     :description: This method processes the incoming audio frames to look for the wake word
#     """
#     frames = []
#     data = []
#     res = True
#     while res:
#         curr_chunk = stream.read(1024, exception_on_overflow=False)
#         data.append(curr_chunk)
#         print("....waiting....", end='')
#         wake_word_detector = process_frame(curr_chunk, frames, data, model, request)
#         if wake_word_detector:
#             res = False
#             wav_file = save_file(data)
#             audio = whisperx.load_audio(wav_file)
#             output = model_asr.transcribe(audio, 2)
#             text = request.body.decode()
#             print(output)
#             print(text)
#             if output['segments'] == text:
#                 print("The wake word has been detected")
#                 return wake_word_detector
#             if output['segments'] != text:
#                 print("******************************", end='')



import whisperx
import pyaudio
import torch
from .speechframework.models import ConformerModel
import numpy as np
import wave
from speechbrain.processing.features import STFT, spectral_magnitude, Filterbank
import torchaudio
from torch.nn.utils.rnn import pack_sequence
from transformers import BertTokenizer
import torch.nn as nn
import sys
from string import punctuation
from pdb import set_trace as bp
from django.http import HttpResponse, HttpResponseServerError, JsonResponse


TOK = BertTokenizer.from_pretrained('bert-base-uncased')
model_asr = whisperx.load_model("small", 'cpu', compute_type="int8", language="en")
whisperx_align, metadata = whisperx.load_align_model(language_code="en", device="cpu")
model_vad, utils = torch.hub.load(repo_or_dir='snakers4/silero-vad',
                                model='silero_vad',
                                force_reload=True)
FORMAT = pyaudio.paInt16
CHANNELS = 1
SAMPLE_RATE = 16000
CHUNK = 1024
SILENCE_THRESHOLD = 80  # in milliseconds
(get_speech_timestamps,
 save_audio,
 read_audio,
 VADIterator,
 collect_chunks) = utils

vad_iterator = VADIterator(model_vad)


def save_file(data):
    """
    Saves the audio file to the disk
    :param data: List of audio data chunks
    :return: The name of the saved file
    
    """
    output_file = "my_voice.wav"
    sample_width = 2  # 2 bytes for 16-bit audio, 1 byte for 8-bit audio
    with wave.open(output_file, 'wb') as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(sample_width)
        wf.setframerate(SAMPLE_RATE)

        for chunk in data:
            wf.writeframes(chunk)
        wf.close()
    return output_file

def load_wavform(file):
    """
    Loads wavform file with a sample rate of 16000
    :file: The path to the file to load
    :return: The loaded wavform object
    """
    wavform, sr = torchaudio.load(file)

    wavform = wavform.type('torch.FloatTensor')
    if sr > 16000:
        wavform = torchaudio.transforms.Resample(sr, 16000)(wavform)
    return wavform


def get_features(wavform):
    """
    Extracts features from the audio data
    :param wavform: The audio data
    :return: The extracted features
    """
    filterbank = Filterbank(n_mels=40)
    stft = STFT(sample_rate=16000, win_length=25, hop_length=10, n_fft=400)

    features = stft(wavform)
    features = spectral_magnitude(features)
    features = filterbank(features)
    features = pack_sequence(features, enforce_sorted=False)

    return features

def get_text(request):
    """
    Tokenizes the text
    :param request: The request object
    :return: The tokenized text
    
    """
    text = request.body.decode() 
    text = TOK(text).input_ids
    text = torch.tensor(text)
    text = [text]
    text = pack_sequence(text, enforce_sorted=False)
    return text


def get_match_probs(indata, frames, data, model, request):
    """
    If enough frames are collected, gets the probability they match the wake word
    :param indata: The current input chunk of audio data
    :param frames: The list of frames for collecting the audio data
    :param data: The audio data accumulated so far
    :param model: The wake word detection model
    :param request: The request object
    :return: The probability the wake word is present in the given audio segments or None if not enough frames
    """
    # get most recent audio chunk into np array of size 1024
    indata = np.frombuffer(indata, np.int8)
    a = int(indata.size)
    if a < 1024:
        indata = np.pad(indata, (0, 1024-a), mode='constant', constant_values=0)

    # add the chunk to our frames
    frames.append(indata)  # Apply windowing function to the input frame
    num_frames = 16

    # if we have enough frames, we can run the model
    output = None
    if len(frames) >= num_frames:
        # save the audio data to a file
        wav_file = save_file(data)
        data.pop(0)
        # clear the frames list
        frames.pop(0)
        wavform = load_wavform(wav_file)
        features = get_features(wavform)
        # The word selected by the user on the front end
        text = get_text(request)
        with torch.no_grad():
            output = model(features, text)
    return output
    

def check_for_word(indata, frames, data, model, request):
    """
    Determines if a word was found
    :param indata: The current input chunk of audio data
    :param frames: The list of frames for collecting the audio data
    :param data: The audio data accumulated so far
    :param model: The wake word detection model
    :param request: The request object
    :returns: whether a word was found and the match probability if it was found (otherwise None)
    """
    output = get_match_probs(indata, frames, data, model, request)
    # If the model outputs the word is detected with a confidence of 0.75 or more, we return True
    if output is None or np.where(output < 0.75, 0, 1) != 1:
        return False, None
    else:
        print(f"\nDetected a word with {output} confidence")
        return True, output


def strip_format(s):
    s = s.translate(str.maketrans('', '', punctuation))
    s = s.strip()
    s = s.lower()
    return s

def wait_to_wake(stream, model, request):
    """
    Waits for the wake word 
    :param stream: The open stream object
    :param model: Wake word detection model
    :param request: The request object
    :return: The presence/absence of the wake word after double checking the transcription and the associated probabilities
    :description: This method processes the incoming audio frames to look for the wake word
    """
    frames = []
    data = []
    res = True
    print("Now waiting....")
    while res:
        # add the current chunk to the data list
        curr_chunk = stream.read(1024, exception_on_overflow=False)
        data.append(curr_chunk)
        # check if the wake word is detected
        is_word, wake_probs = check_for_word(curr_chunk, frames, data, model, request)
        if is_word:
            res = False
            print("The wake word has been detected")
            return True, wake_probs
        else:
            print(".", end='')
                # return False, wake_probs


def start_wake_detection(request):
    """
    Initialize audio processes in IKLE mode and wait for wake word
    :param request: The request object
    :return: None
    :description: This method opens the audio stream, loads the wake word model and waits for the wake word to return

    """
    audio = pyaudio.PyAudio()
    stream = audio.open(format=FORMAT,
                        channels=CHANNELS,
                        rate=SAMPLE_RATE,
                        input=True,
                        frames_per_buffer=1024)
    device = torch.device('cpu')
    checkpoint_path = "word_level_train_015_256_bert1_st00_2fc_conf_16_sig_bce_rop_80.pt"
    pretrained_model = torch.load(checkpoint_path, map_location=device)
    model_state_dict = pretrained_model["model_state_dict"]
    model_params = {'num_classes': pretrained_model['model_params']['num_classes'],
                    'feature_size': pretrained_model['model_params']['feature_size'],
                    'hidden_size': pretrained_model['model_params']['hidden_size'],
                    'num_layers': pretrained_model['model_params']['num_layers'],
                    'dropout': pretrained_model['model_params']['dropout'],
                    'bidirectional': pretrained_model['model_params']['bidirectional'],
                    'device': device}
    model = ConformerModel(**model_params)
    model.load_state_dict(model_state_dict)
    model.eval()
    print("Waiting for the wake word to start the recording (Wake word detector):")
    is_wake_word, wake_probs = wait_to_wake(stream, model, request)
    return wake_probs


def int2float(sound):
    """
    Convert the integer audio data to float
    :param sound: The audio data
    :return: The audio data in float format
    """
    abs_max = np.abs(sound).max()
    sound = sound.astype('float32')
    if abs_max > 0:
        sound *= 1/32768
    sound = sound.squeeze()  # depends on the use case
    return sound


def get_latest_audio(stream, data, sample_rate=16000):
    """
    Grabs the latest audio data from the stream, processes it, and pads it if necessary.
    :param stream: The open stream object from PyAudio.
    :param data: The list to accumulate audio data chunks.
    :param sample_rate: The sample rate of the audio stream (default: 16000).
    :return: Processed audio data as a torch.Tensor.
    """
    audio_chunk = stream.read(1024, exception_on_overflow=False)  # Read audio chunk from the stream
    data.append(audio_chunk)  # Append audio chunk to data list
    
    # Convert audio chunk from int16 to float32
    audio_int16 = np.frombuffer(audio_chunk, np.int16)
    audio_float32 = audio_int16.astype(np.float32) / 32767.0  # Normalize to range [-1, 1]
    audio_tensor = torch.from_numpy(audio_float32)  # Convert to torch.Tensor
    
    # Determine expected number of samples based on sample rate
    if sample_rate == 8000:
        expected_samples = 256
    elif sample_rate == 16000:
        expected_samples = 512
    else:
        raise ValueError(f"Unsupported sample rate: {sample_rate}. Expected 8000 or 16000 Hz.")
    
    # Ensure audio tensor has expected number of samples
    if audio_tensor.size(0) < expected_samples:
        pad_length = expected_samples - audio_tensor.size(0)
        padding = nn.ConstantPad1d((0, pad_length), 0.0)
        audio_tensor = padding(audio_tensor)
    elif audio_tensor.size(0) > expected_samples:
        audio_tensor = audio_tensor[:expected_samples]  # Trim excess samples
    
    return audio_tensor


def save_file(data):
    """
    Saves the audio file to the disk
    :param data: List of audio data chunks
    :return: The name of the saved file
    
    """
    output_file = "my_voice.wav"
    sample_width = 2  # 2 bytes for 16-bit audio, 1 byte for 8-bit audio
    with wave.open(output_file, 'wb') as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(sample_width)
        wf.setframerate(SAMPLE_RATE)

        for chunk in data:
            wf.writeframes(chunk)
        wf.close()
    return output_file


def transcribe_audio(request):
    """
    Records and transcribes the audio
    Should be called after the wake word is detected
    :param request: The request object
    :return: JsonResponse with the transcription results
    """
    audio = pyaudio.PyAudio()
    stream = audio.open(format=FORMAT,
                        channels=CHANNELS,
                        rate=SAMPLE_RATE,
                        input=True,
                        frames_per_buffer=1024)
    
    if request.method == 'POST':
        is_wake_word = True
        data = []
        count = 0
        continue_recording = True 
    else:
        is_wake_word = False
        continue_recording = False

    while continue_recording:
        # Record the incoming audio
        audio_float32 = get_latest_audio(stream, data)
        
        # Check if the audio is silent and if so count the number of milliseconds
        try:
            new_confidence = model_vad(audio_float32, 16000).item()
        except Exception:
            save_file(data)
            continue
        
        is_voice = round(new_confidence)
        if is_voice == 0:
            count += 1
            print('.', sep=' ', end='', flush=True)
        else:
            count = 0  # Reset the count if the value is not 0
        
        # If 80 milliseconds of silence is detected, stop the recording
        if count == 80:
            print(f"{count} milliseconds elapsed during waiting")
            res = save_file(data)
            continue_recording = False
            
            # Transcribe the audio and align the transcription with the audio
            audio = whisperx.load_audio(res)
            result = model_asr.transcribe(audio, 2)
            result2 = whisperx.align(result["segments"], whisperx_align, metadata, audio, 'cpu', return_char_alignments=False)
            
            
            print(result["segments"][0]["text"]) if result["segments"] else print("No speech detected") ##This prints the text after detecting the wake word
            print(result2["word_segments"])
            
            # Prepare JSON response
            response_data = {
                "transcription": result2["word_segments"],
                "language": "en"  # Assuming English language for transcription
            }
            
            return JsonResponse(response_data)
    
    stream.stop_stream()
    stream.close()
    
    # If no transcription found, return empty response
    return JsonResponse({"transcription": [], "language": "en"})


# def wake_and_asr(request):
#     """
#     Wait for wake word and then transcribe the audio
#     :param request: The request object
#     :return: The transcription of the audio
#     """
#     start_wake_detection(request)
#     results = transcribe_audio(request)
#     return results