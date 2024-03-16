
import cv2, copy

import pyshine as ps
import xml.etree.ElementTree as ET

from utils.Utils import get_xml_depth_rank_list, parse_bounds, find_parent

def screenshot_processing(screenshot_path, process_parsed_xml):
    image = cv2.imread(screenshot_path)

    #print(parsed_xml)
    xml_depth_rank_list = get_xml_depth_rank_list(process_parsed_xml)

    tree = ET.fromstring(process_parsed_xml)

    labeling_list = []

    for xml_tag in tree.iter():
        if xml_tag.tag in ['input', 'button', 'checker', 'p']:

            if xml_tag.tag == 'p':
                parent_ui = find_parent(process_parsed_xml, xml_depth_rank_list, int(xml_tag.attrib['index']), index=True)
                if parent_ui["tag"] in ['input', 'button', 'checker'] or find_parent(process_parsed_xml, xml_depth_rank_list, int(parent_ui['index']))["tag"] in ['input', 'button', 'checker']:
                    continue

            #print(xml_tag.tag)
            left, top, right, bottom = parse_bounds(xml_tag.attrib["bounds"])

            label = xml_tag.attrib['index']

            #label_pos = ((left + right) // 2, (top + bottom) // 2)

            #image = cv2.putText(image, label, label_pos, cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)


            text_x = right-45
            text_y = bottom-30

            text_color = (10, 10, 10)
            bg_color = (255, 250, 250)

            tmp_labeling_list = []

            for area in labeling_list:
                if (left <= (area[5]) <= right and top <= (area[6]) <= bottom):
                    tmp_area = copy.deepcopy(area)
                    tmp_area[5] = tmp_area[5] - (right - left)
                    tmp_labeling_list.append(tmp_area)

                else:
                    if not (left <= (area[0] + area[2]) / 2 <= right and top <= (area[1] + area[3]) / 2 <= bottom):
                        tmp_labeling_list.append(area)

            labeling_list = tmp_labeling_list

            labeling_list.append([left, top, right, bottom, label, text_x, text_y, text_color, bg_color])

    for area in labeling_list:
        image = cv2.rectangle(image, (area[0], area[1]), (area[2], area[3]), (0, 0, 255), 2)
        image = ps.putBText(image, area[4], text_offset_x=area[5], text_offset_y=area[6],
                            vspace=10, hspace=10, font_scale=0.8, thickness=2, background_RGB=area[8],
                            text_RGB=area[7], alpha=0.5)

    #image = luminance_edit(image)

    image_path = screenshot_path.split(".jpg")[0] + "_process.jpg"
    cv2.imwrite(image_path, image)

    return image_path

