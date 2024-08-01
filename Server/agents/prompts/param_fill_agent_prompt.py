import json

from utils.utils import generate_numbered_list


def get_sys_prompt(subtask: dict, qa_history):
    if len(qa_history) > 0:
        qa_list = generate_numbered_list(qa_history)
    else:
        qa_list = "No QA at this point."

    sys_msg = (
        "You are a smartphone assistant to help users complete task."
        "Given an HTML code of the current app screen (delimited by <screen></screen>)"
        "and a function to execute (delimited by tripple quote), your job is to fill in the parameters for the given function."
        "Your response should be in JSON format.\n\n"

        "*** Guidelines***\n"
        "1. If the exact details for a parameter aren't available, write 'unknown'. **DO NOT INVENT VALUES**\n"
        "2. In the given task, 'last' mostly means 'latest'.\n"
        "3. Refer to below QA list for more information.\n"
        "4. **YOUR RESPONSE SHOULD CLOSELY MIRROR YOUR PREVIOUS RESPONSE.** This example is a direct representation of how your answers should be formatted.\n\n"

        "QA List:\n"
        "'''\n"
        f"{qa_list}\n"
        "'''\n\n"

        "Function to fill in:\n"
        f"{json.dumps(subtask)}\n\n"

        "Respond using the JSON format described below. Ensure the response can be parsed by Python json.loads.\n\n"
        "Response Format:\n"
        '{<parameter_name>: <parameter_value, If the parameter values are not explicitly mentioned in the task or past events, just write "unknown">,...}\n'
        'Respond only with the parameters\n\n'
    )
    return sys_msg


def get_usr_prompt(instruction: str, screen: str):
    usr_prompt = (
        f"Task: '{instruction}'\n\n"

        "HTML code of the example app screen:\n"
        f"<screen>{screen}</screen>\n\n"

        "Response:\n"
    )

    return usr_prompt


def get_prompts(instruction: str, subtask: dict, qa_history: list, screen: str, example: dict):
    sys_msg = get_sys_prompt(subtask, qa_history)
    messages = [
        {"role": "system", "content": sys_msg}
    ]

    if len(example) > 0:
        example_instruction = example['instruction']
        example_screen = example['screen']
        example_usr_msg = get_usr_prompt(example_instruction, example_screen)
        messages.append({"role": "user", "content": example_usr_msg})

        example_response = example['response']['action']['parameters']
        example_response_msg = {"role": "assistant", "content": json.dumps(example_response)}
        messages.append(example_response_msg)

    usr_msg = get_usr_prompt(instruction, screen)
    messages.append({"role": "user", "content": usr_msg})
    return messages
