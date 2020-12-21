# New York City Ride Sharing Analysis 

Author: Christian Rivera ( criver32@uic.edu )

This project repeatedly queries a database containing records of taxi rides in New York City, and determines the potential benefits of merging these rides via ride sharing. In order to process a large volume of rides efficiently, regions considered are divided into separate geographical areas and processed individually. The size of these regions changes dynamically based on current demands as the program runs. See bellow for a comparison of results using different matching algorithms.

## Required Python Libraries

matplotlib

numpy

pandas

mysql

networkx

## Data Preprocessing

Run preprocess.py on the raw .csv files. The data can be accessed [here](https://www1.nyc.gov/site/tlc/about/tlc-trip-record-data.page). Note the preprocessing script is intended for yellow taxi data recorded in the year 2015 or earlier.

Usage:
    python preprocess.py -f \<filename\>

The resulting preprocessed .csv is ready to be loaded into the database.

## Configure Database Connection

Once your database is set up, configure all of the fields in login.py to match your DB login credentials.

## Running the Ride Merging Code

Run main.py to start the querying algorithm.

Usage:
    python main.py -mo \<month\> -d \<day\> -it \<max_iterations\> -a \<algorithm\>

If max_iterations is not set, 7 days of data will be processed.

There are two options for algorithm, either 'networkx' (optimal) or 'greedy' (fast).

## Results

These graphs show the percentage of distance saved by merging rides and the average execution time per 5 minutes of data, as a function of the maximum delay allowed when merging rides. Comparing the results for the two matching algorithms considered, we see that the greedy approach slightly underperforms the optimal solution in the distance saved, but it is significantly faster when a longer delay is used. These results were obtained by running the code on 3 months of data taken from 2012.

![distance saved](https://raw.githubusercontent.com/crivera32/ride-sharing-analysis/main/plots/distance_small.png)
![execution time](https://raw.githubusercontent.com/crivera32/ride-sharing-analysis/main/plots/time_small.png)

