
def make_messages(encoded_xml, is_vision=True):
    if is_vision:

        sys_msg = \
"""Given a HTML code of a mobile app screen delimited by <screen></screen> and screenshot(labeled), list out all actions can be done on this screen. The HTML code represents the screen of a mobile app, with each node representing an UI element on the screen. and look the given screenshot.(current mobile app)

Reference the five HTML code Reading advice:
1. Having prior knowledge to understand the overall HTML code and identify the nature of the page(screenshot) will be helpful.
2. Matching screenshot's ui index with HTML code's ui index is very helpful to understand this mobile app
3. Tags such as <button>, <checker>, and <input> exist for user interaction through clicks. These tags have the potential to trigger actions (action will change currnet screen).
4. Primarily understanding the types of tags, their IDs, descriptions, and text is a priority.
5. Understanding the parent tags of elements that have the potential for action will be beneficial.
6. The <button> tag in <button id='click_target' clickable='true' index='22'> <img id='photo' index='23'/> <p id='contact_name' index='24' type='text'>Create new contact</p> </button> might not reveal its function directly at first glance. However, the purpose of the button can be inferred from its child tags, such as <img> and <p>. For example, in this case, the inclusion of text 'Create new contact' and an image suggests that the button is used for adding a new contact. It's important to consider the button and its child elements together to understand the overall function and intent of the button. Additionally, if there is another clickable button among the child elements, that child should be regarded as an independent element with its own separate functionality.
             
Follow the seven steps step by step:
1. Read and understand the mobile screen HTML code delimited by <screen></screen> and mobile screenshot
2. Identify all possible actions(many!) that must be performed surely on this mobile screen. The reasons for the judgment must be clear.
3. Identify UI elements relevant to the actions.
4. Identify information (parameters) required to execute the action.
5. Generate questions for information required to perform the action. Make questions as specific as possible.
6. Merge all actions considered similar functionality by abstracting them into a bigger action with multiple parameters. Try to make the list connotative as possible. An action can include multiple relevant UIs. For example, if you have “input_name”, “input_email”, “input_phone_number” actions, merge them into a single “fill_in_info” action. If each action is perceived to have unique functionality, they should not be merged.
7. Summary of the current screen's all of actions (except the current screen's information! You can use only extracted actions in the step).

Check the below four constraints:
1. Try to make the actions as general as possible. Refrain from using names that are specific to the context of the screen. For example, in the case of contacts screen, instead of “call_Bob”, use “call_contact”
2. Try to make parameters human friendly. Refrain from using index or code centric words as parameters. For example, in the case of contacts screen, instead of “contact_index”, use “contact_name”
3. Try to give list of options to the parameter’s question if the parameter has only short and unique valid values (Lists of recommendations, contacts, or search results are not unique because their values can change later. What remains constant are settings or the names of Tabs, which are unique.). If valid values are names specific to the context of the screen, omit the options (Constraint 1). For example, instead of “which tab do you want to select?“, use “which tab do you want to select? ['Contacts', 'Dialpad', 'Messages']"
4. When you assigning UI elements to the action, only HTML tags such as <button>, <input>, and <checker>(It doesn't have to be a tag listed, as long as it's a tag that triggers interaction when viewed.) that enable user interaction through user's input should be assigned. Not all UI should be assigned. And don't duplicate!!

"""

    else:
        sys_msg = \
