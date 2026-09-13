# Create the home directory for the user
mkdir -p /home/user

# Create the servers.graph file
echo "Server1,Server2,5" > /home/user/servers.graph
echo "Server2,Server3,3" >> /home/user/servers.graph
echo "Server1,Server3,7" >> /home/user/servers.graph
echo "Server3,Server4,2" >> /home/user/servers.graph
echo "Server2,Server4,6" >> /home/user/servers.graph

# Create the start_server.txt file
echo "Server1" > /home/user/start_server.txt

# Create the end_server.txt file
echo "Server4" > /home/user/end_server.txt

# Create the pipeline.log file
touch /home/user/pipeline.log

# Install pytest
pip3 install pytest

# Create a test script
echo "import pytest" > /home/user/test_pipeline.py
echo "def test_shortest_path():" >> /home/user/test_pipeline.py
echo "    with open('/home/user/shortest_path.txt', 'r') as f:" >> /home/user/test_pipeline.py
echo "        output = f.read().strip()" >> /home/user/test_pipeline.py
echo "    expected_output = 'Server1,Server2,Server3,Server4,10'" >> /home/user/test_pipeline.py
echo "    assert output == expected_output" >> /home/user/test_pipeline.py

# Make the test script executable
chmod 755 /home/user/test_pipeline.py

# Change the ownership of the files to the user
chown -R user:user /home/user

# Give the user read, write, and execute permissions
chmod -R 777 /home/user
