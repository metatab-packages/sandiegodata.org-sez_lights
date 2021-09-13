# SEZ Light Buffers and Rings

This dataset provides sums of the pixels values in the [nighttime lights data](https://data.sandiegodata.org/dataset/figshare-com-harmonized-ntl/) in regions around the SEZs from the [World Bank's SEZ dataset](https://data.sandiegodata.org/dataset/worldbank-org-sez/). THe
buffers are a circle for a specified radius around each SEZ, and the rings have
a minimum radius of the specific radius, and a maximum radius of (1+sqrt(2))
times larger, so the area of the ring for a radius is equal to the area of the
buffer circle.

Here is an example of the buffer and ring for an SEZ in South Korea:

<img src="http://library.metatab.org/sandiegodata.org-sez_lights-1.1.2/doc/ring_raster.png" width=720>


This file can be joined to the SEZ data on the ``unique_id`` column. For each SEZ and year of the NTL data, this file includes the sum of the pixel values from the NTL rasters for both the ring and the buffer, and the radius specified in the ``radius`` column. The ``*_count`` column is the number of non-null pixels in each region. 
 
