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

from login import *
from queries import *
from globals import *

host, userName, pswd, dbName, tableName = getLogin()

# Factor to divide geographical regions by
geoDivision = 16

# NYC boundaries
bounds = getBounds(geoDivision)

active_area = {
    'x1': None,
    'y1': None,
    'x2': None,
    'y2': None
}

to_coords = [ [ {'x':None,'y':None} for j in range(geoDivision) ] for i in range(geoDivision) ]

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

def query_all_locations():
    total_rides = 0
    total_merged = 0
    total_savings = 0.0
    original_distance = 0.0

    heatmap = np.zeros(shape=(geoDivision,geoDivision))
    location = {
        'x': bounds['xMin'],
        'y': bounds['yMin'],
        'w': bounds['xDiv'],
        'h': bounds['yDiv']
    }
    location['x'] = bounds['xMin']

    # Start location loop
    for x in range(geoDivision):
        print(f'\n{x}',end='',flush=True)
        if x < 10:
            print(' ',end='',flush=True)
        location['y'] = bounds['yMin']
        for y in range(geoDivision):

            to_coords[x][y] = { 'x':location['x'], 'y':location['y'] }

            mark = '.'
            query = get_ridecount_all_time_query(location)
            result = execute_read_query(connection, query)

            heatmap[x][y] = float(len(result))
            total_rides += len(result)

            if len(result) > 1:
                mark = 'o'

            print(f' {mark}',end='',flush=True)
            location['y'] += bounds['yDiv']
        location['x'] += bounds['xDiv']
    # End location loop

    print('\n')
    return total_rides, total_merged, total_savings, original_distance, heatmap

print()
print('#########################')
print('# Ride Sharing Analysis #')
print('#########################')

ride_limit = 300

# Create DB connection
connection = create_connection(host, userName, pswd, dbName)

rides, merged, savings, original_distance, heatmap = query_all_locations()

active_cells = np.zeros(heatmap.shape)
for i,j in np.ndindex(heatmap.shape):
    if heatmap[i][j] > ride_limit:
        active_cells[i][j] = 1

        if active_area['x1']==None:
            active_area['x1']=to_coords[i][j]['x']
        active_area['x1']=min(to_coords[i][j]['x'],active_area['x1'])

        if active_area['y1']==None:
            active_area['y1']=to_coords[i][j]['y']
        active_area['y1']=min(to_coords[i][j]['y'],active_area['y1'])

        if active_area['x2']==None:
            active_area['x2']=to_coords[i][j]['x']+bounds['xDiv']
        active_area['x2']=max(to_coords[i][j]['x']+bounds['xDiv'],active_area['x1'])

        if active_area['y2']==None:
            active_area['y2']=to_coords[i][j]['y']+bounds['yDiv']
        active_area['y2']=max(to_coords[i][j]['y']+bounds['yDiv'],active_area['y1'])

    else:
        active_cells[i][j] = 0


# Use this function to display the returned heatmaps
def showHeatmap(heatmap):
    # Plot frequency
    fig, ax = plt.subplots()
    im = ax.imshow(heatmap)
    ax.set_xticks(np.arange(geoDivision))
    ax.set_yticks(np.arange(geoDivision))
    ax.set_xticklabels(list(range(geoDivision)))
    ax.set_yticklabels(list(range(geoDivision)))

    for i in range(geoDivision):
        for j in range(geoDivision):
            text = ax.text(j, i, round(float(heatmap[i, j]),2),ha="center", va="center", color="w", size=4)

    ax.set_title("ride frequency plot")
    plt.show()

showHeatmap(heatmap/np.max(heatmap))
#showHeatmap(active_cells)

#print(active_area)
