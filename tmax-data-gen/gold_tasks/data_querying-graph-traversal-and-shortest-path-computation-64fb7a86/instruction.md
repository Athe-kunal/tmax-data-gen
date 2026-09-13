As a database reliability engineer managing backups, I need to create a pipeline that processes a graph representing the network of database servers. The graph is stored in a file named `/home/user/servers.graph` and contains information about the servers and their connections. Each line in the file represents a connection between two servers, with the server IDs separated by a comma, along with the weight of the connection.

The goal is to write a Python script that performs a graph traversal and shortest path computation on this graph. The script should take the `/home/user/servers.graph` file as input and output the shortest path between two specified servers to `/home/user/shortest_path.txt`.

The graph traversal should start from a server specified in `/home/user/start_server.txt` and end at a server specified in `/home/user/end_server.txt`. The shortest path should be computed using Dijkstra's algorithm.

The output in `/home/user/shortest_path.txt` should contain the server IDs in the shortest path, separated by commas, along with the total weight of the path.

To verify the correctness of the pipeline, I will use a test script that checks the output in `/home/user/shortest_path.txt` against the expected output.

Please create a Python script at `/home/user/run_pipeline.py` that performs the graph traversal and shortest path computation. The script should be executable and should not require any external libraries.

The `/home/user/servers.graph` file contains the following data:
```
Server1,Server2,5
Server2,Server3,3
Server1,Server3,7
Server3,Server4,2
Server2,Server4,6
```
The `/home/user/start_server.txt` file contains the ID of the starting server:
```
Server1
```
The `/home/user/end_server.txt` file contains the ID of the ending server:
```
Server4
```
The expected output in `/home/user/shortest_path.txt` should be in the format `Server1,Server2,Server3,Server4,10`, where `10` is the total weight of the shortest path.

Please ensure that the `/home/user/run_pipeline.py` script is executable and that the output in `/home/user/shortest_path.txt` matches the expected output.

After executing the script, I want to verify that the output in `/home/user/shortest_path.txt` is correct. I will use a test script to check the output against the expected output. If the output is correct, the test script will pass, indicating that the pipeline is working correctly.

To verify the output, I will check the following:
- The output file `/home/user/shortest_path.txt` exists and is not empty.
- The output file contains the correct server IDs in the shortest path, separated by commas.
- The output file contains the correct total weight of the shortest path.
If all these conditions are met, the test script will pass, and I will know that the pipeline is working correctly.

To run the test script, I will use the command `python -m pytest` in the terminal. Please ensure that the test script is configured to run correctly with this command.

Create a log file `/home/user/pipeline.log` to record the execution of the pipeline, including any errors or exceptions that occur during execution.
