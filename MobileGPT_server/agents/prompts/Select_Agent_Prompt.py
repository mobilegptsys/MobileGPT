from utils.Utils import generate_numbered

def make_messages_select(instruction, screen, sub_tasks, history, feedback, is_vision):

    sub_tasks = generate_numbered(sub_tasks)

    if is_vision:
        sys_msg = \
f"""You are a smartphone assistant to help users complete tasks by interacting with mobile apps.
Given a task, a list of actions, past events, and HTML code of the current mobile screen and labeld screenshot of the current mobile screen, determine the next action to take.

Advice:
1. Understand HTML code's UI and mobile screenshot. the UIs' index is matched the screenshot's label (boxed and tagged)

Constraints:
1. You can perform a single action at a time.
2. Exclusively use the action listed below.
3. Always choose the best matching action. Ignore the ordering of the actions in the list.
4. If past events indicate that the task has been completed, make sure to use the 'finish' action.
5. You must choose your next action from a predefined list of actions.
6. You can't ask users to control their smart phone. Only you can control it. However, you can use ask for information use Ask action.

List of actions(you can use):
{sub_tasks} 

Performance Evaluation:
1. Continuously review and analyze your actions to ensure you are performing to the best of your abilities.
2. Constructively self-evaluate how close you are to completing the task.
3. Reflect on past events to refine your approach. It may be unnecessary to repeat actions that have already been taken in the past. 
4. Every action has a cost, so be smart and efficient. Aim to complete the task in the least number of steps. If you have already accomplished the given Task, you should call Finish without needing to do anything further.

Begin!
"""

    else:
        sys_msg = \
f"""You are a smartphone assistant to help users complete tasks by interacting with mobile apps.
Given a task, a list of actions, past events, and HTML code of the current mobile screen, determine the next action to take.

Constraints:
1. You can perform a single action at a time.
2. Exclusively use the action listed below.
3. Always choose the best matching action. Ignore the ordering of the actions in the list.
4. If past events indicate that the task has been completed, make sure to use the 'finish' action.
5. You must choose your next action from a predefined list of actions.
6. You can't ask users to control their smart phone. Only you can control it. However, you can use ask for information use Ask action.

List of actions(you can use):
{sub_tasks}

Performance Evaluation:
1. Continuously review and analyze your actions to ensure you are performing to the best of your abilities.
2. Constructively self-evaluate how close you are to completing the task.
3. Reflect on past events to refine your approach. It may be unnecessary to repeat actions that have already been taken in the past. 
4. Every action has a cost, so be smart and efficient. Aim to complete the task in the least number of steps. If you have already accomplished the given Task, you should call Finish without needing to do anything further.

Begin!
"""

    if feedback == None:
        human_msg = \
f"""
Task: {instruction}

Past Events:
'''
{history}
'''

HTML code of the current screen information delimited by <screen> </screen>:
<screen>{screen}</screen>

Based on the past events (delimited by triple quotes), determine which next action to take. You must choose your next action from a predefined list of actions.
Respond using the JSON format described below

Response Format
{{"reasoning": <reasoning>, "completion_rate": <indicate how close you are to completing the task>,"function_call": {{"name":<action_name>, "parameters":{{<parameter_name>: <parameter_value, **Do not presume or infer user\'s preference from any labels, ranks, or other markers.** If the parameter values are not explicitly mentioned in the given task or past events, just write "unknown">}}}}}}
"""
    else:
        human_msg = \
f"""
Task: {instruction}

Past Events:
'''
{history}
'''

HTML code of the current screen information delimited by <screen> </screen>:
<screen>{screen}</screen>]

feedback from Exception:
{feedback}

Based on the past events (delimited by triple quotes), determine which next action to take. You must choose your next action from a predefined list of actions.
Respond using the JSON format described below

Response Format
{{"reasoning": <reasoning>, "completion_rate": <indicate how close you are to completing the task>,"function_call": {{"name":<action_name>, "parameters":{{<parameter_name>: <parameter_value, **Do not presume or infer user\'s preference from any labels, ranks, or other markers.** If the parameter values are not explicitly mentioned in the given task or past events, just write "unknown">}}}}}}
"""

    return [sys_msg, human_msg]

def make_messages_history(sub_task, sub_task_reason, action_history):

    sys_msg = \
f"""I will give you a list of commands and reasoning behind the commands. Summarize what has been achieve through the list of commands(This Function is ended, so I need the summary.). Summarize and human-friendly like user position (Start the sentence with a verb and refrain from using code specific details(like command name, completion etc.)
I need short phrase that summarizes the whole commands list perfectly. The phrase should include a summary of [commands, purposes(reason), outcomes, and other important details(if there is failure, exception etc..)], which must not be omitted from the summary. and the sentence must include specifically what is selected (when question is occurred.)

Suggested Verbs to start the phrase: {{Selected, Clicked, Entered, Opened, Finished, Displayed, Shared}}

Function:
{sub_task}

Reason for select the Function:
{sub_task_reason}

sequence of commands that compose the Function:
{action_history}

Respond Examples:
1. Opened navigation menu.
2. Clicked New Group option
3. Searched for Bob
4. Shared information about distance limitation to user
"""

    human_msg = ""

    return [sys_msg, human_msg]
