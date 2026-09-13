#!/bin/bash

# Create the user's home directory
mkdir -p /home/user

# Create the log file with the specified entries
cat > /home/user/audit.log << EOF
10.0.0.1 - - [10/Oct/2023:13:55:36 +0000] "GET /admin HTTP/1.1" 200
10.0.0.2 - - [10/Oct/2023:13:56:00 +0000] "GET /user HTTP/1.1" 200
10.0.0.3 - - [10/Oct/2023:13:57:00 +0000] "GET /admin HTTP/1.1" 401
EOF

# Create the data dump with the specified data
cat > /home/user/data_dump.csv << EOF
id,username,email,password_hash,access_level
1,user1,user1@example.com,abc123,admin
2,user2,user2@example.com,def456,user
3,user3,user3@example.com,ghi789,admin
EOF

# Change the ownership of the files to the user
chown -R user:user /home/user

# Set the permissions for the user's home directory
chmod -R 777 /home/user
