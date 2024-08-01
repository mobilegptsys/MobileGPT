import json
import os
from enum import Enum

import pandas as pd

from agents.derive_agent import DeriveAgent
from agents.explore_agent import ExploreAgent
from agents.select_agent import SelectAgent
from memory.memory_manager import Memory
from utils.utils import log, parse_completion_rate


class Status(Enum):
    LEARN = 0
    RECALL = 1
    WAIT = 2


class MobileGPT:
    def __init__(self, socket):
        self.socket = socket

        self.encoded_xml = ""
        self.hierarchy_xml = ""
        self.parsed_xml = ""

        self.instruction = ""
        self.task = None
        self.memory = None

        self.current_subtask = None
        self.current_screen_xml = ""
        self.current_page_index = -1
        self.current_subtask_data = {}

        self.subtask_history = []
        self.task_path = []
        self.qa_history = []

        self.explore_agent = None
        self.select_agent = None
        self.derive_agent = None

        # 0 = Learning, 1 = Recalling
        self.task_status = Status.RECALL
        self.subtask_status = Status.WAIT

    def init(self, instruction: str, task: dict, is_new_task: bool):
        self.instruction = instruction
        self.task = task
        self.memory = Memory(task['app'], instruction, task['name'])
        self.explore_agent = ExploreAgent(self.memory)
        self.select_agent = SelectAgent(self.memory, self.instruction)
        self.derive_agent = DeriveAgent(self.memory, self.instruction)

        if is_new_task:
            self.task_status = Status.LEARN

        log('Mobile Agent Initialized for app: ' + task['app'] + ' / Task: ' + task['name'])

    def get_next_action(self, parsed_xml=None, hierarchy_xml=None, encoded_xml=None):
        log(":::::::::MobileGPT received new screen:::::::::", 'red')
        parsed_xml = parsed_xml or self.parsed_xml
        hierarchy_xml = hierarchy_xml or self.hierarchy_xml
        encoded_xml = encoded_xml or self.encoded_xml

        self.parsed_xml = parsed_xml
        self.hierarchy_xml = hierarchy_xml
        self.encoded_xml = encoded_xml

        self.current_screen_xml = encoded_xml

        page_index, new_subtasks = self.memory.search_node(parsed_xml, hierarchy_xml, encoded_xml)

        if page_index == -1:
            page_index = self.explore_agent.explore(parsed_xml, hierarchy_xml, encoded_xml)

        if page_index != self.current_page_index:
            self.memory.init_page_manager(page_index)
            self.current_page_index = page_index

            if self.subtask_status == Status.LEARN:
                self.__finish_subtask()

        available_subtasks = self.memory.get_available_subtasks(page_index)
        if len(new_subtasks) > 0:
            available_subtasks += new_subtasks

        if self.current_subtask is None:
            next_subtask = self.memory.get_next_subtask(page_index, self.qa_history, self.current_screen_xml)

            if not next_subtask:
                response, new_action = self.select_agent.select(available_subtasks, self.subtask_history,
                                                                self.qa_history,
                                                                encoded_xml)

                if new_action:
                    self.memory.add_new_action(page_index)
                    available_subtasks = self.memory.get_available_subtasks(page_index)

                next_subtask = response['action']
                if next_subtask['name'] != 'read_screen':
                    msg = response['speak']
                    self.__send_speak_action(msg)

            if self.current_subtask_data:
                self.task_path.append(self.current_subtask_data)

            self.current_subtask_data = {"page_index": self.current_page_index,
                                         "subtask_name": next_subtask['name'], "subtask": next_subtask, "actions": []}

            self.derive_agent.init_subtask(next_subtask, self.subtask_history)
            self.current_subtask = next_subtask

            if next_subtask['name'] in ['finish', 'speak', 'scroll_screen']:
                return self.__handle_primitive_subtask(next_subtask)

        subtask_parameters = self.current_subtask['parameters']
        for key, value in subtask_parameters.items():
            if value == "unknown":
                raw_subtask = next(
                    (subtask for subtask in available_subtasks if subtask['name'] == self.current_subtask['name']),
                    None)
                print(raw_subtask)
                if raw_subtask:
                    if isinstance(raw_subtask['parameters'], str):
                        raw_subtask['parameters'] = json.loads(raw_subtask['parameters'])
                    question = raw_subtask['parameters'][key]
                    ask_action = {"name": "ask", "parameters": {"info_name": key, "question": question}}
                    return ask_action

        next_action = self.memory.get_next_action(self.current_subtask, self.encoded_xml)
        current_action_data = {"page_index": self.current_page_index, "action": next_action, "screen": self.encoded_xml,
                               "example": {}}
        if next_action:
            self.subtask_status = Status.RECALL
            if "examples" in next_action:
                next_action, example = self.derive_agent.derive(self.encoded_xml, examples=next_action['examples'])
                current_action_data['action'] = next_action
                current_action_data['example'] = example

        else:
            if self.subtask_status == Status.WAIT or self.subtask_status == Status.LEARN:
                self.subtask_status = Status.LEARN
                # Here
                next_action, example = self.derive_agent.derive(self.encoded_xml)
                current_action_data['action'] = next_action
                current_action_data['example'] = example

            elif self.subtask_status == Status.RECALL:
                self.__prepare_diverge_subtask()
                return self.get_next_action(parsed_xml, hierarchy_xml, encoded_xml)

        self.current_subtask_data['actions'].append(current_action_data)

        if next_action['name'] == 'finish':
            self.__finish_subtask(mark_finish=False, explicit_finish=True)
            next_action = self.get_next_action(parsed_xml, hierarchy_xml, encoded_xml)

        return next_action

    def set_qa_answer(self, info_name: str, question: str, answer: str):
        qa = {"info": info_name, "question": question, "answer": answer}
        self.qa_history.append(qa)

        subtask_parameters = self.current_subtask['parameters']
        if info_name in subtask_parameters:
            subtask_parameters[info_name] = answer
            return self.get_next_action()
        else:
            log(f"Something wrong. Cannot find {info_name} inside subtask: {self.current_subtask}", "red")

    def __finish_subtask(self, mark_finish=True, explicit_finish=False):
        log("finish subtask!!", "red")
        log(f"subtask: {self.subtask_status}, task: {self.task_status}", "red")
        if self.subtask_status == Status.LEARN and self.task_status == Status.LEARN:
            if mark_finish:
                finish_action = {"name": "finish", "parameters": {}}
                self.current_subtask_data['actions'].append(
                    {
                        "page_index": self.current_page_index,
                        "action": finish_action,
                        "screen": self.encoded_xml,
                        "example": {}
                    }
                )

            action_summary = self.derive_agent.summarize_actions()
            if action_summary:
                self.subtask_history.append(action_summary)

        if self.subtask_status == Status.RECALL:
            if explicit_finish:
                history = f"Performed an action: {self.current_subtask}"
                self.subtask_history.append(history)

        self.current_subtask = None
        self.subtask_status = Status.WAIT

    def __prepare_diverge_subtask(self) -> None:
        """
        Prepare for diverging to a new subtask.
        Returns:
        """
        history = f"I have performed an action: {self.current_subtask}. But I am not sure if it was successful."
        self.subtask_history.append(history)

        self.current_subtask = None
        self.subtask_status = Status.WAIT

    def __send_speak_action(self, msg) -> None:
        """
        Send a speak action to the device.
        Args:
            msg: message to be spoken by the device.
        """
        speak_action = {"name": "speak", "parameters": {"message": msg}}  # speak action
        self.socket.send(json.dumps(speak_action).encode())
        self.socket.send("\r\n".encode())

    def __handle_primitive_subtask(self, next_subtask: dict) -> None:
        if next_subtask['name'] == 'finish':
            self.__finish_task()
            return

        elif next_subtask['name'] == 'speak':
            msg = next_subtask['parameters']['message']
            speak_action = {"name": "speak", "parameters": {"message": msg}}  # speak action
            self.socket.send(json.dumps(speak_action).encode())
            self.socket.send("\r\n".encode())

            history = f"Spoke to the user: '{msg}'"
            self.subtask_history.append(history)
            self.current_subtask = None
            self.subtask_status = Status.WAIT

            completion_rate = parse_completion_rate(next_subtask['parameters']['completion_rate'])
            return self.get_next_action()

        elif next_subtask['name'] == 'scroll_screen':
            direction = next_subtask['parameters']['direction']
            index = next_subtask['parameters']['scroll_ui_index']

            scroll_action = {"name": "scroll", "parameters": {"index": index, "direction": direction}}
            self.socket.send(json.dumps(scroll_action).encode())
            self.socket.send("\r\n".encode())

            if self.task_status == Status.LEARN:
                target_info = next_subtask['parameters']['target_info']
                history = f"Scrolled screen {direction} to find '{target_info}'"
                self.subtask_history.append(history)
            self.current_subtask = None
            self.subtask_status = Status.WAIT

    def __finish_task(self) -> None:
        """
        Finish the task.
        Returns:
        """
        log("------------END OF THE TASK------------", "blue")
        self.current_subtask = None
        self.subtask_status = Status.WAIT

        self.socket.send("$$$$$".encode())
        self.socket.send("\r\n".encode())

        self.subtask_history = [f'Performed an instruction {self.instruction}']

        self.task_path.append({"page_index": self.current_page_index,
                               "subtask_name": "finish",
                               "subtask": {"name": "finish",
                                           "description": "Use this to signal that the task has been completed",
                                           "parameters": {}
                                           },
                               "actions": []})
        if self.task_status == Status.LEARN:
            # self.task_path = self.memory.merge_subtasks(self.task_path)

            global_task_database_path = f"./memory/tasks.csv"
            global_task_database = pd.read_csv(global_task_database_path)
            global_task_database = pd.concat([global_task_database, pd.DataFrame([self.task])], ignore_index=True)
            global_task_database.to_csv(global_task_database_path, index=False)

            self.memory.save_task(self.task_path)
        # self.memory.save_task_path(self.task_path)
