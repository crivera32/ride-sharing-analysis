#
# Author: Christian Rivera
#

# Lat and Long boundaries of New York City.
# Ignore any trips outside of this.
def getBounds(geoDivision):
  #'''
  bounds = {
    'xMin': -74.299698,
    'xMax': -73.668740,
    'yMin': 40.472695,
    'yMax': 40.931986,
  }
  bounds['xRange'] = bounds['xMax'] - bounds['xMin']
  bounds['yRange'] = bounds['yMax'] - bounds['yMin']
  bounds['xDiv'] = bounds['xRange']/float(geoDivision)
  bounds['yDiv'] = bounds['yRange']/float(geoDivision)
  return bounds

# Time interval (minutes) for each query
timeInterval = 5

# Maximum wait time (minutes) allowed when merging trips
maxDelay = 5