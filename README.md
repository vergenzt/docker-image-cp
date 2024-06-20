# docker-image-cp

Command line utility to copy files out of a Docker image.

## Installation

```
pipx install docker-image-cp
```

## Usage

<!--[[[cog
  os.environ["COLUMNS"] = "100"
  print("```")
  print(sp.check_output([".venv/bin/docker-image-cp", "--help"], text=True, stderr=sp.STDOUT))
  print("```")
]]]-->
```
usage: docker-image-cp [-h] (-i IID | -b CTX) [-C] SRC [DST]

positional arguments:
  SRC                  Source path to copy from within the image. May be relative, in which case
                       it's relative to the image's workdir.
  DST                  Dest path on host to copy to. Defaults to SRC if SRC is relative, else DST
                       is required.

options:
  -h, --help           show this help message and exit
  -i IID, --image IID  ID of a pre-existing image to copy from.
  -b CTX, --build CTX  Context path for building an image to copy from.
  -C, --no-cleanup     Don't delete image or container when done. (Default is to always remove
                       container, and attempt to remove image if it was built by this command.)

```
<!--[[[end]]] (checksum: bbc078e4b09d4ed290288b10398ddf04)-->
