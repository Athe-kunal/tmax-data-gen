#!/bin/bash

# Create the /home/user/archived_data directory
mkdir -p /home/user/archived_data

# Create 100 files with the .data extension
for i in {1..100}; do
  touch /home/user/archived_data/file$i.data
done

# Generate the rename_log.txt file
for i in {1..100}; do
  original_name="file$i.data"
  new_name="doc_$(printf "%03d" $i).data"
  echo "$original_name -> $new_name"
done | sort > /home/user/rename_log.txt

# Set the correct permissions
chmod -R 777 /home/user
