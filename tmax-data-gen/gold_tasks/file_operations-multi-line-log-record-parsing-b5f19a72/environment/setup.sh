# Create the /home/user/logs directory
mkdir -p /home/user/logs

# Create the /home/user/parser directory
mkdir -p /home/user/parser

# Create the test log file "test.log" in the /home/user/logs directory
cat > /home/user/logs/test.log <<EOF
2022-01-01 12:00:00,000 [THREAD1] INFO MESSAGE1
  KEY1=VALUE1
  KEY2=VALUE2
2022-01-01 12:00:01,000 [THREAD2] ERROR MESSAGE2
  KEY3=VALUE3
  KEY4=VALUE4
EOF

# Create the expected output file "expected_output.txt" in the /home/user/parser directory
cat > /home/user/parser/expected_output.txt <<EOF
2022-01-01 12:00:00,000 [THREAD1] INFO MESSAGE1
KEY1=VALUE1
KEY2=VALUE2
2022-01-01 12:00:01,000 [THREAD2] ERROR MESSAGE2
KEY3=VALUE3
KEY4=VALUE4
EOF

# Change permissions to allow the user to read and write files
chmod -R 777 /home/user
