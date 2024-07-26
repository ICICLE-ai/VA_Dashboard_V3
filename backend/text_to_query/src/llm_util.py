def openai_completion(prompt, client, model='gpt-3.5-turbo-instruct'):
    try:
        completion = client.completions.create(model=model, prompt=prompt, max_tokens=512, n=1, stop=None)
        response_content = completion.choices[0].text.strip()
    except Exception as e:
        print(e)
        return ''
    return response_content


def openai_chat_completion(messages, client, model='gpt-3.5-turbo', json_mode=False, seed=1):
    response_format = None
    if json_mode:
        response_format = {"type": "json_object"}

    try:
        chat_completion = client.chat.completions.create(messages=messages, model=model, seed=seed, response_format=response_format)
        response_content = chat_completion.choices[0].message.content
    except Exception as e:
        print(e)
        return ''
    return response_content
