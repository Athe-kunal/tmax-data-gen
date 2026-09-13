# test_final_state.py

import os
import pytest
import stat

# Expected directories and files
EXPECTED_DIRECTORIES = [
    '/home/user/extracted_errors',
    '/home/user/important_errors',
    '/home/user/logs'
]
EXPECTED_LOG_FILE = '/home/user/logs/extraction_log.txt'
ARCHIVE_FILES = [
    '/home/user/backup_data/system_logs.tar.gz.00',
    '/home/user/backup_data/system_logs.tar.gz.01',
    '/home/user/backup_data/system_logs.tar.gz.02'
]

def test_directories_exist():
    """Test that the expected directories exist."""
    for directory in EXPECTED_DIRECTORIES:
        assert os.path.exists(directory), f"Directory '{directory}' does not exist."

def test_log_file_exists():
    """Test that the log file exists."""
    assert os.path.exists(EXPECTED_LOG_FILE), f"Log file '{EXPECTED_LOG_FILE}' does not exist."

def test_archive_files_exist():
    """Test that the archive files exist."""
    for archive_file in ARCHIVE_FILES:
        assert os.path.exists(archive_file), f"Archive file '{archive_file}' does not exist."

def test_log_file_contents():
    """Test the contents of the log file."""
    with open(EXPECTED_LOG_FILE, 'r') as log_file:
        log_contents = log_file.readlines()

    # Extracted files and their corresponding hard links
    extracted_files = [line.strip().split(': ')[1] for line in log_contents if line.startswith('Extracted file: ')]
    hard_links = [line.strip().split(': ')[1] for line in log_contents if line.startswith('Hard link: ')]

    # Check that the number of extracted files and hard links match
    assert len(extracted_files) == len(hard_links), "Number of extracted files and hard links do not match."

    # Check that the extracted files exist
    for file in extracted_files:
        assert os.path.exists(os.path.join('/home/user/extracted_errors', file)), f"Extracted file '{file}' does not exist."

    # Check that the hard links exist and share the same inodes as the extracted files
    for file, hard_link in zip(extracted_files, hard_links):
        assert os.path.exists(hard_link), f"Hard link '{hard_link}' does not exist."
        assert os.stat(os.path.join('/home/user/extracted_errors', file)).st_ino == os.stat(hard_link).st_ino, f"Extracted file '{file}' and hard link '{hard_link}' do not share the same inode."

def test_hard_links():
    """Test that the hard links are correctly created."""
    for file in os.listdir('/home/user/extracted_errors'):
        hard_link = os.path.join('/home/user/important_errors', f'CRITICAL_{file}')
        assert os.path.exists(hard_link), f"Hard link '{hard_link}' does not exist."
        assert os.path.islink(hard_link) is False, f"Hard link '{hard_link}' is a symbolic link, not a hard link."
        assert os.stat(os.path.join('/home/user/extracted_errors', file)).st_ino == os.stat(hard_link).st_ino, f"Extracted file '{file}' and hard link '{hard_link}' do not share the same inode."
