"""
Copyright (c) Cutleast
"""

import zlib
from io import BufferedReader, BytesIO

from . import utilities as utils
from .subrecord import SUBRECORD_MAPPING, TIFC, Subrecord


class Record:
    """
    Contains parsed record data.
    """

    data_stream: BufferedReader
    type: str = "Record"

    def __init__(self, data_stream: BufferedReader, type: str = None):
        self.data_stream = data_stream
        self.type = type if type else self.type

    def __repr__(self):
        string = "\n\t{"

        for key, value in self.__dict__.items():
            if key not in ["data_stream", "_stream", "data"]:
                string += f"\n\t\t{key} = {value!r}"
            elif key == "data":
                string += f"\n\t\t{key} = {value[:64]!r}"

        string += "\n\t}"

        return string

    def __str__(self):
        return self.__repr__()

    def __len__(self):
        try:
            return self.size + 8
        except AttributeError:
            return 0

    def parse(self):
        self.size = int.from_bytes(
            self.data_stream.read(4),
            "little"
        )

        self.flags = int.from_bytes(
            self.data_stream.read(4),
            "little"
        )

        self.formid = self.data_stream.read(4).hex()

        self.timestamp = int.from_bytes(
            self.data_stream.read(2),
            "little"
        )

        self.version_control_info = int.from_bytes(
            self.data_stream.read(2),
            "little"
        )

        self.internal_version = int.from_bytes(
            self.data_stream.read(2),
            "little"
        )

        _ = self.data_stream.read(2)

        self.data = self.data_stream.read(self.size)
        self._stream = BytesIO(self.data)
        if self.type in PARSE_WHITELIST:
            self.parse_subrecords()
        else:
            print(f"{self.type!r} not in PARSE_WHITELIST!")
            self.subrecords = []

        return self

    def parse_subrecords(self):
        self.subrecords: list[Subrecord] = []

        while (subrecord_type := self._stream.read(4)):
            try:
                subrecord_type = subrecord_type.decode()
            except UnicodeDecodeError:
                # print(f"Failed to process subrecord {subrecord_type!r}!")
                # self._stream.seek(-24, 1)
                # print(self._stream.read(64))
                break

            if subrecord_type == "XXXX":
                xxxx_size = int.from_bytes(
                    self._stream.read(2),
                    "little"
                )
                field_size = int.from_bytes(
                    self._stream.read(xxxx_size),
                    "little"
                )
                field_type = self._stream.read(4).decode()
                field_data = self._stream.read(field_size)
                _ = self._stream.read(2)
                subrecord = Subrecord(self._stream, field_type)
                subrecord.size = field_size
                subrecord.data = field_data
                self.subrecords.append(subrecord)
                continue

            # print(f"\tParsing {subrecord_type!r} subrecord...")

            if subrecord_type in SUBRECORD_MAPPING:
                subrecord = SUBRECORD_MAPPING[subrecord_type]
                subrecord = subrecord(self._stream).parse()
            else:
                subrecord = Subrecord(self._stream, subrecord_type).parse()

            self.subrecords.append(subrecord)

        return self


class GRUP(Record):
    """
    Class for GRUP records.
    """

    type = "GRUP"

    def __repr__(self):
        string = "\n{"

        for key, value in self.__dict__.items():
            if key not in ["data_stream", "_stream", "data"]:
                string += f"\n\t{key} = {value!r}"
            elif key == "data":
                string += f"\n\t{key} = {value[:64]!r}"

        string += "\n}"

        return string

    def __len__(self):
        try:
            if self.group_size >= 24:
                return self.group_size - 24
            else:
                return self.group_size
        except AttributeError:
            return 0

    def parse(self):
        self.group_size = int.from_bytes(
            self.data_stream.read(4),
            "little"
        )

        self.label = self.data_stream.read(4).decode()

        if self.label in GRUP_OVERRIDE and self.label in PARSE_WHITELIST:
            self.data_stream.seek(-12, 1)
            return GRUP_OVERRIDE[self.label](self.data_stream).parse()

        self.group_type = int.from_bytes(
            self.data_stream.read(4),
            "little", signed=True
        )

        self.timestamp = int.from_bytes(
            self.data_stream.read(2),
            "little"
        )

        self.version_control_info = int.from_bytes(
            self.data_stream.read(2),
            "little"
        )

        _ = self.data_stream.read(4)

        self.data = self.data_stream.read(len(self))
        self._stream = BytesIO(self.data)

        if self.label in GRUP_WHITELIST:
            self.parse_records()
        else:
            # print(f"{self.label!r} not in GRUP_WHITELIST!")
            self.records = []

        self.subrecords = []

        return self

    def parse_records(self):
        self.records: list[Record] = []

        data_read = 0

        while data_read < len(self):
            try:
                record_type = self._stream.read(4)
                record_type = record_type.decode()
            except UnicodeDecodeError:
                # print(f"Failed to process record {record_type!r}!")
                break
                # print(self)
                # sys.exit()

            if record_type != self.label:
                # self._stream.seek(-4, 1)
                break

            # print(f"Parsing {record_type!r} record...")

            if record_type in RECORD_MAPPING:
                record = RECORD_MAPPING[record_type]
                record = record(self._stream)
            else:
                record = Record(self._stream, record_type)

            record = record.parse()

            data_read += len(record)

            self.records.append(record)

        return self


