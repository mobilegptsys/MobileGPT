import json


def generate_numbered_list(candidates):
    apps = []
    for _, row in candidates.iterrows():
        app = {"app_name": row['app_name'], "description": row['description']}
        apps.append(json.dumps(app))

    return "\n".join([f"{i + 1}. {item}" for i, item in enumerate(apps)])


def get_sys_prompt(candidates):
    numbered_candidates = generate_numbered_list(candidates)

    sys_msg = (
        "You are a mobile app agent, an AI designed to select the most appropriate mobile app "
        "for the given goal. From the following list of candidate mobile apps, choose the "
        "most suitable app to launch based on the app's description.\n\n"

        "List of Candidate Mobile Apps:\n"
        f"{numbered_candidates}\n\n"

        "Respond only in the following json format. And ensure the response can be parsed by "
        "Python json.loads\n"
        "Response Format: \n"
        '{"reasoning": "<reasoning>", "app": "<app_name>"}'
    )
    return sys_msg


def get_usr_prompt(instruction):
    usr_msg = (
        f"GOAL: {instruction}"
    )
    return usr_msg


def get_prompts(instruction, candidates):
    sys_msg = get_sys_prompt(candidates)
    usr_msg = get_usr_prompt(instruction)
    messages = [{"role": "system", "content": sys_msg},
                {"role": "user", "content": usr_msg}]
    return messages
