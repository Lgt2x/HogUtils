import argparse
import pathlib
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
    name: str = "" # Name with original case
    flags: int = 0
    size: int = 0
    timestamp: int = 0
    hogfile: str = "" # HOG file it was extracted from
    content: bytes = b""


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
                self.entries[input_file.name.lower()] = HogEntry(size=len(self.data), name=input_file.name)
                self.entries[input_file.name.lower()].content = self.data
                return
            print(
                f"Could not find Hog file {HOG_HEADER_TAG} identifier in {input_file}. Got {header.tag} instead"
            )
            raise ValueError

        # Read the rest of the metadata
        header.nfiles = self.read_int32()
        header.file_data_offset = self.read_int32()
        self.read_bytes(56)  # Reserved

        print(f"Reading {header.nfiles} files from {input_file}")

        # Read each file meta data
        names: list[str] = []
        for _ in range(header.nfiles):
            name = self.read_string(36)
            names.append(name.lower()) # Store as lowercase in the map
            self.entries[names[-1]] = HogEntry()
            self.entries[names[-1]].flags = self.read_int32()
            self.entries[names[-1]].size = self.read_int32()
            self.entries[names[-1]].timestamp = self.read_int32()
            self.entries[names[-1]].hogfile = input_file.name
            self.entries[names[-1]].name = name # Keep original case

        # Read file contents
        for filename in names:
            self.entries[filename].content = self.read_bytes(
                self.entries[filename].size
            )

    def extract(self, output_dir: pathlib.Path):
        if not output_dir.is_dir():
            raise FileNotFoundError(f"Could not find output directory {output_dir}")

        for name, entry in self.entries.items():
            # Extract to file with a lowercase name
            with pathlib.Path(output_dir / name).open("wb") as f:
                f.write(entry.content)
                print(f"Extracted {name}")

    def combine(self, output_hog: pathlib.Path):
        with output_hog.open("wb") as f:
            print(f"Writing {len(self.entries)} files to {output_hog}")

            # Header
            f.write(HOG_HEADER_TAG.encode("ascii"))
            f.write(int(len(self.entries)).to_bytes(4, "little"))
            offset = (
                len(HOG_HEADER_TAG) + 4 + 4 + 56 + (4 + 4 + 4 + 36) * len(self.entries)
            )
            f.write(offset.to_bytes(4, "little"))
            f.write(bytearray(0xFF for _ in range(56)))

            # File entries
            for _, entry in sorted(
                self.entries.items(), key=lambda entry: entry[0].lower()
            ):
                f.write(entry.name.encode("ascii"))
                f.write(int(0).to_bytes(36 - len(entry.name)))  # Padding
                f.write(int(entry.flags).to_bytes(4, "little"))
                f.write(int(entry.size).to_bytes(4, "little"))
                f.write(int(entry.timestamp).to_bytes(4, "little"))

            # Content
            for _, entry in sorted(
                self.entries.items(), key=lambda entry: entry[0].lower()
            ):
                f.write(entry.content)

    def print_content(self):
        print(f"Found {len(self.entries)} entries")
        print(f"{'Name':<36}{'Size':<10}{'Flags':<10}{'Timestamp':<12}{'From':<10}")
        for _, entry in sorted(self.entries.items(), key=lambda entry: entry[0].lower()):
            print(
                f"{entry.name:<36}{format_size(entry.size):<10}{entry.flags:<10}{entry.timestamp:<12}{entry.hogfile:<10}"
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
        prog="hogutils",
        description="Display & Edit Descent 3 HOG files",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument(
        "action",
        choices=["show", "extract", "combine"],
        help="""- show: display the input HOG file(s) content to standard output, or to output file is specified
- extract: extract files' content into the output directory specified with --output
- combine: create a new output HOG file from all input files, HOG or not
""",
    )
    parser.add_argument(
        "-i", "--input", action="append", nargs="+", help="Input file to read"
    )
    parser.add_argument(
        "-f",
        "--file-input",
        nargs=1,
        help="Read input file names from a file, one file name per line",
    )
    parser.add_argument("-o", "--output", nargs=1, help="Output file or directory")

    args = parser.parse_args()

    if not args.input and not args.file_input:
        print("Error: you must specify either --input or --file-input")
        exit(1)

    # Read input file(s)
    reader = HogReader()
    if args.input:
        for input_file in [f for file_group in args.input for f in file_group]:
            reader.read_file(pathlib.Path(input_file))
    if args.file_input:
        with open(args.file_input[0], "r") as f:
            while line := f.readline():
                file = pathlib.Path(line.strip())
                # Handle case-sensitive file names: also try to open the file with a lowercase name
                file_lower = pathlib.Path(file.parent / file.name.lower())
                if file.exists():
                    reader.read_file(file)
                elif file_lower.exists():
                    reader.read_file(file_lower)
                else:
                    print(f"Warning: skipping file {file} not found")

    try:
        if args.action == "show":
            reader.print_content()
        elif args.action == "extract":
            if not args.output:
                print("Error: you must specify an output directory")
                exit(1)
            reader.extract(output_dir=pathlib.Path(args.output[0]))
        elif args.action == "combine":
            if not args.output:
                print("Error: you must specify an output file")
                exit(1)
            reader.combine(pathlib.Path(args.output[0]))
    except Exception as e:
        print(f"Error: {e.args}")
