import json

from utils.utils import generate_numbered_list


def get_usr_prompt(action_history):
    # Remove completion rate from the list of actions. This confuses GPT.
    for action in action_history:
        del action['completion_rate']
    numbered_history = generate_numbered_list(action_history)

    usr_msg = (
        "I will give you a list of commands and reasoning behind each command. Summarize in one phrase what has been achieve through this list of commands. "
        "Be short and human-friendly (Start the sentence with a verb and refrain from using code specific details). "
        "I just need one phrase that summarizes the whole list of commands. The phrase should include a summary of commands(steps), purposes(reason), next plan, and other important details such as failures (if any).\n\n"
        "Suggested Verbs to start the phrase: {Selected, Clicked, Entered, Opened, Finished, Displayed}\n\n"
                
        "Example Responses:\n"
        "Opened navigation menu. Suggested Next plan:  See more menus\n"
        "Clicked New Group option. Suggested Next plan: Create new group\n"
        "Clicked Search button. Suggested Next plan: Search for contact.\n\n"
        
        "List of commands to summarize:\n"
        f"{numbered_history}\n\n"

        "Response:\n"
    )
    return usr_msg


def get_prompts(action_history: list):
    usr_msg = get_usr_prompt(action_history)
    messages = [
                {"role": "user", "content": usr_msg}]
    return messages
