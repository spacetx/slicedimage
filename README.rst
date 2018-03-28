===================
Sliced imaging data
===================

Background
==========

If we want to store imaging data on the cloud and allow scientists to experiment
with this data with interactive local tools (e.g., Jupyter notebooks), we should
provide an easy interface to retrieve this data.  We should future-proof this
model for extremely large images with multiple dimensions, where users may want
to pull slices of this data without having to download the entire image.

Proposal
--------

Images should be stored in a tiled format such that ranged requests can be used
to efficiently fetch slices of the data.  The most obvious format is
2-dimensional tiles, with additional dimensions written to separate files.  Each
set should be described in a manifest file indicating the constituent files and
where in the n-dimensional space each tile represents.

There should be a python API that allows users to point at a manifest, ranges
across multiple dimensions, and yields the data in numpy format.  The python API
should retrieve the manifest, calculate the objects needed, fetch them in
parallel, decode them, and slice out the data needed.

Format
------

Each image set should have a json document that serves as the table of contents
(TOC) describing the tiles that make up the set.

.. _TOC:

TOC
~~~

The TOC should have the following fields:

===================  ======  ========  =========================================
Field Name           Type    Required  Description
-------------------  ------  --------  -----------------------------------------
version              string  Yes       Semantic versioning of the file format.
dimensions           list    Yes       Names of the dimensions.  Dimensions must
                                       include `x` and `y`.
tiles                dict    Yes       See Tiles_
default_tile_shape   tuple   No        Default pixel dimensions of a tile,
                                       ordered as x, y, and optionally, z.
default_tile_format  string  No        Default file format of the tiles.
zoom                 dict    No        See Zoom_
extras               dict    No        Additional application-specific payload.  The
                                       vocabulary and the schema are uncontrolled.
===================  ======  ========  =========================================

.. _Tiles:

Tiles
~~~~~

Each item in the tiles section describes a file:

============  ======  ========  ================================================
Field Name    Type    Required  Description
------------  ------  --------  ------------------------------------------------
file          string  Yes       Relative path to the file.
coordinates   dict    Yes       Maps a dimension name (specified in the TOC_) to
                                either a single dimension value, or a tuple
                                specifying the range for that dimension.  Note
                                that this does not have to be the discrete
                                dimensions like pixels or the z-order, though it
                                can be.  The `x` and `y` coordinates must be
                                provided as ranges.
tile_shape    tuple   No        Pixel dimensions of a tile, ordered as x, y, and
                                optionally, z.  If this is not provided, it
                                defaults to `default_tile_shape` in the TOC_).
                                If neither is provided, the tile shape is
                                inferred from actual file.
tile_format   string  No        File format of the tile.  If this is not
                                provided, it defaults to `default_tile_format`
                                in the TOC_).  If neither is provided, the tile
                                format is inferred from actual file.
sha256        string  No        SHA256 checksum of the tile data.
extras        dict    No        Additional application-specific payload.  The
                                vocabulary and the schema are uncontrolled.
============  ======  ========  ================================================

.. _Zoom:

Zoom
~~~~
