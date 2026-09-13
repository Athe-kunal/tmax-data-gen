#!/bin/bash

# Create the SQLite database and table
sqlite3 /home/user/data.db "CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, department TEXT)"

# Insert data into the users table
sqlite3 /home/user/data.db "INSERT INTO users (id, name, department) VALUES (1, 'John', 'Sales')"
sqlite3 /home/user/data.db "INSERT INTO users (id, name, department) VALUES (2, 'Jane', 'Marketing')"
sqlite3 /home/user/data.db "INSERT INTO users (id, name, department) VALUES (3, 'Bob', 'IT')"
sqlite3 /home/user/data.db "INSERT INTO users (id, name, department) VALUES (4, 'Alice', 'HR')"
sqlite3 /home/user/data.db "INSERT INTO users (id, name, department) VALUES (5, 'Mike', 'Finance')"
sqlite3 /home/user/data.db "INSERT INTO users (id, name, department) VALUES (6, 'Emma', 'Sales')"
sqlite3 /home/user/data.db "INSERT INTO users (id, name, department) VALUES (7, 'Tom', 'Marketing')"
sqlite3 /home/user/data.db "INSERT INTO users (id, name, department) VALUES (8, 'Lisa', 'IT')"
sqlite3 /home/user/data.db "INSERT INTO users (id, name, department) VALUES (9, 'David', 'HR')"
sqlite3 /home/user/data.db "INSERT INTO users (id, name, department) VALUES (10, 'Sarah', 'Finance')"

# Create the interactions JSON file
cat > /home/user/interactions.json <<EOF
[
  {"src": 1, "dst": 2, "weight": 5},
  {"src": 1, "dst": 3, "weight": 3},
  {"src": 2, "dst": 4, "weight": 2},
  {"src": 3, "dst": 5, "weight": 4},
  {"src": 4, "dst": 6, "weight": 1},
  {"src": 5, "dst": 7, "weight": 6},
  {"src": 6, "dst": 8, "weight": 3},
  {"src": 7, "dst": 9, "weight": 2},
  {"src": 8, "dst": 10, "weight": 5},
  {"src": 9, "dst": 1, "weight": 4},
  {"src": 10, "dst": 2, "weight": 6}
]
EOF

# Install Rust and cargo
apt update
apt install -y rustc cargo

# Create the Rust program file
cat > /home/user/process_graph.rs <<EOF
// This file will be used by the agent to write the Rust program
EOF

# Make the directory and files writable
chmod -R 777 /home/user
