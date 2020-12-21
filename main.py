#
# Author: Christian Rivera
#
import mysql
import mysql.connector
from mysql.connector import Error
import math
import time
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import networkx as nx

from login import *
from queries import *
from globals import *

import argparse
parser = argparse.ArgumentParser()
parser.add_argument('-a','--algorithm', type=str, choices=['networkx', 'greedy'], default='networkx')
parser.add_argument('-yr','--year', type=int, default=2012)
parser.add_argument('-mo','--month', type=int, choices=list(range(1,13)), default=1)
parser.add_argument('-d','--day', type=int, choices=list(range(1,32)), default=1)
parser.add_argument('-hr','--hour', type=int, choices=list(range(0,24)), default=0)
parser.add_argument('-min','--minute', type=int, choices=list(range(0,60,5)), default=0)
parser.add_argument('-it','--iterations', type=int, default=2016)
args = parser.parse_args()

host, userName, pswd, dbName, tableName = getLogin()

# Factor to divide geographical regions by
# (if this is set to 1, no division occurs)
geoDivision = 1
max_geoDivision = 64
ride_threshold = {'upper':1000, 'lower': 500}
grid_size_counter = 3

# which matching algorithm to use (can be set to 'greedy' or 'networkx')
matching_algorithm = args.algorithm

# month to query
selected_month = args.month

# NYC boundaries
bounds = getBounds(geoDivision)

active_area = {
    'x1': None,
    'y1': None,
    'x2': None,
    'y2': None
}

query_time = {
  'empty':{
    'time':0.0,
    'count':0.0
  },
  'nonempty':{
    'time':0.0,
    'count':0.0
  },
}

# coords to km conversion
def lat_to_km(lat):
    return (lat - bounds['xMin'])*110.574
def lng_to_km(lng):
    return (lng - bounds['yMin'])*111.320*math.cos(math.radians(40.730610))

def distance(a,b):
    return math.sqrt((a[0]-b[0])*(a[0]-b[0]) + (a[1]-b[1])*(a[1]-b[1]))

# Get distance for each leg of the trip
def chain_distance(a,b,c,d):
    d1 = distance(a,b)
    d2 = distance(b,c)
    d3 = distance(c,d)
    return d1+d2+d3, d1, d2, d3

# Check to make sure the new pickup and dropoff
# times will be within the delay limit
def check_delay(times, distances, speed):
  # new pickup time
  new_pickup = times[0] + distances[0] / speed
  if new_pickup > times[1] + maxDelay:
    return False

  # new dropoff time 1
  new_dropoff_1 = new_pickup + distances[1] / speed
  if new_dropoff_1 > times[2] + maxDelay:
    return False

  # new dropoff time 2
  new_dropoff_2 = new_dropoff_1 + distances[2] / speed
  if new_dropoff_2 > times[3] + maxDelay:
    return False

  return True


