import os, csv, re
from termcolor import colored
import xml.etree.ElementTree as ET

from openai import OpenAI

def log(msg, color='white'):
    if not color:
        print(msg)
        return

    colored_log = colored(msg, color, attrs=['bold'])
    print(colored_log)
    print()

def load_memory(memory_path, memory_header):
    if not os.path.exists(memory_path):
        memory_file = open(memory_path, "w", newline='', encoding='utf-8')
        memory_writer = csv.writer(memory_file, delimiter='%')
        memory_writer.writerow(memory_header)
        memory_file.close()

    memory_file = open(memory_path, "r", encoding='utf-8')
    memory_reader = csv.DictReader(memory_file, delimiter='%')
    memory_data = list(memory_reader)
    memory_file.close()

    return memory_data

def update_memory(memory_path, memory_data):
    memory_file = open(memory_path, "a", newline='', encoding='utf-8')
    memory_writer = csv.writer(memory_file, delimiter='%')
    memory_writer.writerow(memory_data)
    memory_file.close()

def save_memory(memory_path, memory_data, memory_header):
    memory_file = open(memory_path, "w", newline='', encoding='utf-8')
    memory_writer = csv.writer(memory_file, delimiter='%')
    memory_writer.writerow(memory_header)

    for data in memory_data:
        memory_writer.writerow(data)

    memory_file.close()

def generate_vector(input, model="text-embedding-ada-002"):
    client = OpenAI(api_key = os.getenv("OPENAI_API_KEY"))

    try:
        vector = client.embeddings.create(input = [input], model=model).data[0].embedding
    except Exception as e:
        return generate_vector(input, model)
    return vector

def generate_numbered(data: list) -> str:
    result_string = ""

    for index, item in enumerate(data, start=1):
        result_string += f"{index}. {item}\n"

    return result_string

def parse_bounds(bounds):
    matches = re.findall(r'\d+', bounds)  # \d+ matches one or more digits
    xmin = int(matches[0])
    ymin = int(matches[1])
    xmax = int(matches[2])
    ymax = int(matches[3])
    return xmin, ymin, xmax, ymax

def get_xml_depth_rank_list(parsed_xml, need_all=False):
    tree = ET.ElementTree(ET.fromstring(parsed_xml))
    root = tree.getroot()

    def traverse(node, depth):
        for rank, child in enumerate(node):
            if need_all:
                xml_depth_rank_list.append([{'index' : child.attrib['index'], 'bounds' : child.attrib['bounds'], \
                                             'id' : child.attrib['id'] if 'id' in child.attrib else 'NONE', \
                                             'class' : child.attrib['class'] if 'class' in child.attrib else 'NONE'}, depth, rank])
            else:
                xml_depth_rank_list.append([{'index' : child.attrib['index']}, depth, rank])
            traverse(child, depth + 1)
    if need_all:
        xml_depth_rank_list = [[{'index' : root.attrib['index'], 'bounds' : root.attrib['bounds']}, 0, 0]]
    else:
        xml_depth_rank_list = [[{'index' : root.attrib['index']}, 0, 0]]
    traverse(root, 1)

    return xml_depth_rank_list

def find_parent(parsed_xml, xml_depth_rank_list, target_ui_index, index=False):
    parent_dict = {}
    parent_index = None

    target_ui_index = int(target_ui_index)

    #print(xml_depth_rank_list)
    #print(target_ui_index)

    first = True
    for IDR in xml_depth_rank_list:
        parent_dict[IDR[1]] = int(IDR[0]["index"])
        if int(IDR[0]["index"]) == target_ui_index:
            if first:
                parent_index = parent_dict[IDR[1]]
                break
            parent_index = parent_dict[IDR[1]-1]
            break
        first = False

    tree = ET.fromstring(parsed_xml)

    if int(parent_index) == int(tree.attrib.get('index', 'NONE')):
        parent_node = tree
    else:
        parent_node = tree.find(f".//*[@index='{parent_index}']")

    parent_tag = {
        'tag': parent_node.tag,
        'id': parent_node.attrib.get('id', 'NONE'),
        'class': parent_node.attrib.get('class', 'NONE')
    }

    if index:
        parent_tag['index'] = parent_node.attrib.get('index')

    return parent_tag

def find_child(parsed_xml, xml_depth_rank_list, target_ui_index):   
    child_indexs = []
    there_are_child = False

    target_ui_index = int(target_ui_index)

    for IDR in xml_depth_rank_list:
        if int(IDR[0]["index"]) == target_ui_index:
            there_are_child = IDR[1]
            continue

        if there_are_child:
            if IDR[1] == there_are_child+1:
                child_indexs.append(int(IDR[0]["index"]))
            elif IDR[1] == there_are_child:
                break

    child_length = len(child_indexs)
    child_tags = []

    if child_length != 0:
        for child_index in child_indexs:
            tree = ET.ElementTree(ET.fromstring(parsed_xml))
            child_node = tree.find(f".//*[@index='{child_index}']")

            child_tag = {
                'tag': child_node.tag,
                'id': child_node.attrib.get('id', 'NONE'),
                'class': child_node.attrib.get('class', 'NONE')
            }

            child_tags.append(child_tag)

    return child_tags

def load_xml(dierctory):
    file = open(dierctory, "r", encoding='utf-8')
    xml = file.read()
    return xml

def is_same_ui(one, two):
    if one["id"] == two["id"] and one["class"] == two["class"] and one["bounds"] == two["bounds"]:
        return True
    else:
        return False

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

def get_children_with_depth_and_rank(element, depth=1):
    children_info = []
    for rank, child in enumerate(element, start=1):
        children_info.append((child, depth, rank))
        children_info.extend(get_children_with_depth_and_rank(child, depth + 1))
    return children_info


def has_descendant_at_depth_and_rank(element, depth, rank):
    if depth == 1:
        return len(element) >= rank
    else:
        for child in element:
            if has_descendant_at_depth_and_rank(child, depth - 1, rank):
                return True
    return False


def find_elements_with_specific_child_depth_and_rank(root, depth, rank):
    matching_elements = []

    for elem in root.iter():
        if has_descendant_at_depth_and_rank(elem, depth, rank):
            matching_elements.append(elem)

    return matching_elements


def find_element_by_depth_and_rank(element, target_depth, rank, current_depth=1):
    # Check if we're at the desired depth
    if current_depth == target_depth:
        try:
            return element[rank - 1]  # Indexing is 0-based, hence rank-1
        except IndexError:
            return None

    # If we're not yet at the desired depth, traverse deeper
    for child in element:
        result = find_element_by_depth_and_rank(child, target_depth, rank, current_depth + 1)
        if result is not None:
            return result

    return None

def Text_extrator():
    pass
