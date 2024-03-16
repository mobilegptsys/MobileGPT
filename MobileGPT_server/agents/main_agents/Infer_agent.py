from agents.prompts.Infer_Agent_Prompt import make_messages

from utils.Utils import generate_numbered, log
from utils.Query import query, vision_query

import os, json

class Infer_Agent:
    def __init__(self, goal_sub_task):
        self.goal_sub_task = goal_sub_task
        self.info_needed = None

        self.action_history = []

    def infer_action_no_vision(self, goal_sub_task, sub_task_reason, screen_xml, example=None, feedback=None):           #example이 있다면 ~ prompt가 달리짐
        if feedback == None or "":
            feedback = "None"

        if len(self.action_history) == 0:
            action_history = "No history, yet."
        else:
            action_history = generate_numbered([one["thoughts"] for one in self.action_history])

        messages = make_messages(goal_sub_task, sub_task_reason, action_history, screen_xml, example, feedback)

        retries = 0
        while retries < 2:
            try:
                if example != None:
                    response = query(messages, os.getenv("APP_SELECT_AGENT_GPT_VERSION"), return_json=True)
                    return response
                else:
                    response = query(messages, os.getenv("INFER_AGENT_GPT_VERSION"), return_json=True)
                    return response
            except json.decoder.JSONDecodeError as e:
                print(f"JSON decoding error: {e} - 재시도 중... ({retries + 1}/{2})")
                retries += 1

        log("frequently error is raised!", "red")
        quit()


    def infer_action_vision(self, goal_sub_task, sub_task_reason, screen_xml, scr_shot_path, example=None, feedback=None):
        screenshot_paths = [scr_shot_path]

        if feedback == None or "":
            feedback = "None"

        if len(self.action_history) == 0:
            action_history = "No history, yet."
        else:
            action_history = generate_numbered([one["thoughts"] for one in self.action_history])

        messages = make_messages(goal_sub_task, sub_task_reason, action_history, screen_xml, example, feedback, is_vision=True)

        retries = 0
        while retries < 2:
            try:
                response = vision_query(screenshot_paths, messages, return_json=True)
                return response

            except json.decoder.JSONDecodeError as e:
                print(f"JSON decoding error: {e} - 재시도 중... ({retries + 1}/{2})")
                retries += 1

        log("frequently error is raised!", "red")
        quit()
