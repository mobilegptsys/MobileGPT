from utils.utils import generate_numbered_list

default_subtasks = [
    {"name": "scroll_screen",
     "description": "Useful when you need to scroll up or down to view more UIs and actions. Make sure to stop when you find that you want.",
     "parameters": {
         "scroll_ui_index": "index of the UI to scroll",
         "direction": "direction to scroll",
         "target_info": "what are you looking for?"}
     },
    {"name": "speak",
     "description": "Tell information in the screen to the user. Use this only when the user has explicitly stated you to tell him something.",
     "parameters": {
         "message": "what you want to say to the user in natural language (non-question format)."}
     },
    {"name": "finish",
     "description": "Use this to signal that the request has been completed",
     "parameters": {}
     }
]


def get_sys_prompt(available_subtasks):
    subtasks = available_subtasks + default_subtasks
    numbered_subtasks = generate_numbered_list(subtasks)
    sys_msg = (
        "You are a smartphone assistant to help users use the mobile app. "
        "Given a list of actions available on the current mobile screen (delimited by <screen></screen>) and past events that lead to this screen, determine the next action to take in order to complete the user's request.\n\n"

        "***Guidelines***:\n"
        "Follow the below steps step by step:\n"
        "1. First, read through history of past events (delimited by triple quotes) to grasp the overall flow of the execution.\n"
        "2. Read through the screen HTML code delimited by <screen></screen> to grasp the overall intent of the current app screen.\n"
        "3. Select an action that will bring you closer to completing the user's request. If past events indicate that the request has been completed, select 'finish' action. Do not proceed further steps.\n"
        "4. If you believe the required action is not on the list, you can make a new one.\n"
        "5. Based on the user's request, screen HTML code, and the QA list, fill in the parameters of the selected action.\n"
        "6. Self-evaluate how close you are to completing the subtask\n\n"

        "***Constraints for selecting an action***:\n"
        "1. You can perform only a single action at a time.\n"
        "2. Always select the best matching action. You can make a new one if the required action is not on the list. The new action must be very specific in its purpose, not just 'click' or 'input' something.\n"
        "3. Always reflect on past events to determine your next action. Avoid repeating the same action.\n"
        "4. If the action's parameters are not explicitly mentioned anywhere in the prompt, just write 'unknown'. Never assume or guess the parameter's values.\n\n"

        "List of available actions:\n"
        f"{numbered_subtasks}"
        "- If the required action is not on the list, you can make a new one. Make sure the new action is very specific in its purpose, not just 'click' or 'input' something. Provide a detailed description of the action and its parameters in the following structured json format.\n"
        '- {"name": <new action name>, "description": <detailed description of the new action>, "parameters": {<parameter_name>: <description of the parameters, including list of available options>,...}}\n\n'


        "Respond using the JSON format described below\n"
        "Response Format:\n"
        '{"reasoning": <reasoning based on past events and screen HTML code>, '
        '"new_action"(include only when you need to make a new action): {"name": <new action name. This must not be click or input>, "description": <detailed description of the new action>, "parameters": {<parameter_name>: <description of the parameters, including available options>,...}},'
        '"action": {"name":<action_name>, "parameters": {<parameter_name>: <parameter_value, If the parameter values are not explicitly mentioned in the prompt, just write "unknown">,...}},'
        '"completion_rate": <how close you are to completing the task>, '
        '"speak": <brief summary of the action in natural language to communicate with the user. Make it short.>}\n'
        "Begin!"
    )
    return sys_msg


def get_usr_prompt(instruction, subtask_history, qa_history, screen):
    if len(subtask_history) == 0:
        numbered_subtask_history = "0. No event yet.\n"
    else:
        numbered_subtask_history = generate_numbered_list(subtask_history)

    if len(qa_history) == 0:
        numbered_qa_history = "No QA at this point."
    else:
        numbered_qa_history = generate_numbered_list(qa_history)

    usr_msg = (
        f"User's Request: {instruction}\n\n"

        "QA List:\n"
        "'''\n"
        f"{numbered_qa_history}"
        "'''\n\n"

        "Past Events:\n"
        "'''\n"
        f"{numbered_subtask_history}'''\n\n"

        "HTML code of the current app screen delimited by <screen> </screen>:\n"
        f"<screen>{screen}</screen>\n\n"

        "Constructively self-evaluate how close you are to completing the request. "
        "If past events indicate that the user's request has been accomplished, You must select the 'finish' action. Do not proceed further steps.\n\n"
        "Response:\n"
    )

    return usr_msg


def get_prompts(instruction: str, available_subtasks: list, subtask_history: list, qa_history: list, screen: str):
    sys_msg = get_sys_prompt(available_subtasks)
    usr_msg = get_usr_prompt(instruction, subtask_history, qa_history, screen)
    messages = [{"role": "system", "content": sys_msg},
                {"role": "user", "content": usr_msg}]
    return messages
