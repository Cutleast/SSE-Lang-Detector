"""
Copyright (c) Cutleast
"""

from io import BufferedReader
from pathlib import Path

from .plugin import Plugin
from .record import CELL_GRUP, DIAL, DIAL_GRUP, GRUP, Record
from .subrecord import EDID


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

    @staticmethod
    def extract_cell_strings(cell_group: CELL_GRUP):
        """
        Extracts strings from <cell_group>.
        """

        strings: list[dict[str, str]] = []

        for cell_block in cell_group.cell_blocks:
            for subblock in cell_block.subblocks:
                record = subblock.CELL
                edid = PluginParser.get_record_edid(record)
                for subrecord in record.subrecords:
                    if hasattr(subrecord, "string"):
                        string: str = subrecord.string
                        if string:
                            strings.append(
                                {
                                    "editor_id": edid,
                                    "type": f"{record.type} {subrecord.type}",
                                    "string": string,
                                }
                            )

        return strings

    @staticmethod
    def extract_group_strings(group: GRUP):
        """
        Extracts strings from parsed <group>.
        """

        strings: list[dict[str, str]] = []

        for record in group.records:
            if isinstance(record, DIAL):
                edid = PluginParser.get_record_edid(record)
                for subrecord in record.subrecords:
                    if hasattr(subrecord, "string"):
                        string: str = subrecord.string
                        if string:
                            strings.append(
                                {
                                    "editor_id": edid,
                                    "type": f"{record.type} {subrecord.type}",
                                    "string": string,
                                }
                            )

                if record.GRUP:
                    for dial_record in record.GRUP.records:
                        for dial_subrecord in dial_record.subrecords:
                            if hasattr(dial_subrecord, "string"):
                                string: str = dial_subrecord.string
                                if string:
                                    strings.append(
                                        {
                                            "editor_id": edid,
                                            "type": f"{dial_record.type} {dial_subrecord.type}",
                                            "string": string,
                                        }
                                    )
            elif isinstance(record, GRUP) and not isinstance(record, DIAL_GRUP):
                strings += PluginParser.extract_group_strings(record)
            else:
                edid = PluginParser.get_record_edid(record)
                for subrecord in record.subrecords:
                    if hasattr(subrecord, "string"):
                        string: str = subrecord.string
                        if string:
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
            raise Exception("Plugin not parsed!")

        strings: dict[str, list[dict[str, str]]] = {}

        for group in self.parsed_data.groups:
            if isinstance(group, CELL_GRUP):
                current_group: list[dict[str, str]] = PluginParser.extract_cell_strings(
                    group
                )
            else:
                current_group: list[
                    dict[str, str]
                ] = PluginParser.extract_group_strings(group)

            if current_group:
                if group.label in strings:
                    strings[group.label] += current_group
                else:
                    strings[group.label] = current_group

        return strings
