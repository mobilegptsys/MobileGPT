import shutil
from datetime import datetime
import json
import os
import re
import xml.etree.ElementTree as ET

from utils.utils import log


def find_parent_node(root, child_index: int) -> (int, ET):
    """
    Finds the parent element of the child with a specific index value.

    Parameters:
    - root: The root element of the XML tree.
    - child_index: The index of the child element.

    Returns:
    - The parent element of the found child, or None if not found.
    """
    if isinstance(child_index, str):
        log("index is String!!!!!", "red")
        child_index = int(child_index)
    for parent in root.iter():
        for rank, child in enumerate(parent):
            if int(child.get("index")) == child_index:
                return rank, parent
    return 0, None


def find_children_with_attributes(element, depth=1):
    """
    Recursively finds children with 'text' or 'description' attributes up to a depth of 3.

    Parameters:
    - element: The current element to search within.
    - depth: The current depth in the tree.

    Returns:
    - A list of tuples, each containing (child, rank, depth) for valid children.
    """
    valid_children = []
    if depth > 3:  # Base case: if depth exceeds 3, stop the recursion.
        return valid_children

    for rank, child in enumerate(element, start=0):
        # Check if child has the 'text' or 'description' attribute
        if child.text is not None or 'description' in child.attrib:
            valid_children.append((child, depth, rank))
        # Recurse to find valid children of the current child, increasing the depth
        valid_children.extend(find_children_with_attributes(child, depth + 1))

    return valid_children


def match_conditions(node, condition):
    """Check if a node matches the given condition."""
    for key, value in condition.items():
        if value == 'NONE':
            continue
        if key == 'tag':
            if node.tag != value:
                return False
        elif key == 'class_name':
            if node.attrib.get('class', 'NONE') != value:
                return False
        elif key == 'text':
            text = node.text
            if text is None:
                text = node.attrib.get('text', 'NONE')
            if text != value:
                return False
        else:
            if node.attrib.get(key, 'NONE') != value:
                return False
    return True


def find_matching_node(tree: ET, requirements):
    """Find a node in the tree that matches specific requirements."""
    matched_nodes = []

    def check_node(node, depth=0, cur_parent=None):
        if not match_conditions(node, requirements['self']):
            return None

        if cur_parent and not match_conditions(cur_parent, requirements['parent']):
            return None

        children_requirements = requirements.get('children', [])

        matched_children = []
        for child_cond, child_depth, child_rank in children_requirements:
            children = find_children_by_depth_and_rank(node, child_depth, child_rank)
            for child in children:
                if match_conditions(child, child_cond):
                    if child not in matched_children:
                        matched_children.append(child)
                        break

        if len(matched_children) != len(children_requirements):
            return None
        return node

    def find_children_by_depth_and_rank(element, target_depth, target_rank, current_depth=1):
        matched_elements = []

        if current_depth == target_depth:
            try:
                matched_elements.append(element[target_rank])
            except IndexError:
                pass
        else:
            for child in element:
                matched_elements.extend(
                    find_children_by_depth_and_rank(child, target_depth, target_rank, current_depth + 1))

        return matched_elements

    for node in tree.iter():
        _, parent = find_parent_node(tree, int(node.get("index")))
        result = check_node(node, cur_parent=parent)
        if result is not None:
            matched_nodes.append(result)
    return matched_nodes


def get_trigger_ui_attributes(trigger_ui_indexes: dict, screen: str) -> dict:
    trigger_ui_data = {}
    for subtask_name, ui_indexes in trigger_ui_indexes.items():
        trigger_uis_attributes = []
        for ui_index in ui_indexes:
            ui_attributes = get_ui_key_attrib(int(ui_index), screen)

            skip = False
            new_self_attribute_str = json.dumps(ui_attributes['self'], sort_keys=True)
            for ui_attribute in trigger_uis_attributes:
                existing_self_attribute = json.dumps(ui_attribute['self'], sort_keys=True)
                if new_self_attribute_str == existing_self_attribute:
                    skip = True
            if not skip:
                trigger_uis_attributes.append(ui_attributes)

        trigger_ui_data[subtask_name] = trigger_uis_attributes

    return trigger_ui_data


def get_extra_ui_attributes(trigger_ui_indexes: list, screen: str):
    tree = ET.fromstring(screen)

    extra_ui_indexes = []
    for tag in ['input', 'button', 'checker']:
        for node in tree.findall(f".//{tag}"):
            index = int(node.attrib['index'])
            if index not in trigger_ui_indexes:
                extra_ui_indexes.append(index)

    extra_ui_attributes = []
    for index in extra_ui_indexes:
        ui_attributes = get_ui_key_attrib(index, screen)
        extra_ui_attributes.append(ui_attributes)
    return extra_ui_attributes


