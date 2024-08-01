import xml.etree.ElementTree as ET


def reformat_xml(xml_string):
    tree = ET.fromstring(xml_string)

    def process_element(element):
        attrib_text = {
            "text": "text",
            "id": "resource-id",
            "description": "content-desc",
            "important": "important",
            "class": "class"
        }

        attrib_bool = {
            "checkable": "checkable",
            "clickable": "clickable",
            "scrollable": "scrollable",
            "long-clickable": "long-clickable",
        }

        attrib_int = {
            "bounds": "bounds",
            "index": "index",
        }

        new_text_attrib = {
            key: element.attrib[value] for key, value in attrib_text.items() if
            value in element.attrib and element.attrib[value] != ""
        }

        new_bool_attrib = {
            key: element.attrib[value] for key, value in attrib_bool.items() if
            value in element.attrib and element.attrib[value] != "false"
        }

        new_int_attrib = {
            key: element.attrib[value] for key, value in attrib_int.items() if value in element.attrib
        }

        if "id" in new_text_attrib:
            new_text_attrib["id"] = new_text_attrib["id"].split("/")[-1]

        new_text_attrib.update(new_bool_attrib)
        new_text_attrib.update(new_int_attrib)

        class_name = element.attrib.get("class", "unknown")
        class_name_short = class_name.split(".")[-1]

        if class_name_short == "EditText":
            new_element = ET.Element("input", new_text_attrib)
            if len(element) == 0 and "text" in new_element.attrib:
                text = new_element.attrib.get("text", "")
                del new_element.attrib["text"]
                new_element.text = text
        elif new_text_attrib.get("checkable", "") == "true":
            new_text_attrib["checked"] = element.attrib.get("checked", "false")
            del new_text_attrib["checkable"]
            new_element = ET.Element("checker", new_text_attrib)

        elif new_text_attrib.get("clickable", "") == "true":
            del new_text_attrib["clickable"]
            new_element = ET.Element("button", new_text_attrib)

        elif class_name_short in ["FrameLayout", "LinearLayout", "RelativeLayout", "ViewGroup", "ConstraintLayout",
                                  "unknown"]:
            new_element = ET.Element("div", new_text_attrib)

        elif class_name_short == "ImageView":
            new_element = ET.Element("img", new_text_attrib)

        elif class_name_short == "TextView":
            new_element = ET.Element("p", new_text_attrib)
            if len(element) == 0 and "text" in new_element.attrib:
                text = new_element.attrib.get("text", "")
                del new_element.attrib["text"]
                new_element.text = text

        elif new_bool_attrib.get("scrollable", "") == "true":
            new_element = ET.Element("scroll", new_text_attrib)
        else:
            new_element = ET.Element(class_name.split(".")[-1], new_text_attrib)

        for child in element:
            new_child = process_element(child)

            if new_child is not None:
                new_element.append(new_child)

        if (new_element.tag not in ['button', 'checker']) and (len(element) == 0 and len(new_element.attrib) <= 4):
            if new_element.text is None or len(new_element.text) == 0:
                return None

        return new_element

    new_tree = process_element(tree)
    return ET.tostring(new_tree, encoding='unicode')


def hierarchy_parse(parsed_xml):
    tree = ET.fromstring(parsed_xml)

    # Remove any semantic info
    for element in tree.iter():
        if 'bounds' in element.attrib:
            del element.attrib['bounds']
        if 'important' in element.attrib:
            del element.attrib['important']
        if 'index' in element.attrib:
            del element.attrib['index']
        # if 'description' in element.attrib:
        #     del element.attrib['description']
        if element.text:
            element.text = ''
        # if 'class' in element.attrib:
        #     del element.attrib['class']
        if 'text' in element.attrib:
            del element.attrib['text']

    hierarchy_xml = ET.tostring(tree, encoding='unicode')

    hierarchy_xml = remove_redundancies(hierarchy_xml)

    return hierarchy_xml


def delete_option_information(parsed_xml):
    tree = ET.fromstring(parsed_xml)
    for element in tree.iter():
        if 'bounds' in element.attrib:
            del element.attrib['bounds']
        if 'important' in element.attrib:
            del element.attrib['important']
        if 'class' in element.attrib:
            del element.attrib['class']

    encoded_xml = ET.tostring(tree, encoding='unicode')

    return encoded_xml


def remove_nodes_with_empty_bounds(element):
    for node in list(element):
        if node.get('bounds') == "[0,0][0,0]":
            element.remove(node)
        else:
            remove_nodes_with_empty_bounds(node)

def simplify_structure(xml_string):
    tree = ET.ElementTree(ET.fromstring(xml_string))
    root = tree.getroot()
    def simplify_element(elem):
        while len(list(elem)) == 1 and all(x not in elem.attrib for x in ['text', 'description']):
            if elem.tag in ['button', 'checker']:
                break
            child = elem[0]
            elem.tag = child.tag
            elem.attrib = child.attrib
            elem.text = child.text
            elem[:] = child[:]  # Replace elem's children with child's children

        for subelem in list(elem):
            simplify_element(subelem)

    simplify_element(root)

    return ET.tostring(root, encoding='unicode')

def remove_redundancies(xml_string):
    tree = ET.ElementTree(ET.fromstring(xml_string))
    root = tree.getroot()
    def elem_key(elem):
        return (
            elem.tag, tuple(elem.attrib.items()),
            tuple((child.tag, tuple(child.attrib.items())) for child in list(elem)))

    for scroll in root.findall('.//scroll'):
        seen = {}
        items_to_remove = []
        for child in list(scroll):
            key = elem_key(child)
            if key in seen:
                items_to_remove.append(child)
            else:
                seen[key] = child

        for item in items_to_remove:
            scroll.remove(item)

    return ET.tostring(root, encoding='unicode')


def parse(raw_xml):
    reformatted_xml = reformat_xml(raw_xml)

    simplified_xml = simplify_structure(reformatted_xml)
    root = ET.fromstring(simplified_xml)

    remove_nodes_with_empty_bounds(root)
    parsed_xml = ET.tostring(root, encoding='unicode')

    return parsed_xml
