from utils.Utils import generate_numbered

def make_messages(instruction, known_api_list):
    sys_msg1 = \
"""Given the user instruction, check if it matches any of the listed APIs. If there's a match, modify the matched API's description and parameters to cover both the original purpose and the new instruction, ensuring the original meaning is not lost. If there's no match, suggest a new API. 

**Guidelines for Matching API with User Instruction:**
1. An API matches the user instruction if it can cover all the steps required for the instruction with some generalization.
2. An API does NOT match if the user instruction requires additional steps beyond what the API description provides.

**Guidlines for how to make a new API:**
1. Break down the user instruction into an function name and parameters combination. The combination should CLEARLY REPRESENT all phrases in the instruction.
2. Find out name of the app to execute this command, if specified. Otherwise, write "unknown"

List of existing APIs:
"""

    sys_msg2 = \
"""
Reference Examples:
{"name":"findRestaurantsByCuisineAndLocation", "description": "This API is used to find restaurants in a specific location based on the type of cuisine.", "parameters":{"cuisine_type":"The type of cuisine to search for", "location":"The location to search in"}, "app": "unknown"}
{"name":"findHotelsByLocationAndDate", "description": "This API is used to find available hotels in a specific location within a specific date range.", "parameters":{"location":"The location to search in", "start_date":"The start date of the stay", "end_date":"The end date of the stay"}, "app": "unknown"}
{"name":"findDayTripPackagesByLocation", "description": "This API is used to find day trip packages in a specific location.", "parameters":{"location":"The location to search for day trip packages"}, "app": "unknown"}
{"name":"findAndSaveHotelsByLocationDateAndRating", "description": "This API is used to find available hotels in a specific location within a specific date range and rating, and save it to the user's trip plan.", "parameters":{"location":"The location to search in", "start_date":"The start date of the stay", "end_date":"The end date of the stay", "rating":"The rating of the hotel to search for", "trip_plan":"The trip plan to save the found hotel to"}, "app": "unknown"}

Respond using the JSON format below. Ensure the response can be parsed by Python json.loads:
{"reasoning":<reasoning>, "found_match": <true or false>,  "name":<api_name>, "description": <description of what api intends to do>, "parameters":{"<parameter_name>":"<parameter description>",...}, "app": "<name of the app to execute this command, if specified. Otherwise, write \'unknown\'>"}

"""

    known_api_list_str = generate_numbered(known_api_list)
    sys_msg = sys_msg1 + known_api_list_str + sys_msg2

    human_msg = \
f""" User instruction: : {instruction}"""

    return [sys_msg, human_msg]