import re
import xml.etree.ElementTree as ET

from utils.Utils import get_children_with_depth_and_rank, get_siblings_with_rank

class Generalizer:
    @classmethod
    def generalize_action(cls, screen: str, action: dict, arguments: dict) -> dict:

        arguments_ = {}
        for arg in arguments:
            arguments_[arg] = arguments[arg]["value"]
        arguments = arguments_

        # log("generalizing command: " + json.dumps(command) + " to : \n" + json.dumps(arguments) + "\n" + screen)
        generalized_action = cls.generalize_to_arguments(action, arguments)
        generalized_action = cls.generalize_to_screen(generalized_action, screen, arguments)
        # log("generalized command: " + json.dumps(generalized_command))
        return generalized_action

    @classmethod
    def generalize_to_screen(cls, action: dict, screen: str, api_args: dict) -> dict:
        api_args_ = {}
        for arg in api_args.keys():
            if arg not in action['args'].keys():
                api_args_[f"{arg}"] = api_args[f"{arg}"]

        api_args = api_args_

        action_args = action['args']
        ui_index = action_args['index']
        ui_tree = ET.fromstring(screen)

        # first find corresponding UI.
        target_ui = ui_tree.findall(f".//*[@index='{ui_index}']")[0]
        # print(ET.tostring(target_ui, encoding='unicode'))

        ui_attrib = {key: value for key, value in target_ui.attrib.items() if key in ['text', 'description']}
        if target_ui.text is not None:
            ui_attrib['text'] = target_ui.text
        # update action arguments with UI attributes
        action_args.update(ui_attrib)

        # generalize ui attributes to arguments
        for a_key in api_args:
            for ui_key in ui_attrib:
                if str(api_args[a_key]).lower() in ui_attrib[ui_key].lower():
                    # log(f"replacing: {ui_attrib[ui_key]} with <{a_key}>...", 'cyan')
                    pattern = re.compile(re.escape(api_args[a_key]), re.IGNORECASE)
                    temp = pattern.sub(f"<{a_key}>", ui_attrib[ui_key])
                    action_args[ui_key] = temp

        if len(ui_attrib) == 0:
            children = get_children_with_depth_and_rank(target_ui)
            for child in children:
                elem, depth, rank = child
                child_attrib = {key: value for key, value in elem.attrib.items() if key in ['text', 'description']}
                if elem.text is not None:
                    child_attrib['text'] = elem.text

                # generalize child's attributes to arguments
                for a_key in api_args:
                    for ui_key in child_attrib:
                        if str(api_args[a_key]).lower() in child_attrib[ui_key].lower():
                            pattern = re.compile(re.escape(str(api_args[a_key])), re.IGNORECASE)
                            temp = pattern.sub(f"<{a_key}>", child_attrib[ui_key])

                            if 'children' not in action_args:
                                action_args['children'] = []
                            action_args['children'].append((depth, rank, {ui_key: temp}))
                            # log(f"'{child_attrib[ui_key]}' at child ({depth}, {rank}) replaced with '{temp}'", 'cyan')

            if 'children' not in action_args:
                sibilings = get_siblings_with_rank(ui_tree, target_ui)
                for sib, rank in sibilings:
                    sib_attrib = {key: value for key, value in sib.attrib.items() if key in ['text', 'description']}
                    if sib.text is not None:
                        sib_attrib['text'] = sib.text

                    # generalize sib's attributes to arguments
                    for a_key in api_args:
                        for ui_key in sib_attrib:
                            if api_args[a_key].lower() in sib_attrib[ui_key].lower():
                                pattern = re.compile(re.escape(api_args[a_key]), re.IGNORECASE)
                                temp = pattern.sub(f"<{a_key}>", sib_attrib[ui_key])

                                if 'children' not in action_args:
                                    action_args['children'] = []
                                action_args['children'].append((0, rank, {ui_key: temp}))

            if 'children' not in action_args and len(api_args) == 0:
                for rank, child in enumerate(target_ui, start=1):
                    child_attrib = {key: value for key, value in child.attrib.items() if key in ['text', 'description']}
                    if child.text is not None:
                        child_attrib['text'] = child.text

                    if len(child_attrib) > 0:
                        if 'children' not in action_args:
                            action_args['children'] = []
                        action_args['children'].append((1, rank, child_attrib))
        return action

    @classmethod
    def generalize_to_arguments(cls, action: dict, api_args: dict) -> dict:
        # generalize command arguments to api arguments
        action_args = action['args']
        for a_key in api_args:
            for c_key in action_args:
                if c_key != "index" and api_args[a_key] in action_args[c_key]:
                    # log(f"replacing: {command_args[c_key]} with <{a_key}>...", 'cyan')
                    temp = action_args[c_key].replace(api_args[a_key], f"<{a_key}>")
                    action_args[c_key] = temp
        return action