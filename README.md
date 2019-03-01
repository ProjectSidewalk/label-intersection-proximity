## label-intersection-proximity

Given a point in DC, this tool computes the point's proximity to the end of the nearest OpenStreetMap road segment. This is an approximation for the point's proximity to an intersection. The tool is written in Python 3 using shapely and rtree.

Setup:
```bash
$ pip install -r requirements.txt
```

Usage:
```bash
$ python main.py [lat] [lng]
```

### Understanding the output
The tool outputs two metrics; the first is an absolute distance, in meters, from the (closer) end of the nearest street segment to the point on the segment closest to the input point. The other is a "middleness" metric, expressed as a percentage. It is 0% at both ends of the nearest street segment and 100% at the exact center of the segment. Refer to [this diagram](https://i.imgur.com/QYIM6B0.png) for further detail.

To assist in debugging, a geojson representation of the street segment closest to the input point is also printed.

### Other cities
You can use this tool with other cities by replacing the geojson file in the `input` folder with your own geojson file representing the street network of the city you are interested in.