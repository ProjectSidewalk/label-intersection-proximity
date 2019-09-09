import os

# All the default settings for the project are stored here.
INFTY = 1000000
MIN_SIZE = .0006
street_network_index = None

default_settings = {
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
for city in default_settings:
    for key in default_settings[city]:
        default_settings[city][key] = os.path.join(os.path.dirname(os.path.abspath(__file__)), "default_input", default_settings[city][key])
