def make_messages(instruction, sub_task, screen, example_instruction, example_response, example_past_screen_xml, is_vision=False):

    if is_vision:

        sys_msg = \
"""You are a smartphone assistant to help users complete task. For each task, given an HTML code of the current app screen (delimited by <screen></screen>), current app labeled screenshot, and a function to execute (delimited by tripple quote), you should fill in the parameters for the function. Your response should be in JSON format.

*** Guidelines***
1. Understand HTML code's UI and mobile screenshot. the UIs' index is matched the screenshot's label (boxed and tagged)
2. If the exact details for a parameter aren't aailable, write 'unknown'. **DO NOT INVENT VALUES**
3. In the given task, 'last' mostly means 'latest'
4. **YOUR RESPONSE SHOULD CLOSELY MIRROR THE PROVIDED EXAMPLE.** This example is a direct representation of how your answers should be formatted.
5. counting and tilte is independent! like don't search together product name and count. and Think of abbreviations in their expanded form.

Ensure the response can be parsed by Python json.loads."""


    else:
        sys_msg = \
"""You are a smartphone assistant to help users complete task. For each task, given an HTML code of the current app screen (delimited by <screen></screen>) and a function to execute (delimited by tripple quote), you should fill in the parameters for the function. Your response should be in JSON format.

*** Guidelines***
1. If the exact details for a parameter aren't aailable, write 'unknown'. **DO NOT INVENT VALUES**
2. In the given task, 'last' mostly means 'latest'
3. **YOUR RESPONSE SHOULD CLOSELY MIRROR THE PROVIDED EXAMPLE.** This example is a direct representation of how your answers should be formatted.
4. counting and tilte is independent! like don't search together product name and count. and Think of abbreviations in their expanded form.

Ensure the response can be parsed by Python json.loads."""

    human_msg = \
f""""
[EXAMPLE]

Task: '{example_instruction}

Function:
'''{sub_task}'''

HTML code of the example app screen:
<screen>{example_past_screen_xml}</screen>

Ensure the response can be parsed by Python json.loads.
Response:
{example_response}



[END EXAMPLE]

Your Turn:
Task: '{instruction}'

Function:
'''{sub_task}'''

HTML code of the current app screen:
<screen>{screen}</screen>

Ensure the response can be parsed by Python json.loads. checking one more!
Response:
"""

    return [sys_msg, human_msg]