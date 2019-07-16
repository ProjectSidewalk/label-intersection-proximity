import pandas as pd
from intersection_proximity import compute_proximity

predictor = compute_proximity


def test(row):
    near_dist = row.near_dist
    far_dist = row.far_dist

    middleness = 100 * min(near_dist, far_dist) / ((near_dist + far_dist) / 2)
    min_dist = min(near_dist, far_dist)

    print('-------------------------------')
    print(row.lat, row.lng)
    a, b = predictor(row.lat, row.lng)
    print('predicted', a, b)
    print('actual', min_dist, middleness)


ground_truth = pd.read_csv('ground_truth_intersection_proximity.csv')
ground_truth.apply(test, axis=1)
