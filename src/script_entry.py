"""
This file is part of SEE Lang Detector
and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

from file_entry import FileEntry
import subprocess
from pathlib import Path
import os


with open("./assets/psc_blacklist.txt", "r", encoding="utf8") as file:
    PSC_BLACKLIST = [
        line
        for line in file.readlines()
        if not line.startswith("#") and line.strip()
    ]

STRING_BLACKLIST = [
    "{0}"
]


class ScriptEntry(FileEntry):
    """
    Class for script file entry.
    """

    decompiler_path = Path('./assets/champollion/Champollion.exe').resolve()

    def _exec_command(self, args: str):
        cmd = f""""{self.decompiler_path}" {args}"""

        output = ""

        with subprocess.Popen(
            cmd,
            shell=True,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf8",
            errors="ignore"
        ) as process:
            self.pid = process.pid
            for line in process.stdout:
                output += line

        self.pid = None

        if process.returncode:
            self.app.log.error(f"Champollion Command:\n{cmd}")
            self.app.log.error(f"Champollion Output:\n{output}")
            raise RuntimeError("Failed to execute Champollion command! Check output above!")

    def decompile_script(self):
        """
        Decompiles script to better extract strings.
        """

        if not self.file_path.is_file():
            raise FileNotFoundError(f"PEX File '{self.file_path}' does not exist!")

        out_path = (Path("temp") / self.file_path.name).resolve().with_suffix(".psc")

        os.makedirs(out_path.parent, exist_ok=True)

        if out_path.is_file():
            os.remove(out_path)

        args = f""""{self.file_path}" --psc "{out_path.parent}" """
        self._exec_command(args)

        return out_path
    
    @staticmethod
    def clean_psc_comments(psc_code: str):
        # Clean comment at beginning
        psc_code = "".join(psc_code.splitlines(True)[7:])

        # Clean one line comments
        psc_code = "".join([
            line.strip()
            for line in psc_code.splitlines(keepends=True)
            if (not line.startswith(";")) and line.strip()
        ])

        return psc_code
    
    @staticmethod
    def extract_line_strings(line: str):
        strings: list[str] = []

        line = line.strip()

        while line.count('"') >= 2:
            if line.endswith('"'):
                break
            _, string, line = line.split('"', 2)

            strings.append(string)

        return strings

    def extract_strings(self):
        """
        Extracts strings from compiled script file.
        """

        psc_file = self.decompile_script()

        result: list[dict[str, str]] = []

        cleaned_code = self.clean_psc_comments(psc_file.read_text("utf8"))

        for line in cleaned_code.splitlines():
            if not '"' in line or any([
                string.lower() in line.lower()
                for string in PSC_BLACKLIST
            ]):
                continue
            else:
                strings = self.extract_line_strings(line)
                for string in strings:
                    if string not in STRING_BLACKLIST:
                        result.append({
                            "editor_id": "",
                            "type": "PEX",
                            "string": string
                        })

        self.strings = result
        return result
