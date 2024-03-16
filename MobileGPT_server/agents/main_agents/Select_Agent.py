from agents.prompts.Select_Agent_Prompt import make_messages_history, make_messages_select

from utils.Query import query, vision_query
from utils.Utils import generate_numbered, log

import os, json

class SubTaskError(Exception):
    pass

class Select_Agent:
    def __init__(self, sub_tasks):
        self.sub_task = sub_tasks

    def select_subtask_no_vision(self, instruction, screen, sub_task_history):

        if len(sub_task_history) == 0:
            sub_task_history = "No history, yet."
        else:
            sub_task_history = generate_numbered(sub_task_history)

        feedback = None

        retries = 0
        while retries < 2:
            try:
                messages = make_messages_select(instruction, screen, self.sub_task, sub_task_history, feedback, is_vision=False)
                response = query(messages, os.getenv("SELECT_AGENT_GPT_VERSION"), return_json=True)

                if response["function_call"]["name"] not in [sub_task["name"] for sub_task in self.sub_task]:
                    raise SubTaskError(f"Unexpected sub task: {response['function_call']['name']}")

                return response

            except json.decoder.JSONDecodeError as e:
                print(f"JSON decoding error: {e} - 재시도 중... ({retries + 1}/{2})")
                retries += 1

            except SubTaskError as e:
                # Handle the specific case where the function call name is not expected
                print(f"SubTask error: {e}")

                feedback = f"The selected {response} is not predefined action(can't operate). You should select only given list of actions. Try other action from the given actions."

                retries += 1

        log("frequently error is raised!", "red")
        quit()


    def select_subtask_vision(self, instruction, screen, sub_task_history, scr_shot_path):

        screenshot_paths = [scr_shot_path]

        if len(sub_task_history) == 0:
            sub_task_history = "No history, yet."
        else:
            sub_task_history = generate_numbered(sub_task_history)

        feedback = None

        retries = 0
        while retries < 2:
            try:
                messages = make_messages_select(instruction, screen, self.sub_task, sub_task_history, feedback, is_vision=True)
                response = vision_query(screenshot_paths, messages, return_json=True)

                if response["function_call"]["name"] not in [sub_task["name"] for sub_task in self.sub_task]:
                    raise SubTaskError(f"Unexpected sub task: {response['function_call']['name']}")

                return response

            except json.decoder.JSONDecodeError as e:
                print(f"JSON decoding error: {e} - 재시도 중... ({retries + 1}/{2})")
                retries += 1

            except SubTaskError as e:
                # Handle the specific case where the function call name is not expected
                print(f"SubTask error: {e}")

                feedback = f"The selected {response} is not predefined action(can't operate). You should select only given list of actions. Try other action from the given actions."

                retries += 1

        log("frequently error is raised!", "red")
        quit()


    @classmethod
    def make_sub_task_summary(self, sub_tasks, sub_task, action_history):

        sub_task_select_reason = sub_task["sub_task"]["reasoning"]
        sub_task = sub_tasks[sub_task["sub_task"]["function_call"]["name"]]

        messages = make_messages_history(sub_task, sub_task_select_reason, generate_numbered(action_history))
        response = query(messages, os.getenv("SELECT_AGENT_HISTORY_GPT_VERSION"), return_json=False)

        return response
