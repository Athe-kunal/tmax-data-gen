# test_final_state.py

import os
import pytest
import csv
from collections import defaultdict, deque

# Define the absolute paths
GRAPH_EDGES_CSV = '/home/user/graph_edges.csv'
SHORTEST_PATH_RESULT_TXT = '/home/user/shortest_path_result.txt'
LOGS_TXT = '/home/user/logs.txt'
MAIN_RS = '/home/user/src/main.rs'
CARGO_TOML = '/home/user/Cargo.toml'

def build_graph(graph_edges_csv):
    """
    Build an adjacency list representation of the graph from the edge list.
    """
    graph = defaultdict(list)
    with open(graph_edges_csv, 'r') as f:
        reader = csv.reader(f)
        for row in reader:
            source_node, target_node, _ = row
            graph[source_node].append(target_node)
    return graph

def bfs(graph, start_node, target_node):
    """
    Perform a breadth-first search traversal from the start node to find the shortest path distance to the target node.
    """
    queue = deque([(start_node, 0)])
    visited = set()
    while queue:
        node, distance = queue.popleft()
        if node == target_node:
            return distance
        if node in visited:
            continue
        visited.add(node)
        for neighbor in graph[node]:
            queue.append((neighbor, distance + 1))
    return -1

def test_final_state():
    # Check if the necessary files exist
    assert os.path.exists(GRAPH_EDGES_CSV)
    assert os.path.exists(SHORTEST_PATH_RESULT_TXT)
    assert os.path.exists(LOGS_TXT)
    assert os.path.exists(MAIN_RS)
    assert os.path.exists(CARGO_TOML)

    # Build the graph and perform BFS traversal
    graph = build_graph(GRAPH_EDGES_CSV)
    shortest_path_distance = bfs(graph, 'NODE_42', 'NODE_91')

    # Check the contents of the shortest path result file
    with open(SHORTEST_PATH_RESULT_TXT, 'r') as f:
        result = int(f.read().strip())
    assert result == shortest_path_distance

    # Check the contents of the log file (assuming it's not empty)
    assert os.path.getsize(LOGS_TXT) > 0

    # Check the contents of the Cargo.toml file (assuming it's not empty)
    assert os.path.getsize(CARGO_TOML) > 0

    # Check the contents of the main.rs file (assuming it's not empty)
    assert os.path.getsize(MAIN_RS) > 0

# Run the test
pytest.main([__file__])
