# test_final_state.py
import pytest
import os
import re

# Define the expected values
expected_alpha = 0.4
expected_beta = 0.2
expected_gamma = 0.1

# Define the sequences
sequences = [
    "seq1",
    "seq2",
    "seq3"
]

# Define the absolute paths
sequences_file = "/home/user/sequences.fasta"
results_file = "/home/user/results.txt"
log_file = "/home/user/log.txt"

# Define the tolerance for floating point comparisons
tolerance = 1e-6

def test_sequences_file_exists():
    """Test if the sequences file exists"""
    assert os.path.exists(sequences_file)

def test_results_file_exists():
    """Test if the results file exists"""
    assert os.path.exists(results_file)

def test_log_file_exists():
    """Test if the log file exists"""
    assert os.path.exists(log_file)

def test_results_file_contents():
    """Test the contents of the results file"""
    with open(results_file, "r") as f:
        lines = f.readlines()
        # Check if the number of lines is correct
        assert len(lines) == len(sequences) + 1  # +1 for the header
        # Check the header
        assert lines[0].strip() == "sequence_id alpha beta gamma"
        # Check each line
        for i, line in enumerate(lines[1:]):
            sequence_id, alpha, beta, gamma = line.strip().split()
            assert sequence_id == sequences[i]
            assert abs(float(alpha) - expected_alpha) < tolerance
            assert abs(float(beta) - expected_beta) < tolerance
            assert abs(float(gamma) - expected_gamma) < tolerance

def test_log_file_contents():
    """Test the contents of the log file"""
    with open(log_file, "r") as f:
        lines = f.readlines()
        # Check if the number of lines is correct
        assert len(lines) == len(sequences) * 2  # 2 lines per sequence
        # Check each pair of lines
        for i in range(0, len(lines), 2):
            sequence_id = sequences[i // 2]
            assert lines[i].strip() == f"Sequence ID: {sequence_id}"
            match = re.match(r"Optimized Parameters: alpha = ([0-9\.]+), beta = ([0-9\.]+), gamma = ([0-9\.]+)", lines[i + 1].strip())
            assert match
            alpha, beta, gamma = float(match.group(1)), float(match.group(2)), float(match.group(3))
            assert abs(alpha - expected_alpha) < tolerance
            assert abs(beta - expected_beta) < tolerance
            assert abs(gamma - expected_gamma) < tolerance
