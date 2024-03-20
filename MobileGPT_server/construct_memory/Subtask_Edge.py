from utils.Utils import log, update_memory

import json

class Sub_task_Edge:
    def __init__(self, sub_task: dict, source: int = -1):
        self.source = source
        # {"name": action_name, "description:": action_description, "arguments": {<arg_name>:<arg_question>, ...}}
        self.sub_task = sub_task
        self.action_states = {}
        self.state_count = 0


    def add_action_state(self, screen_xml, index=None) -> int:
        self.state_count = len(self.action_states)

        for state in self.action_states:
            state_ = self.action_states[state]
            skip_count = False

            for edge in state_.action_edges:
                if edge.event["response"]["thoughts"]["command"]["name"] == "finish":
                    skip_count = True

            if skip_count:
                self.state_count -= 1

        print(self.state_count)

        if index == None:
            index = self.state_count

        log(f"adding new state #{index} to sub_task edge: '{self.sub_task['name']}'", "red")
        action_node = Action_State(screen_xml, index, self.source, self.sub_task)
        self.action_states[index] = action_node
        self.state_count += 1

        return index


class Action_State:
    def __init__(self, screen_xml, index: int = -1, source=None, sub_task=None):
        self.index = index
        self.action_edges = []
        self.screen_xml = screen_xml

        self.source = source
        self.sub_task = sub_task


    def add_action_edge(self, action_start_state: int, action_target_state: int = -1, goal: str="", info: dict={}, history: list=[], response: dict={}, result: str = ""):
        log("adding new command edge to graph", "green")
        event = {"screen": self.screen_xml, "goal": goal, "info": info, "history": history, "response": response}

        if result != "":
            edge = Action_Edge(start=action_start_state, target=action_target_state, event=event, result=result, source=self.source, sub_task=self.sub_task)
        else:
            edge = Action_Edge(start=action_start_state, event=event, source=self.source, sub_task=self.sub_task)
        self.action_edges.append(edge)

        return edge


class Action_Edge:
    def __init__(self, start: int = -1, target: int = -1, event: dict = {}, result: str = "", destination : int = -1, source=None, sub_task=None):
        self.start: int = start
        self.target: int = target
        self.event: dict = event
        self.result = result
        self.traversed: bool = False
        self.destination = destination

        self.source = source
        self.sub_task = sub_task

    def update_memory(self, app):            #얘는 나중에 전체 generalize 한 다음에 처리해야 함
        data = [self.source, self.sub_task["name"], self.start, self.target, self.event["screen"], self.event["goal"], json.dumps(self.event["info"]), json.dumps(self.event["history"]), json.dumps(self.event["response"]), self.result, self.destination]
        update_memory(f"./server_memory/database/{app}/{app}_edge.csv", data)

        log(f"store action edge result : {self.result}", "red")