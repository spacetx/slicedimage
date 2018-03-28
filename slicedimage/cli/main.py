from __future__ import absolute_import, division, print_function, unicode_literals

import argparse

from .checksum import checksum


def main():
    parser = argparse.ArgumentParser()

    subparsers = parser.add_subparsers(dest="slicedimage_command")

    checksum_command = subparsers.add_parser("checksum", help="Read a TOC file and add missing checksums.")
    checksum_command.add_argument("in_url", help="URL for the source TOC file")
    checksum_command.add_argument("out_path", help="Path to write TOC file with checksums")
    checksum_command.add_argument("--pretty", action="store_true", help="Pretty-print the output file")
    checksum_command.set_defaults(slicedimage_command=checksum)

    args, argv = parser.parse_known_args()

    if args.slicedimage_command is None:
        parser.print_help()
        parser.exit(status=2)

    args.slicedimage_command(args, print_help=len(argv) != 0)
