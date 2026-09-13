#!/bin/bash

# Create the necessary directories
mkdir -p /home/user/citation_graph/data
mkdir -p /home/user/citation_graph/src

# Create the papers.jsonl file with the given data
cat > /home/user/citation_graph/data/papers.jsonl <<EOF
{"id": "paper1", "title": "Paper 1", "references": ["paper2", "paper3"]}
{"id": "paper2", "title": "Paper 2", "references": ["paper1", "paper4"]}
{"id": "paper3", "title": "Paper 3", "references": ["paper1", "paper2"]}
{"id": "paper4", "title": "Paper 4", "references": ["paper2", "paper3"]}
EOF

# Create a basic Cargo project structure
cat > /home/user/citation_graph/Cargo.toml <<EOF
[package]
name = "citation_graph"
version = "0.1.0"
edition = "2021"

[dependencies]
serde = { version = "1.0", features = ["derive"] }
serde_json = "1.0"
EOF

# Create a basic main.rs file
cat > /home/user/citation_graph/src/main.rs <<EOF
// This file should be modified to solve the task
fn main() {
    // TO DO: implement the logic to read the papers.jsonl file, build the graph, calculate the in-degrees, and identify the most cited paper
}
EOF

# Install necessary dependencies
apt update
apt install -y cargo

# Change ownership and permissions
chown -R user:user /home/user
chmod -R 777 /home/user
