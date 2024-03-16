def make_messages(instruction, candidates_applist):

    sys_msg = \
"""You are a mobile app agent, an AI designed to run the appropriate app. Play to your strengths as an LLM and pursue simple strategies with no legal complications. Select the most appropriate application package from the list to achieve the given goal.

The application list format:
1. <Application Package name> #$# <Information of the application>
2. <Application Package name> #$# <Information of the application>
"""

    human_msg = \
f"""GOAL: {instruction}

Candidate Application List:
{candidates_applist}

Ensure the response is only one of the given application package name."""

    return [sys_msg, human_msg]