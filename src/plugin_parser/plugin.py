"""
Copyright (c) Cutleast
"""

from dataclasses import dataclass
from io import BufferedReader

from .record import GRUP, Record


@dataclass
class Plugin:
    """
    Contains parsed plugin data.
    """

    data_stream: BufferedReader
    parsed_data = None

    def __repr__(self):
        string = ""

        string += f"File Header: {self.TES4}"

        string += f"\n\nRecord Groups: {self.groups}\n"

        return string

    def __str__(self):
        return self.__repr__()

    def parse(self):
        self.groups: list[GRUP] = []

        self.data_stream.seek(4, 1)

        self.TES4 = Record(self.data_stream, "TES4").parse()

        while self.data_stream.read(4) == b"GRUP":
            self.groups.append(
                GRUP(self.data_stream).parse()
            )

        return self


