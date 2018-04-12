from copy import copy

from ._imagepartition import ImagePartition


class TocPartition(object):
    def __init__(self, extras=None):
        self.extras = extras
        self._tocs = list()

    def validate(self):
        pass

    def add_toc(self, toc):
        self._tocs.append(toc)

    def all_tocs(self):
        """Return all TOCs referenced by this TOC, directly or indirectly."""
        result = []
        for toc in self._tocs:
            if isinstance(toc, TocPartition):
                result.extend(toc.all_tocs())
            elif isinstance(toc, ImagePartition):
                result.append(toc)
        return result

    def get_matching_tiles(self, matcher=None):
        result = []
        for toc in self.all_tocs():
            result.extend(toc.get_matching_tiles(matcher))
        return result

    def clone_shape(self):
        """
        Builds and returns a clone with the same tile structure as this TocPartition.  The clone's tiles will not
        contain any image data.
        """
        result = TocPartition(extras=copy(self.extras))
        for toc in self._tocs:
            clone = toc.clone_shape()
            clone._name_or_url = toc._name_or_url
            result.add_toc(clone)

        return result
