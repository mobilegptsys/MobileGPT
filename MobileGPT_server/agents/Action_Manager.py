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

class Action_Manager:
    def __init__(self, sub_task_edge: Sub_task_Edge, arguments: dict = {}, reasoning: dict = {}, is_vision=False, app=""):
        self.sub_task_edge = sub_task_edge
        self.description = self.sub_task_edge.sub_task['description']
        # {"name": action_name, "description:": action_description, "arguments": {<arg_name>:<arg_question>, ...}}
        self.goal_sub_task = self.parse_arguments(self.description, arguments)
        self.sub_task_reason = reasoning

        # { < argument_name >: {'description': < description >, 'value': < value >}, ...}
        self.arguments = arguments

        self.error_count = 0

        self.current_screen = ""
        self.prev_screen = ""

        self.current_state_index: int = 0
        self.prev_state_index: int = -1

        self.last_traveling_edge : Action_Edge = None
        self.edges_traveled = []

        self.infer_agent: Infer_Agent = Infer_Agent(f"{self.goal_sub_task}")
        self.infer_agent.info_needed = self.arguments

        self.is_vision = is_vision
        self.app = app

        self.dont_save = False
        self.scr_shot_path = ""

    def operate(self, encoded_xml, scr_shot_path):
        log("Action Manager received new screen", 'yellow')

        self.prev_screen = self.current_screen
        self.current_screen = encoded_xml

        self.scr_shot_path = scr_shot_path

        self.error_count = 0

        action = self.action_from_state(self.current_state_index)
        log(f"load saved action information", "blue")

        if action is None:
            log(f"There is not saved information about current state {self.current_state_index}", "blue")
            # Make example from previous screen and corresponding command.
            example_template = self.example_from_state(self.current_state_index)
            # Inference new command from this screen.
            action = self.infer_action(encoded_xml, example_template)

            self.prev_state_index = self.current_state_index
            self.current_state_index = self.sub_task_edge.add_action_state(self.current_screen)

            if self.last_traveling_edge is not None:
                self.last_traveling_edge.start = self.prev_state_index
                self.last_traveling_edge.target = self.current_state_index
                self.last_traveling_edge.result = "Command success, continue with the next command."

                self.generalize_action()

                if not self.dont_save:
                    self.last_traveling_edge.update_memory(self.app)

                self.dont_save = False

            self.make_edge(state=self.sub_task_edge.action_states[self.current_state_index])

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

        self.infer_agent.action_history.append(response)

        return response

    def make_edge(self, state=None, finish_graph: bool = False, destination_node_index: int = -1):
        if finish_graph:
            self.prev_state_index = self.current_state_index
            self.current_state_index = self.sub_task_edge.add_action_state(self.current_screen)

            if not self.dont_save:
                self.last_traveling_edge.destination = destination_node_index
                self.last_traveling_edge.start = self.prev_state_index
                self.last_traveling_edge.target = self.current_state_index
                self.last_traveling_edge.result = "Command success, finish command."

                self.generalize_action()

                self.last_traveling_edge.update_memory(self.app)

            self.dont_save = False

        else:
            edge = state.add_action_edge(action_start_state=self.prev_state_index,
                                         goal=self.infer_agent.goal_sub_task,
                                         info=self.infer_agent.info_needed,
                                         history=self.infer_agent.action_history[:-1],
                                         response=self.infer_agent.action_history[-1])

            edge.traversed = True
            self.dont_save = False

            self.edges_traveled.append(edge)
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

        if not self.dont_save:
            self.last_traveling_edge.result = f"Assistant:\"{question}\", User:\"{value}\""
            self.last_traveling_edge.target = self.current_state_index
            self.last_traveling_edge.update_memory(self.app)

        action = self.action_from_state(self.current_state_index)

        if action is None:
            example_str = self.example_from_state(self.current_state_index)
            feedback = f"Feedback: The answers to previous questions you asked (\"{question}\") are: \"{value}\"."

            self.infer_agent.action_history.append({"thoughts": feedback})

            action = self.infer_action(self.current_screen, example=example_str, feedback=feedback)

        self.prev_state_index = self.current_state_index
        self.current_state_index = self.sub_task_edge.add_action_state(self.current_screen)

        self.make_edge(state=self.sub_task_edge.action_states[self.current_state_index])

        return feedback, action

    def Error(self, msg: str) -> dict:
        log("Command Agent received Error: " + msg, 'red')
        self.error_count += 1
        if self.error_count > 1:
            return self.force_quit_action()

        last_action = self.infer_agent.action_history[-1]
        prev_response = last_action
        prev_command = prev_response['thoughts']['command']['name']

        # Add Error message as the result of previous command
        self.last_traveling_edge.result = f"Error: command '{prev_command}' failed. {msg}"

        action = self.action_from_state(self.current_state_index)

        if action is None:
            example_str = self.example_from_state(self.current_state_index)
            feedback = f"Feedback: previous command '{prev_command}' failed. {msg}."

            self.infer_agent.action_history.append({"thoughts": feedback})

            action = self.infer_action(self.current_screen, example=example_str, feedback=feedback)

        del self.edges_traveled[-1]
        del self.sub_task_edge.action_states[self.current_state_index].action_edges[-1]
        self.make_edge(self.sub_task_edge.action_states[self.current_state_index])

        return feedback, action


    def force_quit_action(self, finish_task=False, already_saved=None) -> dict:
        if finish_task:
            log("Finish the proceeding sub task", "red")
            if already_saved:
                response = {"thoughts": {
                    "reasoning": "",
                    "completion": "100%",
                    "criticism": "",
                    "command": {"name": "finish",
                                "args": {"response": f"{self.goal_sub_task} complete!"}}}}
                return response
        else:
            log("error is repeating just quit this action", "red")

        if len(self.edges_traveled) == 0:
            response = {"thoughts": {
                "reasoning": "",
                "completion": "100%",
                "criticism": "",
                "command": {"name": "finish",
                            "args": {"response": f"Error performing action: {self.goal_sub_task}, lets try other approach."}}}}
        else:
            response = {"thoughts": {       #"args": {"response": f"Looks like I finished the {self.goal_sub_task}"}}}}
                "reasoning": "",
                "completion": "100%",
                "criticism": "",
                "command": {"name": "finish",
                            "args": {"response": f"Error performing action: {self.goal_sub_task}, lets try other approach. if action is scroll, then there is no change about scroll action's result."}}}}

        self.infer_agent.action_history.append(response)

        self.prev_state_index = self.current_state_index
        self.current_state_index = self.sub_task_edge.add_action_state(self.current_screen)
        self.make_edge(self.sub_task_edge.action_states[self.current_state_index])

        self.last_traveling_edge.update_memory(self.app)

        return response

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
            log(f"examining edge to: state #{edge.start}, traversed: {edge.traversed}")
            if edge.traversed is False:
                log(f"found path! adapting command to: state #{edge.start}", "cyan")
                adapt_action = Filler.adapt_action(self.current_screen, copy.deepcopy(edge.event['response']["thoughts"]["command"]), self.arguments)

                if adapt_action == "skip_ask":
                    edge.traversed = True
                    continue

                if adapt_action is not None:
                    edge.traversed = True

                    #self.last_traveling_edge = edge
                    #self.edges_traveled.append(edge)

                    self.prev_state_index = self.current_state_index
                    self.current_state_index = int(edge.target)
                    self.dont_save = True

                    log(json.dumps(adapt_action), "blue")

                    response_ = copy.deepcopy(edge.event["response"])

                    if 'speak' in response_["thoughts"]:
                        del response_["thoughts"]["speak"]

                    response_["thoughts"]["reasoning"] = "this command is newly adapted, so check command (what is interactioned)"
                    response_["thoughts"]["command"] = adapt_action

                    # add adapted response to event history.
                    self.infer_agent.action_history.append(response_)

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
            log(f"examining edge to: state #{edge.target}, traversed: {edge.traversed}")
            if edge.traversed is False:
                screen = edge.event['screen']
                goal = edge.event['goal']
                info = edge.event['info']
                history = edge.event['history']
                response = edge.event['response']

                if response["thoughts"]["command"]["name"] in ["click", "long-click", "input", "scroll"]:
                    example_str = Examplifier.generate_example_str(screen, goal, info, history, response)

                    edge.traversed = True
                    return example_str

        log(f"no path to make example!", "red")
        return None

    def generalize_action(self):
        if self.last_traveling_edge.event['response']['thoughts']['command']['name'] in ['click', 'long-click', 'scroll', 'input']:

            state: Action_State = self.sub_task_edge.action_states[self.prev_state_index]
            before_generalize = copy.deepcopy([edge.event['response']['thoughts']['command'] for edge in state.action_edges])

            log(f"""generalizing sub task graph for last action: {self.goal_sub_task}, before action - {self.last_traveling_edge.event['response']}""", 'white')
            Generalizer.generalize_action(self.last_traveling_edge.event["screen"], self.last_traveling_edge.event['response']['thoughts']['command'], self.arguments)
            #self.last_traveling_edge.update_memory(self.app)

            after_action = self.last_traveling_edge.event['response']['thoughts']['command']
            
            log(f"""generalizing sub task graph for last action: {self.goal_sub_task}, after action - {self.last_traveling_edge.event['response']}""", 'white')

            if after_action in before_generalize:
                self.dont_save = True


    def parse_arguments(self, description, arguments: dict) -> str:
        # arguments = {< argument_name >: {'description': < description >, 'value': < value >}, ...}
        # Extract the value part from your dictionary
        new_dict = {key: value['value'] for key, value in arguments.items()}

        # Convert the new dictionary to JSON format
        json_str = json.dumps(new_dict)

        # Format the string as required
        goal_detail = "Task : " + description + " (arguments:" + json_str + ")"
        return goal_detail