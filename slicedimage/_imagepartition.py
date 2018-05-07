from __future__ import absolute_import, division, print_function, unicode_literals


from ._typeformatting import format_imagepartition_dimensions, format_imagepartition_shape


class ImagePartition(object):
    def __init__(self, dimensions, shape, default_tile_shape=None, default_tile_format=None, extras=None):
        self.dimensions = format_imagepartition_dimensions(dimensions)
        self.shape = format_imagepartition_shape(shape)
        self.default_tile_shape = tuple() if default_tile_shape is None else tuple(default_tile_shape)
        self.default_tile_format = default_tile_format
        self.extras = {} if extras is None else extras
        self._tiles = []

        self._discrete_dimensions = set()

    def validate(self):
        raise NotImplementedError()

    def add_tile(self, tile):
        self._tiles.append(tile)

    def tiles(self, filter_fn=lambda _: True):
        """
        Return the tiles in this image partition.  If a filter_fn is provided, only the tiles for which filter_fn
        returns True are returned.
        """
        for tile in self._tiles:
            if filter_fn(tile):
                yield tile

    def get_dimension_shape(self, dimension_name):
        return self.shape[dimension_name]
