import json
from typing import List

import requests
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, BaseMessage


class OllamaWrapper:
    def __init__(self, api_key, model='llama3.1:8b', url="https://openwebui.pods.tacc.develop.tapis.io/ollama/"):
        self.api_key = api_key
        self.model = model
        self.url = url

    def invoke(self, messages: List[BaseMessage], max_tokens: int, seed: int, logprobs: bool, top_logprobs: int, temperature: float, logit_bias=None):
        response_json = request_ollama_server(self.model, self.api_key, messages, self.url, n_probs=top_logprobs, seed=seed, temperature=temperature, n_predict=max_tokens)
        return response_json
        # logprobs_list = get_ollama_logprobs(response_json)
        # logprobs_dict = {'content': [{'token': logprobs_list[0]['token'], 'logprob': logprobs_list[0]['logprob'], 'top_logprobs': logprobs_list}]}
        # ai_message = AIMessage(content=response_json["content"], response_metadata={'model_name': self.model_name, 'logprobs': logprobs_dict})
        # return ai_message


def request_ollama_server(model: str, api_key: str, messages: list, url, n_probs=20, seed=1, n_predict=256, temperature=0.0):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    data = {
        # "model": model,
        "messages": langchain_message_to_chatml(messages),
        # "max_tokens": n_predict,
    }
    response = requests.post(url, headers=headers, data=json.dumps(data))
    return response.json()


class LlamaCppWrapper:

    def __init__(self, model_path, url="http://localhost:8080/completion"):
        """
        /.../llama.cpp/llama-server -m ./models/llama-3.1-8b-instruct-f16.gguf --port 8080 --n-gpu-layers 100 --threads 1 --all-logits
        """
        self.model_path = model_path
        self.url = url

    def invoke(self, messages: List[BaseMessage], max_tokens: int, seed: int, logprobs: bool, top_logprobs: int, temperature: float, logit_bias=None):
        prompt = langchain_message_to_llama_3_prompt(messages)
        response_json = request_llama_cpp_server(prompt, self.url, n_probs=top_logprobs, seed=seed, temperature=temperature, n_predict=max_tokens)
        logprobs_list = get_llama_cpp_logprobs(response_json)
        logprobs_dict = {'content': [{'token': logprobs_list[0]['token'], 'logprob': logprobs_list[0]['logprob'], 'top_logprobs': logprobs_list}]}
        ai_message = AIMessage(content=response_json["content"], response_metadata={'model_name': self.model_path, 'logprobs': logprobs_dict})
        return ai_message


def langchain_message_to_llama_3_prompt(messages: list):
    prompt = "<|begin_of_text|>"
    for message in messages:
        if isinstance(message, SystemMessage):
            prompt += f"<|start_header_id|>system<|end_header_id|>" + message.content + "<|eot_id|>"
        elif isinstance(message, HumanMessage):
            prompt += f"<|start_header_id|>user<|end_header_id|>" + message.content + "<|eot_id|>"
        elif isinstance(message, AIMessage):
            prompt += f"<|start_header_id|>assistant<|end_header_id|>" + message.content + "<|eot_id|>"
    prompt += "<|start_header_id|>assistant<|end_header_id|>"
    return prompt


def langchain_message_to_chatml(messages: list):
    res = []
    for message in messages:
        if isinstance(message, SystemMessage):
            res.append({'role': 'system', 'content': message.content})
        elif isinstance(message, HumanMessage):
            res.append({'role': 'user', 'content': message.content})
        elif isinstance(message, AIMessage):
            res.append({'role': 'assistant', 'content': message.content})
    return res


def request_llama_cpp_server(prompt, url="http://localhost:8080/completion", n_probs=20, seed=1, n_predict=256, temperature=0.0):
    headers = {
        "Content-Type": "application/json"
    }

    data = {
        "prompt": prompt,
        "n_predict": n_predict,
        "temperature": temperature,
        "n_probs": n_probs,
        "seed": seed
    }
    response = requests.post(url, headers=headers, json=data)
    return response.json()


def get_llama_cpp_logprobs(response: dict):
    probs = response["completion_probabilities"][0]['probs']
    res = []
    for p in probs:
        res.append({'token': p['tok_str'], 'logprob': p['prob']})
    return res


if __name__ == "__main__":
    response_json = request_llama_cpp_server(prompt="Who are you?")
    print(response_json)
    print()
    print(get_llama_cpp_logprobs(response_json))
