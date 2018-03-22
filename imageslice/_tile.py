from __future__ import absolute_import, division, print_function, unicode_literals

from six import BytesIO

from ._formats import ImageFormat


class Tile(object):
    def __init__(self, coordinates, tile_shape=None, extras=None):
        self._source_fh_callable = None
        self._numpy_array = None
        self.coordinates = coordinates
        self.tile_shape = tile_shape
        self.tile_format = None
        self.extras = {} if extras is None else extras

    def set_numpy_array(self, numpy_array):
        if self.tile_shape is not None:
            assert self.tile_shape == numpy_array.shape

        self._source_fh_callable = None
        self._numpy_array = numpy_array
        self.tile_format = ImageFormat.NUMPY

    def set_source_fh_callable(self, source_fh_callable, tile_format):
        self._source_fh_callable = source_fh_callable
        self._numpy_array = None
        self.tile_format = tile_format

    def write(self, dst_fh):
        """
        Write the contents of this tile out to a given file handle.
        """
        import numpy

        if self._source_fh_callable is not None:
            assert self._numpy_array is None
            with self._source_fh_callable() as src_fh:
                self._numpy_array = self.tile_format.reader_func(src_fh)
            self._source_fh_callable = None
            self.tile_format = ImageFormat.NUMPY

        numpy.save(dst_fh, self._numpy_array)

    def copy(self, dst_fh):
        """
        Write the contents of this tile out to a given file handle, in the original file format provided.
        """
        if self._source_fh_callable is not None:
            assert self._numpy_array is None
            with self._source_fh_callable() as src_fh:
                data = src_fh.read()
                self._numpy_array = self.tile_format.reader_func(BytesIO(data))
                dst_fh.write(data)
            self._source_fh_callable = None
            self.tile_format = ImageFormat.NUMPY
