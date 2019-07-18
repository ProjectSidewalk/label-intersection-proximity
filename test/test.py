import pandas as pd
import math
from intersection_proximity import compute_proximity

predictor = compute_proximity


def test(row):
    near_dist = row.near_dist
    far_dist = row.far_dist

    middleness = 100 * min(near_dist, far_dist) / ((near_dist + far_dist) / 2)
    min_dist = min(near_dist, far_dist)

    print('-------------------------------')
    print('id:', row.label_id)
    print('%.6f, %.6f' % (row.lat, row.lng))
    a, b = predictor(row.lat, row.lng)
    print('predicted', a, b)
    print('actual', min_dist, middleness)

    absolute_ = math.fabs(min_dist - a) < 5
    middleness_ = math.fabs(middleness - b) < 10

    if not absolute_:
        print('*** ABSOLUTE ***')
    elif not middleness_:
        print('*** MIDDLENESS ***')

    return pd.Series({
        'absolute': absolute_,
        'middleness': middleness_
    })


ground_truth = pd.read_csv('ground_truth_intersection_proximity.csv')
result = ground_truth.apply(test, axis=1)

absolute_correct = sum(result.absolute)
middleness_correct = sum(result.middleness)
total_entries = len(result)

print('-------------------------------')
print('ABSOLUTE DISTANCE: ')
print(f'\t {absolute_correct} / {total_entries} = {100*absolute_correct/total_entries:.2f}%')
print('MIDDLENESS: ')
print(f'\t {middleness_correct} / {total_entries} = {100*middleness_correct/total_entries:.2f}%')
