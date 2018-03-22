from __future__ import absolute_import, division, print_function, unicode_literals

import numbers
from copy import copy

from ._tile import Tile


class SlicedImage(object):
    def __init__(self, dimensions, default_tile_shape=None, default_tile_format=None, baseurl=None, extras=None):
        self.dimensions = dimensions
        self.default_tile_shape = default_tile_shape
        self.default_tile_format = None if default_tile_format is None else default_tile_format
        self.baseurl = baseurl
        self.extras = {} if extras is None else extras
        self._tiles = []

        self._discrete_dimensions = set()

    def validate(self):
        pass

    def add_tile(self, tile):
        self._tiles.append(tile)

    def get_matching_tiles(self, matcher=None):
        if matcher is None:
            return self._tiles
        return [tile for tile in self._tiles if matcher(tile)]

    def get_dimension_shape(self, dimension_name):
        encountered_values = set()
        for tile in self._tiles:
            coordinate_value = tile.coordinates[dimension_name]
            if not isinstance(coordinate_value, numbers.Number):
                raise ValueError("get_dimension_shape can only be called on dimensions with only discrete values")
            encountered_values.add(coordinate_value)
        return len(encountered_values)

    def get_dimension_map(self, dimension_name):
        encountered_values = set()
        for tile in self._tiles:
            coordinate_value = tile.coordinates[dimension_name]
            if isinstance(coordinate_value, list):
                coordinate_value = tuple(coordinate_value)
            encountered_values.add(coordinate_value)
        encountered_values_sorted = sorted(encountered_values)
        return (
            encountered_values_sorted,
            {coordinate_value: idx for idx, coordinate_value in enumerate(encountered_values_sorted)},
        )

    def clone(self):
        result = SlicedImage(
            copy(self.dimensions),
            copy(self.default_tile_shape),
            copy(self.default_tile_format),
            copy(self.baseurl),
            copy(self.extras)
        )

        for tile in self._tiles:
            tile_copy = Tile(
                copy(tile.coordinates),
                copy(tile.tile_shape),
                copy(tile.extras)
            )
            result.add_tile(tile_copy)

        return result
