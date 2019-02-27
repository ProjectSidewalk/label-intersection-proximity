var turf = require('@turf/turf');
var fs = require('fs');

// GEOJSON file of the street network
var streets = fs.readFileSync('./input/full_dc.geojson');

streetSegments = JSON.parse(streets);
