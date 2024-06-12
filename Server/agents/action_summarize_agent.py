import os

from agents.prompts import action_summarize_prompt
from utils.utils import query


def summarize_actions(action_history: list):
    prompts = action_summarize_prompt.get_prompts(action_history)
    response = query(prompts, model=os.getenv("ACTION_SUMMARIZE_AGENT_GPT_VERSION"))
    return response