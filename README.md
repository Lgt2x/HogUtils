# HogUtils

Utility Python script to manipulate the Descent 3 HOG container format. Only depends on the standard library.

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