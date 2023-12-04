"""
Copyright (c) Cutleast
"""

from io import BufferedReader
from pathlib import Path
from .script import Script


class ScriptParser:
    """
    Class for script parser.
    Used to parse compiled papyrus scripts.
    """

    script_path: Path = None
    script_stream: BufferedReader = None
    parsed_data = None

    def __init__(self, script_path: Path):
        self.script_path = script_path
    
    def open_stream(self):
        """
        Opens file stream if not already open.
        """

        if self.script_stream is None:
            self.script_stream = open(self.script_path, "rb")

    def close_stream(self):
        """
        Closes file stream if opened.
        """

        if self.script_stream:
            self.script_stream.close()
            self.script_stream = None

    def parse_script(self):
        """
        Parses raw data and returns parsed
        Script instance.
        """

        self.open_stream()

        self.parsed_data = Script(self.script_stream).parse()

        self.close_stream()

        return self.parsed_data
