"""
Copyright (c) Cutleast
"""

from io import BufferedReader
from .datatypes import Datatype
from .integer_types import uint16


class StringTable(Datatype):
    """
    Used to parse string tables.
    """

    def __init__(self, stream: BufferedReader):
        self.count = uint16(stream)

        self.strings = [
            string
            for i in range(self.count)
            if (string := wstring(stream))
        ]

        self.used_strings: list[str] = []

    def get_string(self, index: int):
        """
        Returns string at <index> or <index>
        if <index> is out of range.
        """

        if 0 <= index < self.count:
            string = self.strings[index]
            
            if string not in self.used_strings:
                self.used_strings.append(string)

            return string
        else:
            return index

    def clean_used_strings(self):
        for string in self.used_strings:
            self.strings.remove(string)

        self.strings.sort()


def wstring(stream: BufferedReader):
    return stream.read(uint16(stream)).decode()

