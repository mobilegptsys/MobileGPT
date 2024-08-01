import os

from agents.prompts import param_fill_agent_prompt
from utils.utils import query, log


def parm_fill_subtask(instruction: str, subtask: dict, qa_history: list, screen: str, example: dict):
    prompts = param_fill_agent_prompt.get_prompts(instruction, subtask, qa_history, screen, example)
    if len(example) > 0:
     response = query(prompts, model=os.getenv("PARAMETER_FILLER_AGENT_GPT_VERSION"))
    else:
        response = query(prompts, model="gpt-4o")
    return response
