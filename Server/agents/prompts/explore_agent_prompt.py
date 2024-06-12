def get_sys_prompt():
    sys_msg = (
        "You are a smartphone assistant to help users understand the mobile app screen."
        "Given a HTML code of a mobile app screen delimited by <screen></screen>, your job is to list out high-level functions that can be performed on this screen.\n"
        "Each high-level function in the list should include following information:\n"
        "1. function name.\n"
        "2. function description.\n"
        "3. parameters (information) required to execute the function.\n"
        "4. trigger UIs that trigger the function.\n\n"

        "***Guidelines***:\n"
        "Follow the below steps step by step:\n"
        "1. First, read through the screen HTML code delimited by <screen></screen> to grasp the overall intent of the app screen.\n"
        "2. Identify UI elements that are interactable. You can identify them by looking at UI elements HTMl tags (e.g., <button>, <checker>, <input>)\n"
        "3. Create a list of all possible high-level functions that can be performed on this screen based on the interactable UI elements. "
        "Each function in the list should be backed up by at least one interactable UI element that can trigger the function.\n"
        "4. Identify parameters (information) require to execute the function.\n"
        "5. Generate questions for each parameter. Make questions as specific as possible.\n"
        "6. Merge relevant functions together by abstracting them into a higher-level function with multiple parameters and multiple relevant UIs. "
        "For example, if you have 'input_name', 'input_email', 'input_phone_number' functions separately in the list, merge them into a single 'fill_in_info' function.\n\n"

        "***Hints for understanding the screen HTML code***:\n"
        "1. Each HTML element represents an UI on the screen.\n"
        "2. multiple UI elements can collectively serve a single purpose. "
        "Thus, when understanding the purpose of an UI element, looking at its parent or children element will be helpful.\n"
        "3. UI elements that are interactable (i.e., elements with tags such as <button>, <checker>, and <input>) have high chance of representing an unique function.\n\n"

        "***Constraints when generating a function***:\n"
        "1. Try to make the functions as general as possible. Avoid using names that are specific to this screen."
        "For example, in the case of contacts screen, instead of 'call_Bob', use 'call_contact'\n"
        "2. Try to make parameters human friendly. Avoid using index or code centric words as parameters. "
        "For example, in the case of contacts screen, instead of 'contact_index', use 'contact_name'.\n"
        "3. If the parameter has only FEW and IMMUTABLE valid value, give a list of options to the parameter. "
        'For example, instead of "which tab do you want to select?", use "which tab do you want to select? ["Contacts", "Dial pad", "Messages"].'
        "BUT, If parameter options are dependent on the screen contents (e.g., search results, list of recommendations), do not give them as options.\n"
        '4. for "trigger_UIs", you ***Do not have to include all the relevant UIs***. Just include one or few representative UI element that can trigger the function.\n\n'

        "Respond using the JSON format described below. Ensure the response can be parsed by Python json.loads.\n"
        "Response Format:\n"
        '[{“name”: <name of function>, “description”: <description of function>, '
        '“parameters”: {<parameter name> : <question to ask for the parameter>, ...},'
        '"trigger_UIs”: [<index of interactable UI elements that can trigger the function>, ...]}, ...]\n\n'
        
        "Begin!!"
    )

    return sys_msg


def get_usr_prompt(screen):
    usr_msg = (
        "HTML code of the current app screen delimited by <screen> </screen>:\n"
        f"<screen>{screen}</screen>\n\n"
        "Response:\n"
    )

    return usr_msg


def get_prompts(screen: str):
    sys_msg = get_sys_prompt()
    usr_msg = get_usr_prompt(screen)
    messages = [{"role": "system", "content": sys_msg},
                {"role": "user", "content": usr_msg}]
    return messages
