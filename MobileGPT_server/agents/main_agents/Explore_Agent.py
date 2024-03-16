import os, json

from agents.prompts.Explore_Agent_Prompt import make_messages, make_message_expand

from utils.Query import query, vision_query
from utils.Utils import log, generate_numbered

class Explore_Agent:
    def explore_screen_no_vision(self, encoded_xml):
        messages = make_messages(encoded_xml, is_vision=False)

        retries = 0
        while retries < 2:
            try:
                response = query(messages, os.getenv("EXPLORE_AGENT_GPT_VERSION"), return_json=True)
                return response

            except json.decoder.JSONDecodeError as e:
                print(f"JSON decoding error: {e} - 재시도 중... ({retries + 1}/{2})")
                retries += 1

        log("frequently error is raised!", "red")
        quit()


    def explore_screen_vision(self, scr_shot_path, encoded_xml):

        screenshot_paths = [scr_shot_path]

        retries = 0
        while retries < 2:
            try:
                messages = make_messages(encoded_xml, is_vision=True)
                response = vision_query(screenshot_paths, messages, return_json=True)

                return response

            except json.decoder.JSONDecodeError as e:
                print(f"JSON decoding error: {e} - 재시도 중... ({retries + 1}/{2})")
                retries += 1

        log("frequently error is raised!", "red")
        quit()

    def expand_screen_no_vision(self, encoded_xml, sub_tasks, unknown_uis):
        messages = make_message_expand(encoded_xml, generate_numbered(sub_tasks), unknown_uis, is_vision=False)
        response = query(messages, os.getenv("EXPLORE_AGENT_GPT_VERSION"), return_json=True)

        new_sub_task = response["New_Actions"]
        expanded_sub_task = response["Matched_Actions"]

        return new_sub_task, expanded_sub_task

    def expand_screen_vision(self, scr_shot_path, encoded_xml, sub_tasks, unknown_uis):

        messages = make_messages(prev_clicked_ui, encoded_xml, is_vision=True)
        response = vision_query(screenshot_paths, messages, os.getenv("EXPLORE_AGENT_GPT_VERSION"), return_json=True)

        return response