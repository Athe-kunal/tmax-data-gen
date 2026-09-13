As a data analyst processing CSV files, I need to compute the shortest path distance in a graph represented by an edge list. I have a CSV file `/home/user/graph_edges.csv` containing three comma-separated columns: `source_node`, `target_node`, and `edge_weight`. However, this graph contains unweighted edges (all `edge_weight` values are 1), and I need to find the minimum number of hops between `SOURCE_NODE` and `TARGET_NODE`. 

To start, I need to inspect the initial environment and identify the inputs, tools, and current state relevant to the task. The graph is directed, meaning edges point from `source_node` to `target_node`. My goal is to write a script that reads `/home/user/graph_edges.csv`, computes the shortest path distance from `SOURCE_NODE` to `TARGET_NODE`, and outputs the result to a file located at `/home/user/shortest_path_result.txt`.

The script should efficiently build the graph using an adjacency list (or equivalent index strategy) before performing the traversal. Since the graph is unweighted, the shortest path distance will be the minimum number of hops between the two nodes. If there is no path between the nodes, the script should output `-1` to indicate that.

To verify the result, I will use a test command that checks the contents of `/home/user/shortest_path_result.txt` against the expected output. The test command will be defined in the `test.sh` script located at `/home/user/test.sh`. 

Please create the necessary scripts and files to solve this task. Make sure to log any intermediate results or errors to a file located at `/home/user/logs.txt` for debugging purposes.
