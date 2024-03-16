import os

from agents.prompts.Instruction_Translator_Agent_Prompt import make_messages
from utils.Query import query

class Instruction_Translator:
    def translate(self, instruction: str, known_api_list: list, package_list: list) -> (str, str):
        package_list = [str(package["package_name"]).lower().strip() for package in package_list]

        downloaded_app_api = []

        for api in known_api_list:
            if str(api['app']).lower().strip().strip('"') in package_list:
                downloaded_app_api.append(api['api'])

        prompt_messages = make_messages(instruction, downloaded_app_api)

        generalized_api = query(prompt_messages, os.getenv("INSTRUCTION_TRANSLATOR_AGENT_GPT_VERSION"), return_json=True)

        return generalized_api
