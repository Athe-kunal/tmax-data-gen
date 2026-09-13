#!/bin/bash

# Create the home directory for the user
mkdir -p /home/user

# Create the access log file
echo "192.168.1.100 - - [10/Oct/2023:13:55:36 +0000] \"GET /index.php?name=Robert'); UNION SELECT * FROM users WHERE id=1;#\" 200 1234" > /home/user/access.log

# Create the data dump file
echo "id,name,email,ssn,cc_number
1,John Doe,johndoe@example.com,123-45-6789,1234-5678-9012-3456
2,Jane Doe,janedoe@example.com,987-65-4321,9876-5432-1098-7654
3,Bob Smith,bobsmith@example.com,111-11-1111,1111-1111-1111-1111" > /home/user/compromised_db_dump.csv

# Install necessary packages
apt update
apt install -y python3 python3-pip

# Install pytest
pip3 install pytest

# Create a directory for the python scripts
mkdir -p /home/user/python_scripts

# Change permissions
chmod -R 777 /home/user
