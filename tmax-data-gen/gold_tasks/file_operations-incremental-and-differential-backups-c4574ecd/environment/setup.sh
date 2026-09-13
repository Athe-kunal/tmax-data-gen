#!/bin/bash

# Install necessary packages
apt update
apt install -y rust cargo

# Create directories
mkdir -p /home/user/base_backup
mkdir -p /home/user/inc_backup

# Create files in base_backup directory
dd if=/dev/zero of=/home/user/base_backup/file1.txt bs=1024 count=1
dd if=/dev/zero of=/home/user/base_backup/file2.txt bs=2048 count=1

# Create files in inc_backup directory
dd if=/dev/zero of=/home/user/inc_backup/file1.txt bs=1024 count=1
dd if=/dev/zero of=/home/user/inc_backup/file2.txt bs=2048 count=1
dd if=/dev/zero of=/home/user/inc_backup/file3.txt bs=4096 count=1

# Create backups.json file
echo '{
    "base": "/home/user/base_backup",
    "inc": "/home/user/inc_backup"
}' > /home/user/backups.json

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

# Change ownership and permissions
chown -R user:user /home/user
chmod -R 777 /home/user
