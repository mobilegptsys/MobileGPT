import re
import xml.etree.ElementTree as ET
from copy import deepcopy

from utils import parsing_utils
from utils.utils import log


def generalize_action(action: dict, subtask: dict, screen) -> dict:
    if "index" in action['parameters']:
        action = deepcopy(action)
        subtask_arguments = subtask['parameters']
        generalized_action = generalize_action_to_arguments(action, subtask_arguments)
        generalized_action = generalize_action_to_screen(generalized_action, screen, subtask_arguments)
        return generalized_action
    else:
        return action


def adapt_action(action: dict, screen: str, subtask_args: dict) -> dict:
    if 'index' in action['parameters']:
        adapted_action = adapt_action_to_arguments(action, subtask_args)
        adapted_action = adapt_action_to_screen(adapted_action, screen)
        return adapted_action
    else:
        return action


def adapt_action_to_arguments(action: dict, subtask_args: dict) -> (dict, bool):
    def reverse_replacement(s, subtask_arg_key, subtask_arg_value):
        def replace_match(match):
            placeholder = match.group(0)
            list_name, index = placeholder[1:-1].split('__')
            index = int(index)
            if list_name == subtask_arg_key:
                if index == -1:
                    return subtask_arg_value
                else:
                    words = subtask_arg_value.split()
                    return words[index]


        pattern = re.compile(r'<[^>]+>')
        return pattern.sub(replace_match, s)

    action_copy = deepcopy(action)
    action_args = action_copy['parameters']
    if any(key in action_args for key in ['text', 'description']):
        for a_key in action_args:
            for s_key in subtask_args:
                replaced_string = reverse_replacement(action_args[a_key], s_key, subtask_args[s_key])
                if replaced_string:
                    action_args[a_key] = replaced_string
                    break

    if 'children' in action_args:
        for child in action_args['children']:
            _, _, child_attrib = child
            for c_key in child_attrib:
                for s_key in subtask_args:
                    replaced_string = reverse_replacement(child_attrib[c_key], s_key, subtask_args[s_key])
                    if replaced_string:
                        child_attrib[c_key] = replaced_string
                        break

    if 'parent' in action_args:
        _, parent_attrib = action_args['parent']
        for p_key in parent_attrib:
            for s_key in subtask_args:
                replaced_string = reverse_replacement(parent_attrib[p_key], s_key, subtask_args[s_key])
                if replaced_string:
                    parent_attrib[p_key] = replaced_string
                    break

    return action_copy


def adapt_action_to_screen(action: dict, screen: str):
    action_name = action['name']
    action_args = action['parameters']

    action_attrib = action_args.copy()
    del action_attrib['index']
    if action_name == 'input':
        del action_attrib['input_text']
    if action_name == 'scroll':
        del action_attrib['direction']

    ui_tree = ET.fromstring(screen)

    if all(key not in action_attrib for key in ['parent', 'children', 'attrib']):
        for ui in ui_tree.iter():
            ui_attrib = {key: value for key, value in ui.attrib.items() if key in ['text', 'description']}
            if ui.text is not None:
                ui_attrib['text'] = ui.text

            if any(ui_attrib.get(ui_key).lower() == action_attrib.get(a_key).lower() for a_key in action_attrib for
                   ui_key in ui_attrib):
                action_args['index'] = ui.get('index')
                return action

    if 'children' in action_attrib:
        candidate_group = []
        for child in action_attrib['children']:
            depth, rank, target_attrib = child
            candidate_group.append(parsing_utils.find_elements_with_specific_child_depth_and_rank(ui_tree, depth, rank))

        candidate_uis = set(candidate_group[0])
        for group in candidate_group[1:]:
            candidate_uis.intersection_update(group)

        candidate_index = 0
        for candidate in candidate_uis:
            child_match_counter = len(action_attrib['children'])
            for child in action_attrib['children']:
                depth, rank, target_attrib = child

                target_child = parsing_utils.find_element_by_depth_and_rank(candidate, depth, rank)

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

    if 'parent' in action_attrib:
        child_rank, parent_attrib = action_attrib['parent']
        for ui in ui_tree.iter():
            ui_attrib = {key: value for key, value in ui.attrib.items() if key in ['text', 'description']}
            if ui.text is not None:
                ui_attrib['text'] = ui.text

            if any(ui_attrib.get(ui_key).lower() == parent_attrib.get(p_key).lower() for p_key in parent_attrib for
                   ui_key in ui_attrib):
                target_child_ui = ui[child_rank]
                action_args['index'] = target_child_ui.get('index')
                return action

    if 'attrib' in action_attrib:
        required_attrib = action_attrib['attrib']
        candidates = parsing_utils.find_matching_node(ui_tree, required_attrib)
        if len(candidates) > 0:
            for candidate in candidates:
                candidate_index = candidate.get('index')
                if candidate_index != 0:
                    action_args['index'] = candidate_index
                    return action

    return None


