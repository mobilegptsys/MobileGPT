import json

from utils.utils import generate_numbered_list

default_actions = [
    {
        "name": "ask",
        "description": "Ask the user more information to complete the task. Avoid asking unnecessary information or confirmation from the user",
        "parameters": {"info_name": {"type": "string",
                                     "description": "name of the information you need to get from the user (Info Name)"},
                       "question": {"type": "string",
                                    "description": "question to ask the user to get the information"}},
    },
    {
        "name": "click",
        "description": "Click a specific button on the screen",
        "parameters": {"index": {"type": "integer", "description": "index of the UI element to be clicked"}}
    },
    {
        "name": "long-click",
        "description": "Long-click a UI. You can use this only for UIs with long-clickable attribute",
        "parameters": {"index": {"type": "integer", "description": "index of the UI element to be clicked"}}
    },
    # {
    #     "name": "long-click",
    #     "description": "Long-click a UI to see more options relevant to the UI. You can use this only for UIs with long-clickable attribute",
    #     "parameters": {"index": {"type": "integer", "description": "index of the UI element to be clicked"}}
    # },
    {
        "name": "input",
        "description": "Input text on the screen.",
        "parameters": {"index": {"type": "integer", "description": "index of the UI element that takes text input"},
                       "input_text": {"type": "string", "description": "text or value to input"}}
    },
    {
        "name": "scroll",
        "description": "Scroll up or down to view more UIs",
        "parameters": {"index": {"type": "integer", "description": "index of the UI element to scroll."},
                       "direction": {"type": "string", "description": "direction to scroll, default='down'",
                                     "enum": ["up", "down"]}}
    },
    {
        "name": "repeat-click",
        "description": "Repeat click action multiple times",
        "parameters": {"index": {"type": "integer", "description": "index of the UI element to clicked."},
                       "number": {"type": "integer", "description": "number of times you want to click."}}
    },
    {
        "name": "finish",
        "description": "Use this to signal that you have finished the given subtask.",
        "parameters": {}
    }
]


def get_sys_prompt():
    numbered_actions = generate_numbered_list(default_actions)
    sys_msg = (
        "You are a smartphone assistant agent that can interact with a mobile app. Your job is to help users use the mobile app by guiding users how to perform specific subtask within their final goal."
        "Given a list of actions available on the current mobile screen (delimited by <screen></screen>) and past events that lead to this screen, determine the next action to take in order to complete the given subtask.\n\n"

        "***Guidelines***:\n"
        "Follow the below steps step by step:\n"
        "1. First, read through history of past events (delimited by triple quotes) to grasp the overall flow of the task execution.\n"
        "2. Read through the screen HTML code delimited by <screen></screen> to grasp the overall intent of the current app screen.\n"
        "3. Select an action that will bring you closer to completing the given subtask. If past events indicate that the task has been completed, select 'finish' action.\n"
        "4. Self-evaluate how close you are to completing the subtask\n"
        "5. Plan your next moves\n\n"

        "***Hints for understanding the screen HTML code***:\n"
        "1. Each HTML element represents an UI element on the screen.\n"
        "2. multiple UI elements can collectively serve a single purpose. "
        "Thus, when understanding the purpose of an UI element, looking at its parent or children element will be helpful.\n\n"

        "***Hints for selecting the next action***:\n"
        "1. Always reflect on past events to determine your next action. Avoid repeating the same action.\n"
        '2. If you need more information to complete the task, use "ask" command to get more information from the user. '
        "But be very careful not to ask unnecessarily or repeatedly. If human don't know the answer, do your best to find it out yourself.\n"

        "***Constraints for selecting an action***:\n"
        "1. You can perform only single action at a time.\n"
        "2. Exclusively use the actions listed below.\n"
        "3. Make sure to select the 'finish' action when past events indicate that the subtask has been completed.\n"
        "4. Only complete the subtask given to you. The rest is up to the user. Do not proceed further steps.\n\n"

        "List of available actions:\n"
        f"{numbered_actions}\n"


        "Make sure to select the 'finish' action when past events indicate that the given subtask has been completed.\n\n"

        "Respond using the JSON format described below\n"
        "Response Format:\n"
        '{"reasoning": <reasoning based on past events and screen HTML code>, "action": {"name":<action_name>, "parameters": {<parameter_name>: <parameter_value>,...}},'
        '"completion_rate": <indicate how close you are to completing the task>, "plan": <plan for your next moves>}\n'
        "Begin!"
    )
    return sys_msg


def get_usr_prompt(instruction, subtask, history, screen, examples):
    if len(history) == 0:
        numbered_history = "0. No event yet.\n"
    else:
        numbered_history = generate_numbered_list(history)

    usr_msg = ""
    if len(examples) > 0:
        for i, example in enumerate(examples):
            example_instruction = example['instruction']
            example_subtask = example['subtask']
            example_screen = f"...(abbreviated for brevity)...{example['screen']}...(abbreviated for brevity)..."
            example_response = example['response']

            usr_msg += (
                f"[EXAMPLE #{i}]\n"
                f"User's final goal (instruction): {example_instruction}\n"
                "(Only complete the below subtask given to you. You can ignore parameters with unknown values. But Do not proceed further steps)\n"
                f"Subtask given to you: {example_subtask}\n\n"

                "Past Events:\n"
                "'''\n"
                f"...(abbreviated for brevity)...\n"
                f"'''\n\n"

                "HTML code of the current app screen delimited by <screen> </screen>:\n"
                f"<screen>{example_screen}</screen>\n\n"

                "Response:\n"
                f"{example_response}\n"
                f"[END OF EXAMPLE {i}]\n\n"
            )

        usr_msg += "Your Turn:\n"

    usr_msg += (
        f"User's final goal (instruction): {instruction}\n"
        "(Only complete the below subtask given to you. You can ignore parameters with unknown values. But Do not proceed further steps)\n"
        f"Subtask given to you: {json.dumps(subtask)}\n\n"

        "Past Events:\n"
        "'''\n"
        f"{numbered_history}\n"
        f"'''\n\n"

        "HTML code of the current app screen delimited by <screen> </screen>:\n"
        f"<screen>{screen}</screen>\n\n"

        "Response:\n"
    )

    return usr_msg


def get_prompts(instruction: str, subtask: dict, history: list, screen: str, examples: list):
    sys_msg = get_sys_prompt()
    usr_msg = get_usr_prompt(instruction, subtask, history, screen, examples)
    messages = [{"role": "system", "content": sys_msg},
                {"role": "user", "content": usr_msg}]
    return messages
