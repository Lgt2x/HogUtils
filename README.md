# HogUtils

Utility Python script to manipulate the Descent 3 HOG container format. Only depends on the Python standard library.

```
HOG FILE FORMAT v2.0, used in Descent 3

HOG_TAG_STR		[strlen()]
NFILES			[int32]
HDRINFO			[HOG_HDR_SIZE]
FILE_TABLE		[sizeof(FILE_ENTRY) * NFILES]
FILE 0			[filelen(FILE 0)]
FILE 1			[filelen(FILE 1)]
...
FILE NFILES-1		[filelen(NFILES -1)]
```

## Usage

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
## Example

Create a new HOG file from all combined base game HOG files:

```bash
python hogutils.py combine --input d3-linux.hog d3.hog extra.hog extra1.hog extra13.hog ppics.hog --output combined.hog
```
