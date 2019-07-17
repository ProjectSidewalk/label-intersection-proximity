import pandas as pd
from dbfread import DBF
from rtree import index
import geojson
from shapely.ops import linemerge, split, nearest_points
from shapely.geometry import MultiLineString, LineString, Point, MultiPoint
import pickle

multiplier = 1e5 # multiply all floats by this multiplier so we can compare them
MIN_SIZE = .0006
MAX_DIST = 1/multiplier  # maximum distance between intersection and street for a street to to be cut


def generate_street_edge_name_map(road_network_dump, osm_way_ids, street_edge_name_file):
    osm_data = pd.DataFrame(DBF(road_network_dump).records)
    osm_data.set_index('osm_id', inplace=True)
    street_name = osm_data['name']

    street_id = pd.read_csv(osm_way_ids)
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


def generate_intersection_points(street_network_file, street_edge_name_file, intersection_points_file):
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
    points_to_streets = dict()

    edge_to_name = pd.read_csv(street_edge_name_file)
    edge_to_name.set_index('street_edge_id', inplace=True)

    for edge_id, coords_list in edge_id_to_coords_list.items():
        try:
            street_name = edge_to_name.loc[edge_id].street_name
        except KeyError:
            continue

        for float_point in coords_list:
            point_lng, point_lat = int(float_point[0] * multiplier), int(float_point[1] * multiplier)

            # print(float_point)
            if (point_lng, point_lat) not in points_to_streets:
                points_to_streets[point_lng, point_lat] = set()

            if type(street_name) == str:
                points_to_streets[point_lng, point_lat].add(street_name)

    # print ((-122327192, 47628370) in intersection_points)
    # import random
    # crop = random.sample(intersection_points, 10)
    # with open(intersection_points_file, 'w') as f:
    #     for (a, b) in intersection_points:
    #         f.write(f'{a} {b}\n')
    # print(len(intersection_points))

    # filter all points that aren't on > 1 streets
    intersection_points = dict()
    for point, street_names in points_to_streets.items():
        if len(street_names) > 1:
            intersection_points[point] = street_names

    with open(intersection_points_file, 'wb') as f:
        pickle.dump(intersection_points, f)

# get_intersection_points('input/roads-for-cv-seattle.geojson', 'input/street-edge-name-seattle.csv', 'input/intersection-points-seattle.pickle')


def generate_real_segments(street_network_file, intersection_points_file, street_edge_name_file, real_segments_file):
    with open(street_network_file) as f:
        streets_gj = geojson.load(f)

    # Read streets into a list of street edge id->coordinates mapping
    streets_list = streets_gj['features']

    edge_id_to_coords_list = {}

    # load all edges
    for street_segment in streets_list:
        edge_id, coords_list = extract_street_coords_from_geojson(street_segment)
        edge_id_to_coords_list[edge_id] = coords_list

    # now group streets with the same name together
    name_to_edge = pd.read_csv(street_edge_name_file)
    street_linestrings = name_to_edge.groupby('street_name').apply(lambda x: linemerge([edge_id_to_coords_list[k] for k in x.street_edge_id.values]))

    with open(intersection_points_file, 'rb') as f:
        intersection_points = pickle.load(f)

    def cut_street(street, p):
        if street.type == 'GeometryCollection':
            street = MultiLineString(street)

        if street.distance(p) < MAX_DIST:
            # cut the segment and return it
            # note: this only works because the point is pretty close to a vertex on the LineString!
            # TODO change to use shapely.ops.snap with tolerance MAX_DIST

            if street.type == 'LineString':
                mp = MultiPoint(list(street.coords))
            else:
                assert street.type == 'MultiLineString'
                points = []
                for line_string in street.geoms:
                    points += line_string.coords

                mp = MultiPoint(points)

            split_vertex = nearest_points(mp, p)[0]

            return split(street, split_vertex)

        return street

    for point, street_names in intersection_points.items():
        for street_name in street_names:
            # cut streets at each intersection point
            street_linestrings.at[street_name] = cut_street(street_linestrings.loc[street_name],
                                                            Point([point[0] / multiplier, point[1] / multiplier]))

    # now generate a list of all the segments we found
    real_segments = list()
    for geometry_collection in street_linestrings.values:
        if geometry_collection.type in ['GeometryCollection', 'MultiLineString']:
            for linestring in geometry_collection:
                real_segments.append(linestring)

        elif geometry_collection.type == 'LineString':
            real_segments.append(geometry_collection)

        else:
            raise Exception(f'Unexpected type found when generating real segments: {geometry_collection.type}')

    # pickle the real segments (no need to create new edge id's because they would be irrelevant)
    with open(real_segments_file, 'wb') as f:
        pickle.dump(real_segments, f)


# generate_real_segments('input/roads-for-cv-seattle.geojson', 'input/intersection-points-seattle.pickle',
#                        'input/street-edge-name-seattle.csv', 'input/real-segments-seattle.pickle')

def get_rtree(lines):
    def generate_items():
        sindx = 0
        for lid, l in lines:
            for i in range(len(l)-1):
                a, b = l[i]
                c, d = l[i+1]
                segment = ((a,b), (c,d))
                box = (min(a, c), min(b,d), max(a, c), max(b,d))
                #box = left, bottom, right, top
                yield (sindx, box, (lid, segment))
                sindx += 1
    return index.Index(generate_items())


def make_street_network_index(real_segments_file):
    # Load the pickled segments file
    with open(real_segments_file, 'rb') as f:
        real_segments = pickle.load(f)

    # Read segments into a list of id->coordinates mapping
    id_to_segment = []
    for i in range(len(real_segments)):
        id_to_segment.append((i, list(real_segments[i].coords)))

    # Index the streets
    idx = get_rtree(id_to_segment)
    return idx, real_segments


def run_preprocess(city_settings):
    generate_street_edge_name_map(city_settings['road_network_dump'], city_settings['osm_way_ids'],
                                  city_settings['street_edge_name_filename'])

    generate_intersection_points(city_settings['street_network_filename'], city_settings['street_edge_name_filename'],
                                 city_settings['intersection_points_filename'])

    generate_real_segments(city_settings['street_network_filename'], city_settings['intersection_points_filename'],
                           city_settings['street_edge_name_filename'], city_settings['real_segments_output_filename'])


if __name__ == '__main__':

    import os
    settings = {
        'seattle': {
            # inputs
            'street_network_filename': 'roads-for-cv-seattle.geojson',
            'osm_way_ids': 'osm-way-ids-seattle.csv',
            'road_network_dump': 'seattle-roads.dbf',

            # outputs
            'intersection_points_filename': 'intersection-points-seattle.pickle',
            'street_edge_name_filename': 'street-edge-name-seattle.csv',
            'real_segments_output_filename': 'real-segments-seattle.pickle'
        }
    }

    # convert to absolute paths
    for city in settings:
        for key in settings[city]:
            settings[city][key] = os.path.join(os.path.dirname(os.path.abspath(__file__)), "input", settings[city][key])

    run_preprocess(settings['seattle'])
