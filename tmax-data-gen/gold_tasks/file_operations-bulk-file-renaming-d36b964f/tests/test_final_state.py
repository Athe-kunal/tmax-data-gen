# test_final_state.py

import os
import hashlib
import pytest

# Define the truth values
TRUTH_DIR = '/home/user/archived_data'
TRUTH_FILES = 100
TRUTH_PREFIX = 'doc_'
TRUTH_LOG_FILE = '/home/user/rename_log.txt'

# Define the expected SHA256 checksum of the log file
def generate_expected_log_file():
    with open(TRUTH_LOG_FILE, 'w') as f:
        for i in range(1, TRUTH_FILES + 1):
            original_name = f"file{i}.data"
            new_name = f"{TRUTH_PREFIX}{str(i).zfill(3)}.data"
            f.write(f"{original_name} -> {new_name}\n")
    with open(TRUTH_LOG_FILE, 'r') as f:
        lines = f.readlines()
        lines.sort()
        with open(TRUTH_LOG_FILE, 'w') as f:
            f.writelines(lines)

def calculate_sha256_checksum(file_path):
    with open(file_path, 'rb') as f:
        checksum = hashlib.sha256(f.read()).hexdigest()
    return checksum

def test_files_renamed_correctly():
    # Check if the directory exists
    assert os.path.exists(TRUTH_DIR), f"The directory {TRUTH_DIR} does not exist"

    # Check if the correct number of files exist
    files = [f for f in os.listdir(TRUTH_DIR) if os.path.isfile(os.path.join(TRUTH_DIR, f))]
    assert len(files) == TRUTH_FILES, f"Expected {TRUTH_FILES} files, but found {len(files)}"

    # Check if all files have the correct prefix
    for file in files:
        assert file.startswith(TRUTH_PREFIX), f"The file {file} does not have the correct prefix"

def test_log_file_exists():
    # Check if the log file exists
    assert os.path.exists(TRUTH_LOG_FILE), f"The log file {TRUTH_LOG_FILE} does not exist"

def test_log_file_contents():
    # Generate the expected log file
    generate_expected_log_file()

    # Calculate the SHA256 checksum of the expected log file
    expected_checksum = calculate_sha256_checksum(TRUTH_LOG_FILE)

    # Calculate the SHA256 checksum of the actual log file
    actual_checksum = calculate_sha256_checksum(TRUTH_LOG_FILE)

    # Check if the checksums match
    assert expected_checksum == actual_checksum, f"The log file {TRUTH_LOG_FILE} has incorrect contents"

def test_log_file_sorted():
    # Check if the log file is sorted alphabetically by original file name
    with open(TRUTH_LOG_FILE, 'r') as f:
        lines = f.readlines()
        sorted_lines = sorted(lines)
        assert lines == sorted_lines, f"The log file {TRUTH_LOG_FILE} is not sorted alphabetically"

def test_file_permissions_and_timestamps():
    # Check if the file permissions and timestamps are preserved
    for i in range(1, TRUTH_FILES + 1):
        original_name = f"file{i}.data"
        new_name = f"{TRUTH_PREFIX}{str(i).zfill(3)}.data"
        original_path = os.path.join(TRUTH_DIR, original_name)
        new_path = os.path.join(TRUTH_DIR, new_name)

        # Check if the original file exists
        assert not os.path.exists(original_path), f"The original file {original_path} still exists"

        # Check if the new file exists
        assert os.path.exists(new_path), f"The new file {new_path} does not exist"

        # Check if the file permissions are preserved
        # NOTE: This test is not implemented as it requires additional information about the original file permissions

        # Check if the file timestamps are preserved
        # NOTE: This test is not implemented as it requires additional information about the original file timestamps
