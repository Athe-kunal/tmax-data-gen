As a business-intelligence developer publishing dashboards, I need to create a pipeline that processes a graph representing a network of IoT devices. The graph is stored in a file named `/home/user/devices.graph` and contains information about the devices and their connections. Each line in the file represents a connection between two devices, with the device IDs separated by a comma, along with the weight of the connection.

The goal is to write a Bash script that performs a graph traversal and shortest path computation on this graph. The script should take the `/home/user/devices.graph` file as input and output the shortest path between two specified devices to `/home/user/shortest_path.txt`.

The graph traversal should start from a device specified in `/home/user/start_device.txt` and end at a device specified in `/home/user/end_device.txt`. The shortest path should be computed using Dijkstra's algorithm.

The output in `/home/user/shortest_path.txt` should contain the device IDs in the shortest path, separated by commas, along with the total weight of the path.

To verify the correctness of the pipeline, I will use a test script that checks the output in `/home/user/shortest_path.txt` against the expected output.

Please create a Bash script at `/home/user/run_pipeline.sh` that performs the graph traversal and shortest path computation. The script should be executable and should not require any external libraries.

The `/home/user/devices.graph` file contains the following data:
```
Device1,Device2,5
Device2,Device3,3
Device1,Device3,7
Device3,Device4,2
Device2,Device4,6
```
The `/home/user/start_device.txt` file contains the ID of the starting device:
```
Device1
```
The `/home/user/end_device.txt` file contains the ID of the ending device:
```
Device4
```
The expected output in `/home/user/shortest_path.txt` should be in the format `Device1,Device2,Device3,Device4,10`, where `10` is the total weight of the shortest path.

Please ensure that the `/home/user/run_pipeline.sh` script is executable and that the output in `/home/user/shortest_path.txt` matches the expected output.

After executing the script, I want to verify that the output in `/home/user/shortest_path.txt` is correct. I will use a test script to check the output against the expected output. If the output is correct, the test script will pass, indicating that the pipeline is working correctly.

To verify the output, I will check the following:
- The output file `/home/user/shortest_path.txt` exists and is not empty.
- The output file contains the correct device IDs in the shortest path, separated by commas.
- The output file contains the correct total weight of the shortest path.
If all these conditions are met, the test script will pass, and I will know that the pipeline is working correctly.