def get_ui_key_attrib(ui_index: int, screen: str, include_desc=True) -> dict:
    tree = ET.fromstring(screen)
    """
    [ ({"index": <ui index>}, <depth>, <rank>), ...]
    """

    node = tree.find(f".//*[@index='{ui_index}']")

    its_attributes = {'tag': node.tag, 'id': node.attrib.get('id', 'NONE'),
                      'class': node.attrib.get('class', 'NONE')}
    if include_desc:
        its_attributes['description'] = node.attrib.get('description', 'NONE')

    _, parent_node = find_parent_node(tree, ui_index)
    parent_attributes = {}
    if parent_node:
        parent_attributes = {'tag': parent_node.tag, 'id': parent_node.attrib.get('id', 'NONE'),
                             'class': parent_node.attrib.get('class', 'NONE')}
        if include_desc:
            parent_attributes['description'] = parent_node.attrib.get('description', 'NONE')

    children = find_children_with_attributes(node)

    children_attributes_str = []
    for child in children:
        child_node, depth, rank = child
        child_attribute = {'tag': child_node.tag, 'id': child_node.attrib.get('id', 'NONE'),
                           'class': child_node.attrib.get('class', 'NONE')}
        if include_desc:
            child_attribute['description'] = child_node.attrib.get('description', 'NONE')

        child_attribute_str = json.dumps((child_attribute, depth, rank))
        if child_attribute_str not in children_attributes_str:
            children_attributes_str.append(child_attribute_str)

    children_attributes = [json.loads(child_attribute_str) for child_attribute_str in children_attributes_str]
    return {"self": its_attributes, "parent": parent_attributes, "children": children_attributes}


def get_children_with_depth_and_rank(element, depth=1) -> (ET, int, int):
    children_info = []
    for rank, child in enumerate(element, start=1):
        children_info.append((child, depth, rank))
        children_info.extend(get_children_with_depth_and_rank(child, depth + 1))
    return children_info


def get_siblings_with_rank(root, element):
    parent_map = {c: p for p in root.iter() for c in p}
    parent = parent_map.get(element)
    if parent is None:
        return []

    siblings_with_rank = []
    rank = 1
    for child in parent:
        if child != element:
            siblings_with_rank.append((child, rank))
        rank += 1
    return siblings_with_rank


def shrink_screen_xml(screen: str, target_ui_index: int, range_around: int = 10):
    original_tree = ET.fromstring(screen)
    # Create the lower and upper bounds
    lower_bound = target_ui_index - range_around
    upper_bound = target_ui_index + range_around

    new_tree = ET.Element(original_tree.tag, original_tree.attrib)

    def copy_within_range(source_node, dest_node):
        dest_node.text = source_node.text
        dest_node.tail = source_node.tail

        for child in source_node:
            index = int(child.get("index", 0))

            if lower_bound <= index <= upper_bound:
                new_child = ET.SubElement(dest_node, child.tag, child.attrib)
                copy_within_range(child, new_child)
            else:
                if any(lower_bound <= int(desc.get("index", 0)) <= upper_bound for desc in child.iter()):
                    new_child = ET.SubElement(dest_node, child.tag, child.attrib)
                    copy_within_range(child, new_child)

    copy_within_range(original_tree, new_tree)

    shrunk_xml = ET.tostring(new_tree, encoding="utf-8").decode("utf-8")
    return shrunk_xml


def find_elements_with_specific_child_depth_and_rank(root, depth, rank):
    matching_elements = []

    for elem in root.iter():
        if has_descendant_at_depth_and_rank(elem, depth, rank):
            matching_elements.append(elem)

    return matching_elements


def has_descendant_at_depth_and_rank(element, depth, rank):
    if depth == 1:
        return len(element) >= rank
    else:
        for child in element:
            if has_descendant_at_depth_and_rank(child, depth - 1, rank):
                return True
    return False


def find_element_by_depth_and_rank(element, target_depth, rank, current_depth=1):
    if current_depth == target_depth:
        try:
            return element[rank - 1]  # Indexing is 0-based, hence rank-1
        except IndexError:
            return None

    for child in element:
        result = find_element_by_depth_and_rank(child, target_depth, rank, current_depth + 1)
        if result is not None:
            return result

    return None


def save_screen_info(app_name: str, task_name: str, dest_dir: str, screen_num=None) -> None:
    def parse_datetime(dirname):
        return datetime.strptime(dirname, "%Y_%m_%d %H:%M:%S")

    def get_index(filename):
        base = os.path.basename(filename)
        index = int(base.split('.')[0])
        return index

    base_path = f'memory/log/{app_name}/{task_name}/'

    directories = next(os.walk(base_path))[1]

    datetime_directories = [(parse_datetime(dir), dir) for dir in directories]

    datetime_directories.sort(reverse=True)  # Newest first

    most_recent_log_dir = datetime_directories[0][1]
    most_recent_screenshot_path = os.path.join(base_path, most_recent_log_dir, "screenshots")
    most_recent_xml_path = os.path.join(base_path, most_recent_log_dir, "xmls")

    files = [f for f in os.listdir(most_recent_screenshot_path) if f.endswith('.jpg')]
    indices = [get_index(file) for file in files]
    if screen_num is not None:
        index = screen_num
    else:
        index = max(indices) if indices else None  # Check if the list is not empty

    shutil.copy(os.path.join(most_recent_screenshot_path, f"{index}.jpg"), os.path.join(dest_dir, "screenshot.jpg"))
    shutil.copy(os.path.join(most_recent_xml_path, f"{index}.xml"), os.path.join(dest_dir, "raw.xml"))
    shutil.copy(os.path.join(most_recent_xml_path, f"{index}_encoded.xml"), os.path.join(dest_dir, "html.xml"))
    shutil.copy(os.path.join(most_recent_xml_path, f"{index}_hierarchy_parsed.xml"),
                os.path.join(dest_dir, "hierarchy.xml"))
    shutil.copy(os.path.join(most_recent_xml_path, f"{index}_parsed.xml"), os.path.join(dest_dir, "parsed.xml"))
    shutil.copy(os.path.join(most_recent_xml_path, f"{index}_pretty.xml"), os.path.join(dest_dir, "pretty.xml"))
