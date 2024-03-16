from utils.Utils import generate_numbered
import xml.etree.ElementTree as ET

def shrink_tree_around_index(xml_screen, target_index, range_around=10):
    # Create the lower and upper bounds
    root = ET.fromstring(xml_screen)

    lower_bound = target_index - range_around
    upper_bound = target_index + range_around

    # New root for the shrunk tree
    new_root = ET.Element(root.tag, root.attrib)

    def copy_within_range(source_node, dest_node):
        # Copy text and tail attributes
        dest_node.text = source_node.text
        dest_node.tail = source_node.tail

        for child in source_node:
            index = int(child.get("index", 0))

            # Copy child if it's within the range
            if lower_bound <= index <= upper_bound:
                new_child = ET.SubElement(dest_node, child.tag, child.attrib)
                copy_within_range(child, new_child)
            else:
                # Check descendants for any within the range
                if any(lower_bound <= int(desc.get("index", 0)) <= upper_bound for desc in child.iter()):
                    new_child = ET.SubElement(dest_node, child.tag, child.attrib)
                    copy_within_range(child, new_child)

    copy_within_range(root, new_root)

    # Convert the modified tree back to a string
    shrunk_xml = ET.tostring(new_root, encoding="utf-8").decode("utf-8")
    return shrunk_xml

def generate_example_str(screen, goal, info, history, response):

    usr_prompt = \
f"""
[EXAMPLE]
Task: {goal}

Reason for the Task: 
{response["thoughts"]["reasoning"]}

Past Events:'''
{generate_numbered(history)}
'''

HTML code of the example screen information delimited by <screen> </screen>:
<screen>{shrink_tree_around_index(screen, int(response["thoughts"]["command"]["args"]["index"]))}</screen>

Response: {response}

[END EXAMPLE]
Your Turn:
"""

    return usr_prompt