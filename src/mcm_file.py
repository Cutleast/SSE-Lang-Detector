"""
This file is part of SEE Lang Detector
and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

from file_entry import FileEntry


class MCMEntry(FileEntry):
    """
    Class for MCM file entry.
    """

    def extract_strings(self):
        """
        Extracts strings from MCM translation file.
        """

        result: list[dict[str, str]] = []

        with open(self.file_path, "r", encoding="utf-16") as file:
            for line in file.readlines():
                if not line.strip():
                    continue
                
                try:
                    string_id, string = line.split("\t", 1)

                    if string_id and string:
                        result.append({
                            "editor_id": string_id.strip(),
                            "type": "MCM",
                            "string": string.strip()
                        })
                except ValueError:
                    continue

        self.strings = result
        return result
