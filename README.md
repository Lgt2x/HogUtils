# Descent 3 Utils

Utility Python scripts to manipulate different Descent 3 formats .HOG and .OGF

## HOG

HOG is a container format that bundles multiple files.

Use the `hogutils.py` script to operate on HOG files:

```
usage: hogutils [-h] [-i INPUT [INPUT ...]] [-f FILE_INPUT] [-o OUTPUT] {show,extract,combine}

Display & Edit Descent 3 HOG files

positional arguments:
  {show,extract,combine}
                        - show: display the input HOG file(s) content to standard output, or to output file is specified
                        - extract: extract files' content into the output directory specified with --output
                        - combine: create a new output HOG file from all input files, HOG or not

options:
  -h, --help            show this help message and exit
  -i, --input INPUT [INPUT ...]
                        Input file to read
  -f, --file-input FILE_INPUT
                        Read input file names from a file, one file name per line
  -o, --output OUTPUT   Output file or directory
```
### Example

Create a new HOG file from all combined base game HOG files:

```bash
python hogutils.py combine --input d3-linux.hog d3.hog extra.hog extra1.hog extra13.hog ppics.hog --output combined.hog
```

## OGF format

OGF stores mipmap textures. The `ogfextract.py` script can read OGF textures and conert them to .png. OGF textures are typically stored in .HOG files.

```
usage: ogfextract [-h] [-i INPUT [INPUT ...]] [-o OUTPUT]

Export OGF texture files to PNG

options:
  -h, --help            show this help message and exit
  -i, --input INPUT [INPUT ...]
                        Input OGF file or directory containing OGF files
  -o, --output OUTPUT   Output directory
```