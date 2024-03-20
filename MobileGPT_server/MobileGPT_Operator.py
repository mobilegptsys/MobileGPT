import json, copy
from PIL import Image, ImageStat

from enum import Enum

from utils.Utils import log, update_memory

from agents.main_agents.App_Select_Agent import App_Select_Agent
from agents.main_agents.Instuction_Translator_Agent import Instruction_Translator
from agents.main_agents.Parameter_Filler_Agent import Parameter_Filler_Agent

from agents.main_agents.Select_Agent import Select_Agent

from agents.Action_Manager import Action_Manager

from construct_memory.Api_Book import Api_Book
from construct_memory.Screen_graph import Screen_Graph

from utils.Input_Processing import screenshot_processing

#to check the current mode
class Mode(Enum):
    AUTO = 0        #self-operate
    DEMO = 1        #memory repair to use the given demo
    RESUME_AUTO = 2

#this operator based on only one of the given user's instruction
class MobileGPT_Operator:
    def __init__(self, socket):
        self.socket = socket

        self.app_select_agent = App_Select_Agent()        #app select agent
        self.instruction_translator = Instruction_Translator()
        self.overlapping_agent = None
        self.parameter_filler = Parameter_Filler_Agent()

        self.action_manager = None

        self.api_book = Api_Book()

        self.instruction = ""
        self.api = ""
        self.app = ""

        self.mode = Mode.AUTO

        self.prev_screen_xml = None
        self.current_screen_xml = None

        self.prev_screenshot = None
        self.current_screenshot = None

        self.screen_graph = None

        # action event history (list of gpt's thought)
        self.sub_task_path = {}
        self.api_arguments: dict = {}

        self.sub_task_history = []
        self.action_history = []

        self.sub_task_history_summary = []
        self.current_sub_task = None

        self.current_node_index: int = -2
        self.prev_node_index: int = -2

        self.parsed_xml = None
        self.hierarchy_xml = None
        self.encoded_xml = None
        self.scr_shot_path = None
        self.is_vision = None

        self.recent_response = None
        self.api_description = ""

        self.already_saved = False

    def init(self, instruction, api, app):
        self.instruction = instruction
        api["app"] = app
        self.api = api

        del self.api["reasoning"]
        del self.api["found_match"]

        self.app = app

        self.screen_graph = Screen_Graph(app)
        self.screen_graph.graph_load()

        self.api_book.load_app_api(app)
        self.sub_task_path = self.api_book.recall_sub_task_path(api['name'])

        log('Mobile Agent Initialized for app: ' + app + ' / API: ' + api['name'])

    def is_FLAG_SECURE(self, image_path, top_fraction=0.2):

        image = Image.open(image_path)
        width, height = image.size
        exclude_height = int(height * top_fraction)
        cropped_image = image.crop((0, exclude_height, width, height))

        rgb_image = cropped_image.convert('RGB')

        variance_sum = 0
        # Adjust the loop to iterate over the cropped image correctly
        for y in range(0, cropped_image.height):  # Start from 0 for the cropped image
            for x in range(cropped_image.width):  # Use cropped_image.width for clarity
                r, g, b = rgb_image.getpixel((x, y))
                variance_sum += ((r - g)**2 + (r - b)**2 + (g - b)**2) / 3

        avg_variance = variance_sum / ((width * (height - exclude_height)))

        return avg_variance < 10

    def operate(self, parsed_xml, hierarchy_xml, encoded_xml, scr_shot_path, sub_task_finish, is_vision) -> dict:
        log("Mobile Agent received new screen", 'yellow')

        self.parsed_xml = parsed_xml
        self.hierarchy_xml = hierarchy_xml
        self.encoded_xml = encoded_xml
        self.scr_shot_path = scr_shot_path
        self.is_vision = is_vision

        self.prev_screenshot = self.current_screenshot
        self.current_screenshot = scr_shot_path

        if self.is_vision:
            if not self.is_FLAG_SECURE(scr_shot_path):
                self.is_vision = True
                process_screenshot = screenshot_processing(scr_shot_path, parsed_xml)
                self.encoded_xml = encoded_xml
                self.scr_shot_path = process_screenshot
            else:
                self.is_vision = False

        self.prev_screen_xml = self.current_screen_xml
        self.current_screen_xml = encoded_xml

        #Explore
        screen_node_change, node_index = self.explore(sub_task_finish)

        # if screen changed from previous one.
        if screen_node_change:
            # choose action to perform on this screen
            # next_sub_task = {"function_call": {"arguments":{<argument_name>: <argument_value>,}, "name":<action_name>}, "completion_rate": <XX%>, "reasoning": <reasoning>}
            next_sub_task = self.select(node_index)

            sub_task_name = next_sub_task['function_call']['name']

            if sub_task_name == 'Finish':
                return self.finish_instruction()

            self.send_sub_task_to_phone(f"""$$##$${self.screen_graph.screen_nodes[node_index].sub_tasks_dict[sub_task_name]["description"]}""")

            self.setting_infer_phase(node_index, sub_task_name, next_sub_task)
            self.action_history = []

        self.prev_node_index = self.current_node_index
        self.current_node_index = node_index

        self.recent_response = self.infer()
        return self.recent_response


    def explore(self, sub_task_finish):

        log("Explore Phase", "white")

        is_new_app_page, node_index = self.screen_graph.Node_Search(self.parsed_xml, self.hierarchy_xml, self.encoded_xml, self.scr_shot_path, self.is_vision)

        if is_new_app_page:
            log(f"This screen is new screen, no explore data. I generate new node of {node_index}", "red")
        else:
            log(f"I know this screen node of {node_index}", "red")

        # check if screen changed from previous one (found new path)
        if self.mode == Mode.AUTO:
            if node_index != self.current_node_index or sub_task_finish:
                # if this is not the starting vertex, generalize command graph
                if self.current_node_index != -2:
                    # generalize actions for the sub_task.
                    response = self.action_manager.make_edge(finish_graph=True, destination_node_index=node_index)     #그전에 마지막 action이 종료됐다면
                    if response != None:
                        self.action_history.append(copy.deepcopy(response))

                    self.sub_task_history_summary.append(Select_Agent.make_sub_task_summary(self.screen_graph.screen_nodes[self.current_node_index].sub_tasks_dict, self.current_sub_task, self.action_history))
                log("new Screen!", "red")
                return True, node_index

        return False, node_index

    def select(self, node_index):
        log("Select Phase", "white")

        node = self.screen_graph.screen_nodes[node_index]

        # {<Action name> : {<arg_name>:<arg_value>, ...}, "completion_rate": <instruction completion rate in percentage>, "reasoning": <reasoning>}
        sub_task = self.fill_parameter_from_path(node_index)

        # if there is no known and untraveled path, find new one, and add it to path.
        if sub_task is None:
            log("I don't know this Selection result about the given instruction on this node(Screen page).", "red")
            select_agent = Select_Agent(node.available_sub_tasks)
            if self.is_vision:
                sub_task: dict = select_agent.select_subtask_vision(instruction=self.instruction, screen=self.current_screen_xml, sub_task_history=self.sub_task_history_summary, scr_shot_path=self.scr_shot_path)
            else:
                sub_task: dict = select_agent.select_subtask_no_vision(instruction=self.instruction, screen=self.current_screen_xml, sub_task_history=self.sub_task_history_summary)
        else:
            log("I know this Selection result about the given instruction on this node(Screen page).", "red")

        self.current_sub_task = {"node_index" : node_index, "sub_task" : sub_task, "screen" : self.current_screen_xml}
        self.sub_task_history.append(self.current_sub_task)

        return sub_task

    def fill_parameter_from_path(self, node_index):

        node_index = str(node_index)

        if self.sub_task_path == {}:
            return None


        self.already_saved = True
        sub_task_instruction = self.sub_task_path["instruction"]

        if node_index in self.sub_task_path:
            for past_sub_task in self.sub_task_path[node_index]:
                if not past_sub_task['traversed']:
                    sub_task_reasoning = past_sub_task['reasoning']
                    sub_task_function_call = past_sub_task['function_call']
                    sub_task_past_screen_xml = past_sub_task['past_screen_xml']

                    for sub_task in self.screen_graph.screen_nodes[int(node_index)].available_sub_tasks:
                        if sub_task["name"] == sub_task_function_call["name"]:
                            #print(self.encoded_xml)

                            if len(sub_task_function_call["parameters"]) == 0 or sub_task_function_call["name"]=="Finish":
                                past_sub_task['traversed'] = True
                                sub_task_ = copy.deepcopy(past_sub_task)

                                sub_task_["completion_rate"] = "10"
                                del sub_task_["traversed"]
                                del sub_task_["past_screen_xml"]

                                return sub_task_

                            if self.is_vision:
                                sub_task = self.parameter_filler.parameter_filling_vision(self.instruction, sub_task, self.encoded_xml, self.scr_shot_path, sub_task_instruction, sub_task_reasoning, sub_task_function_call, sub_task_past_screen_xml)
                            else:
                                sub_task = self.parameter_filler.parameter_filling_no_vision(self.instruction, sub_task, self.encoded_xml, sub_task_instruction, sub_task_reasoning, sub_task_function_call, sub_task_past_screen_xml)

                            if sub_task is not None:
                                past_sub_task['traversed'] = True
                                return sub_task

        return None

    def infer(self):
        log("Infer Phase", "white")

        response = self.action_manager.operate(self.encoded_xml, self.scr_shot_path)
        self.recent_response = response
        self.action_history.append(copy.deepcopy(self.recent_response))

        return response

    def setting_infer_phase(self, node_index, sub_task_name, next_sub_task):
        sub_task_edge = self.load_sub_task_edge(node_index, sub_task_name)
        sub_task_arguments = self.compose_arguments_descriptions_with_values(sub_task_edge, next_sub_task)       # return {<argument_name>: {'description': <description>, 'value': <value>}, ...}
        self.action_manager = Action_Manager(sub_task_edge=sub_task_edge, arguments=sub_task_arguments, reasoning=next_sub_task["reasoning"], is_vision=self.is_vision, app=self.app)

    def load_sub_task_edge(self, node_index: int, sub_task_name: str):
        node = self.screen_graph.screen_nodes[node_index]

        if sub_task_name in node.sub_tasks_edges:
            sub_task_edge = node.sub_tasks_edges[sub_task_name]
            #sub_task_edge.init()
            return sub_task_edge
        else:
            sub_task_edge = node.add_sub_task_edge(sub_task_name)
            return sub_task_edge

    def compose_arguments_descriptions_with_values(self, sub_task_edge, sub_task: dict) -> dict:
        # return {<argument_name>: {'description': <description>, 'value': <value>}, ...}
        sub_task_arguments = sub_task['function_call']['parameters']
        arg_names = list(sub_task_arguments.keys())

        arg_with_descriptions_and_values = {}
        for arg_name in arg_names:
            if arg_name in sub_task_edge.sub_task['parameters']:
                arg_description = sub_task_edge.sub_task['parameters'][arg_name]
                arg_value = sub_task_arguments[arg_name]
                arg_with_descriptions_and_values[arg_name] = {'description': arg_description, 'value': arg_value}
        return arg_with_descriptions_and_values

    #api : {name":<api_name>, "description": <description of what api intends to do>, parameters":{"<parameter_name>":"<parameter description>",...}, "app": "<name of the app to execute this command, if specified. Otherwise, write \'unknown\'>}
    def finish_instruction(self):
        #self.action_manager.force_quit_action()
        log(f"your instruction Finished!", "red")
        # send finishing code.
        self.socket.send("$$$$$".encode())
        self.socket.send("\r\n".encode())

        if self.already_saved:
            return None

        if len(self.sub_task_path) == 0:
            # summarize the path we went through.
            for history in self.sub_task_history:
                node_index = history["node_index"]
                sub_task = history["sub_task"]
                screen_xml = history["screen"]

                if node_index not in self.sub_task_path:
                    self.sub_task_path[node_index] = []

                self.sub_task_path[node_index].append({'name': sub_task['function_call']['name'], 'reasoning': sub_task['reasoning'], 'function_call' : sub_task['function_call'], 'past_screen_xml' : screen_xml})

            self.sub_task_path["instruction"] = self.instruction

            update_memory(self.api_book.api_book_path, [json.dumps(self.api), json.dumps(self.app)])
            update_memory(self.api_book.api_path, [json.dumps(self.api), json.dumps(self.sub_task_path)])

        return None

    def Answer(self, answer):
        feedback, self.recent_response = self.action_manager.Answer(answer)
        self.action_history.append(copy.deepcopy(feedback))
        self.action_history.append(copy.deepcopy(self.recent_response))

        return self.recent_response

    def Error(self, err_msg):
        feedback, self.recent_response = self.action_manager.Error(err_msg)
        self.action_history.append(copy.deepcopy(feedback))
        self.action_history.append(copy.deepcopy(self.recent_response))

        if self.recent_response["thoughts"]["command"]["name"] == "finish":
            if self.recent_response["thoughts"]["command"]["args"]["response"].split(" ")[0] == "Error":
                del self.sub_task_history[-1]
            else:
                del self.action_history[-5:-1]

        return self.recent_response

    def Quit(self):
        self.finish_instruction()

    def send_sub_task_to_phone(self, sub_task_description: str):
        log(f"Sending action to phone: {sub_task_description}", "red")
        self.socket.send(sub_task_description.encode())
        self.socket.send("\r\n".encode())
