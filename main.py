"""news-image-20261126: sum up 26 November 2026's world news in one image.

The image (entry.png, 1024x1024 RGB) was rendered by the agent in this
session and ships in the repository. This program only copies it to the
output directory: the grader runs `python3 -P -s main.py` in a bare
python:3.13 image with no Pillow installed, so it must be standard
library only (os, sys, shutil, hashlib -- no Pillow, no network, no
randomness, no clock).

It resolves its own directory from __file__, so it works from any
working directory, as any user, with a read-only repository.
"""

import hashlib
import os
import shutil
import sys

EXPECTED_WIDTH = 1024
EXPECTED_HEIGHT = 1024
EXPECTED_MODE = "RGB"


def _read_png_header(path):
    """Return (width, height) of a PNG without any imaging lib.

    Reads the IHDR chunk (13 bytes, starting at offset 16): width and
    height are big-endian uint32, bit depth is 1 byte, colour type is
    1 byte. Colour type 2 with bit depth 8 is RGB.
    """
    with open(path, "rb") as f:
        data = f.read(33)
    if len(data) < 33 or data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("not a PNG file: %s" % path)
    if data[12:16] != b"IHDR":
        raise ValueError("missing IHDR chunk: %s" % path)
    width = int.from_bytes(data[16:20], "big")
    height = int.from_bytes(data[20:24], "big")
    bit_depth = data[24]
    colour_type = data[25]
    if bit_depth != 8 or colour_type != 2:
        raise ValueError(
            "expected 8-bit RGB PNG, got bit_depth=%d colour_type=%d"
            % (bit_depth, colour_type)
        )
    return width, height


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    src = os.path.join(here, "entry.png")
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    dst = os.path.join(out_dir, "entry.png")

    shutil.copyfile(src, dst)

    width, height = _read_png_header(dst)
    if (width, height) != (EXPECTED_WIDTH, EXPECTED_HEIGHT):
        raise ValueError(
            "unexpected size %dx%d, expected %dx%d"
            % (width, height, EXPECTED_WIDTH, EXPECTED_HEIGHT)
        )

    sha = hashlib.sha256()
    size = 0
    with open(dst, "rb") as f:
        while True:
            chunk = f.read(1 << 20)
            if not chunk:
                break
            sha.update(chunk)
            size += len(chunk)

    print("entry.png: %dx%d %s, %d bytes, sha256=%s"
          % (width, height, EXPECTED_MODE, size, sha.hexdigest()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
