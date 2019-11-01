import collections
import json
import os
import tempfile
import unittest
from pathlib import Path

import imageio
import numpy as np
from slicedimage._compat import fspath

import slicedimage
from slicedimage._dimensions import DimensionNames
from tests.utils import build_skeleton_manifest

baseurl = Path(__file__).parent.resolve().as_uri()


class TestReader(unittest.TestCase):
    def test_read_tileset(self):
        result = slicedimage.Reader.parse_doc("tileset.json", baseurl)
        self.assertIsInstance(result, slicedimage.TileSet)
        self.assertEqual(result.shape, {'hyb': 4, 'ch': 4})
        self._verify_tiles(result.tiles())

    def test_read_collection(self):
        result = slicedimage.Reader.parse_doc("collection_l1.json", baseurl)
        self.assertIsInstance(result, slicedimage.Collection)
        tileset = result.find_tileset("fov_001")
        self.assertEqual(tileset.shape, {'hyb': 4, 'ch': 4})
        self._verify_tiles(result.tiles())

    def test_read_multilevel_collection(self):
        result = slicedimage.Reader.parse_doc("collection_l2.json", baseurl)
        self.assertIsInstance(result, slicedimage.Collection)
        tileset = result.find_tileset("fov_001")
        self.assertEqual(tileset.shape, {'hyb': 4, 'ch': 4})
        self._verify_tiles(result.tiles())

    def _verify_tiles(self, tile_generator):
        tiles = [tile for tile in tile_generator]
        self.assertEqual(len(tiles), 16)

        for hyb in range(4):
            for ch in range(4):
                for tile in tiles:
                    if tile.indices['hyb'] == hyb and tile.indices['ch'] == ch:
                        break
                else:
                    self.fail("Couldn't find tile of hyb {} ch {}".format(hyb, ch))

        for tile in tiles:
            for value in tile.coordinates.values():
                self.assertTrue(isinstance(value, collections.Hashable))
            for value in tile.indices.values():
                self.assertTrue(isinstance(value, collections.Hashable))


class TestFormats(unittest.TestCase):
    def test_tiff(self):
        """
        Generate a tileset consisting of a single TIFF tile, and then read it.
        """
        with tempfile.TemporaryDirectory() as tempdir:
            tempdir_path = Path(tempdir)
            # write the tiff file
            data = np.random.randint(0, 65535, size=(120, 80), dtype=np.uint16)
            imageio.imwrite(os.path.join(tempdir, "tile.tiff"), data, format="tiff")

            # TODO: (ttung) We should really be producing a tileset programmatically and writing it
            # disk.  However, our current write path only produces numpy output files.
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
                },
            )
            with open(fspath(tempdir_path / "tileset.json"), "w") as fh:
                fh.write(json.dumps(manifest))

            result = slicedimage.Reader.parse_doc("tileset.json", tempdir_path.as_uri())

            self.assertTrue(np.array_equal(list(result.tiles())[0].numpy_array, data))

    def test_png(self):
        """
        Generate a tileset consisting of a single PNG tile, and then read it.
        """
        with tempfile.TemporaryDirectory() as tempdir:
            tempdir_path = Path(tempdir)
            # write the tiff file
            data = np.random.randint(0, 65535, size=(120, 80), dtype=np.uint16)
            imageio.imwrite(os.path.join(tempdir, "tile.png"), data)

            # TODO: (ttung) We should really be producing a tileset programmatically and writing it
            # disk.  However, our current write path only produces numpy output files.
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
                    "file": "tile.png",
                    "format": "PNG",
                },
            )
            with open(fspath(tempdir_path / "tileset.json"), "w") as fh:
                fh.write(json.dumps(manifest))

            result = slicedimage.Reader.parse_doc("tileset.json", tempdir_path.as_uri())

            self.assertTrue(np.array_equal(list(result.tiles())[0].numpy_array, data))

    def test_numpy(self):
        """
        Generate a tileset consisting of a single TIFF tile, and then read it.
        """
        image = slicedimage.TileSet(
            [DimensionNames.X, DimensionNames.Y, "ch", "hyb"],
            {'ch': 1, 'hyb': 1},
            {DimensionNames.Y: 120, DimensionNames.X: 80},
        )

        tile = slicedimage.Tile(
            {
                DimensionNames.X: (0.0, 0.01),
                DimensionNames.Y: (0.0, 0.01),
            },
            {
                'hyb': 0,
                'ch': 0,
            },
        )
        tile.numpy_array = np.random.randint(0, 65535, size=(120, 80), dtype=np.uint16)
        image.add_tile(tile)

        with tempfile.TemporaryDirectory() as tempdir:
            tempdir_path = Path(tempdir)
            partition_file_path = tempdir_path / "tileset.json"
            partition_doc = slicedimage.v0_0_0.Writer().generate_partition_document(
                image, partition_file_path.as_uri())
            with open(fspath(partition_file_path), "w") as fh:
                json.dump(partition_doc, fh)

            result = slicedimage.Reader.parse_doc("tileset.json", tempdir_path.as_uri())

            self.assertTrue(np.array_equal(list(result.tiles())[0].numpy_array, tile.numpy_array))


if __name__ == "__main__":
    unittest.main()
