import os

from agents.prompts import subtask_merge_prompt
from utils.utils import query, log


def merge_subtasks(subtask_history: list):
    prompts = subtask_merge_prompt.get_prompts(subtask_history)
    response = query(prompts, model=os.getenv("SUBTASK_MERGE_AGENT_GPT_VERSION"), is_list=True)
    return response
