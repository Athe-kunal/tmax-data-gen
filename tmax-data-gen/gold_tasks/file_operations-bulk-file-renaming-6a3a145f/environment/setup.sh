#!/bin/bash

# Create the /home/user/deliverables directory
mkdir -p /home/user/deliverables

# Create the files in the /home/user/deliverables directory
touch /home/user/deliverables/file1.py
touch /home/user/deliverables/file2.txt
touch /home/user/deliverables/file3.md
touch /home/user/deliverables/file4.py
touch /home/user/deliverables/file5.txt
touch /home/user/deliverables/file6.md

# Create an empty log file in the /home/user directory
touch /home/user/rename_log.txt

# Set the permissions of the files and directories
chmod -R 777 /home/user

# Verify the initial state
ls -l /home/user/deliverables
cat /home/user/rename_log.txt
