import json
import os
from copy import deepcopy

from agents import action_summarize_agent
from agents.prompts import derive_agent_prompt
from memory.memory_manager import Memory
from utils.utils import query, log, parse_completion_rate
from utils import action_utils, parsing_utils


class DeriveAgent:
    def __init__(self, memory: Memory, instruction: str):
        self.memory = memory
        self.instruction = instruction
        self.subtask = None
        self.subtask_history = []
        self.action_history = []

    def init_subtask(self, subtask: dict, subtask_history: list) -> None:
        self.subtask = subtask
        self.subtask_history = subtask_history
        self.action_history = []

    def derive(self, screen: str, examples=None) -> (dict, dict):
        if examples is None:
            examples = []

        derive_prompt = derive_agent_prompt.get_prompts(self.instruction, self.subtask,
                                                        self.subtask_history + self.action_history, screen, examples)
        response = query(derive_prompt, model=os.getenv("DERIVE_AGENT_GPT_VERSION"))
        response['completion_rate'] = parse_completion_rate(response['completion_rate'])
        self.action_history.append(response)

        example = self.__exemplify(response, screen)
        return response['action'], example

        # Save in real time.
        # self.__generalize_and_save_action(response, screen)

        # generalized_action = self.__generalize_action(response, screen)
        #
        # return response['action'], generalized_action

    def add_finish_action(self) -> None:
        finish_action = {
            "name": "finish",
            "parameters": {},
        }
        self.memory.save_action(self.subtask['name'], finish_action, example=None)

    def summarize_actions(self) -> str:
        if len(self.action_history) > 0:
            action_summary = action_summarize_agent.summarize_actions(self.action_history)
            self.action_history = []
            return action_summary

    def __exemplify(self, response: dict, screen: str) -> dict:
        action = response['action']
        example = {}
        if "index" in action['parameters']:
            shrunk_xml = parsing_utils.shrink_screen_xml(screen, int(action['parameters']['index']))
            example = {"instruction": self.instruction, "subtask": json.dumps(self.subtask), "screen": shrunk_xml,
                       "response": json.dumps(response)}
        return example

    def __generalize_and_save_action(self, response: dict, screen) -> None:
        action = response['action']
        example = {}
        if "index" in response['action']['parameters']:
            action = deepcopy(action)
            subtask_arguments = self.subtask['parameters']
            action = action_utils.generalize_action(action, screen, subtask_arguments)

            shrunk_xml = parsing_utils.shrink_screen_xml(screen, int(action['parameters']['index']))
            example = {"instruction": self.instruction, "subtask": json.dumps(self.subtask), "screen": shrunk_xml, "response": json.dumps(response)}


        self.memory.save_action(self.subtask, action, example)




