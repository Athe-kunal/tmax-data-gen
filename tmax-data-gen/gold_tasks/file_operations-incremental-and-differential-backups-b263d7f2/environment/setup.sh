#!/bin/bash

# Create directories
mkdir -p /home/user/base_backup
mkdir -p /home/user/inc_backup

# Create files in base backup directory
touch /home/user/base_backup/file1.txt
touch /home/user/base_backup/file2.txt
touch /home/user/base_backup/file3.txt

# Create files in incremental backup directory
touch /home/user/inc_backup/file1.txt
touch /home/user/inc_backup/file2.txt
touch /home/user/inc_backup/file3.txt

# Set file sizes
dd if=/dev/zero of=/home/user/base_backup/file1.txt bs=1 count=1024
dd if=/dev/zero of=/home/user/base_backup/file2.txt bs=1 count=2048
dd if=/dev/zero of=/home/user/base_backup/file3.txt bs=1 count=4096
dd if=/dev/zero of=/home/user/inc_backup/file1.txt bs=1 count=1024
dd if=/dev/zero of=/home/user/inc_backup/file2.txt bs=1 count=2048
dd if=/dev/zero of=/home/user/inc_backup/file3.txt bs=1 count=4096

# Create backups.json file
echo '{"base": "/home/user/base_backup", "inc": "/home/user/inc_backup"}' > /home/user/backups.json

# Create sync.log file
echo 'FILE: file1.txt
SIZE: 1024
STATUS: SUCCESS
FILE: file2.txt
SIZE: 2048
STATUS: SUCCESS
FILE: file3.txt
SIZE: 4096
STATUS: FAILED' > /home/user/sync.log

# Create expected_dedup_report.csv file
echo 'filename,saved_bytes
file1.txt,1024
file2.txt,2048' > /home/user/expected_dedup_report.csv

# Set permissions
chmod -R 777 /home/user
