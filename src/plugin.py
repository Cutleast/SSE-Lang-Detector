"""
This file is part of SEE Lang Detector
and falls under the license
GNU General Public License v3.0.
"""

from plugin_parser.plugin_parser import PluginParser
from file_entry import FileEntry


class PluginEntry(FileEntry):
    """
    Class for plugin entry.
    """

    def extract_strings(self):
        """
        Extracts strings from plugin.
        """

        parser = PluginParser(self.file_path)
        parser.parse_plugin()
        result: list[dict[str, str]] = []

        strings = parser.extract_strings()

        for group in strings.values():
            result += group

        self.strings = result
        return result


