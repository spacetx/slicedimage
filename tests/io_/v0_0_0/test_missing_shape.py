import codecs
import json
import tempfile
import unittest
import warnings
from pathlib import Path

import numpy as np

import slicedimage
from slicedimage._dimensions import DimensionNames
from slicedimage.io._keys import TileKeys, TileSetKeys

baseurl = Path(__file__).parent.resolve().as_uri()


class TestMissingShape(unittest.TestCase):
    def test_tileset_without_shapes(self):
        image = slicedimage.TileSet(
            [DimensionNames.X, DimensionNames.Y, "ch", "hyb"],
            {'ch': 2, 'hyb': 2},
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

                # remove the shape information from the tiles.
                for tile in partition_doc[TileSetKeys.TILES]:
                    del tile[TileKeys.TILE_SHAPE]

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
                    with warnings.catch_warnings(record=True) as w:
                        # Cause all warnings to always be triggered.  Duplicate warnings are
                        # normally suppressed.
                        warnings.simplefilter("always")

                        tile_shape = tiles[0].tile_shape

                        self.assertEqual(tile_shape, {DimensionNames.Y: 120, DimensionNames.X: 80})
                        self.assertEqual(len(w), 1)
                        self.assertIn("Decoding tile just to obtain shape", str(w[0].message))
