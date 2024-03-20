from utils.Utils import find_element_by_depth_and_rank, find_elements_with_specific_child_depth_and_rank
import copy
import xml.etree.ElementTree as ET


class Filler:
    @classmethod
    def adapt_action(cls, screen: str, action: dict, arguments: dict) -> dict:
        # log("adapting command: " + json.dumps(command) + " to : \n" + json.dumps(arguments) + "\n" + screen)

        if action['name'] == "finish":
            action["args"] = {"response": "Success!"}

            return action

        arguments_ = {}
        for arg in arguments:
            arguments_[arg] = arguments[arg]["value"]
        arguments = arguments_

        if action["name"] == "ask" and action["args"]["needed_info_name"] in arguments:
            if arguments[action["args"]["needed_info_name"]] != "unknown":
                return "skip_ask"
            else:
                return action

        if 'index' in action['args']:
            adapted_action = cls.adapt_action_to_arguments(action, arguments)
            adapted_action = cls.adapt_action_to_screen(adapted_action, screen)

            if adapted_action != None:
                if adapted_action["name"] == "input":
                    if adapted_action["args"]["input_text"] == "unknown":
                        return None

            return adapted_action

    @classmethod
    def adapt_action_to_arguments(cls, action: dict, api_args: dict) -> (dict, bool):
        action_copy = copy.deepcopy(action)
        action_args = action_copy['args']
        for c_key in action_args:           #index, description
            for a_key in api_args:
                if c_key != "index" and f"<{a_key}>" in action_args[c_key]:
                    # log(f"replacing: <{a_key}> with {api_args[a_key]}...", 'cyan')
                    temp = action_args[c_key].replace(f"<{a_key}>", api_args[a_key])
                    action_args[c_key] = temp

        if 'children' in action_args:
            for child in action_args['children']:
                _, _, target_attrib = child
                for a_key in api_args:
                    for t_key in target_attrib:
                        if f"<{a_key}>" in target_attrib[t_key]:
                            temp = target_attrib[t_key].replace(f"<{a_key}>", api_args[a_key])
                            target_attrib[t_key] = temp
                            # log(f"replacing: <{a_key}> with {api_args[a_key]}...", 'cyan')
                            break
        return action_copy

    @classmethod
    def adapt_action_to_screen(cls, action: dict, screen: str) -> dict | None:
        action_name = action['name']
        action_args = action['args']

        action_attrib = action_args.copy()
        del action_attrib['index']
        if action_name == 'input':
            del action_attrib['input_text']
        if action_name == 'scroll':
            del action_attrib['direction']

        ui_tree = ET.fromstring(screen)

        if 'children' in action_attrib:
            # Get list of all candidate UIs for each child
            candidate_group = []
            for child in action_attrib['children']:
                depth, rank, target_attrib = child
                candidate_group.append(find_elements_with_specific_child_depth_and_rank(ui_tree, depth, rank))

            # get candidate UIs common in all groups
            candidate_uis = set(candidate_group[0])
            for group in candidate_group[1:]:
                candidate_uis.intersection_update(group)
            # print(list(candidate.get('index') for candidate in candidate_uis))

            # Test if each candidate ui's children matches requirements.
            candidate_index = 0
            for candidate in candidate_uis:
                child_match_counter = len(action_attrib['children'])
                for child in action_attrib['children']:
                    depth, rank, target_attrib = child

                    target_child = find_element_by_depth_and_rank(candidate, depth, rank)

                    child_attrib = {key: value for key, value in target_child.attrib.items() if
                                    key in ['text', 'description']}
                    if target_child.text is not None:
                        child_attrib['text'] = target_child.text

                    if any(child_attrib.get(ui_key).lower() == target_attrib.get(t_key).lower() for t_key in target_attrib
                           for ui_key in child_attrib):
                        child_match_counter -= 1

                if child_match_counter == 0:
                    candidate_index = candidate.get('index')
                    break
            if candidate_index != 0:
                action_args['index'] = candidate_index
                return action
            else:
                return None

        # if the target ui has 'text' or 'description' attribute, use it to find corresponding ui on this screen.
        if len(action_attrib) > 0:
            for ui in ui_tree.iter():
                ui_attrib = {key: value for key, value in ui.attrib.items() if key in ['text', 'description']}
                if ui.text is not None:
                    ui_attrib['text'] = ui.text

                if any(ui_attrib.get(ui_key).lower() == action_attrib.get(a_key).lower() for a_key in action_attrib for
                       ui_key in ui_attrib):
                    action_args['index'] = ui.get('index')
                    # log(f"found corresponding UI in this screen: {json.dumps(ui_attrib)}", 'cyan')
                    return action
        # log(f"no UI attribute to adapt to screen, using it as it is...", 'cyan')
        return None