#!/bin/bash

# Install the pexpect library
pip install pexpect

# Create the /home/user directory and its contents
mkdir -p /home/user
chmod 777 /home/user

# Create the legacy export tool script
cat > /home/user/legacy_export.py <<EOF
import getpass
import os
import sys

admin_password = getpass.getpass("Enter admin password: ")
export_path = input("Enter export path: ")

if admin_password == "cloud_admin_99" and export_path == "/home/user/export_data":
    os.makedirs(export_path, exist_ok=True)
    for dir in ["export_dir1", "export_dir2", "export_dir3"]:
        os.makedirs(os.path.join(export_path, dir), exist_ok=True)
    print("Export complete")
else:
    print("Invalid admin password or export path")
    sys.exit(1)
EOF
chmod 777 /home/user/legacy_export.py

# Create the migration_fstab file
cat > /home/user/migration_fstab <<EOF
export_dir1 /home/user/cloud_mounts/export_dir1
# This is a comment
export_dir2 /home/user/cloud_mounts/export_dir2
export_dir3 /home/user/cloud_mounts/export_dir3
EOF
chmod 777 /home/user/migration_fstab

# Create the initial directory structure
mkdir -p /home/user/export_data
mkdir -p /home/user/cloud_mounts

# Set permissions
chmod -R 777 /home/user

# Create the run_export.py script
cat > /home/user/run_export.py <<EOF
import pexpect

child = pexpect.spawn('/home/user/legacy_export.py')
child.expect('Enter admin password:')
child.sendline('cloud_admin_99')
child.expect('Enter export path:')
child.sendline('/home/user/export_data')
child.wait()
EOF
chmod 777 /home/user/run_export.py

# Create the setup_mounts.py script
cat > /home/user/setup_mounts.py <<EOF
import os

with open('/home/user/migration_fstab', 'r') as f:
    for line in f:
        if not line.startswith('#'):
            source, target = line.strip().split()
            target_dir = os.path.dirname(target)
            os.makedirs(target_dir, exist_ok=True)
            if not os.path.islink(target):
                os.symlink(os.path.join('/home/user/export_data', source), target)
EOF
chmod 777 /home/user/setup_mounts.py

# Create the log file
touch /home/user/migration_status.log
chmod 777 /home/user/migration_status.log

# Set final permissions
chmod -R 777 /home/user
