As a researcher organizing datasets, I need to compute the shortest path distance in a graph represented by an edge list. I have a CSV file `/home/user/graph_edges.csv` containing three comma-separated columns: `source_node`, `target_node`, and `edge_weight`. However, this graph contains unweighted edges (all `edge_weight` values are 1), and I need to find the minimum number of hops between `NODE_42` and `NODE_91`. 

To start, I need to inspect the initial environment and identify the inputs, tools, and current state relevant to the task. The graph is directed, meaning edges point from `source_node` to `target_node`. My goal is to write a Rust script that reads `/home/user/graph_edges.csv`, computes the shortest path distance from `NODE_42` to `NODE_91`, and outputs the result to a file located at `/home/user/shortest_path_result.txt`.

The script should efficiently build the graph using an adjacency list (or equivalent index strategy) before performing the traversal. Since the graph is unweighted, the shortest path distance will be the minimum number of hops between the two nodes. If there is no path between the nodes, the script should output `-1` to indicate that.

To verify the result, I will use a test command that checks the contents of `/home/user/shortest_path_result.txt` against the expected output. The test command will be defined in the `test.sh` script located at `/home/user/test.sh`. 

The Rust script should be built using the `cargo build` command, and the test command should be executed using `cargo test`. I also want to log any intermediate results or errors to a file located at `/home/user/logs.txt` for debugging purposes. 

Please create the necessary scripts and files to solve this task. The final state of the system should include the following files:
- `/home/user/graph_edges.csv`: The input graph edge list.
- `/home/user/shortest_path_result.txt`: The output shortest path distance.
- `/home/user/logs.txt`: The log file for intermediate results and errors.
- `/home/user/src/main.rs`: The Rust script that computes the shortest path distance.
- `/home/user/Cargo.toml`: The Cargo configuration file.
