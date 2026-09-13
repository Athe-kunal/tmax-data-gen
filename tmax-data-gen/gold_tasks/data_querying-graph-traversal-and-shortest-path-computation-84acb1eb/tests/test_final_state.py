# test_final_state.py

import os
import pytest

# Constants
SOURCE_NODE = 'SOURCE_NODE'
TARGET_NODE = 'TARGET_NODE'
GRAPH_EDGES_FILE = '/home/user/graph_edges.csv'
EXPECTED_RESULT_FILE = '/home/user/expected_result.txt'
RESULT_FILE = '/home/user/shortest_path_result.txt'
TEST_SCRIPT = '/home/user/test.sh'
LOGS_FILE = '/home/user/logs.txt'

def test_graph_edges_file_exists():
    """Check if the graph edges file exists."""
    assert os.path.exists(GRAPH_EDGES_FILE), f"Graph edges file {GRAPH_EDGES_FILE} does not exist."

def test_expected_result_file_exists():
    """Check if the expected result file exists."""
    assert os.path.exists(EXPECTED_RESULT_FILE), f"Expected result file {EXPECTED_RESULT_FILE} does not exist."

def test_result_file_exists():
    """Check if the result file exists."""
    assert os.path.exists(RESULT_FILE), f"Result file {RESULT_FILE} does not exist."

def test_test_script_exists():
    """Check if the test script exists."""
    assert os.path.exists(TEST_SCRIPT), f"Test script {TEST_SCRIPT} does not exist."

def test_logs_file_exists():
    """Check if the logs file exists."""
    assert os.path.exists(LOGS_FILE), f"Logs file {LOGS_FILE} does not exist."

def test_result_file_contents():
    """Check if the result file contains the expected output."""
    with open(EXPECTED_RESULT_FILE, 'r') as expected_file:
        expected_output = expected_file.read().strip()

    with open(RESULT_FILE, 'r') as result_file:
        result_output = result_file.read().strip()

    assert result_output == expected_output, f"Result file {RESULT_FILE} does not contain the expected output."

def test_test_script_output():
    """Check if the test script outputs the expected result."""
    # Run the test script and capture its output
    test_script_output = os.popen(f"bash {TEST_SCRIPT}").read().strip()

    assert test_script_output == "Test passed", f"Test script {TEST_SCRIPT} did not output the expected result."

def test_shortest_path_distance():
    """Check if the shortest path distance is correct."""
    # Read the graph edges file
    graph = {}
    with open(GRAPH_EDGES_FILE, 'r') as graph_file:
        for line in graph_file:
            source, target, weight = line.strip().split(',')
            if source not in graph:
                graph[source] = []
            graph[source].append(target)

    # Perform BFS to find the shortest path distance
    queue = [(SOURCE_NODE, 0)]
    visited = set()
    while queue:
        node, distance = queue.pop(0)
        if node == TARGET_NODE:
            assert distance == 4, f"Shortest path distance is not 4, but {distance}."
            return
        if node in visited:
            continue
        visited.add(node)
        if node in graph:
            for neighbor in graph[node]:
                queue.append((neighbor, distance + 1))

    assert False, "Target node not reachable from source node."

# Run the tests
pytest.main([__file__])
