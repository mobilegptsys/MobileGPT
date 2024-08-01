from utils.utils import generate_numbered_list


def get_sys_prompt():
    sys_msg = (
        "You are a function merger tasked with combining similar functions together. "
        "Given a sequence of function calls, merge functions with similar purposes to make the sequence more concise.\n\n"

        "***Guidelines***:\n"
        "Follow the below steps:\n"
        "1. First read through the sequence of function calls. These functions are executed in the specified order they appear in the list.\n"
        "2. Identify function calls that are directly next to each other in the list and have the identical purposes.\n"
        '3. "Identical purposes" means they consists of the same action. Function calls that require different actions are not identical, and should not be merged. \n'
        '4. Merge consecutive function calls with "identical purposes". "Consecutive" means that the function calls are directly adjacent in the list without any other function call between them.\n'
        "5. Function calls that are similar but not consecutive (i.e., there is at least one different function call between them) should not be merged.\n\n"

        "**Example**:\n"
        "Given the function calls:\n"
        '1. {"name": "log_in", "description": "User logs into the system"}\n'
        '2. {"name": "log_in", "description": "Logs a user into the system"}\n'
        '3. {"name": "send_email", "description": "Sends an email"}\n'
        '4. {"name": "log_in", "description": "User logs into their account"}\n\n'

        "Merge the first two `log_in` functions because they are consecutive and similar. Do not merge the first and last `log_in` functions because they are not consecutive.\n\n"

        "Given the function calls:\n"
        '1. {"name": "access_more_options", "description": "Access more options"}\n'
        '2. {"name": "navigate_more_options", "description": "Navigate one of the options"}\n'
        '3. {"name": "navigate_settings", "description": "Select one of the settings menu"}\n\n'

        "Merge the first two functions (access_more_options and navigate_more_options) because they both are for selecting a option from more options menu. "
        "But Do not merge third function (navigate_settings) because it is for settings menu.\n\n"

        # "Given the function calls:\n"
        # '1. {"name": "change_settings", "description": "Go to the settings page to change the settings."}\n'
        # '2. {"name": "toggle_settings", "description": "Toggle the specific settings option."}\n\n'
        # 
        # "Do not merge these two functions because the first function (change_settings) is a more comprehensive function that includes "
        # "accessing and modifying various camera settings, while the second function, `toggle_setting`, is specifically for toggling certain settings. "
        # "Do not merge functions just because one is a subset of another.\n\n"

        "***How to Merge Function Calls***:\n"
        "1. The merged function call should have the name that appears first in the list.\n"
        "2. Rewrite the function description if necessary.\n"
        "3. Omit any redundant parameters.\n\n"

        "*** Response Format ***:\n"
        "** Explanation **\n"
        "<Explanation of why and how you merged similar function calls>\n\n"

        "```json\n"
        "[<List of merged function calls in JSON format>]\n"
        "```\n"
    )

    return sys_msg


def example_usr_prompt():
    usr_msg = """
1. {"name": "access_settings", "description": "Opens the settings menu where the user can adjust app preferences.", "parameters": {}}
2. {"name": "change_bitrate", "description": "Change the bitrate for recordings.", "parameters": {"new_bitrate": "What should be the new bitrate for recordings?"}}
3. {"name": "select_bitrate", "description": "Allows the user to select the desired bitrate for audio settings.", "parameters": {"bitrate": "Which bitrate do you want to select? ['32 kbps', '64 kbps', '96 kbps', '128 kbps']"}}
    """

    return usr_msg


def example_resopnse():
    response = """**Explanation**
1. The first function, `access_settings`, is for opening the settings menu.
2. The second function, `change_bitrate`, is for changing the bitrate for recordings.
3. The third function, `select_bitrate`, is for selecting the desired bitrate for audio settings.

The second and third functions both deal with bitrate settings and are directly next to each other in the list. Therefore, they can be merged.

**Merged Function Calls**
- The merged function will have the name of the first function in the pair, which is `change_bitrate`.
- The description will be updated to reflect both actions: changing and selecting the bitrate.
- The parameters will be combined, ensuring no redundancy.

```json
[
    {"name": "access_settings", "description": "Opens the settings menu where the user can adjust app preferences.", "parameters": {}},
    {"name": "change_bitrate", "description": "Change or select the desired bitrate for recordings or audio settings.", "parameters": {"bitrate": "Which bitrate do you want to select? [\"32 kbps\", \"64 kbps\", \"96 kbps\", \"128 kbps\", \"160 kbps\", \"192 kbps\", \"256 kbps\", \"320 kbps\"]"}}
]
```"""
    return response


def get_usr_prompt(subtask_history: list):
    numbered_history = generate_numbered_list(subtask_history, number=True)
    usr_msg = numbered_history

    return usr_msg


def get_prompts(subtask_history: list):
    sys_msg = get_sys_prompt()
    usr_msg = get_usr_prompt(subtask_history)
    messages = [{"role": "system", "content": sys_msg},
                {"role": "user", "content": example_usr_prompt()},
                {"role": "assistant", "content": example_resopnse()},
                {"role": "user", "content": usr_msg}]
    return messages
