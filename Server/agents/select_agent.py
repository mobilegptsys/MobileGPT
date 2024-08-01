import json
import os

from agents.prompts import select_agent_prompt
from memory.memory_manager import Memory
from utils.utils import query, log, parse_completion_rate


class SelectAgent:
    def __init__(self, memory: Memory, instruction: str):
        self.memory = memory
        self.instruction = instruction

    def select(self, available_subtasks: list, subtask_history: list, qa_history: list, screen: str) -> (dict, dict):
        log(f":::SELECT:::", "blue")
        select_prompts = select_agent_prompt.get_prompts(self.instruction, available_subtasks, subtask_history, qa_history, screen)
        response = query(select_prompts, model=os.getenv("SELECT_AGENT_GPT_VERSION"))
        while not self.__check_response_validity(response, available_subtasks):
            assistant_msg = {"role": "assistant", "content": json.dumps(response)}
            select_prompts.append(assistant_msg)

            error_msg = {"role": "user", "content": "Error: The selected action is not in the available actions list."}
            select_prompts.append(error_msg)
            response = query(select_prompts, model=os.getenv("SELECT_AGENT_GPT_VERSION"))

        next_subtask_filled = response['action']
        for subtask in available_subtasks:
            if subtask['name'] == next_subtask_filled['name']:
                next_subtask_raw = subtask
                self.__save_as_example(next_subtask_raw, screen, response)
        if "new_action" in response:
            return response, response['new_action']
        else:
            return response, None

    def __check_response_validity(self, response, available_subtasks):
        action = response['action']

        # Check if the selected action is in the available subtasks
        subtask_match = False
        if action['name'] in ['scroll_screen', 'finish', 'speak']:
            subtask_match = True
            return True

        for subtask in available_subtasks:
            if subtask['name'] == action['name']:
                subtask_match = True
                return True

        if not subtask_match:
            # if this is a new action, we need to add it to the available subtasks
            if "new_action" in response:
                new_action = response['new_action']
                available_subtasks.append(new_action)
                return True

            # if selected action is not in the available subtasks and not provided with new action, we send error message to GPT
            else:
                return False

    def __save_as_example(self, subtask_raw, screen, response):
        del response['completion_rate']
        example = {"instruction": self.instruction, "screen": screen, "response": response}
        self.memory.save_subtask(subtask_raw, example)
