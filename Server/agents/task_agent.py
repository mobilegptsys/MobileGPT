import json
import os

import pandas as pd

from agents.prompts import task_agent_prompt
from utils.utils import query, log


class TaskAgent:
    def __init__(self):
        self.database_path = f"./memory/tasks.csv"
        if not os.path.exists(self.database_path):
            self.database = pd.DataFrame([], columns=['name', 'description', 'parameters', 'app'])
            self.database.to_csv(self.database_path, index=False)
        else:
            self.database = pd.read_csv(self.database_path, header=0)

    def get_task(self, instruction) -> (dict, bool):
        known_tasks = self.database.to_dict(orient='records')
        response = query(messages=task_agent_prompt.get_prompts(instruction, known_tasks),
                         model=os.getenv("TASK_AGENT_GPT_VERSION"))

        task = response["api"]
        is_new = True
        if str(response["found_match"]).lower() == "true":
            self.update_task(task)
            is_new = False

        return task, is_new

    # hard-coded
    # def get_task(self, instruction) -> (dict, bool):
    #     sample_response = """{"name":"sendGenericMessageToTelegram", "description": "send a generic message to Telegram without specifying a recipient or message content", "parameters":{}, "app": "Telegram"}"""
    #
    #     return json.loads(sample_response), True

    def update_task(self, task):
        condition = (self.database['name'] == task['name']) & (self.database['app'] == task['app'])
        index_to_update = self.database.index[condition]

        if not index_to_update.empty:
            # Update the 'description' and 'parameters' for the row(s) that match the condition
            self.database.loc[index_to_update, 'description'] = task['description']
            self.database.loc[index_to_update, 'parameters'] = task['parameters']
        else:
            # Handle the case where no matching row is found
            log("No matching task found to update", "red")