class NPC_(Record):
    """
    Class for NPC_ records.
    """

    type = "NPC_"

    def parse(self):
        # self.type = self.data_stream.read(4).decode()

        self.size = int.from_bytes(
            self.data_stream.read(4),
            "little"
        )

        # _ = self.data_stream.read(2)

        self.flags = int.from_bytes(
            self.data_stream.read(4),
            "little"
        )

        self.formid = self.data_stream.read(4).hex()

        self.timestamp = int.from_bytes(
            self.data_stream.read(2),
            "little"
        )

        self.version_control_info = int.from_bytes(
            self.data_stream.read(2),
            "little"
        )

        self.internal_version = int.from_bytes(
            self.data_stream.read(2),
            "little"
        )

        _ = self.data_stream.read(2)

        # Decompress data if compressed
        if utils.peek(self.data_stream, 4) != b"EDID":
            self.decompressed_size = int.from_bytes(
                self.data_stream.read(4),
                "little"
            )
            self.data = zlib.decompress(self.data_stream.read(self.size-4))
        else:
            self.data = self.data_stream.read(self.size)

        self._stream = BytesIO(self.data)
        self.parse_subrecords()

        return self


class DIAL(Record):
    """
    Class for DIAL group records.
    """

    type = "DIAL"

    def parse(self):
        super().parse()

        if self.get_count():
            self.GRUP = DIAL_GRUP(self.data_stream).parse()
        else:
            self.GRUP = None

        return self

    def get_count(self):
        for subrecord in self.subrecords:
            if isinstance(subrecord, TIFC):
                return subrecord.count


class DIAL_GRUP(GRUP):
    """
    Class for dialog groups.
    """

    type = "DIAL_GRUP"
    label = "DIAL"

    def __repr__(self):
        string = super().__repr__()

        string = "\n".join([
            f"\t\t{line}"
            for line in string.splitlines()
        ])

        return string

    def __len__(self):
        try:
            if self.size >= 24:
                return self.size - 24
            else:
                return self.size
        except AttributeError:
            return 0

    def parse(self):
        _ = self.data_stream.read(4)

        self.size = int.from_bytes(
            self.data_stream.read(4),
            "little"
        )

        _ = self.data_stream.read(4)

        self.group_type = int.from_bytes(
            self.data_stream.read(4),
            "little", signed=True
        )

        self.timestamp = int.from_bytes(
            self.data_stream.read(2),
            "little"
        )

        self.version_control_info = int.from_bytes(
            self.data_stream.read(2),
            "little"
        )

        _ = self.data_stream.read(4)

        self.parse_subgroups()

        return self

    def parse_subgroups(self):
        self.records: list[Record] = []

        while self.data_stream.read(4) == b"INFO":
            self.records.append(
                Record(self.data_stream, "INFO").parse()
            )
        
        self.data_stream.seek(-4, 1)

        return self


class CELL(Record):
    """
    Class for CELL records.
    """

    type = "CELL"

    def __repr__(self):
        string = super().__repr__()

        string = "\n".join([
            f"\t\t{line}"
            for line in string.splitlines()
        ])

        return string

    def parse(self):
        self.type = self.data_stream.read(4).decode()

        self.size = int.from_bytes(
            self.data_stream.read(4),
            "little"
        )

        self.flags = int.from_bytes(
            self.data_stream.read(4),
            "little"
        )

        self.formid = self.data_stream.read(4).hex()

        self.timestamp = int.from_bytes(
            self.data_stream.read(2),
            "little"
        )

        self.version_control_info = int.from_bytes(
            self.data_stream.read(2),
            "little"
        )

        self.internal_version = int.from_bytes(
            self.data_stream.read(2),
            "little"
        )

        _ = self.data_stream.read(2)

        # Decompress data if compressed
        if utils.peek(self.data_stream, 4) not in [b"EDID", b"DATA", b"FULL"]:
            self.decompressed_size = int.from_bytes(
                self.data_stream.read(4),
                "little"
            )
            self.data = zlib.decompress(self.data_stream.read(self.size-4))
        else:
            self.data = self.data_stream.read(self.size)

        self._stream = BytesIO(self.data)
        self.parse_subrecords()

        return self


