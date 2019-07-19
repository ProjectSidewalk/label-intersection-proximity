import math
from shapely.geometry import Polygon, LineString, Point
import geojson
from shapely.ops import transform
from functools import partial
import pyproj
from .preprocessing import make_street_network_index
from .settings import *

# Finding line closest to point helper functions
# From: https://stackoverflow.com/questions/46170577/
# find-closest-line-to-each-point-on-big-dataset-possibly-using-shapely-and-rtree

# MIN_SIZE should be a vaule such that if you build a box centered in each
# point with edges of size 2*MIN_SIZE, you know a priori that at least one
# segment is intersected with the box. Otherwise, you could get an inexact
# solution, there is an exception checking this, though.


def distance(a, b):
    return math.sqrt((a[0]-b[0])**2 + (a[1]-b[1])**2)


def get_distance(apoint, segment):
    a = apoint
    b, c = segment
    # t = <a-b, c-b>/|c-b|**2
    # because p(a) = t*(c-b)+b is the ortogonal projection of vector a
    # over the rectline that includes the points b and c.
    t = (a[0]-b[0])*(c[0]-b[0]) + (a[1]-b[1])*(c[1]-b[1])
    t = t / ( (c[0]-b[0])**2 + (c[1]-b[1])**2 )
    # Only if t 0 <= t <= 1 the projection is in the interior of
    # segment b-c, and it is the point that minimize the distance
    # (by pitagoras theorem).
    if 0 < t < 1:
        pcoords = (t*(c[0]-b[0])+b[0], t*(c[1]-b[1])+b[1])
        dmin = distance(a, pcoords)
        return pcoords, dmin
    elif t <= 0:
        return b, distance(a, b)
    elif 1 <= t:
        return c, distance(a, c)


def get_closest_line_to_each_point(idx, points):
    """
    Get a street segment closest to each point in a list
    :param idx: street network index
    :param points: List of points
    :return: list of closest segments
    """
    result = {}
    for p in points:
        pbox = (p[0]-MIN_SIZE, p[1]-MIN_SIZE, p[0]+MIN_SIZE, p[1]+MIN_SIZE)
        hits = idx.intersection(pbox, objects='raw')
        d = INFTY
        s = None
        for h in hits:
            nearest_p, new_d = get_distance(p, h[1])
            if d >= new_d:
                d = new_d
                s = (h[0], h[1], nearest_p, new_d)
        result[p] = s
        # print(s)

        # some checking you could remove after you adjust the constants
        if s == None:
            raise Exception("It seems INFTY is not big enough.")

        pboxpol = ( (pbox[0], pbox[1]), (pbox[2], pbox[1]),
                    (pbox[2], pbox[3]), (pbox[0], pbox[3]) )
        if not Polygon(pboxpol).intersects(LineString(s[1])):
            msg = "It seems MIN_SIZE is not big enough. "
            msg += "You could get inexact solutions if remove this exception."
            raise Exception(msg)

    return result

######### Other helper functions ############


def extract_street_coords_from_geojson(street):
    """
    Returns tuple mapping street edge id to a list of coordinate tuples
    :param street:
    :return: Ex. ('edge_id', [(5,6),(7,8)])
    """
    edge_id = str(street['properties']['street_edge_id'])
    coords_generator = geojson.utils.coords(street)
    coords_list = []
    for c in coords_generator:
        coords_list.append(c)
    return edge_id, coords_list


def cut(line, distance):
    """
    Cuts a line in two at a distance from its starting point
    https://stackoverflow.com/questions/50332273/shapely-split-linestring-at-arbitrary-point-along-edge
    :param line:
    :param distance:
    :return:
    """
    if distance <= 0.0 or distance >= line.length:
        return [LineString(line)]
    coords = list(line.coords)
    for i, p in enumerate(coords):
        pd = line.project(Point(p))
        if pd == distance:
            return [
                LineString(coords[:i+1]),
                LineString(coords[i:])]
        if pd > distance:
            cp = line.interpolate(distance)
            return [
                LineString(coords[:i] + [(cp.x, cp.y)]),
                LineString([(cp.x, cp.y)] + coords[i:])]

# End of helper functions
# --------------------------------------------


def compute_proximity(label_lat, label_lng, debug=False):
    """
    Compute the intersection proximity, given the latitude and longitude of a label.
    :param label_lat:
    :param label_lng:
    :return: A tuple (distance to intersection, middleness percent)
    """
    global street_network_index
    global real_segments
    # Index the street network if not done yet
    if street_network_index is None:
        street_network_index, real_segments = make_street_network_index(settings['seattle']['real_segments_output_filename'])

    # Points to compute results for, in (lng, lat) form
    # Right now only the first point in this list is processed
    points = [(label_lng, label_lat)]

    closest_line_for_each_point = get_closest_line_to_each_point(street_network_index, points)

    # Just process the first point for now. Get the coords of line closest to first point.
    line_coords = list(closest_line_for_each_point[points[0]][1])

    # Also get the point on the line that is closest to the label coordinate
    closest_point_on_line_coords = closest_line_for_each_point[points[0]][2]
    closest_point_on_line = Point(closest_point_on_line_coords[0], closest_point_on_line_coords[1])

    # For convenience, the same line coords in a format that doesn't use tuples
    line_coords_as_list = []
    for coord in line_coords:
        line_coords_as_list.append(list(coord))

    # Turn the line coords into a shapley line
    # shapely_line = LineString(ast.literal_eval(str(line_coords_as_list)))
    shapely_line = real_segments[closest_line_for_each_point[points[0]][0]]

    line_length = shapely_line.length
    line_start_to_closest_pt_len = shapely_line.project(closest_point_on_line)

    # Position of label on the segment expressed as a fraction between 0 and 1
    point_position_fraction = line_start_to_closest_pt_len / line_length
    # print("Position of label along segment expressed as a fraction (0-1): {}".format(point_position_fraction))

    # Position of label on the segment expressed as a percentage from 0 to 100,
    # where 50 represents the middle of the segment and 0 represents both ends
    middleness_pct = 100 * (min(abs(point_position_fraction - 0),abs(point_position_fraction-1)) / 0.5)
    # print("Middleness percentage (0-100): {}".format(middleness_pct))

    # Get the two segments on either side of the label to compute their lengths
    cut_point = shapely_line.project(closest_point_on_line)
    split_segments = cut(shapely_line, line_start_to_closest_pt_len)

    # We want to find lengths of the two segments in real-world units (meters) rather
    # than degrees, so they need to be projected
    # https://gis.stackexchange.com/questions/80881/what-is-unit-of-shapely-length-attribute
    project = partial(
        pyproj.transform,
        pyproj.Proj(init='EPSG:4326'),
        pyproj.Proj(init='EPSG:32633'))

    left_segment_transformed = transform(project, split_segments[0])
    left_segment_length = left_segment_transformed.length

    right_segment_transformed = transform(project, split_segments[1])
    right_segment_length = right_segment_transformed.length

    # The shorter segment represents the distance from label to end of street segment
    distance_to_segment_end = min(left_segment_length, right_segment_length)
    # print("Distance to end of segment: {} meters".format(distance_to_segment_end))

    # Print the line as geojson
    if debug:
        print("For debugging, here is the line segment found closest to the label:")
        # print(shapely_line)
        print([', '.join([('%.6f' % k) for k in reversed(a)]) for a in list(shapely_line.coords)])

    return distance_to_segment_end, middleness_pct


if __name__ == '__main__':
    print(compute_proximity(47.5775947570801, -122.305442810059))
