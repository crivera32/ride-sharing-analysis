#
# Author: Christian Rivera
#
import mysql
import mysql.connector
from mysql.connector import Error

from login import *
from globals import *

tableName = getLogin()[4]

def create_connection(host_name, user_name, user_password, db_name):
    connection = None
    try:
        connection = mysql.connector.connect(
            host=host_name,
            user=user_name,
            passwd=user_password,
            database=db_name
        )
        print('\nConnected to database.')
    except Error as e:
        print(f"The error '{e}' occurred")

    return connection

def execute_read_query(connection, query):
    cursor = connection.cursor()
    result = None
    try:
        cursor.execute(query)
        result = cursor.fetchall()
        return result
    except Error as e:
        print(f"The error '{e}' occurred")
        return None

def get_query(time, loc):
    query = f'''
            SELECT x1,y1,x2,y2,
                   Duration,
                   pickup_Hour,pickup_Minute,
                   dropoff_Hour,dropoff_Minute,
                   passenger_count
            FROM {tableName}
            WHERE 
            pickup_Year={time['Year']} AND
            pickup_Month={time['Month']} AND
            pickup_Day={time['Day']} AND
            pickup_Hour={time['Hour']} AND
            pickup_Minute>={time['Minute']} AND pickup_Minute<{time['Minute']+timeInterval} AND
            x1>={loc['x']} AND x1<{loc['x']+loc['w']} AND
            y1>={loc['y']} AND y1<{loc['y']+loc['h']};
            '''
    return query

def get_query_no_bounds(time):
    query = f'''
            SELECT x1,y1,x2,y2,
                   Duration,
                   pickup_Hour,pickup_Minute,
                   dropoff_Hour,dropoff_Minute,
                   passenger_count
            FROM {tableName}
            WHERE 
            pickup_Year={time['Year']} AND
            pickup_Month={time['Month']} AND
            pickup_Day={time['Day']} AND
            pickup_Hour={time['Hour']} AND
            pickup_Minute>={time['Minute']} AND pickup_Minute<{time['Minute']+timeInterval};
            '''
    return query

def get_ridecount_all_time_query(loc):
    query = f'''
            SELECT x1,y1,x2,y2,
                   Duration,
                   pickup_Hour,pickup_Minute,
                   dropoff_Hour,dropoff_Minute,
                   passenger_count
            FROM {tableName}
            WHERE
            x1>={loc['x']} AND x1<{loc['x']+loc['w']} AND
            y1>={loc['y']} AND y1<{loc['y']+loc['h']};
            '''
    return query
