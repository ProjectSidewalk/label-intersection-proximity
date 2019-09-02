## label-intersection-proximity
**This repository uses Git LFS; ensure you have git-lfs installed on your system if you would like data files to be cloned.**

Given a point, this tool computes the point's proximity to the nearest street intersection, based on an OpenStreetMap road network. The tool is written in Python 3 using shapely and rtree.

Setup:
```bash
$ pip install -r requirements.txt
```

There's a chance that you will get a missing libspatialindex file. Installation instructions are here: https://libspatialindex.org/.
If you're using conda, run `conda install rtree` and you won't get this issue.

Usage:
Create an intersection proximity object, then call `compute_proximity(lat, lng)`. It will
return the result tuple `(absolute_dist_in_meters, middleness_percentage)`.
```python
>>> import intersection_proximity 
>>> city_config = intersection_proximity.default_settings['seattle']
>>> ip = intersection_proximity.IntersectionProximity(city_config)
Building street name->edge name map... Done!
Finding street intersections... Done!
Generating street segments... Done!
>>> ip.compute_proximity(47.658668, -122.349636)
(32.59994951126359, 55.911741589344274)
>>> ip.compute_proximity(47.658717, -122.349929)
(7.865804175314517, 13.490546455238123)
```

### Understanding the output
The tool outputs two metrics; the first is an absolute distance, in meters, from the (closer) end of the nearest street segment to the point on the segment closest to the input point. The other is a "middleness" metric, expressed as a percentage. It is 0% at both ends of the nearest street segment and 100% at the exact center of the segment. Refer to [this diagram](https://i.imgur.com/QYIM6B0.png) for further detail.

To assist in debugging, a geojson representation of the street segment closest to the input point can be printed; simply
uncomment the debug print lines in `intersection_proximity.py`.

### Other cities
To use another city, just pass in a different `city_config` dictionary. These are structured as so:

```
{
    'street_network_filename': 'roads-for-cv-seattle.geojson',
    'osm_way_ids': 'osm-way-ids-seattle.csv',
    'road_network_dump': 'seattle-roads.dbf',
}
```

'osm-way-ids-seattle.csv' and seattle-roads.dbf can be downloaded from OpenStreetMap. The latter comes from the city's Shapefile.