def generalize_action_to_arguments(action: dict, subtask_args: dict) -> dict:
    action_args = action['parameters']
    for s_key in subtask_args:
        for a_key in action_args:
            if isinstance(action_args[a_key], int):
                action_args[a_key] = str(action_args[a_key])

            if a_key != "index":
                if str(subtask_args[s_key]).lower() in action_args[a_key].lower():
                    pattern = re.compile(re.escape(str(subtask_args[s_key])), re.IGNORECASE)
                    replacement = f"<{s_key}__-1>"
                    replaced_attrib_value = pattern.sub(replacement, action_args[a_key])
                    action_args[a_key] = replaced_attrib_value
                else:
                    arg_words = str(subtask_args[s_key]).split()
                    for index, word in enumerate(arg_words):
                        if word.lower() in action_args[a_key].lower():
                            pattern = re.compile(re.escape(word), re.IGNORECASE)
                            replacement = f"<{s_key}__{index}>"
                            replaced_attrib_value = pattern.sub(replacement, action_args[a_key])
                            action_args[a_key] = replaced_attrib_value

    return action


def generalize_action_to_screen(action: dict, screen: str, subtask_args: dict) -> dict:
    action_args = action['parameters']
    target_ui_index = action_args['index']
    ui_tree = ET.fromstring(screen)

    target_ui = ui_tree.findall(f".//*[@index='{target_ui_index}']")[0]

    target_ui_attrib = {key: value for key, value in target_ui.attrib.items() if key in ['text', 'description']}
    if target_ui.text is not None:
        target_ui_attrib['text'] = target_ui.text

    if len(target_ui_attrib) > 0:
        for s_key in subtask_args:
            for ui_key in target_ui_attrib:
                if str(subtask_args[s_key]).lower() in target_ui_attrib[ui_key].lower():
                    pattern = re.compile(re.escape(str(subtask_args[s_key])), re.IGNORECASE)
                    replacement = f"<{s_key}__-1>"
                    replaced_attrib_value = pattern.sub(replacement, target_ui_attrib[ui_key])
                    target_ui_attrib[ui_key] = replaced_attrib_value
                else:
                    arg_words = str(subtask_args[s_key]).split()
                    for index, word in enumerate(arg_words):
                        if word.lower() in target_ui_attrib[ui_key].lower():
                            pattern = re.compile(re.escape(word), re.IGNORECASE)
                            replacement = f"<{s_key}__{index}>"
                            replaced_attrib_value = pattern.sub(replacement, target_ui_attrib[ui_key])
                            target_ui_attrib[ui_key] = replaced_attrib_value

        action_args.update(target_ui_attrib)

    if len(target_ui_attrib) == 0:
        children = parsing_utils.get_children_with_depth_and_rank(target_ui)
        for child in children:
            elem, depth, rank = child
            original_child_attrib = {key: value for key, value in elem.attrib.items() if key in ['text', 'description']}
            if elem.text is not None:
                original_child_attrib['text'] = elem.text

            generalized_child_attrib = {}

            for s_key in subtask_args:
                for ui_key in original_child_attrib:
                    if str(subtask_args[s_key]).lower() in original_child_attrib[ui_key].lower():
                        pattern = re.compile(re.escape(str(subtask_args[s_key])), re.IGNORECASE)
                        replacement = f"<{s_key}__-1>"
                        replaced_attrib_value = pattern.sub(replacement, original_child_attrib[ui_key])
                        original_child_attrib[ui_key] = replaced_attrib_value
                        generalized_child_attrib[ui_key] = replaced_attrib_value
                    else:
                        arg_words = str(subtask_args[s_key]).split()
                        for index, word in enumerate(arg_words):
                            if word.lower() in original_child_attrib[ui_key].lower():
                                pattern = re.compile(re.escape(word), re.IGNORECASE)
                                replacement = f"<{s_key}__{index}>"
                                replaced_attrib_value = pattern.sub(replacement, original_child_attrib[ui_key])
                                original_child_attrib[ui_key] = replaced_attrib_value
                                generalized_child_attrib[ui_key] = replaced_attrib_value

            if generalized_child_attrib:
                if 'children' not in action_args:
                    action_args['children'] = []
                action_args['children'].append((depth, rank, generalized_child_attrib))

        if 'children' not in action_args:
            siblings = parsing_utils.get_siblings_with_rank(ui_tree, target_ui)
            for sib, rank in siblings:
                original_sib_attrib = {key: value for key, value in sib.attrib.items() if key in ['text', 'description']}
                if sib.text is not None:
                    original_sib_attrib['text'] = sib.text

                generalized_sib_attrib = {}
                for s_key in subtask_args:
                    for ui_key in original_sib_attrib:
                        if str(subtask_args[s_key]).lower() in original_sib_attrib[ui_key].lower():
                            pattern = re.compile(re.escape(str(subtask_args[s_key])), re.IGNORECASE)
                            replacement = f"<{s_key}__-1>"
                            replaced_attrib_value = pattern.sub(replacement, original_sib_attrib[ui_key])
                            original_sib_attrib[ui_key] = replaced_attrib_value
                            generalized_sib_attrib[ui_key] = replaced_attrib_value
                        else:
                            arg_words = str(subtask_args[s_key]).split()
                            for index, word in enumerate(arg_words):
                                if word.lower() in original_sib_attrib[ui_key].lower():
                                    pattern = re.compile(re.escape(word), re.IGNORECASE)
                                    replacement = f"<{s_key}__{index}>"
                                    replaced_attrib_value = pattern.sub(replacement, original_sib_attrib[ui_key])
                                    original_sib_attrib[ui_key] = replaced_attrib_value
                                    generalized_sib_attrib[ui_key] = replaced_attrib_value

                if 'children' not in action_args:
                    action_args['children'] = []
                action_args['children'].append((0, rank, generalized_sib_attrib))

        if 'children' not in action_args:
            child_rank, parent = parsing_utils.find_parent_node(ui_tree, target_ui_index)
            if parent:
                parent_attrib = {key: value for key, value in parent.attrib.items() if key in ['text', 'description']}
                if parent.text is not None:
                    parent_attrib['text'] = parent.text

                for s_key in subtask_args:
                    for ui_key in parent_attrib:
                        if str(subtask_args[s_key]).lower() in parent_attrib[ui_key].lower():
                            pattern = re.compile(re.escape(str(subtask_args[s_key])), re.IGNORECASE)
                            replacement = f"<{s_key}__-1>"
                            replaced_attrib_value = pattern.sub(replacement, parent_attrib[ui_key])
                            action_args['parent'] = (child_rank, {ui_key: replaced_attrib_value})
                        else:
                            arg_words = str(subtask_args[s_key]).split()
                            for index, word in enumerate(arg_words):
                                if word.lower() in parent_attrib[ui_key].lower():
                                    pattern = re.compile(re.escape(word), re.IGNORECASE)
                                    replacement = f"<{s_key}__{index}>"
                                    replaced_attrib_value = pattern.sub(replacement, parent_attrib[ui_key])
                                    action_args['parent'] = (child_rank, {ui_key: replaced_attrib_value})

        if 'children' not in action_args and 'parent' not in action_args:
            key_attributes = parsing_utils.get_ui_key_attrib(target_ui_index, screen, include_desc=True)
            action_args['attrib'] = key_attributes

    return action
