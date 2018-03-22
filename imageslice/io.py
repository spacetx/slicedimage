from __future__ import absolute_import, division, print_function, unicode_literals

import json
import os
import posixpath
import tempfile

from packaging import version
from six.moves import urllib

from .backends import DiskBackend, HttpBackend
from ._formats import ImageFormat
from ._imageslice import ImageSlice
from ._tile import Tile


def infer_backend(url, allow_caching=True):
    parsed = urllib.parse.urlparse(url)

    if parsed.scheme in ("http", "https"):
        backend = HttpBackend(url)
    elif parsed.scheme == "file":
        backend = DiskBackend(parsed.path)
    else:
        raise ValueError("Unable to infer backend for url {}".format(url))

    if allow_caching:
        # TODO: construct caching backend and return that.
        pass

    return backend


def pathsplit(url):
    parsed = urllib.parse.urlparse(url)
    return (
        urllib.parse.urlunsplit(
            (parsed.scheme,
             parsed.netloc,
             posixpath.dirname(parsed.path),
             parsed.params,
             parsed.query,
             parsed.fragment),

        ),
        posixpath.basename(parsed.path),
    )


class Reader(object):
    @staticmethod
    def parse_doc(url):
        baseurl, name = pathsplit(url)
        backend = infer_backend(url, allow_caching=False)
        fh = backend.read_file_handle(name, None)
        json_doc = json.load(fh)

        if version.parse(json_doc[TOCKeys.VERSION]) >= version.parse(v0_0_0.VERSION):
            parser = v0_0_0.Reader()
        else:
            raise ValueError("Unrecognized version number")

        return parser.parse(json_doc, baseurl)

    def parse(self, json_doc, baseurl):
        raise NotImplementedError()


class Writer(object):
    @staticmethod
    def write_to_path(imagestack, path, pretty=False, *args, **kwargs):
        document = v0_0_0.Writer().generate_toc(imagestack, path, *args, **kwargs)
        indent = 4 if pretty else None
        with open(path, "w") as fh:
            json.dump(document, fh, indent=indent)

    @staticmethod
    def default_tile_opener(toc_path, tile, ext):
        tile_basename = os.path.splitext(os.path.basename(toc_path))[0]
        return tempfile.NamedTemporaryFile(
            suffix=".{}".format(ext),
            prefix="{}-".format(tile_basename),
            dir=os.path.dirname(toc_path),
            delete=False,
        )

    @staticmethod
    def default_tile_writer(tile, fh):
        tile.write(fh)

    def generate_toc(self, imagestack, path, *args, **kwargs):
        raise NotImplementedError()


class v0_0_0(object):
    VERSION = "0.0.0"

    class Reader(Reader):
        def parse(self, json_doc, baseurl):
            imageslice = ImageSlice(
                json_doc[TOCKeys.DIMENSIONS],
                json_doc.get(TOCKeys.DEFAULT_TILE_SHAPE, None),
                json_doc.get(TOCKeys.DEFAULT_TILE_FORMAT, None),
                json_doc.get(TOCKeys.BASEURL, None),
                json_doc.get(TOCKeys.EXTRAS, None),
            )
            if imageslice.baseurl is not None:
                baseurl = imageslice.baseurl
            backend = infer_backend(baseurl)

            for tile_doc in json_doc[TOCKeys.TILES]:
                name = tile_doc[TileKeys.FILE]
                tile_format = tile_doc.get(TileKeys.TILE_FORMAT, imageslice.default_tile_format)
                if tile_format is None:
                    # Still none :(
                    extension = os.path.splitext(name)[1]
                    tile_format = ImageFormat.find_by_extension(extension).name

                tile = Tile(
                    tile_doc[TileKeys.COORDINATES],
                    tile_doc.get(TileKeys.TILE_SHAPE, None),
                    tile_doc.get(TileKeys.EXTRAS, None),
                )
                tile.set_source_fh_callable(backend.read_file_handle_callable(name, None), tile_format)
                imageslice.add_tile(tile)

            return imageslice

    class Writer(Writer):
        def generate_toc(
                self,
                imagestack,
                path,
                tile_opener=Writer.default_tile_opener,
                tile_writer=Writer.default_tile_writer):
            json_doc = {
                TOCKeys.DIMENSIONS: imagestack.dimensions,
                TOCKeys.TILES: [],
            }
            
            if imagestack.default_tile_shape is not None:
                json_doc[TOCKeys.DEFAULT_TILE_SHAPE] = imagestack.default_tile_shape
            if imagestack.default_tile_format is not None:
                json_doc[TOCKeys.DEFAULT_TILE_SHAPE] = imagestack.default_tile_format.name
            if len(imagestack.extras) != 0:
                json_doc[TOCKeys.EXTRAS] = imagestack.extras

            for tile in imagestack._tiles:
                tiledoc = {
                    TileKeys.COORDINATES: tile.coordinates,
                }

                with tile_opener(path, tile, ImageFormat.NUMPY.file_ext) as tile_fh:
                    tile_writer(tile, tile_fh)
                    tiledoc[TileKeys.FILE] = os.path.basename(tile_fh.name)

                if tile.tile_shape is not None:
                    tiledoc[TileKeys.TILE_SHAPE] = tile.tile_shape
                if tile.tile_format is not None:
                    tiledoc[TileKeys.TILE_FORMAT] = tile.tile_format.name
                if len(tile.extras) != 0:
                    tiledoc[TileKeys.EXTRAS] = tile.extras
                json_doc[TOCKeys.TILES].append(tiledoc)

            return json_doc


class TOCKeys(object):
    VERSION = "version"
    DIMENSIONS = "dimensions"
    DEFAULT_TILE_SHAPE = "default_tile_shape"
    DEFAULT_TILE_FORMAT = "default_tile_format"
    BASEURL = "baseurl"
    TILES = "tiles"
    ZOOM = "zoom"
    EXTRAS = "extras"


class TileKeys(object):
    FILE = "file"
    COORDINATES = "coordinates"
    TILE_SHAPE = "tile_shape"
    TILE_FORMAT = "tile_format"
    EXTRAS = "extras"
