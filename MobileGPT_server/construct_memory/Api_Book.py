import json

from utils.Utils import load_memory, save_memory, log

class Api_Book:       #API
    def __init__(self):
        self.api_book_path = "./server_memory/api_book.csv"
        self.api_book_header = ['api', 'app']

        self.api_path = ""
        self.path_data = None

        #api : {name":<api_name>, "description": <description of what api intends to do>, parameters":{"<parameter_name>":"<parameter description>",...}, "app": "<name of the app to execute this command, if specified. Otherwise, write \'unknown\'>}
        self.api_book_data = load_memory(self.api_book_path, self.api_book_header)          #[{...}]
        self.api_book_data_dict = [json.loads(api['api']) for api in self.api_book_data]

    def load_app_api(self, app):
        self.api_path = f"./server_memory/database/{app}/{app}_path.csv"
        api_path_header = ['api', 'path']
        self.path_data = load_memory(self.api_path, api_path_header)

    def recall_sub_task_path(self, api):
        path = {}

        for api_ in self.path_data:
            if json.loads(api_["api"])["name"] == api:
                path = json.loads(api_["path"])
                break

        # initialize path to non-traversed.
        for node in path:
            if node != "instruction":
                for sub_task in path[node]:
                    sub_task['traversed'] = False

        log(f"known path (already saved api): {api}")
        return path

    def update_api_description(self, generated_api):

        for index, api in enumerate(self.api_book_data_dict):
            if generated_api['name'] == api['name']:
                if generated_api['app'] == api['app']:
                    api['description'] = generated_api['description']
                    self.api_book_data[index]['api'] = api

        saved_data = [[json.dumps(api["api"]), api["app"]] for api in self.api_book_data]

        save_memory(self.api_book_path, saved_data, self.api_book_header)

