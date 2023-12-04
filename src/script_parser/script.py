"""
Copyright (c) Cutleast
"""

from dataclasses import dataclass
from io import BufferedReader

from .datatypes import Datatype
from .debug_data import DebugInfo
from .flag_data import UserFlags
from .integer_types import *
from .object_data import Objects
from .string_data import StringTable, wstring


@dataclass(repr=False)
class Script(Datatype):
    """
    Contains parsed script data.
    """

    data_stream: BufferedReader
    parsed_data = None

    # def __repr__(self):
    #     string = ""

    #     string += f"File Header:\n"

    #     for key, value in self.header.items():
    #         string += f"{key} = {value!r}\n"

    #     return string

    # def __str__(self):
    #     return self.__repr__()

    def parse(self):
        self.magic = self.data_stream.read(4).hex().upper()
        self.major_version = uint8(self.data_stream)
        self.minor_version = uint8(self.data_stream)
        self.game_id = uint16(self.data_stream)
        self.compilation_time = uint64(self.data_stream)
        self.source_filename = wstring(self.data_stream)
        self.username = wstring(self.data_stream)
        self.machine_name = wstring(self.data_stream)
        self.string_table = StringTable(self.data_stream)
        # StringTable(self.data_stream)
        self.debug_info = DebugInfo(self.data_stream, self.string_table)
        # DebugInfo(self.data_stream)
        self.user_flags = UserFlags(self.data_stream, self.string_table)
        # UserFlags(self.data_stream)
        self.objects = Objects(self.data_stream, self.string_table)

        self.string_table.clean_used_strings()

        return self



