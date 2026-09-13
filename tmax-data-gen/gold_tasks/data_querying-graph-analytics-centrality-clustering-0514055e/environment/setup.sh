# Install necessary packages
apt update
apt install -y rust cargo

# Create directories and files
mkdir -p /home/user/citation_graph/src
mkdir -p /home/user/citation_graph/data

# Create a sample papers.jsonl file
cat > /home/user/citation_graph/data/papers.jsonl <<EOF
{"id": "paper1", "title": "Paper 1", "references": ["paper2", "paper3"]}
{"id": "paper2", "title": "Paper 2", "references": ["paper1", "paper4"]}
{"id": "paper3", "title": "Paper 3", "references": ["paper1", "paper2"]}
{"id": "paper4", "title": "Paper 4", "references": ["paper2", "paper3"]}
EOF

# Create a new Cargo project
cargo new --bin citation_graph
mv /home/user/citation_graph /home/user/citation_graph_original
mv /home/user/citation_graph_original /home/user/citation_graph

# Initialize the Rust project with the necessary dependencies
cat > /home/user/citation_graph/Cargo.toml <<EOF
[package]
name = "citation_graph"
version = "0.1.0"
edition = "2021"

[dependencies]
serde = { version = "1.0", features = ["derive"] }
serde_json = "1.0"
EOF

# Create a main.rs file
cat > /home/user/citation_graph/src/main.rs <<EOF
// This file will be modified by the agent to solve the task
fn main() {
    println!("Hello, world!");
}
EOF

# Set permissions
chmod -R 777 /home/user
