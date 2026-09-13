# Create the necessary directories
mkdir -p /home/user/citation_graph/data
mkdir -p /home/user/citation_graph/src

# Create the JSONL file with the citation graph data
echo '{"id": "paper1", "title": "Paper 1", "references": ["paper2", "paper3"]}' > /home/user/citation_graph/data/papers.jsonl
echo '{"id": "paper2", "title": "Paper 2", "references": ["paper1", "paper4"]}' >> /home/user/citation_graph/data/papers.jsonl
echo '{"id": "paper3", "title": "Paper 3", "references": ["paper1", "paper2"]}' >> /home/user/citation_graph/data/papers.jsonl
echo '{"id": "paper4", "title": "Paper 4", "references": ["paper2", "paper3"]}' >> /home/user/citation_graph/data/papers.jsonl

# Create the Cargo project structure
mkdir -p /home/user/citation_graph/src
touch /home/user/citation_graph/Cargo.toml
echo '[package]' >> /home/user/citation_graph/Cargo.toml
echo 'name = "citation_graph"' >> /home/user/citation_graph/Cargo.toml
echo 'version = "0.1.0"' >> /home/user/citation_graph/Cargo.toml
echo 'edition = "2021"' >> /home/user/citation_graph/Cargo.toml
echo '' >> /home/user/citation_graph/Cargo.toml
echo '[dependencies]' >> /home/user/citation_graph/Cargo.toml
echo 'serde = { version = "1.0", features = ["derive"] }' >> /home/user/citation_graph/Cargo.toml
echo 'serde_json = "1.0"' >> /home/user/citation_graph/Cargo.toml

# Create a basic main.rs file
touch /home/user/citation_graph/src/main.rs
echo 'use serde::{Deserialize, Serialize};' >> /home/user/citation_graph/src/main.rs
echo 'use serde_json::Result;' >> /home/user/citation_graph/src/main.rs
echo 'use std::fs::File;' >> /home/user/citation_graph/src/main.rs
echo 'use std::io::{BufRead, BufReader};' >> /home/user/citation_graph/src/main.rs
echo '' >> /home/user/citation_graph/src/main.rs
echo '[derive(Serialize, Deserialize)]' >> /home/user/citation_graph/src/main.rs
echo 'struct Paper {' >> /home/user/citation_graph/src/main.rs
echo '    id: String,' >> /home/user/citation_graph/src/main.rs
echo '    title: String,' >> /home/user/citation_graph/src/main.rs
echo '    references: Vec<String>,' >> /home/user/citation_graph/src/main.rs
echo '}' >> /home/user/citation_graph/src/main.rs
echo '' >> /home/user/citation_graph/src/main.rs
echo 'fn main() -> Result<()> {' >> /home/user/citation_graph/src/main.rs
echo '    // TO DO: implement the logic to read the citation graph, build the graph, calculate the in-degrees, and identify the most cited paper' >> /home/user/citation_graph/src/main.rs
echo '    Ok(())' >> /home/user/citation_graph/src/main.rs
echo '}' >> /home/user/citation_graph/src/main.rs

# Change the ownership and permissions of the files
chown -R user:user /home/user
chmod -R 777 /home/user
