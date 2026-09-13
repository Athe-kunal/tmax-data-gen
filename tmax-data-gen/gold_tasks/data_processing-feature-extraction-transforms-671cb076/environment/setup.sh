#!/bin/bash

# Create the input file with 1000 translation updates
for i in {1..1000}; do
  timestamp=$(date -u -d "2022-01-01 00:00:00 + $((i-1)) seconds" +"%Y-%m-%dT%H:%M:%S")
  source_text=$(tr -dc 'a-z' < /dev/urandom | fold -w $((RANDOM%100+1)) | head -n 1)
  target_text=$(tr -dc 'a-z' < /dev/urandom | fold -w $((RANDOM%100+1)) | head -n 1)
  echo "{\"id\": \"$i\", \"timestamp\": \"$timestamp\", \"source_lang\": \"en\", \"target_lang\": \"fr\", \"source_text\": \"$source_text\", \"target_text\": \"$target_text\"}" >> /home/user/translation_updates.jsonl
done

# Create the directory and files with the correct permissions
mkdir -p /home/user
touch /home/user/anomalous_translations.txt
touch /home/user/task_log.txt

# Set the permissions
chmod -R 777 /home/user
