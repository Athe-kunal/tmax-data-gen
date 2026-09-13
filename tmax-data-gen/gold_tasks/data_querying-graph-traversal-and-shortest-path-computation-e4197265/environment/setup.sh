#!/bin/bash

# Install necessary packages
apt update
apt install -y rust cargo

# Create the user directory
mkdir -p /home/user

# Create the graph edge list file
echo "source_node,target_node,edge_weight" > /home/user/graph_edges.csv
echo "NODE_42,NODE_43,1" >> /home/user/graph_edges.csv
echo "NODE_43,NODE_44,1" >> /home/user/graph_edges.csv
echo "NODE_44,NODE_91,1" >> /home/user/graph_edges.csv

# Create the logs file
touch /home/user/logs.txt

# Create the Rust script directory
mkdir -p /home/user/src

# Create the Rust script
echo "// Import necessary libraries" > /home/user/src/main.rs
echo "use std::collections::HashMap;" >> /home/user/src/main.rs
echo "use std::collections::VecDeque;" >> /home/user/src/main.rs
echo "use std::fs::File;" >> /home/user/src/main.rs
echo "use std::io::{BufRead, BufReader};" >> /home/user/src/main.rs
echo "use std::io::Write;" >> /home/user/src/main.rs
echo "" >> /home/user/src/main.rs
echo "// Define a function to read the graph edge list and build an adjacency list" >> /home/user/src/main.rs
echo "fn read_graph(filename: &str) -> HashMap<String, Vec<String>> {" >> /home/user/src/main.rs
echo "    let file = File::open(filename).unwrap();" >> /home/user/src/main.rs
echo "    let reader = BufReader::new(file);" >> /home/user/src/main.rs
echo "    let mut graph: HashMap<String, Vec<String>> = HashMap::new();" >> /home/user/src/main.rs
echo "    for line in reader.lines() {" >> /home/user/src/main.rs
echo "        let line = line.unwrap();" >> /home/user/src/main.rs
echo "        let parts: Vec<&str> = line.split(',').collect();" >> /home/user/src/main.rs
echo "        if parts[0] != \"source_node\" {" >> /home/user/src/main.rs
echo "            let source_node = parts[0].to_string();" >> /home/user/src/main.rs
echo "            let target_node = parts[1].to_string();" >> /home/user/src/main.rs
echo "            graph.entry(source_node).or_insert(Vec::new()).push(target_node);" >> /home/user/src/main.rs
echo "        }" >> /home/user/src/main.rs
echo "    }" >> /home/user/src/main.rs
echo "    graph" >> /home/user/src/main.rs
echo "}" >> /home/user/src/main.rs
echo "" >> /home/user/src/main.rs
echo "// Define a function to perform a BFS traversal" >> /home/user/src/main.rs
echo "fn bfs(graph: &HashMap<String, Vec<String>>, start_node: &str, target_node: &str) -> i32 {" >> /home/user/src/main.rs
echo "    let mut queue: VecDeque<(String, i32)> = VecDeque::new();" >> /home/user/src/main.rs
echo "    let mut visited: HashMap<String, bool> = HashMap::new();" >> /home/user/src/main.rs
echo "    queue.push_back((start_node.to_string(), 0));" >> /home/user/src/main.rs
echo "    while let Some((node, distance)) = queue.pop_front() {" >> /home/user/src/main.rs
echo "        if node == target_node {" >> /home/user/src/main.rs
echo "            return distance;" >> /home/user/src/main.rs
echo "        }" >> /home/user/src/main.rs
echo "        if visited.contains_key(&node) {" >> /home/user/src/main.rs
echo "            continue;" >> /home/user/src/main.rs
echo "        }" >> /home/user/src/main.rs
echo "        visited.insert(node.clone(), true);" >> /home/user/src/main.rs
echo "        if let Some(neighbors) = graph.get(&node) {" >> /home/user/src/main.rs
echo "            for neighbor in neighbors {" >> /home/user/src/main.rs
echo "                queue.push_back((neighbor.clone(), distance + 1));" >> /home/user/src/main.rs
echo "            }" >> /home/user/src/main.rs
echo "        }" >> /home/user/src/main.rs
echo "    }" >> /home/user/src/main.rs
echo "    -1" >> /home/user/src/main.rs
echo "}" >> /home/user/src/main.rs
echo "" >> /home/user/src/main.rs
echo "// Define the main function" >> /home/user/src/main.rs
echo "fn main() {" >> /home/user/src/main.rs
echo "    let graph = read_graph(\"/home/user/graph_edges.csv\");" >> /home/user/src/main.rs
echo "    let distance = bfs(&graph, \"NODE_42\", \"NODE_91\");" >> /home/user/src/main.rs
echo "    let mut file = File::create(\"/home/user/shortest_path_result.txt\").unwrap();" >> /home/user/src/main.rs
echo "    file.write_all(distance.to_string().as_bytes()).unwrap();" >> /home/user/src/main.rs
echo "}" >> /home/user/src/main.rs

# Create the Cargo configuration file
echo "[package]" > /home/user/Cargo.toml
echo "name = \"shortest_path\"" >> /home/user/Cargo.toml
echo "version = \"0.1.0\"" >> /home/user/Cargo.toml
echo "edition = \"2021\"" >> /home/user/Cargo.toml
echo "" >> /home/user/Cargo.toml
echo "[dependencies]" >> /home/user/Cargo.toml

# Create the test script
echo "#!/bin/bash" > /home/user/test.sh
echo "expected_output=$(cat /home/user/shortest_path_result.txt)" >> /home/user/test.sh
echo "if [ \$expected_output -eq 2 ]; then" >> /home/user/test.sh
echo "    echo \"Test passed\"" >> /home/user/test.sh
echo "else" >> /home/user/test.sh
echo "    echo \"Test failed\"" >> /home/user/test.sh
echo "fi" >> /home/user/test.sh
chmod +x /home/user/test.sh

# Set permissions
chmod -R 777 /home/user
