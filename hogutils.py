import argparse
import pathlib
import sys
import os
from pathlib import Path
from dataclasses import dataclass, field
from struct import unpack


HOG_HEADER_TAG = "HOG2"
ENDIANNESS = "<"


@dataclass
class HogHeader:
    reserved: list[int] = field(default_factory=list)
    tag: str = ""
    nfiles: int = 0
    file_data_offset: int = 68


@dataclass
class HogEntry:
    flags: int = 0
    size: int = 0
    timestamp: int = 0
    hogfile: str = ""
    content: list[bytes] = field(default_factory=list)


def format_size(num_bytes: int):
    """Format a number of bytes for display"""
    for unit in ("B", "KiB", "MiB", "GiB"):
        if num_bytes <= 1024:
            return f"{num_bytes:.2f}{unit}"
        num_bytes /= 1024
    return f"{num_bytes:.2f}TB"


class HogReader:
    cursor = 0
    entries: dict[str, HogEntry] = {}

    def read_file(self, input_file: pathlib.Path):
        if not input_file.is_file:
            raise FileExistsError(f"Could not find input file {input_file}")

        self.cursor = 0
        self.data = input_file.read_bytes()

        # Read header tag
        header = HogHeader()
        header.tag = self.read_string(4)
        if header.tag != HOG_HEADER_TAG:
            if input_file.suffix.lower() != ".hog":
                # Also accept non-HOG files
                self.entries[input_file.name] = HogEntry(size=len(self.data))
                return
            print(
                f"Could not find Hog file {HOG_HEADER_TAG} identifier in {input_file}. Got {header.tag} instead"
            )
            raise ValueError

        # Read the rest of the metadata
        header.nfiles = self.read_int32()
        header.file_data_offset = self.read_int32()
        self.read_bytes(56)  # Reserved

        # Read each file
        names: list[str] = []
        for _ in range(header.nfiles):
            names.append(self.read_string(36))
            self.entries[names[-1]] = HogEntry()
            self.entries[names[-1]].flags = self.read_int32()
            self.entries[names[-1]].size = self.read_int32()
            self.entries[names[-1]].timestamp = self.read_int32()
            self.entries[names[-1]].hogfile = input_file.name

        for filename in names:
            self.entries[filename].content = self.read_bytes(
                self.entries[filename].size
            )

    def extract(self, output_dir: pathlib.Path):
        if not output_dir.is_dir():
            raise FileNotFoundError(f"Could not find output directory {output_dir}")

        for name, entry in self.entries.items():
            with open(name, "wb") as f:
                f.write(entry.content)
                print(f"Extracted {name}")

    def create(self, output_hog: pathlib.Path):
        header = HogHeader(tag=HOG_HEADER_TAG, nfiles=len(self.entries), timestamp=0)
        with output_hog.open("r") as f:
            pass


    def print_content(self):
        print(f"Found {len(self.entries)} entries")
        print(f"{'Name':<36}{'Size':<10}{'Flags':<10}{'Timestamp':<12}{'From':<10}")
        for name, entry in sorted(self.entries.items()):
            print(
                f"{name:<36}{format_size(entry.size):<10}{entry.flags:<10}{entry.timestamp:<12}{entry.hogfile:<10}"
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
    parser = argparse.ArgumentParser(
        prog="hogutils", description="Display & Edit Descent 3 HOG files", formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        "action",
        choices=["show", "extract", "create"],
        help="""- show: display the input HOG file(s) content to standard output, or to output file is specified
- extract: extract files' content into the output directory specified with --output
- create: create a new output HOG file from input files, HOG or not
""",
    )
    parser.add_argument(
        "-i", "--input", action="append", nargs="+", help="Input file to read"
    )
    parser.add_argument("-o", "--output", nargs=1, help="Output file or directory")

    args = parser.parse_args()

    reader = HogReader()
    for input_file in [f for file_group in args.input for f in file_group]:
        reader.read_file(pathlib.Path(input_file))

    # try:
    if True:
        if args.action == "show":
            reader.print_content()
        elif args.action == "extract":
            reader.extract(output=args.output)
        elif args.action == "create":
            reader.create(args.output)
    # except Exception as e:
    #     print(f"Error: {e.args}")
