"""
Copyright (c) Cutleast
"""

import os
# import sys
from enum import IntEnum
from io import BufferedReader, BytesIO

from .datatypes import Integer, String, Hex
from .record import Record


class Group:
    """
    Class for GRUP records.
    """

    type = "GRUP"
    stream: BufferedReader = None
    records: list[Record] = None

    class GroupType(IntEnum):
        """
        Group types. See https://en.uesp.net/wiki/Skyrim_Mod:Mod_File_Format#Groups for more.
        """

        Normal = 0  # Regular Record
        WorldChildren = 1  # Worldspace
        InteriorCellBlock = 2  # Interior Cell
        InteriorCellSubBlock = 3  # Interior Cell
        ExteriorCellBlock = 4  # Exterior Cell
        ExteriorCellSubBlock = 5  # Exterior Cell
        CellChildren = 6  # Cell Record
        TopicChildren = 7  # Dialogue
        CellPersistentChildren = 8  # Persistent Cell Record
        CellTemporaryChildren = 9  # Temporary Cell Record

    def __init__(self, stream: BufferedReader):
        self.stream = stream

        self.parse()

    def __len__(self):
        try:
            if self.group_size >= 24:
                return self.group_size - 24
            else:
                return self.group_size
        except AttributeError:
            return 0

    def parse(self):
        self.type = String.string(self.stream, 4)
        self.group_size = Integer.uint32(self.stream)
        self.label = self.stream.read(4)
        self.group_type = Integer.int32(self.stream)
        self.timestamp = Integer.uint16(self.stream)
        self.version_control_info = Integer.uint16(self.stream)
        _ = Integer.uint32(self.stream)

        self.data = self.stream.read(len(self))

        # Normal groups
        if self.group_type == Group.GroupType.Normal:
            self.label = String.string(BytesIO(self.label), 4)

            if self.label in GROUP_WHITELIST:
                record_stream = BytesIO(self.data)
                self.parse_records(record_stream)
            else:
                self.records = []

        # Dialogue Groups
        elif self.group_type == Group.GroupType.TopicChildren:
            self.label = Hex.hex(BytesIO(self.label), 4)

            if "DIAL" in GROUP_WHITELIST:
                record_stream = BytesIO(self.data)
                self.parse_records(record_stream)
            else:
                self.records = []

        # Worldspace Group
        elif self.group_type == Group.GroupType.WorldChildren:
            self.label = Hex.hex(BytesIO(self.label), 4)
            self.parse_records(BytesIO(self.data))

        # Exterior Cells
        elif self.group_type == Group.GroupType.ExteriorCellBlock:
            label_stream = BytesIO(self.label)
            self.grid = (
                Integer.int16(label_stream),  # Y
                Integer.int16(label_stream),  # X
            )
            group = Group(BytesIO(self.data))
            self.records = group.records
        elif self.group_type == Group.GroupType.ExteriorCellSubBlock:
            label_stream = BytesIO(self.label)
            self.grid = (
                Integer.int16(label_stream),  # Y
                Integer.int16(label_stream),  # X
            )
            self.parse_records(BytesIO(self.data))

        # Interior Cells
        elif self.group_type in [
            Group.GroupType.InteriorCellBlock,
            Group.GroupType.CellChildren,
        ]:
            self.block_number = Integer.int32(BytesIO(self.label))
            group = Group(BytesIO(self.data))
            self.records = group.records
        elif self.group_type == Group.GroupType.InteriorCellSubBlock:
            self.subblock_number = Integer.int32(BytesIO(self.label))
            self.parse_records(BytesIO(self.data))
        elif self.group_type in [
            Group.GroupType.CellTemporaryChildren,
            Group.GroupType.CellPersistentChildren,
        ]:
            self.label = Hex.hex(BytesIO(self.label), 4)
            self.parse_records(BytesIO(self.data))

        # Unknown
        else:
            print(self.group_type)
            self.label = self.label

        return self

    def parse_records(self, stream: BytesIO):
        self.records: list[Record] = []

        while record_type := String.string(stream, 4):
            stream.seek(-4, os.SEEK_CUR)
            if record_type == "GRUP":
                record = Group(stream)
            else:
                record = Record(stream)

            self.records.append(record)

        return self


# Whitelist for group types that are known to work
GROUP_WHITELIST: list[str] = [
    "ACTI",
    "ARMO",
    "ALCH",
    "AMMO",
    "BOOK",
    "CELL",
    "CLAS",
    "CONT",
    "DIAL",
    "DOOR",
    "ENCH",
    "EXPL",
    # "FACT",  # See above
    "FLOR",
    "FURN",
    "HAZD",
    "INGR",
    "KEYM",
    "LCTN",
    "LSCR",
    "MESG",
    "MGEF",
    "MISC",
    "NOTE",
    "NPC_",
    "PERK",
    "PROJ",
    "QUST",
    "RACE",
    "SCRL",
    "SHOU",
    "SLGM",
    "SPEL",
    "TACT",
    "TREE",
    "WEAP",
    "WOOP",
    "WRLD",
]
