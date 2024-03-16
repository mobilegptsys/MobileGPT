import os
import openai
import re
import json
import requests
import base64
from utils.Utils import log

import time

def check_json_string(s: str, is_list=False):

    if is_list:
        matches = re.search(r'\[.*\]', s, re.DOTALL)

        if matches:
            return matches.group(0)
    else:
        matches = re.search(r'\{.*\}', s, re.DOTALL)

        if matches:
            return matches.group(0)

#model gpt-3.5-turbo-0125   gpt-4-0125-preview	    gpt-4-vision-preview	gpt-4

def query(messages, gpt_version, return_json=False, is_list=False):       #"gpt-4"

    sys_msg = messages[0]
    human_msg = messages[1]

    openai.api_key = os.getenv("OPENAI_API_KEY")
    messages = [{"role": "system", "content": sys_msg}, {"role": "user", "content": human_msg}]

    log("system", 'green')
    log(messages[0]["content"], 'green')

    log("user", 'green')
    log(messages[1]["content"], 'green')

    start_time = time.time()

    response = openai.chat.completions.create(
        model=gpt_version,
        messages=messages,
        temperature=0,
        max_tokens=900,
        top_p=0,
        frequency_penalty=0,
        presence_penalty=0
    )

    finish_time = time.time()

    result = response.choices[0].message.content
    usage_input_token = response.usage.prompt_tokens
    usage_output_token = response.usage.completion_tokens

    log(result, 'blue')
    log(f"usage_input_token : {usage_input_token}, usage_output_token : {usage_output_token}, latency : {finish_time-start_time}", 'blue')

    if return_json:
        return json.loads(check_json_string(result, is_list=is_list))
    else:
        return result

def vision_query(screenshot_paths : list, messages, return_json=False, is_list=False):

    sys_msg = messages[0]
    human_msg = messages[1]

    message = sys_msg + human_msg

    log("system", 'green')
    log(sys_msg, 'green')

    log("user", 'green')
    log(human_msg, 'green')

    api_key = os.getenv("OPENAI_API_KEY")

    images = []
    for screenshot_path in screenshot_paths:
        with open(screenshot_path, "rb") as image_file:
            base64_image =  base64.b64encode(image_file.read()).decode('utf-8')
            images.append(base64_image)

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    payload = {
        "model": "gpt-4-vision-preview",
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": message
                    },
                ]
            }
        ],
        "max_tokens": 2000,
        "temperature" : 0,
        "top_p" : 0,
        "frequency_penalty" : 0,
        "presence_penalty" : 0
    }

    for image in images:
        payload["messages"][0]["content"].append(
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{image}"
                }
            }
        )

    start_time = time.time()

    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload).json()

    finish_time = time.time()

    result = response["choices"][0]["message"]["content"]
    usage_input_token = response["usage"]["prompt_tokens"]
    usage_output_token = response["usage"]["completion_tokens"]

    log(result, 'blue')
    log(f"usage_input_token : {usage_input_token}, usage_output_token : {usage_output_token}, latency : {finish_time-start_time}", 'blue')

    if return_json:
        return json.loads(check_json_string(result, is_list=is_list))
    else:
        return result