class CELL_GRUP(GRUP):
    """
    Class for cell groups.
    """

    type = "GRUP"
    label = "CELL"

    def __len__(self):
        try:
            if self.size >= 24:
                return self.size - 24
            else:
                return self.size
        except AttributeError:
            return 0

    def parse(self):
        self.type = self.data_stream.read(4).decode()

        self.size = int.from_bytes(
            self.data_stream.read(4),
            "little"
        )

        self.label = self.data_stream.read(4).decode()

        self.group_type = int.from_bytes(
            self.data_stream.read(4),
            "little", signed=True
        )

        self.timestamp = int.from_bytes(
            self.data_stream.read(2),
            "little"
        )

        self.version_control_info = int.from_bytes(
            self.data_stream.read(2),
            "little"
        )

        _ = self.data_stream.read(4)

        # self.data = self.data_stream.read(len(self))
        
        self.parse_cell_blocks()

        return self

    def parse_cell_blocks(self):
        self.cell_blocks: list[CELL_BLOCK] = []

        while utils.peek(self.data_stream, 4) == b"GRUP":
            group_type = int.from_bytes(
                utils.peek(self.data_stream, 16)[12:],
                "little", signed=True
            )

            if group_type == 0:
                break

            cell_block = CELL_BLOCK(self.data_stream).parse()
            self.cell_blocks.append(cell_block)

        return self


class CELL_BLOCK(CELL_GRUP):
    """
    Class for cell blocks.
    """

    type = "CELL_BLOCK"

    def __repr__(self):
        string = super().__repr__()

        string = "\n".join([
            f"\t\t{line}"
            for line in string.splitlines()
        ])

        return string

    def parse(self):
        _ = self.data_stream.read(4).decode()

        self.size = int.from_bytes(
            self.data_stream.read(4),
            "little"
        )

        self.block_number = int.from_bytes(
            self.data_stream.read(4),
            "little"
        )

        self.cell_type = int.from_bytes(
            self.data_stream.read(4),
            "little", signed=True
        )

        self.timestamp = int.from_bytes(
            self.data_stream.read(2),
            "little"
        )

        self.version_control_info = int.from_bytes(
            self.data_stream.read(2),
            "little"
        )

        _ = self.data_stream.read(4)

        self.parse_subblocks()

        return self

    def parse_subblocks(self):
        self.subblocks: list[CELL_SUBBLOCK] = []

        while utils.peek(self.data_stream, 4) == b"GRUP":
            group_type = int.from_bytes(
                utils.peek(self.data_stream, 14)[12:],
                "little", signed=True
            )

            if group_type != (self.cell_type + 1):
                break

            subblock = CELL_SUBBLOCK(self.data_stream).parse()
            self.subblocks.append(subblock)

        return self


class CELL_SUBBLOCK(CELL_BLOCK):
    """
    Class for cell sub-blocks.
    """

    type = "CELL_SUBBLOCK"

    def parse(self):
        _ = self.data_stream.read(4).decode()

        self.size = int.from_bytes(
            self.data_stream.read(4),
            "little"
        )

        self.block_number = int.from_bytes(
            self.data_stream.read(2),
            "little"
        )

        _ = self.data_stream.read(2)

        self.cell_type = int.from_bytes(
            self.data_stream.read(2),
            "little", signed=True
        )

        _ = self.data_stream.read(2)

        self.timestamp = int.from_bytes(
            self.data_stream.read(2),
            "little"
        )

        self.version_control_info = int.from_bytes(
            self.data_stream.read(2),
            "little"
        )

        _ = self.data_stream.read(4)

        self.data = self.data_stream.read(len(self))

        stream = BytesIO(self.data)
        
        self.parse_cell(stream)

        return self

    def parse_cell(self, stream):
        self.CELL = CELL(stream).parse()

        return self


class CELL_SUBGRUP(GRUP):
    """
    Class for cell subgroups.
    """

    def parse(self):
        self.type = self.data_stream.read(4).decode()

        self.group_size = int.from_bytes(
            self.data_stream.read(4),
            "little"
        )

        self.label = self.data_stream.read(4)

        self.group_type = int.from_bytes(
            self.data_stream.read(4),
            "little", signed=True
        )

        self.timestamp = int.from_bytes(
            self.data_stream.read(2),
            "little"
        )

        self.version_control_info = int.from_bytes(
            self.data_stream.read(2),
            "little"
        )

        _ = self.data_stream.read(4)

        self.data = self.data_stream.read(len(self))

        return self


