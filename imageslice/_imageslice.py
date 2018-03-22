from __future__ import absolute_import, division, print_function, unicode_literals

import numbers

from ._formats import ImageFormat


class ImageSlice(object):
    def __init__(self, dimensions, default_tile_shape=None, default_tile_format=None, baseurl=None, extras=None):
        self.dimensions = dimensions
        self.default_tile_shape = default_tile_shape
        self.default_tile_format = None if default_tile_format is None else ImageFormat[default_tile_format]
        self.baseurl = baseurl
        self.extras = {} if extras is None else extras
        self._tiles = []

        self._discrete_dimensions = set()

    def validate(self):
        pass

    def add_tile(self, tile):
        self._tiles.append(tile)

    def get_matching_tiles(self, matcher):
        return [tile for tile in self._tiles if matcher(tile)]

    def get_dimension_shape(self, dimension_name):
        encountered_values = set()
        for tile in self._tiles:
            for coordinates in tile.coordinates:
                coordinate_value = coordinates[dimension_name]
                if not isinstance(coordinate_value, numbers.Numbers):
                    raise ValueError("get_dimension_shape can only be called on dimensions with only discrete values")
                encountered_values.add(coordinate_value)
        return len(encountered_values)
