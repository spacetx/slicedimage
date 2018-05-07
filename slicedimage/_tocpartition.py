from __future__ import absolute_import, division, print_function, unicode_literals

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
        for toc in self._tocs:
            if isinstance(toc, TocPartition):
                for subtoc in toc.all_tocs():
                    yield subtoc
            elif isinstance(toc, ImagePartition):
                yield toc

    def tiles(self, filter_fn=lambda _: True):
        result = []
        for toc in self.all_tocs():
            result.extend(toc.tiles(filter_fn))
        return result
