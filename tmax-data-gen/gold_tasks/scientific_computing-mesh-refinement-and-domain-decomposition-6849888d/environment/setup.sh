#!/bin/bash

# Create the user directory
mkdir -p /home/user

# Create the spatial data file
echo "0.1,0.2
0.3,0.4
0.5,0.6
0.7,0.8
0.1,0.2
0.3,0.4
0.5,0.6
0.7,0.8
0.1,0.2
0.3,0.4
0.5,0.6
0.7,0.8
0.1,0.2
0.3,0.4
0.5,0.6
0.7,0.8
0.1,0.2
0.3,0.4
0.5,0.6
0.7,0.8
0.1,0.2
0.3,0.4
0.5,0.6
0.7,0.8" > /home/user/spatial_data.csv

# Install necessary packages
apt update
apt install -y python3 python3-pip
pip3 install numpy scipy

# Create a Python script to generate the spatial data
echo "import numpy as np
import scipy.stats as stats

# Define the domain
x_min, x_max = 0, 1
y_min, y_max = 0, 1

# Define the Gaussian distribution
mu_x, mu_y = 0.5, 0.5
sigma = 0.2

# Generate the spatial data
np.random.seed(0)
x = np.random.uniform(x_min, x_max, 100)
y = np.random.uniform(y_min, y_max, 100)

# Save the spatial data to a file
np.savetxt('/home/user/spatial_data.csv', np.column_stack((x, y)), delimiter=',')" > /home/user/generate_spatial_data.py

# Run the Python script to generate the spatial data
python3 /home/user/generate_spatial_data.py

# Change permissions
chmod -R 777 /home/user
