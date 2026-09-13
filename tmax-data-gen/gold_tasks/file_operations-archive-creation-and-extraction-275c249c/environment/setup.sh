#!/bin/bash

# Create the necessary directories
mkdir -p /home/user/backup_data
mkdir -p /home/user/extracted_errors
mkdir -p /home/user/important_errors
mkdir -p /home/user/logs

# Create the multi-part archive files
tar -cz --multi-volume --volume-size=100M --file=/home/user/backup_data/system_logs.tar.gz.00 /dev/null
tar -cz --multi-volume --volume-size=100M --file=/home/user/backup_data/system_logs.tar.gz.01 /dev/null
tar -cz --multi-volume --volume-size=100M --file=/home/user/backup_data/system_logs.tar.gz.02 /dev/null

# Create the extraction_log.txt file
touch /home/user/logs/extraction_log.txt

# Change the ownership and permissions
chown -R user:user /home/user
chmod -R 777 /home/user

# Create some sample files in the tar archive for testing
tar -cz --append --file=/home/user/backup_data/system_logs.tar.gz.00 application.err.log
tar -cz --append --file=/home/user/backup_data/system_logs.tar.gz.01 database.err.log
tar -cz --append --file=/home/user/backup_data/system_logs.tar.gz.02 network.err.log

# Create the extraction_log.txt content
echo "Extracted file: application.err" >> /home/user/logs/extraction_log.txt
echo "Hard link: /home/user/important_errors/CRITICAL_application.err" >> /home/user/logs/extraction_log.txt
echo "Extracted file: database.err" >> /home/user/logs/extraction_log.txt
echo "Hard link: /home/user/important_errors/CRITICAL_database.err" >> /home/user/logs/extraction_log.txt
echo "Extracted file: network.err" >> /home/user/logs/extraction_log.txt
echo "Hard link: /home/user/important_errors/CRITICAL_network.err" >> /home/user/logs/extraction_log.txt

# Extract the files and create hard links
tar -xzf /home/user/backup_data/system_logs.tar.gz.00 -C /home/user/extracted_errors application.err.log
tar -xzf /home/user/backup_data/system_logs.tar.gz.01 -C /home/user/extracted_errors database.err.log
tar -xzf /home/user/backup_data/system_logs.tar.gz.02 -C /home/user/extracted_errors network.err.log
mv /home/user/extracted_errors/application.err.log /home/user/extracted_errors/application.err
mv /home/user/extracted_errors/database.err.log /home/user/extracted_errors/database.err
mv /home/user/extracted_errors/network.err.log /home/user/extracted_errors/network.err
ln /home/user/extracted_errors/application.err /home/user/important_errors/CRITICAL_application.err
ln /home/user/extracted_errors/database.err /home/user/important_errors/CRITICAL_database.err
ln /home/user/extracted_errors/network.err /home/user/important_errors/CRITICAL_network.err

# Change the ownership and permissions
chown -R user:user /home/user
chmod -R 777 /home/user
