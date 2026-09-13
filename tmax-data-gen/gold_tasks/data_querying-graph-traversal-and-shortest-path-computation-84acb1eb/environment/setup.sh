#!/bin/bash

# Create the necessary directories and files
mkdir -p /home/user

# Create the graph_edges.csv file with the specified edges
echo "SOURCE_NODE,NODE_A,1" > /home/user/graph_edges.csv
echo "NODE_A,NODE_B,1" >> /home/user/graph_edges.csv
echo "NODE_B,NODE_C,1" >> /home/user/graph_edges.csv
echo "NODE_C,TARGET_NODE,1" >> /home/user/graph_edges.csv

# Create the expected_result.txt file with the expected output
echo "4" > /home/user/expected_result.txt

# Create the test.sh script to verify the result
echo "#!/bin/bash" > /home/user/test.sh
echo "if [ \$(cat /home/user/shortest_path_result.txt) -eq \$(cat /home/user/expected_result.txt) ]; then" >> /home/user/test.sh
echo "  echo 'Test passed'" >> /home/user/test.sh
echo "else" >> /home/user/test.sh
echo "  echo 'Test failed'" >> /home/user/test.sh
echo "fi" >> /home/user/test.sh
chmod +x /home/user/test.sh

# Create the logs.txt file for debugging purposes
touch /home/user/logs.txt

# Set the permissions for the user directory
chmod -R 777 /home/user
