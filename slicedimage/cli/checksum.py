from __future__ import absolute_import, division, print_function, unicode_literals

import hashlib
import os
import sys

from slicedimage import Reader, Writer


def checksum(args, print_help):
    try:
        slicedimage = Reader.parse_doc(args.in_url, None)
    except ValueError:
        if os.path.exists(args.in_url):
            newurl = "file://{}".format(args.in_url)
            sys.stderr.write("WARNING: {} is not a url but is a file.  Attempting {}...\n".format(args.in_url, newurl))
            slicedimage = Reader.parse_doc(newurl, None)

    for tile in slicedimage.get_matching_tiles(lambda candidate_tile: candidate_tile.sha256 is None):
        hf = HashFile(hashlib.sha256)
        tile.copy(hf)
        tile.sha256 = hf.hexdigest()

    Writer.write_to_path(
        slicedimage,
        args.out_path,
        pretty=args.pretty,
        tile_opener=identity_file_namer,
        tile_writer=null_writer)


def identity_file_namer(toc_path, tile, ext):
    class fake_handle(object):
        def __init__(self, name):
            self.name = name

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            pass

    return fake_handle(tile._file_or_url)


def null_writer(tile, fh):
    pass


class HashFile(object):
    def __init__(self, hash_constructor):
        self.hasher = hash_constructor()

    def write(self, data):
        self.hasher.update(data)
        return len(data)

    def digest(self):
        return self.hasher.digest()

    def hexdigest(self):
        return self.hasher.hexdigest()
