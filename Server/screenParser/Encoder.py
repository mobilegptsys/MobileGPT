import os
import re

import xml.etree.ElementTree as ET
import xml.dom.minidom

from screenParser import parseXML


def parse_bounds(bounds):
    matches = re.findall(r'\d+', bounds)  # \d+ matches one or more digits
    xmin = int(matches[0])
    ymin = int(matches[1])
    xmax = int(matches[2])
    ymax = int(matches[3])
    return xmin, ymin, xmax, ymax


def is_inside(b1, b2):
    """
    Check if box b1 is inside box b2.

    :param b1: Tuple with coordinates (xmin1, ymin1, xmax1, ymax1) for box 1
    :param b2: Tuple with coordinates (xmin2, ymin2, xmax2, ymax2) for box 2
    :return: True if b1 is inside b2, False otherwise
    """

    xmin1, ymin1, xmax1, ymax1 = b1
    xmin2, ymin2, xmax2, ymax2 = b2

    if xmin1 >= xmin2 and xmax1 <= xmax2 and ymin1 >= ymin2 and ymax1 <= ymax2:
        return True
    else:
        return False


def get_ui_without_text_and_description(tree: ET):
    ui_elements = tree.findall(".//button") + tree.findall(".//input")

    first_filtered_elements = [element for element in ui_elements if
                               'text' not in element.attrib and 'description' not in element.attrib and element.text is None]

    text_elements = tree.findall(".//p")
    second_filtered_elements = first_filtered_elements.copy()
    for element in first_filtered_elements:
        b1 = parse_bounds(element.attrib.get("bounds"))
        for text in text_elements:
            b2 = parse_bounds(text.attrib.get("bounds"))
            if text.text is not None and is_inside(b2, b1):
                second_filtered_elements.remove(element)
                break

    third_filtered_elements = []
    for element in second_filtered_elements:
        xmin, ymin, xmax, ymax = parse_bounds(element.attrib.get("bounds"))
        if ymax < 2400 and xmax < 1080 and element.attrib.get('important') == 'true':
            third_filtered_elements.append(element)
    return third_filtered_elements


class xmlEncoder:
    def __init__(self):
        self.screenshot_directory = ""
        self.xml_directory = ""

    def init(self, log_directory):
        self.screenshot_directory = os.path.join(log_directory, "screenshots")
        self.xml_directory = os.path.join(log_directory, "xmls")

        if not os.path.exists(log_directory):
            os.makedirs(log_directory)

        if not os.path.exists(self.screenshot_directory):
            os.makedirs(self.screenshot_directory)

        if not os.path.exists(self.xml_directory):
            os.makedirs(self.xml_directory)

    """def encode(self, raw_xml, index):
        parsed_xml, hierarchy_xml = self.parse(raw_xml, index)
        tree = ET.fromstring(parsed_xml)
        elements_without_txt_desc = get_ui_without_text_and_description(tree)
        for element in elements_without_txt_desc:
            bounds = parse_bounds(element.get("bounds"))
            screenshot_path = os.path.join(self.screenshot_save_directory, f"{index}.jpg")
            screenshot = Image.open(screenshot_path)
            caption = self.captioner.generate_caption(bounds, screenshot)
            element.attrib['description'] = caption

        # remove bounds attribute, which is unnecessary for gpt.
        for element in tree.iter():
            if 'bounds' in element.attrib:
                del element.attrib['bounds']
            if 'important' in element.attrib:
                del element.attrib['important']
            if 'class' in element.attrib:
                del element.attrib['class']

        encoded_xml = ET.tostring(tree, encoding='unicode')
        pretty_xml = xml.dom.minidom.parseString(encoded_xml).toprettyxml()
        encoded_xml_path = os.path.join(self.xml_file_save_directory, f"{index}_encoded.xml")
        pretty_xml_path = os.path.join(self.xml_file_save_directory, f"{index}_pretty.xml")

        with open(encoded_xml_path, 'w', encoding='utf-8') as f:
            f.write(encoded_xml)
        with open(pretty_xml_path, 'w', encoding='utf-8') as f:
            f.write(pretty_xml)

        return parsed_xml, hierarchy_xml, encoded_xml"""

    def encode(self, raw_xml, index):
        parsed_xml, hierarchy_xml = self.parse(raw_xml, index)
        tree = ET.fromstring(parsed_xml)

        for element in tree.iter():
            if 'bounds' in element.attrib:
                del element.attrib['bounds']
            if 'important' in element.attrib:
                del element.attrib['important']
            if 'class' in element.attrib:
                del element.attrib['class']

        encoded_xml = ET.tostring(tree, encoding='unicode')
        pretty_xml = xml.dom.minidom.parseString(encoded_xml).toprettyxml()
        encoded_xml_path = os.path.join(self.xml_directory, f"{index}_encoded.xml")
        pretty_xml_path = os.path.join(self.xml_directory, f"{index}_pretty.xml")

        with open(encoded_xml_path, 'w', encoding='utf-8') as f:
            f.write(encoded_xml)
        with open(pretty_xml_path, 'w', encoding='utf-8') as f:
            f.write(pretty_xml)

        return parsed_xml, hierarchy_xml, encoded_xml

    def parse(self, raw_xml, index):
        parsed_xml = parseXML.parse(raw_xml)
        hierarchy_xml = parseXML.hierarchy_parse(parsed_xml)

        parsed_xml_path = os.path.join(self.xml_directory, f"{index}_parsed.xml")
        hierarchy_parsed_xml_path = os.path.join(self.xml_directory, f"{index}_hierarchy_parsed.xml")
        with open(parsed_xml_path, 'w', encoding='utf-8') as f:
            f.write(parsed_xml)
        with open(hierarchy_parsed_xml_path, 'w', encoding='utf-8') as f:
            f.write(hierarchy_xml)

        return parsed_xml, hierarchy_xml
