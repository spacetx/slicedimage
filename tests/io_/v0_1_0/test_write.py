import codecs
import hashlib
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np
from imageio import imwrite
from slicedimage._compat import fspath

import slicedimage
from slicedimage import ImageFormat
from slicedimage._dimensions import DimensionNames
from tests.utils import build_skeleton_manifest

if sys.platform == "win32":
    from winmagic import magic
else:
    import magic

baseurl = Path(__file__).parent.resolve().as_uri()


class TestWrite(unittest.TestCase):
    def test_write_tileset(self):
        image = slicedimage.TileSet(
            [DimensionNames.X, DimensionNames.Y, "ch", "hyb"],
            {'ch': 2, 'hyb': 2},
            {DimensionNames.Y: 120, DimensionNames.X: 80},
        )

        for hyb in range(2):
            for ch in range(2):
                tile = slicedimage.Tile(
                    {
                        DimensionNames.X: (0.0, 0.01),
                        DimensionNames.Y: (0.0, 0.01),
                    },
                    {
                        'hyb': hyb,
                        'ch': ch,
                    },
                )
                tile.numpy_array = np.zeros((120, 80))
                tile.numpy_array[hyb, ch] = 1
                image.add_tile(tile)

        with tempfile.TemporaryDirectory() as tempdir:
            with tempfile.NamedTemporaryFile(
                    suffix=".json", dir=tempdir, delete=False) as partition_file:
                partition_file_path = Path(partition_file.name)
                partition_doc = slicedimage.v0_0_0.Writer().generate_partition_document(
                    image, partition_file_path.as_uri())
                writer = codecs.getwriter("utf-8")
                json.dump(partition_doc, writer(partition_file))

            loaded = slicedimage.Reader.parse_doc(
                partition_file_path.name, partition_file_path.parent.as_uri())

            for hyb in range(2):
                for ch in range(2):
                    tiles = [_tile
                             for _tile in loaded.tiles(
                                 lambda tile: (
                                     tile.indices['hyb'] == hyb
                                     and tile.indices['ch'] == ch))]

                    self.assertEqual(len(tiles), 1)

                    expected = np.zeros((100, 100))
                    expected[hyb, ch] = 1

                    self.assertEqual(tiles[0].numpy_array.all(), expected.all())
                    self.assertIsNotNone(tiles[0].sha256)

    def test_write_collection(self):
        image = slicedimage.TileSet(
            [DimensionNames.X, DimensionNames.Y, "ch", "hyb"],
            {'ch': 2, 'hyb': 2},
            {DimensionNames.Y: 120, DimensionNames.X: 80},
        )

        for hyb in range(2):
            for ch in range(2):
                tile = slicedimage.Tile(
                    {
                        DimensionNames.X: (0.0, 0.01),
                        DimensionNames.Y: (0.0, 0.01),
                    },
                    {
                        'hyb': hyb,
                        'ch': ch,
                    },
                )
                tile.numpy_array = np.zeros((120, 80))
                tile.numpy_array[hyb, ch] = 1
                image.add_tile(tile)
        collection = slicedimage.Collection()
        collection.add_partition("fov002", image)

        with tempfile.TemporaryDirectory() as tempdir:
            with tempfile.NamedTemporaryFile(
                    suffix=".json", dir=tempdir, delete=False) as partition_file:
                partition_file_path = Path(partition_file.name)
                partition_doc = slicedimage.v0_0_0.Writer().generate_partition_document(
                    collection, partition_file_path.as_uri())
                writer = codecs.getwriter("utf-8")
                json.dump(partition_doc, writer(partition_file))

            loaded = slicedimage.Reader.parse_doc(
                partition_file_path.name, partition_file_path.parent.as_uri())

            for hyb in range(2):
                for ch in range(2):
                    tiles = [_tile
                             for _tile in loaded.tiles(
                                 lambda tile: (
                                     tile.indices['hyb'] == hyb
                                     and tile.indices['ch'] == ch))]

                    self.assertEqual(len(tiles), 1)

                    expected = np.zeros((100, 100))
                    expected[hyb, ch] = 1

                    self.assertEqual(tiles[0].numpy_array.all(), expected.all())
                    self.assertIsNotNone(tiles[0].sha256)

    def test_checksum_on_write(self):
        """
        Generate a tileset consisting of a single TIFF tile.  Load it and then write it back out
        as a numpy tile, which should be written with different checksums.  Then verify that the
        numpy version can load without an error.
        """
        # write the tiff file
        with tempfile.TemporaryDirectory() as tempdir:
            tempdir_path = Path(tempdir)
            data = np.random.randint(0, 65535, size=(120, 80), dtype=np.uint16)
            file_path = os.path.join(tempdir, "tile.tiff")
            imwrite(file_path, data, format="tiff")
            with open(file_path, "rb") as fh:
                checksum = hashlib.sha256(fh.read()).hexdigest()

            manifest = build_skeleton_manifest()
            manifest['tiles'].append(
                {
                    "coordinates": {
                        DimensionNames.X.value: [
                            0.0,
                            0.0001,
                        ],
                        DimensionNames.Y.value: [
                            0.0,
                            0.0001,
                        ]
                    },
                    "indices": {
                        "hyb": 0,
                        "ch": 0,
                    },
                    "file": "tile.tiff",
                    "format": "tiff",
                    "sha256": checksum,
                },
            )
            with open(fspath(tempdir_path / "tileset.json"), "w") as fh:
                fh.write(json.dumps(manifest))

            image = slicedimage.Reader.parse_doc(
                "tileset.json",
                tempdir_path.as_uri(),
                {"cache": {"size_limit": 0}},  # disabled
            )

            with tempfile.TemporaryDirectory() as output_tempdir:
                with tempfile.NamedTemporaryFile(
                        suffix=".json", dir=output_tempdir, delete=False) as partition_file:
                    partition_file_path = Path(partition_file.name)
                    partition_doc = slicedimage.v0_0_0.Writer().generate_partition_document(
                        image, partition_file_path.as_uri())

                    writer = codecs.getwriter("utf-8")
                    json.dump(partition_doc, writer(partition_file))
                    partition_file.flush()

                loaded = slicedimage.Reader.parse_doc(
                    partition_file_path.name, partition_file_path.parent.as_uri())

                loaded.tiles()[0].numpy_array

    def test_write_tiff(self):
        image = slicedimage.TileSet(
            dimensions=[DimensionNames.X, DimensionNames.Y, "ch", "hyb"],
            shape={'ch': 2, 'hyb': 2},
            default_tile_shape={DimensionNames.Y: 120, DimensionNames.X: 80},
        )

        for hyb in range(2):
            for ch in range(2):
                tile = slicedimage.Tile(
                    coordinates={
                        DimensionNames.X: (0.0, 0.01),
                        DimensionNames.Y: (0.0, 0.01),
                    },
                    indices={
                        'hyb': hyb,
                        'ch': ch,
                    },
                )
                tile.numpy_array = np.zeros((120, 80), dtype=np.uint32)
                tile.numpy_array[hyb, ch] = 1
                image.add_tile(tile)

        with tempfile.TemporaryDirectory() as tempdir:
            with tempfile.NamedTemporaryFile(
                    suffix=".json", dir=tempdir, delete=False) as partition_file:
                partition_file_path = Path(partition_file.name)
                # create the tileset and save it.
                partition_doc = slicedimage.v0_0_0.Writer().generate_partition_document(
                    image, partition_file_path.as_uri(), tile_format=ImageFormat.TIFF)
                writer = codecs.getwriter("utf-8")
                json.dump(partition_doc, writer(partition_file))
                partition_file.flush()

            # construct a URL to the tileset we wrote, and load the tileset.
            loaded = slicedimage.Reader.parse_doc(
                partition_file_path.name, partition_file_path.parent.as_uri())

            # verify that we wrote some tiffs, and all the tiffs we wrote actually identify as
            # tiffs.
            tifffiles = list(Path(tempdir).glob("*.tiff"))
            assert len(tifffiles) > 0
            for tifffile in tifffiles:
                filetype = magic.from_file(fspath(tifffile))
                assert filetype.lower().startswith("tiff")

            # compare the tiles we loaded to the tiles we set up.
            for hyb in range(2):
                for ch in range(2):
                    tiles = [_tile
                             for _tile in loaded.tiles(
                                 lambda tile: (
                                     tile.indices['hyb'] == hyb
                                     and tile.indices['ch'] == ch))]

                    self.assertEqual(len(tiles), 1)

                    expected = np.zeros((120, 80), dtype=np.uint32)
                    expected[hyb, ch] = 1

                    self.assertEqual(tiles[0].numpy_array.all(), expected.all())
                    self.assertIsNotNone(tiles[0].sha256)

    def test_write_png(self):
        image = slicedimage.TileSet(
            dimensions=[DimensionNames.X, DimensionNames.Y, "ch", "hyb"],
            shape={'ch': 2, 'hyb': 2},
            default_tile_shape={DimensionNames.Y: 120, DimensionNames.X: 80},
        )

        for hyb in range(2):
            for ch in range(2):
                tile = slicedimage.Tile(
                    coordinates={
                        DimensionNames.X: (0.0, 0.01),
                        DimensionNames.Y: (0.0, 0.01),
                    },
                    indices={
                        'hyb': hyb,
                        'ch': ch,
                    },
                )
                tile.numpy_array = np.zeros((120, 80), dtype=np.uint32)
                tile.numpy_array[hyb, ch] = 1
                image.add_tile(tile)

        with tempfile.TemporaryDirectory() as tempdir:
            with tempfile.NamedTemporaryFile(
                    suffix=".json", dir=tempdir, delete=False) as partition_file:
                partition_file_path = Path(partition_file.name)
                # create the tileset and save it.
                partition_doc = slicedimage.v0_0_0.Writer().generate_partition_document(
                    image, partition_file_path.as_uri(), tile_format=ImageFormat.PNG)
                writer = codecs.getwriter("utf-8")
                json.dump(partition_doc, writer(partition_file))
                partition_file.flush()

            # construct a URL to the tileset we wrote, and load the tileset.
            loaded = slicedimage.Reader.parse_doc(
                partition_file_path.name, partition_file_path.parent.as_uri())

            # verify that we wrote some pngs, and all the pngs we wrote actually identify as pngs.
            pngfiles = list(Path(tempdir).glob("*.png"))
            assert len(pngfiles) > 0
            for pngfile in pngfiles:
                filetype = magic.from_file(fspath(pngfile))
                assert filetype.lower().startswith("png")

            # compare the tiles we loaded to the tiles we set up.
            for hyb in range(2):
                for ch in range(2):
                    tiles = [_tile
                             for _tile in loaded.tiles(
                                 lambda tile: (
                                     tile.indices['hyb'] == hyb
                                     and tile.indices['ch'] == ch))]

                    self.assertEqual(len(tiles), 1)

                    expected = np.zeros((120, 80), dtype=np.uint32)
                    expected[hyb, ch] = 1

                    self.assertEqual(tiles[0].numpy_array.all(), expected.all())
                    self.assertIsNotNone(tiles[0].sha256)

    def test_multi_directory_write_collection(self):
        """Test that we can write collections with a directory hierarchy."""
        image = slicedimage.TileSet(
            ["x", "y", "ch", "hyb"],
            {'ch': 2, 'hyb': 2},
            {'y': 120, 'x': 80},
        )

        for hyb in range(2):
            for ch in range(2):
                tile = slicedimage.Tile(
                    {
                        'x': (0.0, 0.01),
                        'y': (0.0, 0.01),
                    },
                    {
                        'hyb': hyb,
                        'ch': ch,
                    },
                )
                tile.numpy_array = np.zeros((120, 80))
                tile.numpy_array[hyb, ch] = 1
                image.add_tile(tile)
        collection = slicedimage.Collection()
        collection.add_partition("fov002", image)

        def partition_path_generator(parent_toc_path, toc_name):
            directory = parent_toc_path.parent / toc_name
            directory.mkdir()
            return directory / "{}.json".format(parent_toc_path.stem)

        def tile_opener(tileset_path, tile, ext):
            directory_path = tempfile.mkdtemp(dir=str(tileset_path.parent))
            return tempfile.NamedTemporaryFile(
                suffix=".{}".format(ext),
                prefix="{}-".format(tileset_path.stem),
                dir=directory_path,
                delete=False,
            )

        with tempfile.TemporaryDirectory() as tempdir:
            with tempfile.NamedTemporaryFile(
                    suffix=".json", dir=tempdir, delete=False) as partition_file:
                partition_file_path = Path(partition_file.name)
                partition_doc = slicedimage.v0_0_0.Writer().generate_partition_document(
                    collection, partition_file_path.as_uri(),
                    partition_path_generator=partition_path_generator,
                    tile_opener=tile_opener,
                )
                writer = codecs.getwriter("utf-8")
                json.dump(partition_doc, writer(partition_file))

            loaded = slicedimage.Reader.parse_doc(
                partition_file_path.name, partition_file_path.parent.as_uri())

            for hyb in range(2):
                for ch in range(2):
                    tiles = [
                        _tile
                        for _tile in loaded.tiles(
                            lambda tile: (
                                tile.indices['hyb'] == hyb
                                and tile.indices['ch'] == ch))]

                    self.assertEqual(len(tiles), 1)

                    expected = np.zeros((100, 100))
                    expected[hyb, ch] = 1

                    self.assertEqual(tiles[0].numpy_array.all(), expected.all())
                    self.assertIsNotNone(tiles[0].sha256)


if __name__ == "__main__":
    unittest.main()
