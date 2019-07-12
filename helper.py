import pandas as pd
from dbfread import DBF
import os
import math
import geojson

multiplier = 1e7  # multiply all floats by this multiplier so we can compare them

# pre-processing
def generate_street_edge_name_map(way_info_file, way_street_id_file, street_edge_name_file):
    osm_data = pd.DataFrame(DBF(way_info_file).records)
    osm_data.set_index('osm_id', inplace=True)
    street_name = osm_data['name']

    street_id = pd.read_csv(way_street_id_file)
    street_id.set_index('street_edge_id', inplace=True)

    street_id_name = street_id.apply(lambda x: street_name.loc[x['osm_way_id']], axis=1)
    street_id_name.to_csv(street_edge_name_file, header=['street_name'])


def extract_street_coords_from_geojson(street):
    '''
    Returns tuple mapping street edge id to a list of coordinate tuples
    :param street:
    :return:
    '''
    edge_id = street['properties']['street_edge_id']
    coords_generator = geojson.utils.coords(street)
    coords_list = []
    for c in coords_generator:
        coords_list.append(c)
    return edge_id, coords_list


def get_intersection_points(street_network_file, street_edge_name_file, intersection_points_file):
    with open(street_network_file) as f:
        streets_gj = geojson.load(f)

    # Read streets into a list of street edge id->coordinates mapping
    streets_list = streets_gj['features']

    edge_id_to_coords_list = {}

    # load all edges
    for street in streets_list:
        edge_id, coords_list = extract_street_coords_from_geojson(street)
        edge_id_to_coords_list[edge_id] = coords_list

    # compute which points are intersections of at least two different streets
    points_to_street = {}
    intersection_points = set()

    edge_to_name = pd.read_csv(street_edge_name_file)
    edge_to_name.set_index('street_edge_id')

    for edge_id, coords_list in edge_id_to_coords_list.items():
        try:
            street_name = edge_to_name.loc[edge_id].street_name
        except KeyError:
            continue

        for float_point in coords_list:
            point_lng, point_lat = int(float_point[0] * multiplier), int(float_point[1] * multiplier)
            # print(float_point)
            if (point_lng, point_lat) in points_to_street:
                if points_to_street[point_lng, point_lat] != street_name and type(street_name) == str:
                    # found an intersection
                    intersection_points.add((point_lng, point_lat))
            else:
                points_to_street[point_lng, point_lat] = street_name

    # print ((-122327192, 47628370) in intersection_points)
    # import random
    # crop = random.sample(intersection_points, 10)
    with open(intersection_points_file, 'w') as f:
        for (a, b) in intersection_points:
            f.write(f'{a} {b}\n')
    # print(len(intersection_points))


get_intersection_points('input/roads-for-cv-seattle.geojson', 'input/street-edge-name-seattle.csv', 'input/intersection-points-seattle.txt')


def get_absolute_path(input_file):
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "input", input_file)


def distance(a, b):
    return math.sqrt((a[0]-b[0])**2 + (a[1]-b[1])**2)

