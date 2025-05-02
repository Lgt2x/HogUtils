import sys
import os
from pathlib import Path
from dataclasses import dataclass
from struct import unpack



HELP_TEXT = """
HogUtils.py
Usage: python HogUtils.py <action> <parameters>
Where <action> can be one of:
 * show <hogfile.hog> : list entries of given HOG file
 * extract <hogfile.hog> <entries>: extract comma-separated list of entries from HOG file.
 * create [search_path] <output.hog>: create a new HOG file bundling all files found in search path
 * append <input files> <input.hog> <output.hog>: add input files into input hog to form a new hog file
 * merge <inputs.hog> <output.hog>: merge comma-separated list of HOG files into a single output HOG
 """
HOG_HEADER_TAG = "HOG2"
ENDIANNESS = "<"


class HogHeader:
    tag: str = ""
    nfiles: int = 0
    file_data_offset = 68
    reserved: list[int]


class HogFileEntry:
    name: str
    flags: int
    size: int
    timestamp: int
    content = []


def format_size(num):
    for unit in ("B", "KB", "MB", "GB"):
        if num <= 1024.0:
            return f"{num:.2f}{unit}"
        num /= 1024.0
    return f"{num:.2f}TB"


class HogReader:
    cursor: int = 0
    entries: list[HogFileEntry]

    def open(self, input_file: str):
        self.data = Path(input_file).read_bytes()
        self.header = HogHeader()
        self.header.tag = self.read_string(4)
        if self.header.tag != HOG_HEADER_TAG:
            print(
                f"Could not find Hog file {HOG_HEADER_TAG} identifier. Got {self.header.tag} instead"
            )
            raise ValueError

        self.header.nfiles = self.read_int32()

        self.header.file_data_offset = self.read_int32()

        self.read_bytes(56)  # Reserved

        self.entries = [HogFileEntry() for _ in range(self.header.nfiles)]
        for file in range(self.header.nfiles):
            self.entries[file].name = self.read_string(36)
            self.entries[file].flags = self.read_int32()
            self.entries[file].size = self.read_int32()
            self.entries[file].timestamp = self.read_int32()

        for file in range(self.header.nfiles):
            self.entries[file].content = self.read_bytes(self.entries[file].size)

    def extract(self, names: list[str]):
        for entry in self.entries:
            if entry.name in names:
                with open(entry.name, "wb") as f:
                    f.write(entry.content)
                    names.pop(names.index(entry.name))
                    print(f"Extracted {entry.name}")

        if names:
            print(f"Could not extract items {names}")

    def create_hog_from_files(self, path: str):
        files = os.listdir(path)
        entries: list[HogFileEntry] = []
        for file in files:
            fullpath = os.path.join(path, file)
            if os.path.isfile(fullpath):
                entry = HogFileEntry()
                entry.name = file
                entry.flags = 0x0
                entry.size = os.stat(fullpath).st_size
                entry.content = Path(fullpath).read_bytes()
                entries.append(entry)

        content = []

        header = HogHeader(tag=HOG_HEADER_TAG, nfiles=len(entries), timestamp=0)

    def merge_hogs(self, names: list[str]):
        entries: list[HogFileEntry] = []
        for name in names:
            hog = self.open(name)
            entries += hog.entries

        entries.sort(key=lambda e: e.name)

    def print_content(self):
        print(f"Found {self.header.nfiles} entries")
        print(f"Offset is {self.header.file_data_offset}")
        print(f"{'Name':<36}{'Size':<10}{'Flags':<10}{'Timestamp':<10}")
        for file in range(self.header.nfiles):
            print(
                f"{self.entries[file].name:<36}{format_size(self.entries[file].size):<10}{self.entries[file].flags:<10}{self.entries[file].timestamp:<10}"
            )

    def read_string(self, size):
        return self.read_bytes(size).decode("ascii", "ignore").rstrip("\x00").strip()

    def read_int32(self):
        return unpack(ENDIANNESS + "i", self.read_bytes(4))[0]

    def read_bytes(self, size: int):
        raw = self.data[self.cursor : self.cursor + size]
        self.cursor += size
        return raw


if __name__ == "__main__":
    actions = ["show", "extract", "create", "append", "merge"]
    action = sys.argv[1]
    source = sys.argv[2]

    if action not in actions:
        print(HELP_TEXT)
        exit(1)

    try:
        if action == actions[0]:
            reader = HogReader()
            reader.open(source)
            reader.print_content()
        elif action == actions[1]:
            reader = HogReader()
            reader.open(source)
            extracted_files = sys.argv[3].split(",")
            reader.extract(extracted_files)
        elif action == actions[2]:
            reader = HogReader()
    except Exception as e:
        print(f"Error {e.args}")