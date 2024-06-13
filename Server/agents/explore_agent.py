import json
import os

from agents.prompts import explore_agent_prompt
from memory.memory_manager import Memory
from utils.parsing_utils import get_trigger_ui_attributes, get_extra_ui_attributes
from utils.utils import query, log

import xml.etree.ElementTree as ET


class ExploreAgent:
    def __init__(self, memory: Memory):
        self.memory = memory

    def explore(self, parsed_xml, hierarchy_xml, html_xml, screen_num=None) -> (int, list):
        """
        Desc: Generate a new node based on the given screen xmls
        return: index of the new node.
        """

        prompts = explore_agent_prompt.get_prompts(html_xml)
        subtasks_raw = query(prompts, model=os.getenv("EXPLORE_AGENT_GPT_VERSION"), is_list=True)
        subtasks_raw = list(filter(lambda x: len(x["trigger_UIs"]) > 0, subtasks_raw))

        subtasks_trigger_uis = {subtask['name']: subtask['trigger_UIs'] for subtask in subtasks_raw}
        subtasks_trigger_ui_attributes = get_trigger_ui_attributes(subtasks_trigger_uis, parsed_xml)

        # flatten the list of trigger ui indexes.
        trigger_ui_indexes = [index for ui_indexes in subtasks_trigger_uis.values() for index in ui_indexes]
        extra_ui_attributes = get_extra_ui_attributes(trigger_ui_indexes, parsed_xml)

        available_subtasks = [{key: value for key, value in subtask.items() if key != 'trigger_UIs'} for subtask in
                              subtasks_raw]
        new_node_index = self.memory.add_node(available_subtasks, subtasks_trigger_ui_attributes, extra_ui_attributes, parsed_xml, screen_num)

        self.memory.add_hierarchy_xml(hierarchy_xml, new_node_index)

        return new_node_index, available_subtasks
