# test_final_state.py

import os
import hashlib
import pytest

def calculate_sha256(file_path):
    """Calculate the SHA-256 checksum of a file."""
    sha256 = hashlib.sha256()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256.update(chunk)
    return sha256.hexdigest()

def test_backup_directory_structure():
    """Test that the backup directory structure is correct."""
    backup_dir = '/home/user/backup'
    assert os.path.exists(backup_dir)
    assert os.path.exists(os.path.join(backup_dir, 'documents'))
    assert os.path.exists(os.path.join(backup_dir, 'images'))
    assert os.path.exists(os.path.join(backup_dir, 'videos'))

def test_files_in_backup_directory():
    """Test that all files are present in the backup directory."""
    data_dir = '/home/user/data'
    backup_dir = '/home/user/backup'
    for root, dirs, files in os.walk(data_dir):
        for file in files:
            file_path = os.path.join(root, file)
            relative_path = os.path.relpath(file_path, data_dir)
            backup_file_path = os.path.join(backup_dir, relative_path)
            assert os.path.exists(backup_file_path)

def test_manifest_file():
    """Test that the manifest file is correct."""
    backup_dir = '/home/user/backup'
    manifest_file_path = os.path.join(backup_dir, 'manifest.sha256')
    assert os.path.exists(manifest_file_path)
    with open(manifest_file_path, 'r') as f:
        manifest_lines = f.readlines()
    manifest_lines = [line.strip() for line in manifest_lines]
    manifest_lines.sort()
    for root, dirs, files in os.walk(backup_dir):
        for file in files:
            if file == 'manifest.sha256' or file == 'log.txt':
                continue
            file_path = os.path.join(root, file)
            relative_path = os.path.relpath(file_path, backup_dir)
            sha256 = calculate_sha256(file_path)
            expected_line = f'{sha256}  {relative_path}'
            assert expected_line in manifest_lines

def test_log_file():
    """Test that the log file is correct."""
    backup_dir = '/home/user/backup'
    log_file_path = os.path.join(backup_dir, 'log.txt')
    assert os.path.exists(log_file_path)
    with open(log_file_path, 'r') as f:
        log_line = f.read().strip()
    assert log_line == 'Backup created successfully.'

def test_manifest_file_sorted():
    """Test that the manifest file is sorted alphabetically by relative file path."""
    backup_dir = '/home/user/backup'
    manifest_file_path = os.path.join(backup_dir, 'manifest.sha256')
    with open(manifest_file_path, 'r') as f:
        manifest_lines = f.readlines()
    manifest_lines = [line.strip() for line in manifest_lines]
    sorted_manifest_lines = sorted(manifest_lines, key=lambda x: x.split('  ')[1])
    assert manifest_lines == sorted_manifest_lines
