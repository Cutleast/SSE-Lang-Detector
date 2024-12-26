"""
This file is part of SEE Lang Detector
and falls under the license
GNU General Public License v3.0.
"""


from pathlib import Path
import json


class Dictionary:
    """
    Class to manage saved strings and EDIDs.
    """

    dict_path = Path("./assets/dictionary.json").resolve()
    edids: list[str] = []
    strings: list[str] = []

    def __init__(self):
        self.load_dictonary()

    def save_dictionary(self):
        """
        Saves dictionary to JSON file.
        """

        with open(self.dict_path, "w", encoding="utf8") as file:
            json.dump({
                "edids": self.edids,
                "strings": self.strings
            }, file, indent=4, ensure_ascii=False)

    def load_dictonary(self):
        """
        Loads dictionary from JSON file.
        """

        if not self.dict_path.is_file():
            return

        with open(self.dict_path, "r", encoding="utf8") as file:
            data = json.load(file)
            self.edids = data["edids"]
            self.strings = data["strings"]

    def add_edid(self, edid: str):
        """
        Adds <edid> to the list of EDIDs.
        """

        if edid not in self.edids:
            self.edids.append(edid)

    def add_string(self, string: str):
        """
        Adds <string> to the list of strings.
        """

        if string not in self.strings:
            self.strings.append(string)

