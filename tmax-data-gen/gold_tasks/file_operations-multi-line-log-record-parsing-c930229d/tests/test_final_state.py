# test_final_state.py

import os
import pytest

def test_log_file_exists():
    """Check if the log file exists."""
    log_file_path = "/home/user/logs/config.log"
    assert os.path.exists(log_file_path), f"Log file {log_file_path} does not exist."

def test_extracted_log_file_exists():
    """Check if the extracted log file exists."""
    extracted_log_file_path = "/home/user/extracted_config_logs.txt"
    assert os.path.exists(extracted_log_file_path), f"Extracted log file {extracted_log_file_path} does not exist."

def test_log_file_contents():
    """Check if the log file has the expected contents."""
    log_file_path = "/home/user/logs/config.log"
    expected_contents = """2022-01-01 12:00:00 INFO This is a single-line log message
2022-01-01 12:00:01 ERROR This is a multi-line log message
that spans multiple lines
2022-01-01 12:00:02 WARNING Another single-line log message
"""
    with open(log_file_path, "r") as file:
        log_contents = file.read()
    assert log_contents == expected_contents, f"Log file {log_file_path} has unexpected contents."

def test_extracted_log_file_contents():
    """Check if the extracted log file has the expected contents."""
    extracted_log_file_path = "/home/user/extracted_config_logs.txt"
    expected_contents = """2022-01-01 12:00:00 INFO This is a single-line log message

2022-01-01 12:00:01 ERROR This is a multi-line log message
that spans multiple lines

2022-01-01 12:00:02 WARNING Another single-line log message
"""
    with open(extracted_log_file_path, "r") as file:
        extracted_log_contents = file.read()
    assert extracted_log_contents == expected_contents, f"Extracted log file {extracted_log_file_path} has unexpected contents."

def test_log_file_and_extracted_log_file_contents_match():
    """Check if the extracted log file contents match the expected output."""
    log_file_path = "/home/user/logs/config.log"
    extracted_log_file_path = "/home/user/extracted_config_logs.txt"
    expected_output = """2022-01-01 12:00:00 INFO This is a single-line log message

2022-01-01 12:00:01 ERROR This is a multi-line log message
that spans multiple lines

2022-01-01 12:00:02 WARNING Another single-line log message
"""
    with open(extracted_log_file_path, "r") as file:
        extracted_log_contents = file.read()
    assert extracted_log_contents == expected_output, f"Extracted log file {extracted_log_file_path} does not match expected output."
