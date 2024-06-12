from utils.utils import generate_numbered_list


def get_sys_prompt():
    sys_msg = (
        "You are a function merger tasked with combining similar functions together. "
        "Given a sequence of function calls, merge functions with similar purposes to make the sequence more concise.\n\n"

        "***Guidelines***:\n"
        "Follow the below steps:\n"
        "1. First read through the sequence of function calls. These functions are executed in the specified order they appear in the list.\n"
        "2. Identify function calls that are directly next to each other in the list and serve similar purposes.\n"
        '3. Merge these similar consecutive function calls. "Consecutive" means that the function calls are directly adjacent in the list without any other function call between them.\n'
        "4. Function calls that are similar but not consecutive (i.e., there is at least one different function call between them) should not be merged.\n\n"
        
        "**Example**:\n"
        "Given the function calls:\n"
        '1. {"name": "log_in", "description": "User logs into the system"}\n'
        '2. {"name": "log_in", "description": "Logs a user into the system"}\n'
        '3. {"name": "send_email", "description": "Sends an email"}\n'
        '4. {"name": "log_in", "description": "User logs into their account"}\n\n'
        
        "Merge the first two `log_in` functions because they are consecutive and similar. Do not merge the first and last `log_in` functions because they are not consecutive.\n\n"

        "***Hints for Merging Function Calls***:\n"
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


def get_usr_prompt(subtask_history: list):
    numbered_history = generate_numbered_list(subtask_history)
    usr_msg = numbered_history

    return usr_msg


def get_prompts(subtask_history: list):
    sys_msg = get_sys_prompt()
    usr_msg = get_usr_prompt(subtask_history)
    messages = [{"role": "system", "content": sys_msg},
                {"role": "user", "content": usr_msg}]
    return messages
