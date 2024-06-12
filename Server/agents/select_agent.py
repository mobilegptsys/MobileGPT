import json
import os

from agents.prompts import select_agent_prompt
from memory.memory_manager import Memory
from utils.utils import query, log, parse_completion_rate


class SelectAgent:
    def __init__(self, memory: Memory, instruction: str):
        self.memory = memory
        self.instruction = instruction

    def select(self, available_subtasks: list, subtask_history: list, qa_history: list, screen: str) -> dict:
        log(f":::SELECT:::", "blue")
        select_prompts = select_agent_prompt.get_prompts(self.instruction, available_subtasks, subtask_history, qa_history, screen)
        response = query(select_prompts, model=os.getenv("SELECT_AGENT_GPT_VERSION"))

        next_subtask_filled = response['action']
        for subtask in available_subtasks:
            if subtask['name'] == next_subtask_filled['name']:
                next_subtask_raw = subtask
                self.__save_as_example(next_subtask_raw, screen, response)
        return response

    def __save_as_example(self, subtask_raw, screen, response):
        del response['completion_rate']
        example = {"instruction": self.instruction, "screen": screen, "response": response}
        self.memory.save_subtask(subtask_raw, example)
