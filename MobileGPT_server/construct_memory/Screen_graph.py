import json, os

from utils.Utils import load_memory, update_memory, generate_vector, log, find_parent, find_child, get_xml_depth_rank_list, save_memory

from agents.main_agents.Explore_Agent import Explore_Agent

from construct_memory.Subtask_Edge import Sub_task_Edge

from utils.Pinecone_Controller import Pinecone_Controller
import xml.etree.ElementTree as ET

#Screen_Graph - per app
#Screen_Node  - per app_page
#Subtask_Edge - per app_page's subtasks
#Action_Node  - Subtask's operation (action sequence)
#Action_Edge  - action edge

class Screen_Graph:
    def __init__(self, app: str):
        self.app = app
        self.screen_nodes = {}
        self.node_count = 0

        self.graph_path = f"./server_memory/database/{app}/{app}_graph.csv"
        self.graph_header = ['node_index', 'sub_tasks', 'sub_tasks_ui', 'known_ui', "sub_task_count"]
        self.graph_data = None

        self.edge_path = f"./server_memory/database/{app}/{app}_edge.csv"
        self.edge_header = ['node_index', 'sub_task_name', 'action_start_state', 'action_target_state', 'screen_xml', 'goal', 'info', 'history', 'response', 'result', 'destination_index']
        self.edge_data = None

        self.pinecone_controller = Pinecone_Controller(f"{self.app}_screen_node")
        self.picone_count_path = f"./server_memory/database/{app}/{app}_pincone_count.txt"
        self.picone_count = 0

        if os.path.exists(self.picone_count_path):
            with open(self.picone_count_path, 'r') as file:
                self.picone_count = int(file.read())
        else:
            with open(self.picone_count_path, 'w') as file:
                file.write(str(self.picone_count))

        self.explore_agent = Explore_Agent()
        self.node_threshold = 0.8

    def graph_load(self):
        log("loading graph...", "blue")
        self.graph_data = load_memory(self.graph_path, self.graph_header)
        self.node_count = len(self.graph_data)

        self.edge_data = load_memory(self.edge_path, self.edge_header)

        # self.rendering_data

        for node in self.graph_data:
            log(f"""adding screen node index {node["node_index"]}""", "white")
            screen_node = Screen_Node(index=int(node["node_index"]), sub_tasks=node["sub_tasks"], sub_tasks_ui=node["sub_tasks_ui"], known_ui=node["known_ui"], sub_task_count=node["sub_task_count"])
            self.screen_nodes[int(node["node_index"])] = screen_node

        self.graph_data = [[data["node_index"], data["sub_tasks"], data["sub_tasks_ui"], data["known_ui"], data["sub_task_count"]] for data in self.graph_data]

        for edge in self.edge_data:      #        Screen_Graph [nodes] -> Screen_Node [sub_tasks_edges] -> Sub_task_Edge [nodes] -> Action_Edge
            screen_node = self.screen_nodes[int(edge["node_index"])]
            if edge["sub_task_name"] not in screen_node.sub_tasks_edges:
                screen_node.add_sub_task_edge(edge["sub_task_name"])

            #['node_index', 'sub_task_name', 'action_start_state', 'action_target_state', 'screen_xml', 'goal', 'info', 'history', 'response', 'result', 'destination_index']

            sub_task_edge = screen_node.sub_tasks_edges[edge["sub_task_name"]]
            if edge["action_start_state"] not in sub_task_edge.action_states:
                sub_task_edge.add_action_state(edge["screen_xml"], edge["action_start_state"])

            #self, action_start_state: int, action_target_state: int, goal: str, info: dict, history: list, response: dict, result: str = ""
            action_state = sub_task_edge.action_states[edge["action_start_state"]]
            tmp_edge = action_state.add_action_edge(edge["action_start_state"], edge["action_target_state"], edge["goal"], json.loads(edge["info"]), json.loads(edge["history"]), json.loads(edge["response"]), edge["result"])

            if edge["destination_index"] != -1:
                tmp_edge.destination = edge["destination_index"]

    #if is_vision -> encoded_xml = processing_xml
    def Node_Search(self, parsed_xml, hierarchy_xml, encoded_xml, scr_shot_path, is_vision):
        if self.node_count == 0:                                                     #any node isn't there. So create Node
            self.Node_Generation(parsed_xml, hierarchy_xml, encoded_xml, scr_shot_path, is_vision)
            return True, self.node_count-1

        similar_nodes = self.pinecone_controller.get_candidates(generate_vector(hierarchy_xml), is_include_metadata=True)

        search_case, screen_node_index, can_operated_sub_tasks, unknown_ui = self.Sub_tasks_Can_Operate(parsed_xml, similar_nodes)

        if search_case == "NEW":
            self.Node_Generation(parsed_xml, hierarchy_xml, encoded_xml, scr_shot_path, is_vision)
            return True, self.node_count-1

        elif search_case == "SUB":
            log(f"sub screen node index {screen_node_index}", "white")
            self.screen_nodes[screen_node_index].available_sub_tasks = can_operated_sub_tasks
            self.screen_nodes[screen_node_index].available_init()
            return False, screen_node_index

        elif search_case == "SAME":
            log(f"same screen node index {screen_node_index}", "white")
            self.screen_nodes[screen_node_index].available_sub_tasks = can_operated_sub_tasks
            self.screen_nodes[screen_node_index].available_init()
            return False, screen_node_index

        elif search_case == "EXPAND":         #This expand node about the unknown uis           체크 할 것
            log(f"expanding screen node index {screen_node_index}", "white")
            new_sub_task = self.Node_Expansion(parsed_xml, hierarchy_xml, encoded_xml, can_operated_sub_tasks, screen_node_index, unknown_ui, scr_shot_path, is_vision)
            for one_new_sub_task in new_sub_task:
                can_operated_sub_tasks.append(one_new_sub_task)

            self.screen_nodes[screen_node_index].available_sub_tasks = can_operated_sub_tasks
            self.screen_nodes[screen_node_index].available_init()
            return False, screen_node_index

    def Node_Expansion(self, parsed_xml, hierarchy_xml, encoded_xml, can_operated_sub_tasks, screen_node_index, unknown_ui, scr_shot_path, is_vision):
        if is_vision:
            new_sub_task, expanded_sub_task = self.explore_agent.expand_screen_no_vision(encoded_xml, self.screen_nodes[screen_node_index].sub_tasks, unknown_ui)
        else:
            new_sub_task, expanded_sub_task = self.explore_agent.expand_screen_no_vision(encoded_xml, self.screen_nodes[screen_node_index].sub_tasks, unknown_ui)

        rm = []
        for sub_task in new_sub_task:
            if sub_task["name"] in self.screen_nodes[screen_node_index].sub_tasks_dict.keys():
                for expanded_sub_task_ in expanded_sub_task:
                    if sub_task["name"] == expanded_sub_task_["name"]:
                        for ui_index in sub_task["UI_index"]:
                            expanded_sub_task_["UI_index"].append(ui_index)
                        break

                expanded_sub_task.append(sub_task)
                rm.append(sub_task)

        for r in rm:
            new_sub_task.remove(r)

        for sub_task in new_sub_task:
            remove_ui = []

            for ui_index in sub_task["UI_index"]:
                if ui_index not in unknown_ui:
                    remove_ui.append(ui_index)

            for ui_index in remove_ui:
                sub_task["UI_index"].remove(ui_index)


        for sub_task in expanded_sub_task:
            remove_ui = []

            for ui_index in sub_task["UI_index"]:
                if ui_index not in unknown_ui:
                    remove_ui.append(ui_index)

            for ui_index in remove_ui:
                sub_task["UI_index"].remove(ui_index)

        sub_tasks = []
        for sub_task in new_sub_task:
            if len(sub_task["UI_index"])!=0:
                sub_tasks.append(sub_task)

        for sub_task in sub_tasks:
            self.screen_nodes[screen_node_index].sub_tasks_dict[sub_task["name"]] = sub_task

        tmp_expanded_sub_task = []
        for sub_task in expanded_sub_task:
            if len(sub_task["UI_index"])!=0:
                tmp_expanded_sub_task.append(sub_task)
        expanded_sub_task = tmp_expanded_sub_task


        for sub_task in sub_tasks:
            for ui_index in sub_task["UI_index"]:
                if ui_index in unknown_ui:
                    unknown_ui.remove(ui_index)

        for sub_task in expanded_sub_task:
            for ui_index in sub_task["UI_index"]:
                if ui_index in unknown_ui:
                    unknown_ui.remove(ui_index)

        new_sub_tasks_ui = {}

        for sub_task in sub_tasks:                      #sub_task to UI(positional(parent, child), description, id, classname)
            new_sub_tasks_ui[sub_task["name"]] = self.Subtask_to_UI(sub_task, parsed_xml)

        for sub_task in sub_tasks:
            del sub_task["UI_index"]

        index = 0
        for node in self.graph_data:
            if int(node[0]) == int(screen_node_index):
                break
            index += 1

        tmp_node_data = json.loads(self.graph_data[index][1])
        for sub_task in sub_tasks:
            tmp_node_data.append(sub_task)
            self.screen_nodes[screen_node_index].sub_tasks.append(sub_task)
        self.graph_data[index][1] = json.dumps(tmp_node_data)

        tmp_node_data = json.loads(self.graph_data[index][2])
        for sub_task_ui in new_sub_tasks_ui:
            tmp_node_data[f"{sub_task_ui}"] = new_sub_tasks_ui[f"{sub_task_ui}"]
            self.screen_nodes[screen_node_index].sub_tasks_ui[f"{sub_task_ui}"] = new_sub_tasks_ui[f"{sub_task_ui}"]
        self.graph_data[index][2] = json.dumps(tmp_node_data)

        if len(expanded_sub_task)!=0:       #expanded sub_task's ui append on saved sub_task
            for sub_task in expanded_sub_task:
                if sub_task["name"] not in self.screen_nodes[screen_node_index].sub_tasks_dict.keys():
                    continue

                if self.screen_nodes[screen_node_index].sub_tasks_ui[sub_task["name"]][-1]["structure"] == "True":
                    dummy_action = {"name": sub_task["name"], "description": "dummy", "parameters": {"dummy": "dummy? ['dummy1', 'dummy2']"}, "UI_index": sub_task["UI_index"]}
                else:
                    dummy_action = {"name": sub_task["name"], "description": "dummy", "parameters": {}, "UI_index": sub_task["UI_index"]}

                tmp_node_data = json.loads(self.graph_data[index][2])

                del tmp_node_data[sub_task["name"]][-1]
                del self.screen_nodes[screen_node_index].sub_tasks_ui[sub_task["name"]][-1]

                for sub_task_ui in self.Subtask_to_UI(dummy_action, parsed_xml):
                    tmp_node_data[sub_task["name"]].append(sub_task_ui)
                    self.screen_nodes[screen_node_index].sub_tasks_ui[sub_task["name"]].append(sub_task_ui)
                self.graph_data[index][2] = json.dumps(tmp_node_data)

        known_ui_dict = {"UI_index": unknown_ui, "parameters": {}}

        if known_ui_dict["UI_index"] != []:
            known_ui = self.Subtask_to_UI(known_ui_dict, parsed_xml)

            tmp_node_data = json.loads(self.graph_data[index][3])

            if tmp_node_data != []:
                del tmp_node_data[-1]
                del self.screen_nodes[screen_node_index].known_ui[-1]

            for one_knowun_ui in known_ui:
                tmp_node_data.append(one_knowun_ui)
                self.screen_nodes[screen_node_index].known_ui.append(one_knowun_ui)
            self.graph_data[index][3] = json.dumps(tmp_node_data)


        sub_task_count = len(can_operated_sub_tasks) + len(new_sub_task)

        self.graph_data[index][4] = str(min(int(self.graph_data[index][4]), sub_task_count))
        self.screen_nodes[screen_node_index].sub_task_count = min((int(self.graph_data[index][4]), sub_task_count))


        save_memory(self.graph_path, self.graph_data, self.graph_header)
        self.hierarchy_save(hierarchy_xml, screen_node_index)

        return new_sub_task


    def Node_Generation(self, parsed_xml, hierarchy_xml, encoded_xml, scr_shot_path, is_vision):
        pre_sub_tasks = self.Explore_Sub_Tasks(encoded_xml, scr_shot_path, is_vision)

        sub_tasks = []
        for sub_task in pre_sub_tasks["Actions"]:
            if len(sub_task["UI_index"])!=0:
               sub_tasks.append(sub_task)

        sub_tasks_ui = {}

        for sub_task in sub_tasks:                      #sub_task to UI(positional(parent, child), description, id, classname)
            sub_tasks_ui[sub_task["name"]] = self.Subtask_to_UI(sub_task, parsed_xml)

        extracted_sub_tasks_ui = []
        for sub_task in sub_tasks:
            for index in sub_task["UI_index"]:
                extracted_sub_tasks_ui.append(index)

        for sub_task in sub_tasks:
            del sub_task["UI_index"]

        known_ui = self.Known_UI(extracted_sub_tasks_ui, parsed_xml)

        sub_task_count = len(sub_tasks)

        self.graph_data.append([self.node_count, json.dumps(sub_tasks), json.dumps(sub_tasks_ui), json.dumps(known_ui), sub_task_count])

        log(f"adding screen node index {self.node_count}", "white")
        screen_node = Screen_Node(index=self.graph_data[-1][0], sub_tasks=self.graph_data[-1][1], sub_tasks_ui=self.graph_data[-1][2], known_ui=self.graph_data[-1][3], sub_task_count=self.graph_data[-1][4])
        self.screen_nodes[self.node_count] = screen_node
        self.screen_nodes[self.node_count].available_sub_tasks = sub_tasks
        self.screen_nodes[self.node_count].available_init()

        self.hierarchy_save(hierarchy_xml, self.node_count)
        update_memory(self.graph_path, self.graph_data[-1])

        self.node_count += 1

    def Explore_Sub_Tasks(self, encoded_xml, scr_shot_path, is_vision):        #parsed_xml, hierarchy_xml, process_parsed_xml, action_finish, process_screenshot, is_vision
        if is_vision:
            response = self.explore_agent.explore_screen_vision(scr_shot_path, encoded_xml)
        else:
            response = self.explore_agent.explore_screen_no_vision(encoded_xml)

        return response

    def hierarchy_save(self, hierarchy_xml, screen_node_index):
        self.pinecone_controller.upsert([{'id': str(self.picone_count), "values": generate_vector(hierarchy_xml), "metadata": {'screen_node_index': str(screen_node_index)}}])
        self.picone_count += 1

        with open(self.picone_count_path, 'w') as file:
            file.write(str(self.picone_count))

    def Subtask_to_UI(self, sub_task, parsed_xml):
        #criteria => [tag, id, class_name] : 1,  parent_tag : 2, child_tag : 3, position : 4, structure : 5, index : 6
        #[[[criteria], one_ui], [[criteria], two_ui]]

        represent_uis = []

        parameters = sub_task["parameters"].keys()
        check_structure = False

        if parameters:           #check the description
            for parameter in parameters:
                parameters_description = sub_task["parameters"][parameter]
                if "[" in parameters_description:
                    check_structure = json.loads(parameters_description.split("?")[-1].strip().replace("\'","\""))      #string

        tree = ET.fromstring(parsed_xml)

        xml_depth_rank_list = get_xml_depth_rank_list(parsed_xml)

        for UI in sub_task["UI_index"]:

            if UI != 1:
                xml_tag = tree.find(f".//*[@index='{UI}']")
            else:
                xml_tag = tree

            tag = xml_tag.tag
            id = xml_tag.attrib.get('id', 'NONE')
            class_name = xml_tag.attrib.get('class', 'NONE')
            parent_tag = find_parent(parsed_xml, xml_depth_rank_list, UI)
            if parent_tag["id"] != None:
                parent_tag["tag"] = parent_tag["id"]
                parent_tag["class"] = parent_tag["class"]

            child_tag = find_child(parsed_xml, xml_depth_rank_list, UI)
            position = xml_tag.attrib.get('bounds')
            index = xml_tag.attrib['index']

            represent_uis.append({"tag":tag, "id":id, "class":class_name, "parent_tag":parent_tag, "child_tag":child_tag, "position":position, "index":index})

        ui_information = []

        #criteria => [tag, id, class_name] : 1,  parent_tag : 2, child_tag : 3, position : 4, structure : 5, index : 6

        #delete duplication -> with check identity [1,2,3,4,5]
        def check_and_append_ui_information(group_UI, step, ui_information, parsed_xml, xml_depth_rank_list):
            for criteria, group in list(group_UI.items()):
                if step == 4:
                    ui_information.append([step, [group[0]]])
                    continue

                if self.Is_Independent(step, group, parsed_xml, xml_depth_rank_list):
                    ui_information.append([step, [group[0]]])
                    del group_UI[criteria]

        def update_group_UI(group_UI, step):
            group_UI_ = {}
            for group in group_UI.keys():
                for represent_ui in group_UI[group]:
                    if step == 2:
                        criteria = (represent_ui["tag"], represent_ui["id"], represent_ui["class"], str(represent_ui["parent_tag"]))
                    elif step == 3:
                        child_tags = sorted([one["tag"] + one["id"] + one["class"] for one in represent_ui["child_tag"]])
                        criteria = (represent_ui["tag"], represent_ui["id"], represent_ui["class"], str(represent_ui["parent_tag"]), str(child_tags))
                    elif step == 4:
                        criteria = (represent_ui["tag"], represent_ui["id"], represent_ui["class"], represent_ui["position"])

                    if criteria not in group_UI_:
                        group_UI_[criteria] = []
                    group_UI_[criteria].append(represent_ui)
            return group_UI_

        group_UI = {}
        for represent_ui in represent_uis:
            criteria = (represent_ui["tag"], represent_ui["id"], represent_ui["class"])
            if criteria not in group_UI:
                group_UI[criteria] = []
            group_UI[criteria].append(represent_ui)

        for step in range(1, 5):
            check_and_append_ui_information(group_UI, step, ui_information, parsed_xml, xml_depth_rank_list)
            if group_UI and step < 4:
                group_UI = update_group_UI(group_UI, step + 1)

        if check_structure:
            ui_information.append({"structure" : "True"})
        else:
            ui_information.append({"structure" : "False"})

        return ui_information


    def Is_Independent(self, check_case, group_UI, parsed_xml, xml_depth_rank_list):
        indexes = [group_ui["index"] for group_ui in group_UI]
        base_criteria = (group_UI[0]["tag"], group_UI[0]["id"], group_UI[0]["class"])

        for xml_tag in ET.fromstring(parsed_xml).iter():
            tag = xml_tag.tag
            id = xml_tag.attrib.get('id', 'NONE')
            class_name = xml_tag.attrib.get('class', 'NONE')
            current_criteria = (tag, id, class_name)

            if check_case == 1:
                if group_UI[0]["id"] == "NONE":
                    return False

                if base_criteria == current_criteria and xml_tag.attrib['index'] not in indexes:
                    return False

            elif check_case == 2:
                if base_criteria == current_criteria:
                    parent_tag = find_parent(parsed_xml, xml_depth_rank_list, xml_tag.attrib["index"])
                    base_criteria = base_criteria + (str(group_UI[0]["parent_tag"]),)

                    if base_criteria == current_criteria + (str(parent_tag),) and xml_tag.attrib['index'] not in indexes:
                        return False

            elif check_case == 3:
                if base_criteria == current_criteria:
                    parent_tag = find_parent(parsed_xml, xml_depth_rank_list, xml_tag.attrib["index"])
                    child_tags = find_child(parsed_xml, xml_depth_rank_list, xml_tag.attrib["index"])
                    child_tags_criteria = str(sorted([one["tag"] + one["id"] + one["class"] for one in child_tags]))

                    child_tags = sorted([one["tag"] + one["id"] + one["class"] for one in group_UI[0]["child_tag"]])
                    base_criteria = base_criteria + (str(group_UI[0]["parent_tag"]),) + (str(child_tags),)

                    if base_criteria == current_criteria + (str(parent_tag),) + (child_tags_criteria,) and xml_tag.attrib['index'] not in indexes:
                        return False

        return True

    def Known_UI(self, extracted_sub_tasks_ui, parsed_xml):
        tree = ET.fromstring(parsed_xml)
        known_ui = []
        known_ui_indexes = []

        for tag in ['input', 'button', 'checker']:
            for xml_tag in tree.findall(f".//{tag}"):
                index = int(xml_tag.attrib['index'])
                if index not in extracted_sub_tasks_ui:
                    known_ui_indexes.append(index)

        known_ui_dict = {"UI_index": known_ui_indexes, "parameters": {}}

        if known_ui_dict["UI_index"] != []:
            known_ui = self.Subtask_to_UI(known_ui_dict, parsed_xml)

        return known_ui

    def UI_is_there(self, parsed_xml, sub_task_uis, delete_unknown_ui_indexes, xml_depth_rank_list):
        selected_index = []         #string

        #print(sub_task_uis)

        for sub_task_ui in sub_task_uis[:-1]:            #criteria => [tag, id, class_name] : 1,  parent_tag : 2, child_tag : 3, position : 4,
            sub_task_represent_ui = sub_task_ui[1][0]

            sub_task_ui_1 = (sub_task_represent_ui["tag"], sub_task_represent_ui["id"], sub_task_represent_ui["class"])
            sub_task_ui_2 = (sub_task_represent_ui["tag"], sub_task_represent_ui["id"], sub_task_represent_ui["class"], str(sub_task_represent_ui["parent_tag"]))

            child_tag = sub_task_represent_ui["child_tag"]
            child_tags = sorted([one["tag"] + one["id"] + one["class"] for one in child_tag])

            sub_task_ui_3 = (sub_task_represent_ui["tag"], sub_task_represent_ui["id"], sub_task_represent_ui["class"], str(sub_task_represent_ui["parent_tag"]), str(child_tags))
            sub_task_ui_4 = (sub_task_represent_ui["tag"], sub_task_represent_ui["id"], sub_task_represent_ui["class"], sub_task_represent_ui["position"])

            for xml_tag in ET.fromstring(parsed_xml).iter():
                tag = xml_tag.tag
                id = xml_tag.attrib.get('id', 'NONE')
                class_name = xml_tag.attrib.get('class', 'NONE')
                position = xml_tag.attrib.get('bounds')
                index = xml_tag.attrib['index']

                criteria = (tag, id, class_name)

                if sub_task_ui[0] == 1:
                    if criteria == sub_task_ui_1:
                        selected_index.append(index)

                if sub_task_ui[0] == 4:
                    criteria = (tag, id, class_name, position)
                    if criteria == sub_task_ui_4:
                        selected_index.append(index)

                if sub_task_ui[0] == 2 and criteria == sub_task_ui_1:

                    parent_tag = find_parent(parsed_xml, xml_depth_rank_list, index)
                    if parent_tag["id"] != None:
                        parent_tag["tag"] = parent_tag["id"]
                        parent_tag["class"] = parent_tag["class"]
                    criteria = (tag, id, class_name, str(parent_tag))

                    if criteria == sub_task_ui_2:
                        selected_index.append(index)

                if sub_task_ui[0] == 3 and criteria == sub_task_ui_1:
                    parent_tag = find_parent(parsed_xml, xml_depth_rank_list, index)
                    if parent_tag["id"] != None:
                        parent_tag["tag"] = parent_tag["id"]
                        parent_tag["class"] = parent_tag["class"]

                    child_tag = find_child(parsed_xml, xml_depth_rank_list, index)
                    child_tags = sorted([one["tag"] + one["id"] + one["class"] for one in child_tag])

                    criteria = (tag, id, class_name, str(parent_tag), str(child_tags))
                    if criteria == sub_task_ui_3:
                        selected_index.append(index)

        if selected_index:
            for one_tag_index in selected_index:
                delete_unknown_ui_indexes.append(one_tag_index)
            return True

        else:
            return False


    def Sub_tasks_Can_Operate(self, parsed_xml, similar_nodes):
        search_case = None
        equal_node = None
        result_can_operated_sub_tasks = None
        result_unknown_ui = None

        xml_depth_rank_list = get_xml_depth_rank_list(parsed_xml)

        max_can_operate_sub_tasks_number = 9999

        unknown_ui_indexes = []

        tree = ET.fromstring(parsed_xml)
        for tag in ['input', 'button', 'checker']:
            for xml_tag in tree.findall(f".//{tag}"):
                index = int(xml_tag.attrib['index'])
                unknown_ui_indexes.append(index)

        for similar_node in similar_nodes:
            similarity_score = similar_node['score']
            screen_node_index = int(similar_node['metadata']["screen_node_index"])

            print(f"This screen has similarity score of {1-similarity_score} with node #{screen_node_index}")

            similar_node_sub_tasks = self.screen_nodes[screen_node_index].sub_tasks
            similar_node_sub_task_uis = self.screen_nodes[screen_node_index].sub_tasks_ui
            similar_node_known_ui = self.screen_nodes[screen_node_index].known_ui
            similar_node_sub_task_count = int(self.screen_nodes[screen_node_index].sub_task_count)

            can_operated_sub_tasks = []

            delete_unknown_ui_indexes = []

            for sub_task in similar_node_sub_tasks:
                if self.UI_is_there(parsed_xml, similar_node_sub_task_uis[sub_task["name"]], delete_unknown_ui_indexes, xml_depth_rank_list):
                    can_operated_sub_tasks.append(sub_task)

            self.UI_is_there(parsed_xml, similar_node_known_ui, delete_unknown_ui_indexes, xml_depth_rank_list)

            real_unknown_ui_indexes = []
            for unknown_ui_index in unknown_ui_indexes:
                if str(unknown_ui_index) not in delete_unknown_ui_indexes:
                    real_unknown_ui_indexes.append(unknown_ui_index)

            if similar_node_sub_task_count - len(can_operated_sub_tasks) < max_can_operate_sub_tasks_number:

                tmp_search_case = None

                if len(real_unknown_ui_indexes) == 0 and len(can_operated_sub_tasks) >= 1:
                    tmp_search_case = "SUB"

                if len(real_unknown_ui_indexes) == 0 and len(can_operated_sub_tasks) == similar_node_sub_task_count:
                    tmp_search_case = "SAME"

                if len(real_unknown_ui_indexes) != 0 and len(can_operated_sub_tasks) >= similar_node_sub_task_count * self.node_threshold:
                    tmp_search_case = "EXPAND"

                search_case = tmp_search_case
                max_can_operate_sub_tasks_number = similar_node_sub_task_count - len(can_operated_sub_tasks)
                equal_node = screen_node_index
                result_can_operated_sub_tasks = can_operated_sub_tasks
                result_unknown_ui = real_unknown_ui_indexes

        if search_case == None:
            search_case = "NEW"

        return search_case, equal_node, result_can_operated_sub_tasks, result_unknown_ui


