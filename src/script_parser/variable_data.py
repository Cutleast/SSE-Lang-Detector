"""
Copyright (c) Cutleast
"""

import struct
from io import BufferedReader
from .datatypes import Datatype
from .integer_types import *
from .string_data import StringTable


class Variables(Datatype):
    """
    Used to parse variables section.
    """

    def __init__(self, stream: BufferedReader, string_table: StringTable):
        self.variable_count = uint16(stream)

        self.variables = [
            str(variable)
            for i in range(self.variable_count)
            if (variable := Variable(stream, string_table))
        ]


class Variable(Datatype):
    """
    Used to parse variables.
    """

    def __init__(self, stream: BufferedReader, string_table: StringTable):
        name_index = uint16(stream)
        self.name = string_table.get_string(name_index)

        type_index = uint16(stream)
        self.type_name = string_table.get_string(type_index)

        self.user_flags = uint32(stream)

        self.data = VariableData(stream)


class VariableData(Datatype):
    """
    Used to parsed variable data.
    """

    def __init__(self, stream: BufferedReader):
        TYPES = {
            0: "null",
            1: "identifier",
            2: "string",
            3: "integer",
            4: "float",
            5: "bool"
        }
        
        self.type = TYPES.get(uint8(stream), "")

        match self.type:
            case "identifier", "string":
                self.data = uint16(stream)
            case "integer":
                self.data = int32(stream)
            case "float":
                self.data = float32(stream)
            case "bool":
                self.data = bool(uint8(stream))
