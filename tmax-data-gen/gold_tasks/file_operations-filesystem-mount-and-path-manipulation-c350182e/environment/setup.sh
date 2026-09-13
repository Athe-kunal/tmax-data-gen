#!/bin/bash

# Install the pexpect library
pip install pexpect

# Create the /home/user directory
mkdir -p /home/user

# Create the legacy_export.py script
cat > /home/user/legacy_export.py <<EOF
import sys

def main():
    admin_password = input("Enter admin password: ")
    export_path = input("Enter export path: ")
    print(f"Exporting data to {export_path}...")
    # Simulate data export
    with open(f"{export_path}/exported_data.txt", "w") as f:
        f.write("Exported data")

if __name__ == "__main__":
    main()
EOF

# Create the migration_fstab file
cat > /home/user/migration_fstab <<EOF
# This is a comment
source_dir1 /mnt/target1
source_dir2 /mnt/target2
EOF

# Create the export_data directory
mkdir -p /home/user/export_data

# Create the target directories for symbolic links
mkdir -p /mnt

# Create the symbolic links
ln -s /home/user/export_data/source_dir1 /mnt/target1
ln -s /home/user/export_data/source_dir2 /mnt/target2

# Create the source directories in export_data
mkdir -p /home/user/export_data/source_dir1
mkdir -p /home/user/export_data/source_dir2

# Create a sample file in each source directory
touch /home/user/export_data/source_dir1/sample_file1.txt
touch /home/user/export_data/source_dir2/sample_file2.txt

# Change ownership and permissions
chmod -R 777 /home/user
