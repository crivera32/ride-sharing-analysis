#
# Author: Christian Rivera
#
import pandas as pd
import math
from globals import getBounds

bounds = getBounds(1)

import argparse
parser = argparse.ArgumentParser()
parser.add_argument('-f','--file', type=str, default='unprocessed_file_name')
args = parser.parse_args()

file_name = args.file

print(f'processing: ./data/{file_name}.csv')

def get_datetime(x):
  x = x.replace(' ','-')
  x = x.replace(':','-')
  x = x.replace('/','-')
  
  date = x.split('-')

  date = [int(d) for d in date]

  return date

def get_duration(a,b):
  dta = get_datetime(a)
  dtb = get_datetime(b)

  time_a = dta[3]*60.0 + dta[4]*1.0 + dta[5]/60.0
  time_b = dtb[3]*60.0 + dtb[4]*1.0 + dtb[5]/60.0

  if dta[2]!=dta[2]:
    time_b += (dtb[2]-dta[2])*60.0*24.0
    
  duration = time_b - time_a

  if duration==0:
    duration = -1;

  return duration

def get_distance(x1,y1,x2,y2):
  x_diff = (x1-x2)*(x1-x2)
  y_diff = (y1-y2)*(y1-y2)
  return math.sqrt(x_diff+y_diff)

print()
print('imported dependencies')

#LOAD
df = pd.read_csv(f'./data/{file_name}.csv')
print()
print('loaded csv')
print('shape:',df.shape)

df = df.rename(columns={
    'pickup_longitude':'x1','pickup_latitude':'y1',
    'dropoff_longitude':'x2','dropoff_latitude':'y2'
  })

df = df[df['x1']>bounds['xMin']]
df = df[df['x1']<bounds['xMax']]

df = df[df['y1']>bounds['yMin']]
df = df[df['y1']<bounds['yMax']]

df = df[df['x2']>bounds['xMin']]
df = df[df['x2']<bounds['xMax']]

df = df[df['y2']>bounds['yMin']]
df = df[df['y2']<bounds['yMax']]

df = df[df['y2']>bounds['yMin']]
df = df[df['y2']<bounds['yMax']]

print()
print('finished cleaning coordinates')

pCol,dCol = ['pickup_datetime', 'dropoff_datetime']
date_fields = ['Year', 'Month', 'Day', 'Hour', 'Minute', 'Second']

df['Duration'] = df.apply(lambda x: get_duration(x[pCol],x[dCol]), axis=1)
df = df[df['Duration'] > 0]
print('finished processing duration')

for i in range(len(date_fields)):
  df['pickup_{}'.format(date_fields[i])] = df[pCol].apply(lambda x: get_datetime(x)[i])
  df['dropoff_{}'.format(date_fields[i])] = df[dCol].apply(lambda x: get_datetime(x)[i])
print('finished processing time')

print()
print('saving...')

print('shape:',df.shape)

df.to_csv(f'./preprocessed/{file_name}_preprocessed.csv')
print('\ndone!\n')
