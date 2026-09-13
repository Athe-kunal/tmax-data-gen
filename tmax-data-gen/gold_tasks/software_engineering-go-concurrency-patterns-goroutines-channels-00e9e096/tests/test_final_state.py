# test_final_state.py

import os
import pytest

# Define the expected contents of the response_times.txt file
expected_response_times = {
    "API1": 0.5,
    "API2": 0.7
}

# Define the absolute path to the response_times.txt file
response_times_file = "/home/user/response_times.txt"

def test_response_times_file_exists():
    """Check if the response_times.txt file exists"""
    assert os.path.exists(response_times_file)

def test_response_times_file_contents():
    """Check the contents of the response_times.txt file"""
    with open(response_times_file, "r") as f:
        lines = f.readlines()
        for line in lines:
            api, response_time = line.strip().split(",")
            assert api in expected_response_times
            assert float(response_time) > 0

def test_response_times_file_format():
    """Check the format of the response_times.txt file"""
    with open(response_times_file, "r") as f:
        lines = f.readlines()
        for line in lines:
            api, response_time = line.strip().split(",")
            assert len(api) > 0
            assert response_time.replace('.', '', 1).isdigit()

def test_response_times_file_api_names():
    """Check the API names in the response_times.txt file"""
    with open(response_times_file, "r") as f:
        lines = f.readlines()
        api_names = [line.strip().split(",")[0] for line in lines]
        assert "API1" in api_names
        assert "API2" in api_names

def test_response_times_file_response_times():
    """Check the response times in the response_times.txt file"""
    with open(response_times_file, "r") as f:
        lines = f.readlines()
        response_times = [float(line.strip().split(",")[1]) for line in lines]
        assert all(response_time > 0 for response_time in response_times)

def test_response_times_file_line_count():
    """Check the number of lines in the response_times.txt file"""
    with open(response_times_file, "r") as f:
        lines = f.readlines()
        assert len(lines) == len(expected_response_times)