"""Given a HTML code of a mobile app screen delimited by <screen></screen>, list out what can be done on this screen. The HTML code represents the screen of a mobile app, with each node representing an UI element on the screen.

Reference the five HTML code Reading advice:
1. Having prior knowledge to understand the overall HTML code and identify the nature of the page will be helpful.
2. Tags such as <button>, <checker>, and <input> exist for user interaction through clicks. These tags have the potential to trigger actions (action will change currnet screen).
3. Primarily understanding the types of tags, their IDs, descriptions, and text is a priority.
4. Understanding the parent tags of elements that have the potential for action will be beneficial.
5. The <button> tag in <button id='click_target' clickable='true' index='22'> <img id='photo' index='23'/> <p id='contact_name' index='24' type='text'>Create new contact</p> </button> might not reveal its function directly at first glance. However, the purpose of the button can be inferred from its child tags, such as <img> and <p>. For example, in this case, the inclusion of text 'Create new contact' and an image suggests that the button is used for adding a new contact. It's important to consider the button and its child elements together to understand the overall function and intent of the button. Additionally, if there is another clickable button among the child elements, that child should be regarded as an independent element with its own separate functionality.
             
             
Follow the seven steps step by step:
1. Read and understand the mobile screen HTML code delimited by <screen></screen>
2. Identify all possible actions that must be performed surely on this mobile screen. The reasons for the judgment must be clear.
3. Identify UI elements relevant to the actions.
4. Identify information (parameters) required to execute the action.
5. Generate questions for information required to perform the action. Make questions as specific as possible.
6. Merge all actions considered similar by abstracting them into a bigger action with multiple parameters. Try to make the list connotative as possible. An action can include multiple relevant UIs. For example, if you have “input_name”, “input_email”, “input_phone_number” actions, merge them into a single “fill_in_info” action. When combining similar actions, if each action is perceived to have unique functionality, they should not be merged.
7. Summary of the current screen's all of actions (except the current screen's information! You can use only extracted actions in the step).


Check the below four constraints:
1. Try to make the actions as general as possible. Refrain from using names that are specific to the context of the screen. For example, in the case of contacts screen, instead of “call_Bob”, use “call_contact”
2. Try to make parameters human friendly. Refrain from using index or code centric words as parameters. For example, in the case of contacts screen, instead of “contact_index”, use “contact_name”
3. Try to give list of options to the parameter’s question if the parameter has only short and unique valid values (Lists of recommendations, contacts, or search results are not unique because their values can change later. What remains constant are settings or the names of Tabs, which are unique.). If valid values are names specific to the context of the screen, omit the options (Constraint 1). For example, instead of “which tab do you want to select?“, use “which tab do you want to select? ['Contacts', 'Dialpad', 'Messages']"
4. When you assigning UI elements to the action, only HTML tags such as <button>, <input>, and <checker>(It doesn't have to be a tag listed, as long as it's a tag that triggers interaction when viewed.) that enable user interaction through user's input should be assigned. Not all UI should be assigned. And don't duplicate!!

"""

    human_msg = \
f"""Based on HTML code, find all possible actions from this mobile screen
Screen:
<screen>{encoded_xml}</screen>

Respond using the JSON format described below. and you can answer this JSON format. Don't add any explanation.

Response Format:
{{"Actions": [{{“name”: <name_of_action>, “description”: <description of action>, “parameters”: {{<parameter_name> : <question to ask for the parameter>, ...}},“UI_index”: [<index of relevant interactable UI element>, ...]}}, ...], "summary_this_screen_general_actions":<summary about the extracted general actions like screen explanation>>}}

check again that you found all of actions about currnet screen.
"""

    return [sys_msg, human_msg]


def make_message_expand(encoded_xml, sub_tasks, unknown_uis, is_vision=False):
    if is_vision:

        sys_msg = \
"""Given a HTML code of a mobile app screen delimited by <screen></screen> and screenshot(labeled), match the checking list(UI indexes) to given previous action list. The HTML code and screenshot represents the screen of a mobile app, with each node representing an UI element on the screen.

Reference the five HTML code Reading advice:
1. Having prior knowledge to understand the overall HTML code and identify the nature of the page(screenshot) will be helpful.
2. Matching screenshot's ui index with HTML code's ui index is very helpful to understand this mobile app
            
Follow the seven steps step by step:
1. read the already made action list from similar screen
2. match the each UI index about given action list's action (if there is not matching, you can skip.).
3. Identify the mismatched ui index's action that must be performed surely on this mobile screen. The reasons for the judgment must be clear. (if the ui index's node is dummy or can't infer reasonable action, you must skip!)
4. Identify UI elements relevant to the new actions.
5. Identify information (parameters) required to execute the action.
6. Generate questions for information required to perform the action. Make questions as specific as possible.
7. Merge all actions considered similar by abstracting them into a bigger action with multiple parameters. Try to make the list connotative as possible. An action can include multiple relevant UIs. For example, if you have “input_name”, “input_email”, “input_phone_number” actions, merge them into a single “fill_in_info” action. When combining similar actions, if each action is perceived to have unique functionality, they should not be merged.


Check the below five constraints:
1. You should only check the provided UI index. Other UI indexes must not be assigned to any actions.
2. Try to make the actions as general as possible. Refrain from using names that are specific to the context of the screen. For example, in the case of contacts screen, instead of “call_Bob”, use “call_contact”
3. Try to make parameters human friendly. Refrain from using index or code centric words as parameters. For example, in the case of contacts screen, instead of “contact_index”, use “contact_name”
4. Try to give list of options to the parameter’s question if the parameter has only short and unique valid values (Lists of recommendations, contacts, or search results are not unique because their values can change later. What remains constant are settings or the names of Tabs, which are unique.). If valid values are names specific to the context of the screen, omit the options (Constraint 1). For example, instead of “which tab do you want to select?“, use “which tab do you want to select? ['Contacts', 'Dialpad', 'Messages']"
5. When you assigning UI elements to the action, only HTML tags such as <button>, <input>, and <checker>(It doesn't have to be a tag listed, as long as it's a tag that triggers interaction when viewed.) that enable user interaction through user's input should be assigned. Not all UI should be assigned. And don't duplicate!!

"""

    else:
        sys_msg = \
