from agents.prompts.Parameter_Filler_Agent_Prompt import make_messages

from utils.Query import query, vision_query

import os, json

class Parameter_Filler_Agent:

    def parameter_filling_vision(self, instruction, sub_task, current_screen_xml, scr_shot_path, example_instruction, example_reasoning, example_function_call, example_past_screen_xml):
        screenshot_paths = [scr_shot_path]

        past_response = {"reasoning":example_reasoning, "function_call":example_function_call}
        messages = make_messages(instruction, json.dumps(sub_task, ensure_ascii=False), current_screen_xml, example_instruction, json.dumps(past_response, ensure_ascii=False), example_past_screen_xml, is_vision=True)

        retries = 0
        while retries < 2:
            try:
                response = vision_query(screenshot_paths, messages, return_json=True)
                response["completion_rate"] = 0
                return response

            except json.decoder.JSONDecodeError as e:
                print(f"JSON decoding error: {e} - 재시도 중... ({retries + 1}/{2})")
                retries += 1

        log("frequently error is raised!", "red")
        quit()

    def parameter_filling_no_vision(self, instruction, sub_task, current_screen_xml, example_instruction, example_reasoning, example_function_call, example_past_screen_xml):

        past_response = {"reasoning":example_reasoning, "function_call":example_function_call}
        messages = make_messages(instruction, json.dumps(sub_task, ensure_ascii=False), current_screen_xml, example_instruction, json.dumps(past_response, ensure_ascii=False), example_past_screen_xml)

        response = query(messages, os.getenv("PARAMETER_FILLER_AGENT_GPT_VERSION"), return_json=True)
        response["completion_rate"] = 0

        return response