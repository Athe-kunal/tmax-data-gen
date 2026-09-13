#!/bin/bash

# Install necessary packages
apt update
apt install -y build-essential gcc g++ libstdc++-9-dev

# Create necessary directories
mkdir -p /home/user/data
mkdir -p /home/user/experiments

# Create train.csv file
echo "x,y" > /home/user/data/train.csv
for i in {1..100}; do
  echo "$i,$((i * 2 + 1))" >> /home/user/data/train.csv
done

# Create test.csv file
echo "x" > /home/user/data/test.csv
for i in {1..100}; do
  echo "$i" >> /home/user/data/test.csv
done

# Create cv_results.csv file with header
echo "degree,alpha,mean_mse" > /home/user/experiments/cv_results.csv

# Create predictions.txt file
touch /home/user/experiments/predictions.txt

# Set permissions
chmod -R 777 /home/user
