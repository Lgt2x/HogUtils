import argparse
from dataclasses import dataclass
import pathlib
from struct import unpack
from PIL import Image

OGF_HEADER_TAG_1 = b"\x00\x00z"
OGF_HEADER_TAG_2 = b"\x00\x00y"
ENDIANNESS = "<"


@dataclass
class MipMapTexture:
    image: Image.Image
    filename: str


class OGFReader:
    cursor: int = 0
    color_code: str = 0
    textures: list[MipMapTexture] = []

    def read_texture(self, file: pathlib.Path):
        self.cursor = 0
        self.data = file.read_bytes()

        try:
            self.read_header()
            self.read_content()
        except Exception as e:
            print(f"Could not read {file}: {e}")

    def write_mipmaps(self, output_dir: pathlib.Path):
        print(f"Writing to {output_dir.absolute()}")
        for texture in self.textures:
            self.save_image(texture.image, pathlib.Path(texture.filename), output_dir)

    def read_header(self):
        self.tag = self.read_bytes(3)
        if self.tag != OGF_HEADER_TAG_1 and self.tag != OGF_HEADER_TAG_2:
            raise ValueError(f"Could not find OGF header, got {self.tag} instead")

        self.filename = self.read_varlen_string()
        self.mip_level = self.read_uchar8()
        self.read_bytes(9)  # fillter
        self.width = self.read_int16()
        self.height = self.read_int16()
        self.read_bytes(2)  # 20 28 for some reason

        print(
            f"Reading texture {self.filename}: #maps = {self.mip_level} width = {self.width} height =  {self.height} tag = {self.tag}"
        )

    def read_content(self):
        for _ in range(self.mip_level):
            im = Image.new("RGBA", (self.width, self.height))
            pixels = im.load()
            pos = 0
            while pos < (self.width * self.height):
                length = self.read_uchar8()
                color_packed = self.read_int16()

                # 0 pixels actually mean 1
                if length == 0:
                    length += 1

                if self.tag == OGF_HEADER_TAG_1:
                    # arrrrrgggggbbbbb
                    # TODO: create a proper function to extract bits
                    color = (
                        int((((color_packed & 0b0111110000000000) >> 10) / ((2 << 4) - 1)) * 255),
                        int((((color_packed & 0b0000001111100000) >> 5) /  ((2 << 4) - 1)) * 255),
                        int(((color_packed & 0b0000000000011111) / ((2 << 4) - 1)) * 255),
                        int((((color_packed & 0b1000000000000000) >> 15) * 255)),
                    )
                else:
                    # aaaarrrrggggbbbb
                    color = (
                        int((((color_packed & 0b0000111100000000) >> 8) / ((2 << 3) - 1)) * 255),
                        int((((color_packed & 0b0000000011110000) >> 4) / ((2 << 3) - 1)) * 255),
                        int((((color_packed & 0b0000000000001111)) / ((2 << 3) - 1)) * 255),
                        int((((color_packed & 0b1111000000000000) >> 12) / ((2 << 3) - 1)) * 255),
                    )

                for i in range(pos, pos + length):
                    pixels[i % self.width, i // self.width] = color
                pos += length

            self.textures.append(MipMapTexture(im, self.filename))

            # Each map is 1/4 of the previous one
            self.width //= 2
            self.height //= 2

        return im

    def save_image(
        self, image: Image.Image, filename: pathlib.Path, output_dir: pathlib.Path
    ):
        image.save(
            pathlib.Path(
                output_dir / (f"{filename.stem}_{image.size[0]}_{image.size[1]}.png")
            )
        )

    def read_varlen_string(self) -> str:
        string_coll = bytes()
        while (byte := self.read_bytes(1)) != b"\x00":
            string_coll += byte
        return string_coll.decode("ascii", "ignore").rstrip("\x00").strip()

    def read_uchar8(self) -> int:
        return unpack(ENDIANNESS + "B", self.read_bytes(1))[0]

    def read_int16(self) -> int:
        return unpack(ENDIANNESS + "H", self.read_bytes(2))[0]

    def read_bytes(self, size: int) -> bytes:
        raw = self.data[self.cursor : self.cursor + size]
        self.cursor += size
        return raw


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="ogfextract",
        description="Export OGF texture files to PNG",
    )

    parser.add_argument(
        "-i",
        "--input",
        action="append",
        nargs="+",
        help="Input OGF file or directory containing OGF files",
    )
    parser.add_argument("-o", "--output", nargs=1, help="Output directory")
    args = parser.parse_args()

    if not args.input and not args.file_input:
        print("Error: you must specify at least one --input file or directory")
        exit(1)

    if not args.output:
        print("Error: you must specify the output directory")
        exit(1)

    output_dir = pathlib.Path(args.output[0])
    if not output_dir.is_dir() or not output_dir.exists():
        print(f"Error: output directory {output_dir} does not exist")
        exit(1)

    reader = OGFReader()

    for input_file in [f for file_group in args.input for f in file_group]:
        input_path = pathlib.Path(input_file)
        if input_path.is_dir() and input_path.exists():
            for inner_file in input_path.iterdir():
                if inner_file.suffix.lower() == ".ogf":
                    reader.read_texture(inner_file)
        elif input_path.is_file and input_path.exists():
            reader.read_texture(input_path)

    reader.write_mipmaps(output_dir)
