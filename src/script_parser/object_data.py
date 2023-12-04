"""
Copyright (c) Cutleast
"""

from io import BufferedReader

from .datatypes import Datatype
from .integer_types import *
from .variable_data import Variables
from .string_data import StringTable


class Objects(Datatype):
    """
    Used to parse objects section.
    """

    def __init__(self, stream: BufferedReader, string_table: StringTable):
        self.object_count = uint16(stream)
        self.objects = [
            str(_object)
            for i in range(self.object_count)
            if (_object := Object(stream, string_table))
        ]


class Object(Datatype):
    """
    Used to parse objects.
    """

    def __init__(self, stream: BufferedReader, string_table: StringTable):
        name_index = uint16(stream)
        self.name = string_table.get_string(name_index)
        self.size = uint32(stream)
        # self.data = stream.read(self.size - 4)
        self.data = ObjectData(stream, string_table)


class ObjectData(Datatype):
    """
    Used to parse object data.
    """

    def __init__(self, stream: BufferedReader, string_table: StringTable):
        class_name_index = uint16(stream)
        self.parent_class = string_table.get_string(class_name_index)
        
        docstring_index = uint16(stream)
        self.docstring = string_table.get_string(docstring_index)

        self.user_flags = uint32(stream)

        state_name_index = uint16(stream)
        self.auto_state_name = string_table.get_string(state_name_index)

        self.variables = Variables(stream, string_table)