class Screen_Node:
    def __init__(self, index: int = -1, sub_tasks: str = "", sub_tasks_ui: str = "", known_ui: str = "", sub_task_count: str = ""):
        self.index = index

        # [{"name": <name_of_action>, "description": <description of action>, '"parameters": {<parameter_name>:<question to ask for the parameter>},...},...]
        self.sub_tasks = json.loads(sub_tasks)
        self.sub_tasks_ui = json.loads(sub_tasks_ui)
        self.known_ui = json.loads(known_ui)
        self.sub_task_count = int(sub_task_count)

        self.sub_tasks_dict = {}
        for sub_task in self.sub_tasks:
            self.sub_tasks_dict[sub_task["name"]] = sub_task

        self.initial_sub_tasks()

        self.sub_tasks_edges = {}

        self.available_sub_tasks = None

    def add_sub_task_edge(self, sub_task_name: str):
        sub_task_edge: Sub_task_Edge = Sub_task_Edge(sub_task=self.sub_tasks_dict[sub_task_name], source=self.index)
        self.sub_tasks_edges[sub_task_name] = sub_task_edge
        log(f"adding edge graph starting from node #{self.index} for action '{sub_task_name}'", "blue")
        return sub_task_edge

    def available_init(self):
        self.available_sub_tasks.append(self.sub_tasks_dict["Scroll"])
        self.available_sub_tasks.append(self.sub_tasks_dict["Send Screen to User"])
        self.available_sub_tasks.append(self.sub_tasks_dict["Finish"])


    def initial_sub_tasks(self):
        self.sub_tasks_dict["Scroll"] = {"name": "Scroll", "description": "Useful for when you need to scroll up or down to view more UIs and actions but you must stop when you find or see that you want.","parameters": {"direction": "direction to scroll", "wanted_information": "what is that you found?"}}
        self.sub_tasks_dict["Send Screen to User"] = {"name": "Send Screen to User", "description": "send the user requested information in the screen to the user", "parameters": {"information": "what you want to say to the user in natural language (non-question format)."}}
        self.sub_tasks_dict["Finish"] = {"name": "Finish", "description": "Task has been completed", "parameters": {"response": "Final response to let user know you have finished the task"}}