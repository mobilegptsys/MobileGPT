import copy
import json

from agents.main_agents.Infer_agent import Infer_Agent

from construct_memory.Subtask_Edge import Sub_task_Edge
from construct_memory.Subtask_Edge import Action_Edge
from construct_memory.Subtask_Edge import Action_State

from agents.Generalizer import Generalizer
from agents.Filler import Filler
from utils import Examplifier

from utils.Utils import log, update_memory
import xml.etree.ElementTree as ET

class Action_Manager:
    def __init__(self, sub_task_edge: Sub_task_Edge, arguments: dict = {}, reasoning: dict = {}, is_vision=False, app=""):
        self.sub_task_edge = sub_task_edge
        self.description = self.sub_task_edge.sub_task['description']
        # {"name": action_name, "description:": action_description, "arguments": {<arg_name>:<arg_question>, ...}}
        self.goal_sub_task = self.parse_arguments(self.description, arguments)
        self.sub_task_reason = reasoning

        # { < argument_name >: {'description': < description >, 'value': < value >}, ...}
        self.arguments = arguments
        self.scroll_element = None

        if "wanted_information" in self.arguments.keys():
            self.scroll_element = copy.deepcopy(self.arguments["wanted_information"]["value"])
            del self.arguments["wanted_information"]

        self.error_count = 0

        self.current_screen = ""
        self.prev_screen = ""

        self.current_state_index: int = 0
        self.prev_state_index: int = -1

        self.last_traveling_edge : Action_Edge = None

        self.infer_agent: Infer_Agent = Infer_Agent(f"{self.goal_sub_task}")
        self.infer_agent.info_needed = self.arguments

        self.is_vision = is_vision
        self.app = app

        self.last_action_is_loaded = False
        self.scr_shot_path = ""

        self.error_pre_state_index = -1
        self.error_current_state_index = -1

        self.previous_actions = []

    def operate(self, encoded_xml, scr_shot_path):
        log("Action Manager received new screen", 'yellow')

        self.prev_screen = self.current_screen
        self.current_screen = encoded_xml

        self.scr_shot_path = scr_shot_path

        self.error_count = 0

        action = self.action_from_state(self.current_state_index)
        log(f"load saved action information", "blue")

        if self.scroll_element is not None:
            tree = ET.fromstring(self.current_screen)

            for element in tree.iter():
                if 'description' in element.attrib.keys():
                    if self.scroll_element in element.attrib['description']:
                        action = None
                if "text" in element.keys():
                    if element.text != None:
                        if self.scroll_element in element.text:
                            action = None

        if action is None:
            log(f"There is not saved information about current state {self.current_state_index}", "blue")
            # Make example from previous screen and corresponding command.
            example_template = self.example_from_state(self.current_state_index)
            # Inference new command from this screen.
            action = self.infer_action(encoded_xml, example_template)

            self.prev_state_index = self.current_state_index        #change state
            self.current_state_index = self.sub_task_edge.add_action_state(self.current_screen)

            if self.last_traveling_edge is not None and self.last_action_is_loaded == False:
                self.last_traveling_edge.start = self.prev_state_index
                self.last_traveling_edge.target = self.current_state_index
                self.last_traveling_edge.result = "Command success, continue with the next command."

                self.generalize_action()

                self.last_traveling_edge.update_memory(self.app)
                self.previous_actions.append(self.last_traveling_edge)

            self.make_edge(state=self.sub_task_edge.action_states[self.current_state_index])

            self.last_action_is_loaded = False

        else:
            log(f"I know current state({self.prev_state_index})'s action to the state({self.current_state_index})", "blue")

        return action

    def infer_action(self, screen: str, example: str | None, feedback: str = "") -> dict:
        log(f"asking gpt to choose action", "red")
        # There is no known edge to travel, so set it to None and ask GPT.
        if self.is_vision:
            response = self.infer_agent.infer_action_vision(self.goal_sub_task, self.sub_task_reason, screen, self.scr_shot_path, example=example, feedback=feedback)
        else:
            response = self.infer_agent.infer_action_no_vision(self.goal_sub_task, self.sub_task_reason, screen, example=example, feedback=feedback)

        self.infer_agent.action_history.append(copy.deepcopy(response))

        return response

    def make_edge(self, state=None, finish_graph: bool = False, destination_node_index: int = -1):
        if finish_graph:
            if self.last_action_is_loaded == False and self.error_count <= 1:
                self.prev_state_index = self.current_state_index        #change state
                self.current_state_index = self.sub_task_edge.add_action_state(self.current_screen)

                self.last_traveling_edge.destination = destination_node_index
                self.last_traveling_edge.start = self.prev_state_index
                self.last_traveling_edge.target = self.current_state_index
                self.last_traveling_edge.result = "Command success, finish command."

                self.generalize_action()

                self.last_traveling_edge.update_memory(self.app)
                self.previous_actions.append(self.last_traveling_edge)

                if self.last_traveling_edge.event["response"]["thoughts"]["command"]["name"] != "finish":

                    response = {"thoughts": {
                        "reasoning": "",
                        "completion": "100%",
                        "criticism": "",
                        "command": {"name": "finish",
                                    "args": {"response": f"{self.goal_sub_task} complete!"}}}}

                    self.infer_agent.action_history.append(copy.deepcopy(response))

                    self.make_edge(state=self.sub_task_edge.action_states[self.current_state_index])

                    self.last_traveling_edge.start = self.current_state_index
                    self.last_traveling_edge.result = "Command success, finish command. and the sub_task is ended"

                    self.last_traveling_edge.update_memory(self.app)
                    self.previous_actions.append(self.last_traveling_edge)

                    return response

        else:
            edge = state.add_action_edge(action_start_state=self.prev_state_index,
                                         goal=self.infer_agent.goal_sub_task,
                                         info=self.infer_agent.info_needed,
                                         history=self.infer_agent.action_history[:-1],
                                         response=copy.deepcopy(self.infer_agent.action_history[-1]))

            edge.traversed = True

            self.last_traveling_edge = edge

    def Answer(self, info: str) -> dict:
        log("Command Agent received new answer:" + info, 'yellow')
        question, name, value = info.split("\\", 2)

        # { < argument_name >: {'description': < description >, 'value': < value >}, ...}

        # Fill info_needed for gpt.
        if name in self.infer_agent.info_needed:
            self.infer_agent.info_needed[name]['value'] = value
        if name in self.arguments:
            self.arguments[name]['value'] = value
            self.goal_sub_task = self.parse_arguments(self.description, self.arguments)

        if self.last_action_is_loaded == False:
            self.last_traveling_edge.result = f"Assistant:\"{question}\", User:\"{value}\""
            self.last_traveling_edge.start = self.prev_state_index
            self.last_traveling_edge.target = self.current_state_index

            self.generalize_action()

            self.last_traveling_edge.update_memory(self.app)
            self.previous_actions.append(self.last_traveling_edge)

        action = self.action_from_state(self.current_state_index)

        feedback = f"Feedback: The answers to previous questions you asked (\"{question}\") are: \"{value}\"."

        if action is None:
            example_str = self.example_from_state(self.current_state_index)
            self.infer_agent.action_history.append({"thoughts": feedback})

            action = self.infer_action(self.current_screen, example=example_str, feedback=feedback)

            self.prev_state_index = self.current_state_index
            self.current_state_index = self.sub_task_edge.add_action_state(self.current_screen)

        self.make_edge(state=self.sub_task_edge.action_states[self.current_state_index])

        return feedback, action

    def Error(self, msg: str) -> dict:
        log("Command Agent received Error: " + msg, 'red')
        prev_response = self.infer_agent.action_history[-1]
        prev_command = prev_response['thoughts']['command']['name']

        # Add Error message as the result of previous command
        #self.last_traveling_edge.result = f"Error: command '{prev_command}' failed. {msg}"

        feedback = f"Feedback: previous command '{prev_command}' failed. {msg}."

        if self.error_count == 0:
            self.error_pre_state_index = self.prev_state_index
            self.error_current_state_index = self.current_state_index

        if self.error_count != 0:
            self.prev_state_index = self.error_pre_state_index
            self.current_state_index = self.error_current_state_index

        self.error_count += 1
        if self.error_count > 1:
            return feedback, self.force_quit_action()

        action = self.action_from_state(self.current_state_index)

        if action is None:
            example_str = self.example_from_state(self.current_state_index)
            self.infer_agent.action_history.append({"thoughts": feedback})

            action = self.infer_action(self.current_screen, example=example_str, feedback=feedback)

        del self.sub_task_edge.action_states[self.current_state_index].action_edges[-1]
        self.make_edge(self.sub_task_edge.action_states[self.current_state_index])

        return feedback, action

    def force_quit_action(self) -> dict:
        if self.error_count > 1:
            #에러 발생시 종료된 것
            log("error is repeating just quit this action", "red")

            if len(self.previous_actions) != 0:
                response = {"thoughts": {
                    "reasoning": "",
                    "completion": "100%",
                    "criticism": "",
                    "command": {"name": "finish",
                                "args": {"response": f"{self.goal_sub_task} maybe complete!"}}}}

                self.infer_agent.action_history.append(copy.deepcopy(response))

                self.make_edge(state=self.sub_task_edge.action_states[self.current_state_index])

                self.last_traveling_edge.start = self.current_state_index
                self.last_traveling_edge.result = "Command success, finish command. and the sub_task is ended"

                self.last_traveling_edge.update_memory(self.app)
                self.previous_actions.append(self.last_traveling_edge)

                return response

            response = {"thoughts": {
                "reasoning": "",
                "completion": "100%",
                "criticism": "",
                "command": {"name": "finish",
                            "args": {"response": f"Error performing action: {self.goal_sub_task}, lets try other approach."}}}}

            return  response

    def action_from_state(self, state_index: int) -> dict | None:
        #print(self.sub_task_edge.action_states)
        state_index = str(state_index)

        if state_index in self.sub_task_edge.action_states:
            state: Action_State = self.sub_task_edge.action_states[state_index]
        else:
            return None

        if len(state.action_edges) == 0:
            log(f"No out edge connected to state #{state.index} to be traveled", "red")
            return None

        for edge in state.action_edges:
            log(f"examining adapt edge to: state #{edge.start}, traversed: {edge.traversed}")
            if edge.traversed is False:
                log(f"found path! adapting command to: start state #{edge.start} and target state #{edge.target}", "cyan")
                adapt_action = Filler.adapt_action(self.current_screen, copy.deepcopy(edge.event['response']["thoughts"]["command"]), self.arguments)

                if adapt_action == "skip_ask":
                    edge.traversed = True
                    self.prev_state_index = self.current_state_index
                    self.current_state_index = int(edge.target)

                    self.last_traveling_edge = edge
                    self.last_action_is_loaded = True

                    return self.action_from_state(self.current_state_index)

                if adapt_action is not None:
                    edge.traversed = True

                    self.prev_state_index = self.current_state_index
                    self.current_state_index = int(edge.target)

                    self.last_traveling_edge = edge
                    self.last_action_is_loaded = True

                    log(json.dumps(adapt_action), "blue")

                    response_ = copy.deepcopy(edge.event["response"])

                    if 'speak' in response_["thoughts"]:
                        del response_["thoughts"]["speak"]

                    response_["thoughts"]["reasoning"] = "this command is newly adapted, so check command (what is interactioned)"
                    response_["thoughts"]["command"] = adapt_action

                    # add adapted response to event history.
                    self.infer_agent.action_history.append(copy.deepcopy(response_))

                    return response_

        log(f"no path to adapt!", "red")
        return None

    def example_from_state(self, state_index: int) -> str | None:
        state_index = str(state_index)

        if state_index in self.sub_task_edge.action_states:
            state: Action_State = self.sub_task_edge.action_states[state_index]
        else:
            return None

        if len(state.action_edges) == 0:
            log(f"No out edge connected to state #{state.index} to be examplified", "red")
            return None

        for edge in state.action_edges:
            log(f"examining example edge to: state #{edge.start}, traversed: {edge.traversed}")

            if edge.traversed is False:
                screen = edge.event['screen']
                goal = edge.event['goal']
                info = edge.event['info']
                history = edge.event['history']
                response = edge.event['response']

                if response["thoughts"]["command"]["name"] in ["click", "long-click", "input", "scroll"]:
                    example_str = Examplifier.generate_example_str(screen, goal, info, history, response)

                    return example_str

        log(f"no path to make example!", "red")
        return None

    def generalize_action(self):
        if self.last_traveling_edge.event['response']['thoughts']['command']['name'] in ['click', 'long-click', 'scroll', 'input']:
            log(f"""generalizing sub task graph for last action: {self.goal_sub_task}, before action - {self.last_traveling_edge.event['response']}""", 'white')
            Generalizer.generalize_action(self.last_traveling_edge.event["screen"], self.last_traveling_edge.event['response']['thoughts']['command'], self.arguments)

            log(f"""generalizing sub task graph for last action: {self.goal_sub_task}, after action - {self.last_traveling_edge.event['response']}""", 'white')


    def parse_arguments(self, description, arguments: dict) -> str:
        # arguments = {< argument_name >: {'description': < description >, 'value': < value >}, ...}
        # Extract the value part from your dictionary
        new_dict = {key: value['value'] for key, value in arguments.items()}

        # Convert the new dictionary to JSON format
        json_str = json.dumps(new_dict)

        # Format the string as required
        goal_detail = "Task : " + description + " (arguments:" + json_str + ")"
        return goal_detail