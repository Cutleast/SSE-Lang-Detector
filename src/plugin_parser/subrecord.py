"""
Copyright (c) Cutleast
"""

from io import BufferedReader, BytesIO
from . import utilities as utils
from .datatypes import Integer, String, Float


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

    def parse(self, flags: dict[str, bool]):
        self.type = String.string(self.data_stream, 4)
        self.size = Integer.uint16(self.data_stream)
        self.data = self.data_stream.read(self.size)

        return self


class HEDR(Subrecord):
    """
    Class for HEDR subrecord.
    """

    type = "HEDR"

    def parse(self, flags: dict[str, bool]):
        self.type = String.string(self.data_stream, 4)
        self.size = Integer.uint16(self.data_stream)
        self.version = round(Float.float32(self.data_stream), 2)
        self.records_num = Integer.uint32(self.data_stream)
        self.next_object_id = Integer.uint32(self.data_stream)

        return self


class EDID(Subrecord):
    """
    Class for EDID subrecord.
    """

    type = "EDID"

    def parse(self, flags: dict[str, bool]):
        self.type = String.string(self.data_stream, 4)
        self.size = Integer.uint16(self.data_stream)
        self.editor_id = String.zstring(self.data_stream)

        return self


class StringSubrecord(Subrecord):
    """
    Class for string subrecords.
    """

    type = None

    def parse(self, flags: dict[str, bool]):
        self.type = String.string(self.data_stream, 4)
        self.size = Integer.uint16(self.data_stream)
        self.data = utils.peek(self.data_stream, self.size)

        if flags["Localized"]:
            string_id = String.string(self.data_stream, 4).removesuffix("\x00").strip()
            self.string = string_id
        else:
            try:
                string = String.string(self.data_stream, self.size).removesuffix("\x00").strip()
                if utils.is_valid_string(string) or string.isnumeric():
                    self.string = string
                else:
                    self.string = None
            except UnicodeDecodeError:
                self.string = None

        return self


class FULL(StringSubrecord):
    """
    Class for FULL subrecord.
    """

    type = "FULL"


class DESC(StringSubrecord):
    """
    Class for DESC subrecord.
    """

    type = "DESC"


class NAM1(StringSubrecord):
    """
    Class for NAM1 subrecord.
    """

    type = "NAM1"


class NNAM(StringSubrecord):
    """
    Class for NNAM subrecord.
    """

    type = "NNAM"


class CNAM(StringSubrecord):
    """
    Class for CNAM subrecord.
    """

    type = "CNAM"


class TNAM(StringSubrecord):
    """
    Class for TNAM subrecord.
    """

    type = "TNAM"


class RNAM(StringSubrecord):
    """
    Class for RNAM subrecord.
    """

    type = "RNAM"


class SHRT(StringSubrecord):
    """
    Class for SHRT subrecord.
    """

    type = "SHRT"


class DNAM(StringSubrecord):
    """
    Class for DNAM subrecord.
    """

    type = "DNAM"


class ITXT(StringSubrecord):
    """
    Class for ITXT subrecord.
    """

    type = "ITXT"


class MAST(Subrecord):
    """
    Class for MAST subrecord.
    """

    type = "MAST"

    def parse(self, flags: dict[str, bool]):
        super().parse(flags)
        stream = BytesIO(self.data)
        self.file = String.wzstring(stream)

        return self


class TIFC(Subrecord):
    """
    Class for TIFC subrecord.
    """

    type = "TIFC"

    def parse(self, flags: dict[str, bool]):
        super().parse(flags)
        stream = BytesIO(self.data)
        self.count = Integer.uint32(stream)

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
    "ITXT": ITXT,
}
