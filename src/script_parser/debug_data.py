"""
Copyright (c) Cutleast
"""

from io import BufferedReader
from .datatypes import Datatype
from .integer_types import *
from .string_data import StringTable


class DebugInfo(Datatype):
    """
    Used to parse DebugInfo section.
    """

    def __init__(self, stream: BufferedReader, string_table: StringTable):
        self.has_debug_info = bool(uint8(stream))
        print(self.has_debug_info)

        if self.has_debug_info:
            self.modification_time = uint64(stream)
            self.function_count = uint16(stream)
            self.functions = [
                str(function)
                for i in range(self.function_count)
                if (function := DebugFunction(stream, string_table))#.object_name
            ]


class DebugFunction(Datatype):
    """
    Class for debug functions.
    """

    def __init__(self, stream: BufferedReader, string_table: StringTable):
        object_name_index = uint16(stream)
        self.object_name = string_table.get_string(object_name_index)

        state_name_index = uint16(stream)
        self.state_name = string_table.get_string(state_name_index)

        function_name_index = uint16(stream)
        self.function_name = string_table.get_string(function_name_index)

        self.function_type = uint8(stream)

        self.instruction_count = uint16(stream)

        _line_numbers = [
            number
            for i in range(self.instruction_count)
            if (number := uint16(stream))
        ]