def query_all_locations(currentTime):
    total_rides = 0
    total_merged = 0
    total_savings = 0.0
    total_distance = 0.0

    heatmap = np.zeros(shape=(geoDivision,geoDivision))
    location = {
        'x': bounds['xMin'],
        'y': bounds['yMin'],
        'w': bounds['xDiv'],
        'h': bounds['yDiv']
    }
    location['x'] = bounds['xMin']


    max_rides_in_cell = 0

    # Start location loop
    for x in range(geoDivision):
        if geoDivision > 1:
          print(f'\n{x}',end='',flush=True)
          if x < 10:
            print(' ',end='',flush=True)
        location['y'] = bounds['yMin']
        for y in range(geoDivision):
            mark = '.'

            t_qStart = time.perf_counter()
            query = get_query(currentTime, location)
            t_qEnd = time.perf_counter()

            result = execute_read_query(connection, query)

            n = len(result)

            if n > 0:
              query_time['nonempty']['time'] = query_time['nonempty']['time'] + (t_qEnd - t_qStart)
              query_time['nonempty']['count'] = query_time['nonempty']['count'] + 1
            else:
              query_time['empty']['time'] = query_time['empty']['time'] + (t_qEnd - t_qStart)
              query_time['empty']['count'] = query_time['empty']['count'] + 1

            max_rides_in_cell = max(max_rides_in_cell, n)

            heatmap[x][y] = len(result)
            total_rides += len(result)
            distance_list = np.zeros(n)

            # Sum distances of each trip
            for i in range(n):
              x1,y1,x2,y2 = result[i][0:4]
              x1,x2 = lng_to_km(x1),lng_to_km(x2)
              y1,y2 = lat_to_km(y1),lat_to_km(y2)
              total_distance += distance((x1,y1),(x2,y2))
              distance_list[i] = distance((x1,y1),(x2,y2))


            if len(result) > 1:

                mark = 'o'

                ##################################################
                # Ride merging algorithm: compare each pair of
                # trips and decide whether to merge

                # Get max savings for each trip pair
                merge_value = np.zeros(shape=(n,n))

                # For each trip pair i,j
                for i,j in np.ndindex(n,n):
                #for i in range(n):
                #  for j in range(i+1,n):
                    if j<=i:
                        continue

                    ### Trip A
                    # Coords
                    ax1,ay1,ax2,ay2 = result[i][0:4]
                    a_duration = result[i][4]

                    # Start and end times
                    at1 = result[i][5]*60 + result[i][6]
                    at2 = result[i][7]*60 + result[i][8]

                    # Convert to km
                    ax1,ax2 = lng_to_km(ax1),lng_to_km(ax2)
                    ay1,ay2 = lat_to_km(ay1),lat_to_km(ay2)

                    # passenger count
                    a_passengers = result[i][9]

                    ### Trip B
                    # Coords
                    bx1,by1,bx2,by2 = result[j][0:4]
                    b_duration = result[j][4]

                    # Start and end times
                    bt1 = result[j][5]*60 + result[j][6]
                    bt2 = result[j][7]*60 + result[j][8]

                    # Convert to km
                    bx1,bx2 = lng_to_km(bx1),lng_to_km(bx2)
                    by1,by2 = lat_to_km(by1),lat_to_km(by2)

                    # passenger count
                    b_passengers = result[j][9]

                    # Account for number of passengers
                    # If we have more than 3, we cannot merge
                    if a_passengers + b_passengers > 3:
                      continue

                    # compute speed of both trips
                    if a_duration <= 0 or b_duration <= 0:
                      continue

                    a_speed = float(distance((ax1,ay1),(ax2,ay2))) / float(a_duration)
                    b_speed = float(distance((bx1,ay1),(bx2,by2))) / float(b_duration)
                    
                    if a_speed <= 0 or b_speed <= 0:
                      continue

                    avg_speed = (a_speed + b_speed) / 2.0

                    # Analyze four possible merged trips
                    trip_savings = [0,0,0,0]
                    original_distance = distance((ax1,ay1),(ax2,ay2)) + distance((bx1,by1),(bx2,by2))

                    # Case 1: ao - bo - ad - bd
                    total_dist,d1,d2,d3 = chain_distance((ax1,ay1),(bx1,by1),(ax2,ay2),(bx2,by2))
                    if total_dist < original_distance:
                        trip_savings[0] = original_distance - total_dist
                    # Account for pickup and dropoff times
                    if check_delay([at1, bt1, at2, bt2], [d1,d2,d3], avg_speed)==False:
                      continue

                    # Case 2: ao - bo - bd - ad
                    total_dist,d1,d2,d3 = chain_distance((ax1,ay1),(bx1,by1),(bx2,by2),(ax2,ay2))
                    if total_dist < original_distance:
                        trip_savings[1] = original_distance - total_dist
                    # Account for pickup and dropoff times
                    if check_delay([at1, bt1, bt2, at2], [d1,d2,d3], avg_speed)==False:
                      continue

                    # Case 3: bo - ao - bd - ad
                    total_dist,d1,d2,d3 = chain_distance((bx1,by1),(ax1,ay1),(bx2,by2),(ax2,ay2))
                    if total_dist < original_distance:
                        trip_savings[2] = original_distance - total_dist
                    # Account for pickup and dropoff times
                    if check_delay([bt1, at1, bt2, at2], [d1,d2,d3], avg_speed)==False:
                      continue

                    # Case 4: bo - ao - ad - bd
                    total_dist,d1,d2,d3 = chain_distance((bx1,by1),(ax1,ay1),(ax2,ay2),(bx2,by2))
                    if total_dist < original_distance:
                        trip_savings[3] = original_distance - total_dist
                    # Account for pickup and dropoff times
                    if check_delay([bt1, at1, at2, bt2], [d1,d2,d3], avg_speed)==False:
                      continue

                    max_savings = np.max(trip_savings)
                    merge_value[i][j] = max_savings
                    merge_value[j][i] = max_savings

                # End for each

                ##################################################
                # Maximum matching algorithm.
                # Two options are available:
                # - the NetworkX library's matching algorithm
                # - a basic, greedy matching algorithm

                # NetworkX algorithm
                if matching_algorithm=='networkx':
                  graph = nx.from_numpy_matrix(merge_value)
                  matchings = nx.max_weight_matching(graph, maxcardinality=True)
                  for i,j in matchings:
                    total_merged += 1
                    total_savings += merge_value[i][j]

                # Greedy algoritm
                elif matching_algorithm=='greedy':
                  for i in range(n):
                    maxarg = np.argmax(merge_value[i])
                    saved = merge_value[i][maxarg]
                    if saved > 0:
                      total_merged += 1
                      total_savings += saved

                      # stop this trip from being merged with another
                      for j in range(n):
                        merge_value[j][maxarg] = 0
                        merge_value[j][i] = 0
                        merge_value[maxarg][j] = 0
                else:
                  print(f'\n*** ERROR: UNKNOWN ALGORITHM "{matching_algorithm}" ***\n')
                  quit()

                ##################################################

            if geoDivision > 1:
              print(f' {mark}',end='',flush=True)
            location['y'] += bounds['yDiv']
        location['x'] += bounds['xDiv']
    # End location loop

    print('\n')
    return total_rides, total_merged, total_savings, total_distance, max_rides_in_cell, heatmap

