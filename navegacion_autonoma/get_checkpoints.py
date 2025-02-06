#!/usr/bin/env python
import csv
import numpy as np

# function to get checkpoints from a csv file
def get_checkpoints(path):
    # create checkpoints vector
    checkpoints = []
    # open the file
    with open(path, mode = "r") as file:
        # read the csv as a numpy array
        lines = csv.reader(file)
        # for each line append the checkpoint as numpy vector transforming the data to a float
        for line in lines:
            checkpoints.append(np.array(line).astype(np.float))
    return checkpoints

# get ruta_eps3_corta.csv checkpoints
checkpoints = get_checkpoints("rutas/ruta_eps3_corta/ruta_eps3_corta.csv")
print(checkpoints)