"""
Copyright (c) Cutleast
"""

import sys

from io import BufferedReader
from pathlib import Path

from .group import Group

from .plugin import Plugin
from .record import Record
from .subrecord import EDID, StringSubrecord


class PluginParser:
    """
    Class for plugin parser.
    Used to parse plugin data.
    """

    """
    Plugin structure:
    TES4 (Plugin Header)
     -> Records
         -> Subrecords
    GRUP (Record Groups)
     -> Records
         -> Subrecords
    """

    plugin_path: Path = None
    plugin_stream: BufferedReader = None
    parsed_data: Plugin = None
    last_edid: str = None

    def __init__(self, plugin_path: Path):
        self.plugin_path = plugin_path

    def open_stream(self):
        """
        Opens file stream if not already open.
        """

        if self.plugin_stream is None:
            self.plugin_stream = open(self.plugin_path, "rb")

    def close_stream(self):
        """
        Closes file stream if opened.
        """

        if self.plugin_stream:
            self.plugin_stream.close()
            self.plugin_stream = None

    def parse_plugin(self):
        """
        Parses raw data and returns parsed
        Plugin instance.
        """

        self.open_stream()

        self.parsed_data = Plugin(self.plugin_stream).parse()

        self.close_stream()

        return self.parsed_data

    @staticmethod
    def get_record_edid(record: Record):
        try:
            for subrecord in record.subrecords:
                if isinstance(subrecord, EDID):
                    return subrecord.editor_id
        except AttributeError:
            return None

    def extract_group_strings(self, group: Group):
        """
        Extracts strings from parsed <group>.
        """

        strings: list[dict[str, str]] = []

        if group.records is None:
            _dict = group.__dict__.copy()
            _dict.pop("data")
            print(group.data[:64])
            print(_dict)
            sys.exit()

        for record in group.records:
            if isinstance(record, Group):
                strings += self.extract_group_strings(record)
            else:
                edid = self.get_record_edid(record)
                if edid is None:
                    edid = self.last_edid
                else:
                    self.last_edid = edid
                for subrecord in record.subrecords:
                    if isinstance(subrecord, StringSubrecord):
                        string: str = subrecord.string
                        if string and string != edid:
                            strings.append(
                                {
                                    "editor_id": edid,
                                    "type": f"{record.type} {subrecord.type}",
                                    "string": string,
                                }
                            )

        return strings

    def extract_strings(self):
        """
        Extracts strings from parsed plugin.
        """

        if not self.parsed_data:
            self.parse_plugin()

        strings: dict[str, list[dict[str, str]]] = {}

        for group in self.parsed_data.groups:
            current_group: list[
                dict[str, str]
            ] = self.extract_group_strings(group)

            if current_group:
                if group.label in strings:
                    strings[group.label] += current_group
                else:
                    strings[group.label] = current_group

        return strings
