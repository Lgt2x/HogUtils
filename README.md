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
usage: hogutils [-h] [-i INPUT [INPUT ...]] [-o OUTPUT] {show,extract,create}

Display & Edit Descent 3 HOG files

positional arguments:
  {show,extract,create}
                        - show: display the input HOG file(s) content to standard output, or to output file is specified
                        - extract: extract files' content into the output directory specified with --output
                        - create: create a new output HOG file from input files, HOG or not

options:
  -h, --help            show this help message and exit
  -i, --input INPUT [INPUT ...]
                        Input file to read
  -o, --output OUTPUT   Output file or directory
```