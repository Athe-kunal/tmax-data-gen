#!/bin/bash

# Create the devices.graph file
echo "Device1,Device2,5" > /home/user/devices.graph
echo "Device2,Device3,3" >> /home/user/devices.graph
echo "Device1,Device3,7" >> /home/user/devices.graph
echo "Device3,Device4,2" >> /home/user/devices.graph
echo "Device2,Device4,6" >> /home/user/devices.graph

# Create the start_device.txt file
echo "Device1" > /home/user/start_device.txt

# Create the end_device.txt file
echo "Device4" > /home/user/end_device.txt

# Create the test script
echo "#!/bin/bash" > /home/user/test_script.sh
echo "" >> /home/user/test_script.sh
echo "# Check if the output file exists and is not empty" >> /home/user/test_script.sh
echo "if [ -s \"/home/user/shortest_path.txt\" ]; then" >> /home/user/test_script.sh
echo "  # Read the output file" >> /home/user/test_script.sh
echo "  output=\$(cat \"/home/user/shortest_path.txt\")" >> /home/user/test_script.sh
echo "" >> /home/user/test_script.sh
echo "  # Check if the output contains the correct device IDs and total weight" >> /home/user/test_script.sh
echo "  if [ \"\$output\" = \"Device1,Device2,Device3,Device4,10\" ]; then" >> /home/user/test_script.sh
echo "    echo \"Test passed: Output is correct\"" >> /home/user/test_script.sh
echo "  else" >> /home/user/test_script.sh
echo "    echo \"Test failed: Output is incorrect\"" >> /home/user/test_script.sh
echo "  fi" >> /home/user/test_script.sh
echo "else" >> /home/user/test_script.sh
echo "  echo \"Test failed: Output file is empty or does not exist\"" >> /home/user/test_script.sh
echo "fi" >> /home/user/test_script.sh

# Make the test script executable
chmod +x /home/user/test_script.sh

# Create the run_pipeline.sh script (empty for now)
touch /home/user/run_pipeline.sh
chmod +x /home/user/run_pipeline.sh

# Set permissions
chmod -R 777 /home/user