print()
print('#########################')
print('# Ride Sharing Analysis #')
print('#########################')

# Create DB connection
connection = create_connection(host, userName, pswd, dbName)

currentTime = {
    'Year': args.year,
    'Month': selected_month,
    'Day': args.day,
    'Hour': args.hour,
    'Minute': args.minute
}

totals = {'rides':0,'merged':0,'saved distance':0.0,'original distance':0.0}

current_iteration = 0

t_i = time.perf_counter()
# Start main loop
for day in range(args.day, 32):
  currentTime['Day'] = day
  for hour in range(0,24):
      currentTime['Hour'] = hour
      counter = grid_size_counter
      for minute in range(0,60,timeInterval):
          currentTime['Minute'] = minute
          s = '\nQuerying rides at '+str(hour)+':'
          if minute < 10:
              s += '0'
          s += str(minute)
          s += ' on day ' + str(day)
          print(s)

          t_0 = time.perf_counter()
          rides, merged, savings, original_distance, max_rides, heatmap = query_all_locations(currentTime)
          t_1 = time.perf_counter()

          print(f'Results for this {timeInterval}-minute window:')
          print(f'\tExecution time: {t_1-t_0:.2f} s')
          print('\tRides:',rides)
          print('\tMax rides:',max_rides)
          print('\tMerges:',merged)
          print('\tDistance saved:', round(savings,2), 'km')
          print('\tOriginal distance:', round(original_distance,2), 'km')

          totals['rides'] += rides
          totals['merged'] += merged
          totals['saved distance'] += savings
          totals['original distance'] += original_distance

          if max_rides > ride_threshold['upper']:
            geoDivision *= 2
            counter = grid_size_counter
          elif max_rides < ride_threshold['lower']:
            geoDivision /= 2
            counter = grid_size_counter
          elif counter > 0:
            counter -= 1
          else:
            geoDivision /= 2
            counter = grid_size_counter


          geoDivision = max(1, geoDivision)
          geoDivision = min(max_geoDivision, geoDivision)
          geoDivision = int(geoDivision)
          bounds = getBounds(geoDivision)

          current_iteration += 1

          if current_iteration > args.iterations:
            break
      if current_iteration > args.iterations:
        break
  if current_iteration > args.iterations:
    break

# End main loop

t_f = time.perf_counter()

print()
print('=== TOTAL RESULTS ===')
print('Total execution time:', round(t_f-t_i,2), 's')
print('Total rides:',totals['rides'])
print('Total merges:',totals['merged'])
print('Distance saved:', round(totals['saved distance'],2), 'km')
print('Original distance:', round(totals['original distance'],2), 'km')
if totals['original distance'] > 0:
  print('Percent Saved:', round(100*totals['saved distance']/totals['original distance'],2))
print()
if query_time['empty']['count'] > 0:
  print('Average empty query time: {:.20f} s'.format(query_time['empty']['time']/query_time['empty']['count']))
if query_time['nonempty']['count'] > 0:
  print('Average nonempty query time: {:.20f} s'.format(query_time['nonempty']['time']/query_time['nonempty']['count']))
if query_time['empty']['count'] > 0 and query_time['nonempty']['count'] > 0:
  print('Average total query time: {:.20f} s'.format((query_time['nonempty']['time']+query_time['empty']['time'])/(query_time['nonempty']['count']+query_time['empty']['count'])))
print()

