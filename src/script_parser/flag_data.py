"""
Copyright (c) Cutleast
"""

from io import BufferedReader
from .datatypes import Datatype
from .integer_types import *
from .string_data import StringTable


class UserFlags(Datatype):
    """
    Used to parse user flag section.
    """

    def __init__(self, stream: BufferedReader, string_table: StringTable):
        self.user_flag_count = uint16(stream)
        self.user_flags = [
            str(user_flag)
            for i in range(self.user_flag_count)
            if (user_flag := UserFlag(stream, string_table)).name or user_flag.flag_index
        ]


class UserFlag(Datatype):
    """
    Used to parse user flags.
    """

    def __init__(self, stream: BufferedReader, string_table: StringTable):
        name_index = uint16(stream)
        self.name = string_table.get_string(name_index)

        self.flag_index = uint8(stream)

    def __repr__(self):
        return f"{self.name}: {self.flag_index}"
