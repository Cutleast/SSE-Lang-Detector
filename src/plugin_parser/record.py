"""
Copyright (c) Cutleast
"""

import os
import zlib
from io import BufferedReader, BytesIO

from .datatypes import Flags, Integer, String, Hex
from .subrecord import SUBRECORD_MAPPING, Subrecord


class Record:
    """
    Contains parsed record data.
    """

    stream: BufferedReader
    type: str = "Record"

    subrecords: list["Record"] = []

    flag_types = {
        0x00000080: "Localized",
        0x00001000: "Ignored",
        0x00040000: "Compressed",
    }
    flags: dict[str, bool] = {}

    def __init__(self, stream: BufferedReader):
        self.stream = stream

        self.parse()

    def parse(self):
        self.type = String.string(self.stream, 4)
        self.size = Integer.uint32(self.stream)
        self.flags = Flags.flags(self.stream, 4, self.flag_types)
        self.formid = Hex.hex(self.stream, 4)
        self.timestamp = Integer.uint16(self.stream)
        self.version_control_info = Integer.uint16(self.stream)
        self.internal_version = Integer.uint16(self.stream)
        _ = Integer.uint16(self.stream)  # Unknown

        # Decompress data if compressed
        if self.flags["Compressed"]:
            self.decompressed_size = Integer.uint32(self.stream)
            self.data = zlib.decompress(self.stream.read(self.size - 4))
        else:
            self.data = self.stream.read(self.size)

        # Parse subrecords (also known as fields)
        subrecord_stream = BytesIO(self.data)
        if self.type in PARSE_WHITELIST:
            self.parse_subrecords(subrecord_stream)
        else:
            self.subrecords = []

        return self

    def parse_subrecords(self, stream: BytesIO):
        self.subrecords: list[Subrecord] = []

        while subrecord_type := String.string(stream, 4):
            stream.seek(-4, os.SEEK_CUR)
            if subrecord_type == "XXXX":  # Special Subrecords in Dialogs
                subrecord_type = String.string(stream, 4)
                xxxx_size = Integer.uint16(stream)
                field_size = Integer.uint(stream, xxxx_size)
                field_type = String.string(stream, 4)
                field_data = stream.read(field_size)
                _ = Integer.uint16(stream)
                subrecord = Subrecord(stream, field_type)
                subrecord.size = field_size
                subrecord.data = field_data
            elif subrecord_type in SUBRECORD_MAPPING:
                subrecord = SUBRECORD_MAPPING[subrecord_type]
                subrecord = subrecord(stream)
            else:
                subrecord = Subrecord(stream, subrecord_type)

            subrecord.parse(self.flags)

            self.subrecords.append(subrecord)

        return self


# Whitelist for record types that are known to work
# And that contain strings that are visible in-game
PARSE_WHITELIST: list[str] = [
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
    # "FACT",  # Does not seem to be visible in-game, despite having FULL subrecords
    "FLOR",
    "FURN",
    "HAZD",
    "INFO",
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
    "TES4",
    "TREE",
    "WEAP",
    "WOOP",
    "WRLD",
]
