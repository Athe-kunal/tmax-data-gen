#!/bin/bash

# Create the initial directory structure
mkdir -p /home/user/data/documents
mkdir -p /home/user/data/images
mkdir -p /home/user/data/videos

# Create the files in the initial directory structure
touch /home/user/data/documents/example1.txt
touch /home/user/data/documents/example2.txt
touch /home/user/data/images/image1.jpg
touch /home/user/data/images/image2.png
touch /home/user/data/videos/video1.mp4
touch /home/user/data/videos/video2.mp4

# Create the backup directory structure
mkdir -p /home/user/backup/documents
mkdir -p /home/user/backup/images
mkdir -p /home/user/backup/videos

# Copy the files from the initial directory structure to the backup directory structure
cp -r /home/user/data/documents/* /home/user/backup/documents/
cp -r /home/user/data/images/* /home/user/backup/images/
cp -r /home/user/data/videos/* /home/user/backup/videos/

# Generate the SHA-256 checksum manifest
find /home/user/backup/ -type f -print0 | sort -z | xargs -0 sha256sum > /home/user/backup/manifest.sha256

# Create the log file
echo "Backup created successfully." > /home/user/backup/log.txt

# Set the permissions
chmod -R 777 /home/user
