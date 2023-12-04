"""
Copyright (c) Cutleast
"""

from dataclasses import dataclass
from fnmatch import fnmatch
from io import BufferedReader
from pathlib import Path

import lz4.frame

from .datatypes import *
from .file_name_block import FileNameBlock
from .file_record import FileRecord, FileRecordBlock
from .folder_record import FolderRecord
from .header import Header


@dataclass
class Archive:
    """
    Contains parsed archive data.
    """

    archive_path: Path
    data_stream: BufferedReader
    parsed_data = None

    def match_names(self):
        """
        Matches file names to their records.
        """

        result: dict[str, FileRecord] = {}

        index = 0
        for file_record_block in self.file_record_blocks:
            for file_record in file_record_block.file_records:
                result[self.file_name_block.file_names[index]] = file_record
                index += 1

        return result
    
    def process_compression_flags(self):
        """
        Processes compression flags in files.
        """

        for file_record in self.files.values():
            has_compression_flag = file_record.has_compression_flag()

            if has_compression_flag:
                file_record.compressed = not self.header.archive_flags["Compressed Archive"]
            else:
                file_record.compressed = self.header.archive_flags["Compressed Archive"]

    def parse(self):
        self.header = Header(self.data_stream).parse()
        self.folders = [
            FolderRecord(self.data_stream).parse()
            for i in range(self.header.folder_count)
        ]
        self.file_record_blocks = [
            FileRecordBlock(self.data_stream).parse(
                self.folders[i].count
            )
            for i in range(len(self.folders))
        ]
        self.file_name_block = FileNameBlock(self.data_stream).parse(self.header.file_count)
        self.files = self.match_names()

        self.process_compression_flags()

        return self

    def glob(self, pattern: str):
        """
        Returns a list of file paths that
        match the <pattern>.

        Parameters:
            pattern: str, everything that fnmatch supports
        
        Returns:
            list of matching filenames
        """

        matching_files: list[Path] = []
        
        # Normalize pattern
        pattern = str(Path(pattern))

        for file in self.files:
            # Normalize file path
            filepath = str(Path(file))

            if fnmatch(filepath, pattern):
                matching_files.append(Path(file))

        return matching_files
    
    def extract_file(self, filename: str | Path, dest_folder: Path):
        filename = Path(filename).name

        if filename not in self.files:
            raise FileNotFoundError("File is not in archive!")

        file_record = self.files[filename]

        # Get current index
        cur_index = self.data_stream.tell()

        # Go to file raw data
        self.data_stream.seek(file_record.offset)

        if self.header.archive_flags["Embed File Names"]:
            filename = String.bstring(self.data_stream).decode(errors="ignore")

        if file_record.compressed:
            original_size = Integer.ulong(self.data_stream)
            data = self.data_stream.read(file_record.size-4)
            data = lz4.frame.decompress(data)
        else:
            data = self.data_stream.read(file_record.size)

        destination = dest_folder / filename
        os.makedirs(destination.parent, exist_ok=True)
        with open(destination, "wb") as file:
            file.write(data)
        
        if not destination.is_file():
            raise Exception(f"Failed to extract file '{filename}' from archive '{self.archive_path}'!")

        # Go back to current index
        self.data_stream.seek(cur_index)
