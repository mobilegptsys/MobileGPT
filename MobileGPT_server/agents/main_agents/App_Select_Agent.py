import os
import re

from serpapi import GoogleSearch

from utils.Pinecone_Controller import Pinecone_Controller
from utils.Utils import load_memory, update_memory, generate_vector, log
from utils.Query import query

from agents.prompts.App_select_Agent_Prompt import make_messages

class App_Select_Agent:
    def __init__(self):
        self.namespace_name = os.getenv("MOBILEGPT_USER_NAME")
        self.pinecone_controller = Pinecone_Controller(self.namespace_name)

        self.applist_path = f"./server_memory/applist/{self.namespace_name}_applist.csv"
        self.applist_header = ['package_name', 'app_name', 'description']
        self.applist = load_memory(self.applist_path, self.applist_header)

    def store_applist(self, package_lists):        #save the applists
        # log("All applications: ")
        # log("\n".join(app_names), "blue")
        package_names, app_names, descriptions = self.get_descriptions(package_lists)       #load the serpapi the app's description

        if len(descriptions) == 0:          #if there is not loaded app's description
            return

        upsert_response = self.pinecone_controller.upsert(self.generate_applist_vectors_to_upsert(package_names, app_names, descriptions))
        log("Number of stored applications: " + str(upsert_response), "green")

    def get_descriptions(self, package_lists):
        package_names = []
        app_names = []
        descriptions = []

        downloaded_applist = [app["package_name"] for app in self.applist]

        for package_name in package_lists:
            if not package_name in downloaded_applist:
                app_name, description = self.get_description(package_name)
                if description:
                    package_names.append(package_name)
                    app_names.append(app_name)
                    descriptions.append(description)

                update_memory(self.applist_path, [package_name, str(app_name), str(description)])
                self.applist.append({"package_name" : package_name, "app_name" : str(app_name), "description" : str(description)})

        return package_names, app_names, descriptions

    def get_description(self, package_name):
        params = {
            "engine": "google_play_product",
            "store": "apps",
            "product_id": package_name,
            "api_key": os.getenv("GOOGLESEARCH_KEY")
        }

        search_result = GoogleSearch(params).get_dict()

        app_name = None
        description = None

        if "about_this_app" in search_result and "snippet" in search_result["about_this_app"]:
            app_name = search_result["product_info"]["title"]
            description = search_result["about_this_app"]["snippet"]
        else:
            log("No description: " + package_name, 'red')

        return app_name, description

    def generate_applist_vectors_to_upsert(self, package_names, app_names, descriptions):
        description_vectors = [generate_vector(app_name + ". " + description) for app_name, description in zip(app_names, descriptions)]
        result = [{'id': package_name, "values": description_vector, "metadata":{'app_name' : app_name, 'description' : description}} for package_name, app_name, description, description_vector in zip(package_names, app_names, descriptions, description_vectors)]

        return result

    def predict_app(self, instruction):
        goal_vector = generate_vector(instruction)
        candidates_applist = self.pinecone_controller.get_candidates(goal_vector, is_include_metadata=True)

        # Select one application from top 5
        numbered_candidates_applist = self.generate_numbered_applist_to_prompt(candidates_applist)
        prompt_messages = make_messages(instruction, numbered_candidates_applist)
        predict_app = query(prompt_messages, os.getenv("APP_SELECT_AGENT_GPT_VERSION"))

        pattern = r"(?:\d+\.\s)?([^#]*)(?:\s#\$#)?"
        match = re.search(pattern, predict_app)

        predict_app = match.group(1).strip()

        log("Instruction: ")
        log(f"{instruction}")
        log("predicted App: ")
        log(predict_app, "green")

        return predict_app

    def generate_numbered_applist_to_prompt(self, responses):
        result = []
        for response in responses:
            result.append(response['id'] + " #$# " + response['metadata']['description'])

        return "\n".join([f"{i + 1}. {item}" for i, item in enumerate(result)])