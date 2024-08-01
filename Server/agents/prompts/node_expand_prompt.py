import json


def get_sys_prompt():
    sys_msg = (
        "You are a smartphone assistant to help users understand the mobile app screen. "
        "In the HTML code of a mobile app screen delimited by <screen></screen>, "
        "your job is to generate a list of actions related to specific UI elements on the screen.\n\n"

        "Each action in the list should include following information:\n"
        "1. action name.\n"
        "2. action description.\n"
        "3. parameters (information) required to execute the action.\n"
        "4. trigger UIs that trigger the action.\n\n"

        "***Guidelines***:\n"
        "Follow the below steps step by step:\n"
        "1. First, read through the screen HTML code delimited by <screen></screen> to grasp the overall intent of the app screen.\n"
        "2. For each UI index given, create a possible action that can be performed using the UI. "
        "But, try not to make duplicate actions. Ignore the UI index if it has the overlapping action with your previous responses.\n"
        "3. Identify parameters (information) require to execute the action.\n"
        "4. Generate questions for each parameter. Make questions as specific as possible.\n"
        "5. Merge relevant actions together by abstracting them into a bigger action with multiple parameters and multiple relevant UIs. "
        "For example, if you have 'input_name', 'input_email', 'input_phone_number' actions separately in the list, "
        "merge them into a single 'fill_in_info' action.\n\n"

        "***Hints for understanding screen***:\n"
        "1. Each HTML element represents an UI element on the screen.\n"
        "2. multiple UI elements can collectively serve a single purpose. "
        "Thus, when understanding the purpose of an UI element, looking at its parent or children element will be helpful.\n\n"

        "***Constraints when generating an action***:\n"
        "1. Try to make the actions as general as possible. Refrain from using names that are specific to the context of the screen. "
        "For example, in the case of contacts screen, instead of 'call_Bob', use 'call_contact'.\n"
        "2. Try to make parameters human friendly. Refrain from using index or code centric words as parameters. "
        "For example, in the case of contacts screen, instead of 'contact_index', use 'contact_name'.\n"
        "3. If the parameter has only FEW and IMMUTABLE valid value, give a list of options to the parameter. "
        'For example, instead of "which tab do you want to select?", use "which tab do you want to select? ["Contacts", "Dial pad", "Messages"]. '
        'BUT, If valid values are subject to change depending on the context of the user (e.g., search results, list of recommendations), do not include them to options.\n'
        '4. for "trigger_UIs", you ***Do not have to include all the relevant UIs***. Just include one or few representative UI element that can trigger the action.\n'
        '5. Always refer to your previous responses.\n\n'

        "Respond using the JSON format described below. Ensure the response can be parsed by Python json.loads.\n"
        "Response Format:\n"
        '[{“name”: <name_of_action>, “description”: <description of action>, '
        '“parameters”: {<parameter_name> : <question to ask for the parameter>, ...},'
        '"trigger_UIs”: [<index of UI elements that can trigger the action>, ...]}, ...]\n\n'

        "Begin!!"
    )
    return sys_msg


def get_first_usr_prompt(screen, trigger_ui_indexes: list, subtasks):
    usr_msg = (
        "HTML code of a mobile app screen :\n"
        f"<screen>{screen}</screen>\n\n"

        "index of UI elements to extract actions:\n"
        f"{json.dumps(trigger_ui_indexes)}\n\n"

        "actions already known:\n"
        f"{json.dumps(subtasks)}\n"
        "Do not make actions that are similar to those in the list.\n\n"

        "Try not to make duplicate actions with your previous responses. Ignore the UI index if it has the same action as before.\n\n"

        "Response:\n"
    )
    return usr_msg


def get_assistant_prompt(subtasks: list):
    assistant_msg = (
        f"{json.dumps(subtasks)}"
    )
    return assistant_msg


def get_second_usr_prompt(all_known_subtasks, unknown_ui_indexes: list):
    usr_msg = (
        "actions already known:\n"
        f"{json.dumps(all_known_subtasks)}\n"
        "Do not make actions that are similar to those in the list.\n\n"

        "index of UI elements to extract actions:\n"
        f"{json.dumps(unknown_ui_indexes)}\n\n"

        "Try not to make duplicate actions. Ignore the UI index if it has the same action as before.\n\n"

        "Response:\n"
    )
    return usr_msg


def get_prompts(screen: str, extra_subtasks: list, trigger_ui_indexes: list, supported_subtasks: list,
                unknown_ui_indexes: list):
    sys_msg = get_sys_prompt()
    usr_msg_1 = get_first_usr_prompt(screen, trigger_ui_indexes, extra_subtasks)
    assistant_msg = get_assistant_prompt(supported_subtasks)
    for subtask in supported_subtasks:
        del subtask["trigger_UIs"]
    all_known_subtasks = supported_subtasks + extra_subtasks
    usr_msg_2 = get_second_usr_prompt(all_known_subtasks, unknown_ui_indexes)
    messages = [{"role": "system", "content": sys_msg},
                {"role": "user", "content": usr_msg_1},
                {"role": "assistant", "content": assistant_msg},
                {"role": "user", "content": usr_msg_2}]
    return messages
