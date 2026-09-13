#!/bin/bash

# Create the /home/user directory
mkdir -p /home/user

# Create the benchmarks.csv file
echo "model_id,inference_ms,confidence_score" > /home/user/benchmarks.csv
echo "1,10.5,0.8" >> /home/user/benchmarks.csv
echo "2,-5.2,0.7" >> /home/user/benchmarks.csv
echo "3,abc,0.9" >> /home/user/benchmarks.csv
echo "4,20.1,0.6" >> /home/user/benchmarks.csv

# Create the task.log file
touch /home/user/task.log

# Install required packages
apt update
apt install -y bc

# Set permissions
chmod -R 777 /home/user
