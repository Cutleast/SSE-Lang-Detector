"""
Copyright (c) Cutleast
"""

import struct
from io import BufferedReader
from . import utilities as utils
from pathlib import Path
import os


if Path("invalid_strings.txt").is_file():
    os.remove("invalid_strings.txt")


class Subrecord:
    """
    Contains parsed subrecord data.
    """

    data_stream: BufferedReader
    type: str = "Subrecord"

    def __init__(self, data_stream: BufferedReader, type: str = None):
        self.type = type if type else self.type
        self.data_stream = data_stream

    def __repr__(self):
        string = "\n\t\t{"

        for key, value in self.__dict__.items():
            if key != "data_stream" and key != "data":
                string += f"\n\t\t\t{key} = {value!r}"
            elif key == "data":
                string += f"\n\t\t\t{key} = {value[:64]!r}"

        string += "\n\t\t}"

        return string
    
    def __str__(self):
        return str(self.__dict__)

    def __len__(self):
        try:
            return self.size + 6
        except AttributeError:
            return 0

    def parse(self):
        self.size = int.from_bytes(
            self.data_stream.read(2),
            "little"
        )

        self.data = self.data_stream.read(
            self.size
        )

        return self


class HEDR(Subrecord):
    """
    Class for HEDR subrecord.
    """

    type = "HEDR"

    def parse(self):
        self.size = int.from_bytes(
            self.data_stream.read(2),
            "little"
        )

        self.version = round(struct.unpack(
            "f",
            self.data_stream.read(4)
        )[0], 2)

        self.records_num = int.from_bytes(
            self.data_stream.read(4),
            "little"
        )

        self.next_object_id = int.from_bytes(
            self.data_stream.read(4),
            "little"
        )

        return self


class EDID(Subrecord):
    """
    Class for EDID subrecord.
    """

    type = "EDID"

    def parse(self):
        self.size = int.from_bytes(
            self.data_stream.read(2),
            "little"
        )

        self.editor_id = self.data_stream.read(self.size).decode()[:-1]

        return self


class String(Subrecord):
    """
    Class for string subrecords.
    """

    type = None

    def parse(self):
        self.size = int.from_bytes(
            self.data_stream.read(2),
            "little"
        )

        try:
            self.string = self.data_stream.read(self.size)
            decoded = self.string.decode()[:-1]
            if utils.is_valid_string(decoded):
                self.string = decoded
            else:
                # write string to txt file
                with open("invalid_strings.txt", "a", encoding="utf8") as file:
                    file.write(f"{self.string[:-1]}\n")

                self.data = self.string
                self.string = None
        except UnicodeDecodeError:
            self.data = self.string
            self.string = None

        return self


class FULL(String):
    """
    Class for FULL subrecord.
    """

    type = "FULL"


class DESC(String):
    """
    Class for DESC subrecord.
    """

    type = "DESC"


class NAM1(String):
    """
    Class for NAM1 subrecord.
    """

    type = "NAM1"


class NNAM(String):
    """
    Class for NNAM subrecord.
    """

    type = "NNAM"


class CNAM(String):
    """
    Class for CNAM subrecord.
    """

    type = "CNAM"


class TNAM(String):
    """
    Class for TNAM subrecord.
    """

    type = "TNAM"


class RNAM(String):
    """
    Class for RNAM subrecord.
    """

    type = "RNAM"


class SHRT(String):
    """
    Class for SHRT subrecord.
    """

    type = "SHRT"


class DNAM(String):
    """
    Class for DNAM subrecord.
    """

    type = "DNAM"


class MAST(Subrecord):
    """
    Class for MAST subrecord.
    """

    type = "MAST"

    def parse(self):
        self.size = int.from_bytes(
            self.data_stream.read(2),
            "little"
        )

        self.file = self.data_stream.read(self.size)
        self.file = self.file.decode()[:-1]

        return self


class TIFC(Subrecord):
    """
    Class for TIFC subrecord.
    """

    type = "TIFC"

    def parse(self):
        self.size = int.from_bytes(
            self.data_stream.read(2),
            "little"
        )

        self.count = int.from_bytes(
            self.data_stream.read(self.size),
            "little"
        )

        return self


SUBRECORD_MAPPING: dict[str, Subrecord] = {
    "HEDR": HEDR,
    "EDID": EDID,
    "FULL": FULL,
    "DESC": DESC,
    "NAM1": NAM1,
    "NNAM": NNAM,
    "CNAM": CNAM,
    "TNAM": TNAM,
    "RNAM": RNAM,
    "SHRT": SHRT,
    "DNAM": DNAM,
    "MAST": MAST,
    "TIFC": TIFC,
}
