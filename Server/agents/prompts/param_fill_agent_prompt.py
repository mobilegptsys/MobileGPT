import json

from utils.utils import generate_numbered_list


def get_usr_prompt(instruction: str, subtask: dict, qa_history: list, screen: str, example: dict):
    if len(example) > 0:
        example_instruction = example['instruction']
        example_screen = example['screen']
        example_response = example['response']['action']['parameters']

        example_prompt = (
            f"Task: '{example_instruction}'\n\n"

            "Function:\n"
            f"'''{json.dumps(subtask)}'''\n\n"

            "HTML code of the example app screen:\n"
            f"<screen>{example_screen}</screen>\n\n"

            "Response:\n"
            f"{json.dumps(example_response)}"
        )
    else:
        example_prompt = (
            "No example at this point"
        )

    if len(qa_history) > 0:
        qa_list = generate_numbered_list(qa_history)
    else:
        qa_list = "No QA at this point."

    usr_msg = (
        "You are a smartphone assistant to help users complete task."
        "Given an HTML code of the current app screen (delimited by <screen></screen>)"
        "and a function to execute (delimited by tripple quote), your job is to fill in the parameters for the given function."
        "Your response should be in JSON format.\n\n"

        "*** Guidelines***\n"
        "1. If the exact details for a parameter aren't available, write 'unknown'. **DO NOT INVENT VALUES**\n"
        "2. In the given task, 'last' mostly means 'latest'.\n"
        "3. Refer to below QA list for more information.\n"
        "4. **YOUR RESPONSE SHOULD CLOSELY MIRROR THE PROVIDED EXAMPLE.** This example is a direct representation of how your answers should be formatted.\n\n"

        "QA List:\n"
        "'''\n"
        f"{qa_list}\n"
        "'''\n\n"

        "Respond using the JSON format described below. Ensure the response can be parsed by Python json.loads.\n\n"
        "Response Format:\n"
        '{<parameter_name>: <parameter_value, If the parameter values are not explicitly mentioned in the task or past events, just write "unknown">,...}\n\n'

        "[EXAMPLE]\n"
        f"{example_prompt}\n"
        "[END EXAMPLE]\n\n"

        "Your Turn:\n"
        f"Task: '{instruction}'\n\n"

        "Function:\n"
        f"'''{json.dumps(subtask)}'''\n\n"

        "HTML code of the current app screen:\n"
        f"<screen>{screen}</screen>\n\n"

        "Response:\n"
    )

    return usr_msg


def get_prompts(instruction: str, subtask: dict, qa_history: list, screen: str, example: dict):
    usr_msg = get_usr_prompt(instruction, subtask, qa_history, screen, example)
    messages = [
        {"role": "user", "content": usr_msg}]
    return messages