class WRLD(Record):
    """
    Class for WRLD records.
    """

    type = "WRLD"

    def parse(self):
        self.type = self.data_stream.read(4).decode()

        super().parse()

        if utils.peek(self.data_stream, 4) == b"GRUP":
            self.GRUP = WRLD_SUBGRUP(self.data_stream).parse()
        else:
            self.GRUP = None

        return self


class WRLD_GRUP(GRUP):
    """
    Class for world groups.
    """

    type = "WRLD_GRUP"
    label = "WRLD"

    def __len__(self):
        try:
            if self.size >= 24:
                return self.size - 24
            else:
                return self.size
        except AttributeError:
            return 0

    def parse(self):
        self.type = self.data_stream.read(4).decode()

        self.size = int.from_bytes(
            self.data_stream.read(4),
            "little"
        )

        self.label = self.data_stream.read(4).decode()

        self.group_type = int.from_bytes(
            self.data_stream.read(4),
            "little", signed=True
        )

        self.timestamp = int.from_bytes(
            self.data_stream.read(2),
            "little"
        )

        self.version_control_info = int.from_bytes(
            self.data_stream.read(2),
            "little"
        )

        _ = self.data_stream.read(4)

        self.data = self.data_stream.read(len(self))
        
        self._stream = BytesIO(self.data)
        self.parse_world_records()

        return self

    def parse_world_records(self):
        self.records: list[Record] = []

        while utils.peek(self._stream, 4) == b"WRLD":
            self.records.append(
                WRLD(self._stream).parse()
            )


class WRLD_SUBGRUP(GRUP):
    """
    Class for world subgroups.
    """

    type = "WRLD_SUBGRUP"
    label = "WRLD"

    def __len__(self):
        try:
            if self.size >= 24:
                return self.size - 24
            else:
                return self.size
        except AttributeError:
            return 0
    
    def __repr__(self):
        string = super().__repr__()

        string = "\n".join([
            f"\t\t{line}"
            for line in string.splitlines()
        ])

        return string

    def parse(self):
        self.type = self.data_stream.read(4).decode()

        self.size = int.from_bytes(
            self.data_stream.read(4),
            "little"
        )

        _ = self.data_stream.read(4)#.decode()

        self.group_type = int.from_bytes(
            self.data_stream.read(4),
            "little", signed=True
        )

        self.timestamp = int.from_bytes(
            self.data_stream.read(2),
            "little"
        )

        self.version_control_info = int.from_bytes(
            self.data_stream.read(2),
            "little"
        )

        _ = self.data_stream.read(4)

        self.data = self.data_stream.read(len(self))
        
        stream = BytesIO(self.data)
        self.CELL = WRLD_CELL(stream).parse()

        return self


class WRLD_CELL(CELL):
    """
    Class for exterior CELL records.
    """

    type = "WRLD_CELL"

    def parse(self):
        self.type = self.data_stream.read(4).decode()

        self.size = int.from_bytes(
            self.data_stream.read(4),
            "little"
        )

        self.flags = int.from_bytes(
            self.data_stream.read(4),
            "little"
        )

        self.formid = self.data_stream.read(4).hex()

        self.timestamp = int.from_bytes(
            self.data_stream.read(2),
            "little"
        )

        self.version_control_info = int.from_bytes(
            self.data_stream.read(2),
            "little"
        )

        self.internal_version = int.from_bytes(
            self.data_stream.read(2),
            "little"
        )

        _ = self.data_stream.read(2)

        # Decompress data if compressed
        if utils.peek(self.data_stream, 4) not in [b"EDID", b"DATA", b"GRUP"]:
            self.decompressed_size = int.from_bytes(
                self.data_stream.read(4),
                "little"
            )
            try:
                self.data = zlib.decompress(self.data_stream.read(self.size-4))
            except zlib.error:
                self.data = self.data_stream.read(self.size-4)
                self.data_stream.seek(0)
        else:
            self.data = self.data_stream.read(self.size)

        self._stream = BytesIO(self.data)

        if utils.peek(self._stream, 4) == b"GRUP":
            self.GRUP = WRLD_SUBGRUP(self._stream).parse()
            self.subrecords = []
        else:
            self.parse_subrecords()

        return self


# List of special record types
RECORD_MAPPING: dict[str, Record] = {
    "GRUP": GRUP,
    "NPC_": NPC_,
    "DIAL": DIAL,
    "WRLD": WRLD
}

GRUP_OVERRIDE: dict[str, GRUP] = {
    "CELL": CELL_GRUP,
    "WRLD": WRLD_GRUP
}

# Whitelist for record types that are known to work
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
    "FACT",
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

# Whitelist for group types that are known to work
GRUP_WHITELIST: list[str] = [
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
    "FACT",
    "FLOR",
    "FURN",
    "HAZD",
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
    "TREE",
    "WEAP",
    "WOOP",
    "WRLD",
]
