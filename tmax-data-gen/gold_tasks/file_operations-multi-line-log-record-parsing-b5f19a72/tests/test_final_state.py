# test_final_state.py

import os
import pytest

# Define the log directory and the test log file
LOG_DIRECTORY = "/home/user/logs"
TEST_LOG_FILE = "test.log"
EXPECTED_OUTPUT_FILE = "test.log.parsed"
VERIFICATION_LOG_FILE = "verification.log"

# Define the expected contents of the test log file and the expected output file
TEST_LOG_CONTENTS = """2022-01-01 12:00:00,000 [THREAD1] INFO MESSAGE1
  KEY1=VALUE1
  KEY2=VALUE2
2022-01-01 12:00:01,000 [THREAD2] ERROR MESSAGE2
  KEY3=VALUE3
  KEY4=VALUE4
"""

EXPECTED_OUTPUT_CONTENTS = """2022-01-01 12:00:00,000 [THREAD1] INFO MESSAGE1
KEY1=VALUE1
KEY2=VALUE2
2022-01-01 12:00:01,000 [THREAD2] ERROR MESSAGE2
KEY3=VALUE3
KEY4=VALUE4
"""

def test_log_file_exists():
    """Test that the test log file exists in the log directory."""
    log_file_path = os.path.join(LOG_DIRECTORY, TEST_LOG_FILE)
    assert os.path.exists(log_file_path), f"The test log file {TEST_LOG_FILE} does not exist in the log directory {LOG_DIRECTORY}"

def test_log_file_contents():
    """Test that the test log file has the expected contents."""
    log_file_path = os.path.join(LOG_DIRECTORY, TEST_LOG_FILE)
    with open(log_file_path, "r") as log_file:
        log_contents = log_file.read()
    assert log_contents == TEST_LOG_CONTENTS, f"The test log file {TEST_LOG_FILE} does not have the expected contents"

def test_expected_output_file_exists():
    """Test that the expected output file exists in the log directory."""
    expected_output_file_path = os.path.join(LOG_DIRECTORY, EXPECTED_OUTPUT_FILE)
    assert os.path.exists(expected_output_file_path), f"The expected output file {EXPECTED_OUTPUT_FILE} does not exist in the log directory {LOG_DIRECTORY}"

def test_expected_output_file_contents():
    """Test that the expected output file has the expected contents."""
    expected_output_file_path = os.path.join(LOG_DIRECTORY, EXPECTED_OUTPUT_FILE)
    with open(expected_output_file_path, "r") as expected_output_file:
        expected_output_contents = expected_output_file.read()
    assert expected_output_contents == EXPECTED_OUTPUT_CONTENTS, f"The expected output file {EXPECTED_OUTPUT_FILE} does not have the expected contents"

def test_verification_log_file_exists():
    """Test that the verification log file exists in the log directory."""
    verification_log_file_path = os.path.join(LOG_DIRECTORY, VERIFICATION_LOG_FILE)
    assert os.path.exists(verification_log_file_path), f"The verification log file {VERIFICATION_LOG_FILE} does not exist in the log directory {LOG_DIRECTORY}"

def test_original_log_file_not_modified():
    """Test that the original log file has not been modified."""
    log_file_path = os.path.join(LOG_DIRECTORY, TEST_LOG_FILE)
    with open(log_file_path, "r") as log_file:
        log_contents = log_file.read()
    assert log_contents == TEST_LOG_CONTENTS, f"The original log file {TEST_LOG_FILE} has been modified"

def test_parser_directory_exists():
    """Test that the parser directory exists."""
    parser_directory = "/home/user/parser"
    assert os.path.exists(parser_directory), f"The parser directory {parser_directory} does not exist"

def test_expected_output_file_in_parser_directory():
    """Test that the expected output file exists in the parser directory."""
    expected_output_file_path = os.path.join("/home/user/parser", "expected_output.txt")
    assert os.path.exists(expected_output_file_path), f"The expected output file expected_output.txt does not exist in the parser directory /home/user/parser"
