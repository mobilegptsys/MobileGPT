import xml.etree.ElementTree as ET

def reformat_xml(xml_string):
    tree = ET.fromstring(xml_string)
    index = -1       #?

    def process_element(element):
        nonlocal index
        attrib_text = {
            "text": "text",
            "id": "resource-id",
            "description": "content-desc",
            "important": "important",
            "class": "class"
        }

        attrib_bool = {
            "checkable": "checkable",
            "checked": "checked",
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

        # for "id" attribute, only take what is after "id/"
        if "id" in new_text_attrib:
            new_text_attrib["id"] = new_text_attrib["id"].split("/")[-1]

        new_int_attrib["index"] = str(index)
        index = index+1

        # Append new_bool_attrib to new_text_attrib
        new_text_attrib.update(new_bool_attrib)
        new_text_attrib.update(new_int_attrib)

        ## Hard-coded for booking.com ##
        if new_text_attrib.get("description", "") == "Accommodation search box":
            new_text_attrib['description'] = "Accommodation info box"

        # make tag name more HTML like.
        class_name = element.attrib.get("class", "unknown")
        class_name_short = class_name.split(".")[-1]        #-2  widget or view

        if class_name_short == "EditText":
            new_element = ET.Element("input", new_text_attrib)
            if len(element) == 0 and "text" in new_element.attrib:
                text = new_element.attrib.get("text", "")
                new_element.attrib['type'] = "text"
                del new_element.attrib["text"]
                new_element.text = text

        elif new_text_attrib.get("clickable", "") == "true":
            new_element = ET.Element("button", new_text_attrib)

        elif new_text_attrib.get("checkable", "") == "true":
            new_element = ET.Element("checker", new_text_attrib)

        elif class_name_short in ["FrameLayout", "LinearLayout", "RelativeLayout", "ViewGroup", "ConstraintLayout", "unknown"]:
            new_element = ET.Element("div", new_text_attrib)

        elif class_name_short == "ImageView":
            new_element = ET.Element("img", new_text_attrib)

        elif class_name_short == "TextView":
            new_element = ET.Element("p", new_text_attrib)
            if len(element) == 0:
                text = new_element.attrib.get("text", "")
                new_element.attrib['type'] = "text"
                if "text" in new_element.attrib:
                    del new_element.attrib["text"]
                new_element.text = text

        elif new_bool_attrib.get("scrollable", "") == "true":
            new_element = ET.Element("scroll", new_text_attrib)
        else:
            new_element = ET.Element(class_name.split(".")[-1], new_text_attrib)

        for child in element:
            new_child = process_element(child)

            class_is_in = 0
            if 'class' in new_element.attrib:
                class_is_in = 1

            # skip node that has only one child.
            if len(new_element.attrib) - class_is_in <= 2 and len(element) == 1:
                new_element = new_child
            elif new_child is not None:
                new_element.append(new_child)

        # skip leaf node that is meaningless e.g., no attribute besides bounds and index.
        if len(element) == 0 and len(new_element.attrib) <= 2:
            return None
        else:
            return new_element

    new_tree = process_element(tree)
    return ET.tostring(new_tree, encoding='unicode')

def hierarchy_parse(parsed_xml):
    tree = ET.fromstring(parsed_xml)
    for element in tree.iter():
        if 'bounds' in element.attrib:
            del element.attrib['bounds']
        if 'important' in element.attrib:
            del element.attrib['important']
        if 'index' in element.attrib:
            del element.attrib['index']
        if 'description' in element.attrib:
            del element.attrib['description']
        if 'type' in element.attrib and element.attrib['type'] == 'text':
            element.text = ''
        if 'class' in element.attrib:
            del element.attrib['class']
        if 'text' in element.attrib:
            del element.attrib['text']

    encoded_xml = ET.tostring(tree, encoding='unicode')

    return encoded_xml

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

def parse(raw_xml):
    # Reformat the XML
    parsed_xml = reformat_xml(raw_xml)

    root = ET.fromstring(parsed_xml)
    remove_nodes_with_empty_bounds(root)
    parsed_xml = ET.tostring(root, encoding='unicode')

    return parsed_xml

