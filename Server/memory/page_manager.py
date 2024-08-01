import json
import os

import pandas as pd

from agents import param_fill_agent
from utils.action_utils import adapt_action
from utils.utils import log


def init_database(path: str, headers: list):
    if not os.path.exists(path):
        database = pd.DataFrame([], columns=headers)
        database.to_csv(path, index=False)
    else:
        database = pd.read_csv(path)
    return database


class PageManager:
    def __init__(self, page_path, page_index):
        self.page_index = page_index

        subtask_header = ['name', 'description', 'parameters', 'example']
        action_header = ['subtask_name', 'step', 'action', 'example']
        available_subtask_header = ['name', 'description', 'parameters']

        if not os.path.exists(page_path + f"/{page_index}/"):
            os.makedirs(page_path + f"/{page_index}/")

        self.subtask_db_path = page_path + f"{page_index}/subtasks.csv"
        self.subtask_db = init_database(self.subtask_db_path, subtask_header)

        self.available_subtask_db_path = page_path + f"{page_index}/available_subtasks.csv"
        self.available_subtask_db = init_database(self.available_subtask_db_path, available_subtask_header)

        self.action_db_path = page_path + f"{page_index}/actions.csv"
        self.action_db = init_database(self.action_db_path, action_header)

        self.action_data = self.action_db.to_dict(orient='records')

        for action in self.action_data:
            action['traversed'] = False

    def get_available_subtasks(self):
        return self.available_subtask_db.to_dict(orient='records')

    def add_new_action(self, new_action):
        self.available_subtask_db = pd.concat([self.available_subtask_db, pd.DataFrame([new_action])], ignore_index=True)
        self.available_subtask_db.to_csv(self.available_subtask_db_path, index=False)

    def save_subtask(self, subtask_raw: dict, example: dict):
        filtered_subtask = self.subtask_db[(self.subtask_db['name'] == subtask_raw['name'])]
        if len(filtered_subtask) == 0:
            subtask_data = {
                "name": subtask_raw['name'],
                "description": subtask_raw['description'],
                "parameters": json.dumps(subtask_raw['parameters']),
                "example": json.dumps(example)
            }

            self.subtask_db = pd.concat([self.subtask_db, pd.DataFrame([subtask_data])], ignore_index=True)
            self.subtask_db.to_csv(self.subtask_db_path, index=False)
            log("added new subtask to the database")

    def get_next_subtask_data(self, subtask_name: str) -> dict:
        # Filter the subtask_db for rows matching the specific 'name'
        filtered_subtask = self.subtask_db[(self.subtask_db['name'] == subtask_name)]
        next_subtask_data = filtered_subtask.iloc[0].to_dict()

        return next_subtask_data

    def save_action(self, subtask_name, step: int, action: dict, example=None) -> None:
        if example is None:
            example = {}
        new_action_db = {
            "subtask_name": subtask_name,
            'step': step,
            "action": json.dumps(action),
            "example": json.dumps(example)
        }

        # Write to csv
        self.action_db = pd.concat([self.action_db, pd.DataFrame([new_action_db])], ignore_index=True)
        self.action_db.to_csv(self.action_db_path, index=False)

        # Append to action data
        new_action_data = {
            "subtask_name": subtask_name,
            'step': step,
            "action": json.dumps(action),
            "example": json.dumps(example),
            "traversed": True
        }
        self.action_data.append(new_action_data)

    def get_next_action(self, subtask: dict, screen: str, step: int):
        curr_subtask_name = subtask['name']
        examples = []
        for action_data in self.action_data:
            if action_data.get("subtask_name", "") == curr_subtask_name and action_data.get("step") == step:
                if not action_data.get("traversed", False):
                    action_data['traversed'] = True
                    next_base_action = json.loads(action_data.get("action"))
                    examples.append(json.loads(action_data.get("example")))

                    subtask_arguments = subtask['parameters']
                    adapted_action = adapt_action(next_base_action, screen, subtask_arguments)
                    if adapted_action:
                        return adapted_action

        if len(examples) > 0:
            return {"examples": examples}

        return None

    def update_subtask_info(self, subtask) -> None:
        condition = (self.subtask_db['name'] == subtask['name'])
        if condition.any():
            self.subtask_db.loc[condition, 'name'] = subtask['name']
            self.subtask_db.loc[condition, 'description'] = subtask['description']
            self.subtask_db.loc[condition, 'parameters'] = json.dumps(subtask['parameters'])

            self.subtask_db.to_csv(self.subtask_db_path, index=False)

    def merge_subtask_into(self, base_subtask_name, prev_subtask_name, target_subtask_name):
        actions = self.action_db.to_dict(orient="records")
        starting_step = 0

        for action in actions[:]:  # Iterating over a copy of the list
            subtask_name = action['subtask_name']
            action_data = json.loads(action['action'])
            if subtask_name == prev_subtask_name and action_data['name'] == 'finish':
                starting_Step = action['step']
                actions.remove(action)

        for action in actions[:]:
            subtask_name = action['subtask_name']
            if subtask_name == target_subtask_name:
                action['subtask_name'] = base_subtask_name
                action['step'] = starting_step + action['step']

        self.action_db = pd.DataFrame(actions)
        self.action_db.to_csv(self.action_db_path, index=False)