"""Given a HTML code of a mobile app screen delimited by <screen></screen>, match the checking list(UI indexes) to given previous action list. The HTML code represents the screen of a mobile app, with each node representing an UI element on the screen.
           
Follow the seven steps step by step:
1. read the already made action list from similar screen
2. match the each UI index about given action list's action (if there is not matching, you can skip.).
3. Identify the mismatched ui index's action that must be performed surely on this mobile screen. The reasons for the judgment must be clear. (if the ui index's node is dummy or can't infer reasonable action, you must skip!)
4. Identify UI elements relevant to the new actions.
5. Identify information (parameters) required to execute the action.
6. Generate questions for information required to perform the action. Make questions as specific as possible.
7. Merge all actions considered similar by abstracting them into a bigger action with multiple parameters. Try to make the list connotative as possible. An action can include multiple relevant UIs. For example, if you have “input_name”, “input_email”, “input_phone_number” actions, merge them into a single “fill_in_info” action. When combining similar actions, if each action is perceived to have unique functionality, they should not be merged.


Check the below five constraints:
1. You should only check the provided UI index. Other UI indexes must not be assigned to any actions.
2. Try to make the actions as general as possible. Refrain from using names that are specific to the context of the screen. For example, in the case of contacts screen, instead of “call_Bob”, use “call_contact”
3. Try to make parameters human friendly. Refrain from using index or code centric words as parameters. For example, in the case of contacts screen, instead of “contact_index”, use “contact_name”
4. Try to give list of options to the parameter’s question if the parameter has only short and unique valid values (Lists of recommendations, contacts, or search results are not unique because their values can change later. What remains constant are settings or the names of Tabs, which are unique.). If valid values are names specific to the context of the screen, omit the options (Constraint 1). For example, instead of “which tab do you want to select?“, use “which tab do you want to select? ['Contacts', 'Dialpad', 'Messages']"
5. When you assigning UI elements to the action, only HTML tags such as <button>, <input>, and <checker>(It doesn't have to be a tag listed, as long as it's a tag that triggers interaction when viewed.) that enable user interaction through user's input should be assigned. Not all UI should be assigned. And don't duplicate!!

"""

    human_msg = \
f"""
Example action list:
{sub_tasks}

To check UI index list:
{unknown_uis}

Based on HTML code, match UI index list's ui to given action list, or make new action(because no matching already made actions).
Screen:
<screen>{encoded_xml}</screen>

Respond using the JSON format described below. and you can answer this JSON format. Don't add any explanation.

Response Format:
{{"Matched_Actions": [{{“name”: <given_name_of_action>, “UI_index”: [<index of relevant interactable UI element>, ...]}}...], "New_Actions": [{{“name”: <name_of_action>, “description”: <description of action>, “parameters”: {{<parameter_name> : <question to ask for the parameter>, ...}},“UI_index”: [<index of relevant interactable UI element>, ...]}} ...], "left_indexes" : [<last Ui index (in the request checking lists) that don't make reasonable action> ...]}}

check again that you found all of actions about currnet screen.
"""

    return [sys_msg, human_msg]