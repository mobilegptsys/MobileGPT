import json
import os
from collections import defaultdict
from typing import Dict

import numpy as np
import pandas as pd

from agents import param_fill_agent, subtask_merge_agent
from memory.page_manager import PageManager
from memory.node_manager import NodeManager
from utils import parsing_utils
from utils.action_utils import generalize_action
from utils.utils import get_openai_embedding, log, safe_literal_eval, cosine_similarity


def init_database(path: str, headers: list):
    if not os.path.exists(path):
        database = pd.DataFrame([], columns=headers)
        database.to_csv(path, index=False)
    else:
        database = pd.read_csv(path)
    return database


class Memory:
    def __init__(self, app: str, instruction: str, task_name: str):
        self.app = app
        self.instruction = instruction
        self.task_name = task_name
        self.curr_action_step = 0

        base_database_path = f"./memory/{app}/"
        if not os.path.exists(base_database_path):
            os.makedirs(base_database_path)

        self.task_db_path = base_database_path + "tasks.csv"
        self.page_path = base_database_path + "pages.csv"
        self.screen_hierarchy_path = base_database_path + "hierarchy.csv"

        self.page_database_path = base_database_path + "pages/"
        if not os.path.exists(self.page_database_path):
            os.makedirs(self.page_database_path)

        task_header = ['name', 'path']
        page_header = ['index', 'available_subtasks', 'trigger_uis', 'extra_uis', "screen"]
        hierarchy_header = ['index', 'screen', 'embedding']

        self.task_db = init_database(self.task_db_path, task_header)

        self.page_db = init_database(self.page_path, page_header)
        self.page_db.set_index('index', drop=False, inplace=True)

        self.hierarchy_db = init_database(self.screen_hierarchy_path, hierarchy_header)
        self.hierarchy_db['embedding'] = self.hierarchy_db.embedding.apply(safe_literal_eval)
        self.task_path = self.__get_task_data(self.task_name)
        self.page_managers: Dict[int, PageManager] = {}
        self.page_manager = None

    def init_page_manager(self, page_index: int):
        if page_index not in self.page_managers:
            self.page_managers[page_index] = PageManager(self.page_database_path, page_index)

        self.page_manager = self.page_managers[page_index]

    def search_node(self, parsed_xml, hierarchy_xml, encoded_xml) -> (int, list):
        candidate_nodes_indexes = self.__search_similar_hierarchy_nodes(hierarchy_xml)

        node_manager = NodeManager(self.page_db, self, parsed_xml, encoded_xml)
        node_index, available_subtasks = node_manager.search(candidate_nodes_indexes)
        return node_index, available_subtasks

    def add_node(self, available_subtasks: list, trigger_uis: dict, extra_uis: list, screen: str) -> int:
        new_index = len(self.page_db)
        new_row = {'index': new_index, 'available_subtasks': json.dumps(available_subtasks),
                   'trigger_uis': json.dumps(trigger_uis),
                   'extra_uis': json.dumps(extra_uis), "screen": screen}
        self.page_db = pd.concat([self.page_db, pd.DataFrame([new_row])], ignore_index=True)
        self.page_db.to_csv(self.page_path, index=False)

        page_path = self.page_database_path + f"{new_index}/"
        page_screen_path = os.path.join(page_path, "screen")
        if not os.path.exists(page_path):
            os.makedirs(page_path)
            available_subtasks_df = pd.DataFrame(available_subtasks)
            available_subtasks_df.to_csv(os.path.join(page_path, "available_subtasks.csv"), index=False)
            os.makedirs(page_screen_path)
        parsing_utils.save_screen_info(self.app, self.task_name, page_screen_path)

        return new_index

    def update_node(self, page_index, new_available_subtasks: list, new_trigger_uis: dict, new_extra_uis: list,
                    new_screen: str):
        page_data = json.loads(self.page_db.loc[page_index].to_json())
        page_data = {key: json.loads(value) if key in ['available_subtasks', 'trigger_uis', 'extra_uis'] else value for
                     key, value in page_data.items()}

        # merge old and new infos
        merged_available_subtasks = page_data['available_subtasks'] + new_available_subtasks
        merged_trigger_uis = {}
        merged_trigger_uis.update(page_data['trigger_uis'])
        merged_trigger_uis.update(new_trigger_uis)
        merged_extra_uis = page_data['extra_uis'] + new_extra_uis

        updated_row = {'index': page_index, 'available_subtasks': json.dumps(merged_available_subtasks),
                       'trigger_uis': json.dumps(merged_trigger_uis),
                       'extra_uis': json.dumps(merged_extra_uis), "screen": new_screen}

        self.page_db.loc[page_index] = updated_row
        self.page_db.to_csv(self.page_path, index=False)

        page_path = self.page_database_path + f"{page_index}/"
        available_subtasks_df = pd.DataFrame(merged_available_subtasks)
        available_subtasks_df.to_csv(os.path.join(page_path, "available_subtasks.csv"), index=False)

    def add_hierarchy_xml(self, screen, page_index):
        embedding = get_openai_embedding(screen)
        new_screen_hierarchy = {'index': page_index, 'screen': screen, 'embedding': str(embedding)}
        hierarchy_db = init_database(self.screen_hierarchy_path, ['index', 'screen', 'embedding'])
        hierarchy_db = pd.concat([hierarchy_db, pd.DataFrame([new_screen_hierarchy])], ignore_index=True)
        hierarchy_db.to_csv(self.screen_hierarchy_path, index=False)

        self.hierarchy_db = init_database(self.screen_hierarchy_path, ['index', 'screen', 'embedding'])
        self.hierarchy_db['embedding'] = self.hierarchy_db.embedding.apply(safe_literal_eval)

    def get_next_subtask(self, page_index, qa_history, screen):
        # Initialize action step
        self.curr_action_step = 0

        candidate_subtasks = self.task_path.get(page_index, [])
        next_subtask_name = None
        for subtask in candidate_subtasks:
            if not subtask.get("traversed", False):
                next_subtask_name = subtask.get("name")
                subtask['traversed'] = True
                break
        if next_subtask_name == 'finish':
            finish_subtask = {"name": "finish",
                              "description": "Use this to signal that the task has been completed",
                              "parameters": {}
                              }
            return finish_subtask

        if next_subtask_name:
            next_subtask_data = self.page_manager.get_next_subtask_data(next_subtask_name)

            next_subtask = {'name': next_subtask_data['name'], 'description': next_subtask_data['description'],
                            'parameters': json.loads(next_subtask_data['parameters'])}

            if len(next_subtask['parameters']) > 0:
                params = param_fill_agent.parm_fill_subtask(instruction=self.instruction,
                                                            subtask=next_subtask,
                                                            qa_history=qa_history,
                                                            screen=screen,
                                                            example=json.loads(
                                                                next_subtask_data.get('example', {})))

                next_subtask['parameters'] = params

            return next_subtask

        return None

    def save_subtask(self, subtask_raw: dict, example: dict) -> None:
        self.page_manager.save_subtask(subtask_raw, example)

    def get_next_action(self, subtask: dict, screen: str) -> dict:
        next_action = self.page_manager.get_next_action(subtask, screen, self.curr_action_step)
        self.curr_action_step += 1
        log(f":::DERIVE::: Recalling action : {next_action}", "blue")
        return next_action

    def save_action(self, subtask: dict, action: dict, example=None) -> None:
        if action['name'] == 'finish':
            self.curr_action_step += 1
        self.page_manager.save_action(subtask, self.curr_action_step, action, example)

    def merge_subtasks(self, task_path: list) -> list:
        # Remove finish subtask at the end
        finish_subtask = task_path.pop()

        # Initialize list of subtasks performed.
        raw_subtask_list = []
        for subtask_data in task_path:
            page_index = subtask_data['page_index']
            subtask_name = subtask_data['subtask_name']
            page_data = json.loads(self.page_db.loc[page_index].to_json())
            available_subtasks = json.loads(page_data['available_subtasks'])
            for subtask_available in available_subtasks:
                if subtask_available['name'] == subtask_name:
                    raw_subtask_list.append(subtask_available)

        merged_subtask_list = subtask_merge_agent.merge_subtasks(raw_subtask_list)

        merged_task_path = self.__merge_subtasks_data(task_path, merged_subtask_list)
        # Add Finish subtask at the end back in
        merged_task_path.append(finish_subtask)

        return merged_task_path

    def save_task(self, task_path: list) -> None:
        for subtask in task_path:
            subtask_name = subtask['subtask_name']
            subtask_dict = subtask['subtask']
            actions = subtask['actions']
            step = 0
            for action_data in actions:
                page_index = action_data['page_index']
                action = action_data['action']
                screen = action_data['screen']
                example = action_data['example']

                if action['name'] == 'finish' or example:
                    generalized_action = generalize_action(action, subtask_dict, screen)
                    page_manager = self.page_managers[page_index]
                    page_manager.save_action(subtask_name, step, generalized_action, example)
                step += 1

        known_task_path = {
            key: [item["name"] for item in value]
            for key, value in self.task_path.items()
        }

        for subtask in task_path:
            page_index = subtask['page_index']
            subtask_name = subtask['subtask_name']
            if page_index in known_task_path:
                if subtask_name not in known_task_path[page_index]:
                    known_task_path[page_index].append(subtask_name)
            else:
                known_task_path[page_index] = [subtask_name]

        new_task_path = {
            'name': self.task_name,
            'path': json.dumps(known_task_path)
        }


        condition = (self.task_db['name'] == new_task_path['name'])
        if condition.any():
            self.task_db.loc[condition] = pd.DataFrame([new_task_path])
        else:
            self.task_db = pd.concat([self.task_db, pd.DataFrame([new_task_path])], ignore_index=True)

        self.task_db.to_csv(self.task_db_path, index=False)
        log(f":::SAVE::: Path saved: {new_task_path}")

    def save_task_path(self, new_task_path: dict):
        for page_index, subtasks in new_task_path.items():
            if page_index in self.task_path:
                self.task_path[page_index].extend(subtasks)
            else:
                self.task_path[page_index] = subtasks[:]

        new_task_data = {
            'name': self.task_name,
            'path': json.dumps(self.task_path)
        }

        condition = (self.task_db['name'] == new_task_data['name'])
        if condition.any():
            self.task_db.loc[condition] = new_task_data
        else:
            self.task_db = pd.concat([self.task_db, pd.DataFrame([new_task_data])], ignore_index=True)

        self.task_db.to_csv(self.task_db_path, index=False)

    def __get_task_data(self, task_name):
        # Search for the task
        matched_tasks = self.task_db[(self.task_db['name'] == task_name)]
        if matched_tasks.empty:
            return {}
        else:
            task_data = matched_tasks.iloc[0].to_dict()
            path = json.loads(task_data['path'])

            task_path = {}
            for page_index, subtasks in path.items():
                subtasks_data = []
                for subtask in subtasks:
                    subtasks_data.append({"name": subtask, "traversed": False})
                task_path[int(page_index)] = subtasks_data

            log(f"Known path for the task: {task_name}", "yellow")
            log(task_path, "yellow")

            return task_path

    def __search_similar_hierarchy_nodes(self, hierarchy) -> list:
        new_hierarchy_vector = np.array(get_openai_embedding(hierarchy))
        self.hierarchy_db["similarity"] = self.hierarchy_db.embedding.apply(
            lambda x: cosine_similarity(x, new_hierarchy_vector))

        # get top apps with the highest similarity
        candidates = self.hierarchy_db.sort_values('similarity', ascending=False).head(5).to_dict(orient='records')
        candidate_node_indexes = []
        for node in candidates:
            candidate_node_indexes.append(node['index'])

        return candidate_node_indexes

    def __merge_subtasks_data(self, original_subtasks_data, merged_subtasks) -> list:
        len_diff = len(original_subtasks_data) - len(merged_subtasks)
        for i in range(0, len_diff):
            merged_subtasks.append({"name": "dummy"})

        original_pointer = 0
        merged_pointer = 0
        while original_pointer < len(original_subtasks_data):
            curr_subtask_data = original_subtasks_data[original_pointer]
            curr_subtask_name = curr_subtask_data['subtask_name']
            curr_subtask_actions = curr_subtask_data['actions']

            merged_subtask_dict = merged_subtasks[merged_pointer]
            if merged_subtask_dict['name'] == curr_subtask_name:
                page_index = curr_subtask_data['page_index']
                page_data = json.loads(self.page_db.loc[page_index].to_json())
                available_subtasks = json.loads(page_data['available_subtasks'])
                # Loop through the available subtasks list and replace the subtask with the new one.
                for i in range(len(available_subtasks)):
                    if available_subtasks[i]['name'] == curr_subtask_name:
                        available_subtasks[i] = merged_subtask_dict

                page_data['available_subtasks'] = json.dumps(available_subtasks)
                self.page_db.loc[page_index] = page_data
                self.page_db.to_csv(self.page_path, index=False)

                self.page_managers[page_index].update_subtask_info(merged_subtask_dict)

                merged_subtask_params = merged_subtask_dict['parameters']
                curr_subtask_params = curr_subtask_data['subtask']['parameters']
                for param_name, _ in merged_subtask_params.items():
                    if param_name not in curr_subtask_params:
                        curr_subtask_params[param_name] = None

                original_pointer += 1
                merged_pointer += 1
            else:
                base_subtask_data = original_subtasks_data[original_pointer - 1]
                base_subtask_actions = base_subtask_data['actions']

                base_subtask_params = base_subtask_data['subtask']['parameters']
                curr_subtask_params = curr_subtask_data['subtask']['parameters']
                for param_name, param_value in base_subtask_params.items():
                    if param_value is None and param_name in curr_subtask_params:
                        base_subtask_params[param_name] = curr_subtask_params[param_name]

                base_subtask_actions.pop()

                merged_actions = base_subtask_actions + curr_subtask_actions
                base_subtask_data['actions'] = merged_actions

                original_subtasks_data.pop(original_pointer)

        return original_subtasks_data
