from copy import copy

from ._tile import Tile


class ImagePartition(object):
    def __init__(self, dimensions, shape, default_tile_shape=None, default_tile_format=None, extras=None):
        self.dimensions = tuple(dimensions)
        self.shape = shape
        self.default_tile_shape = tuple(default_tile_shape)
        self.default_tile_format = None if default_tile_format is None else default_tile_format
        self.extras = {} if extras is None else extras
        self._tiles = []

        self._discrete_dimensions = set()

    def validate(self):
        pass

    def add_tile(self, tile):
        self._tiles.append(tile)

    def filter_tiles(self, filter_fn=None):
        if filter_fn is None:
            return self._tiles
        return [tile for tile in self._tiles if filter_fn(tile)]

    def get_dimension_shape(self, dimension_name):
        return self.shape[dimension_name]

    def clone_shape(self):
        """
        Builds and returns a clone with the same tile structure as this ImagePartition.  The clone's tiles will not
        contain any image data.
        """
        result = ImagePartition(
            copy(self.dimensions),
            copy(self.shape),
            default_tile_shape=copy(self.default_tile_shape),
            default_tile_format=copy(self.default_tile_format),
            extras=copy(self.extras)
        )

        for tile in self._tiles:
            tile_copy = Tile(
                copy(tile.coordinates),
                copy(tile.indices),
                tile_shape=copy(tile.tile_shape),
                sha256=copy(tile.sha256),
                extras=copy(tile.extras),
            )
            tile_copy._name_or_url = tile._name_or_url
            result.add_tile(tile_copy)

        return result
