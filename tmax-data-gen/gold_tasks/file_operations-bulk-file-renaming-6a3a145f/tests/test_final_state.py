# test_final_state.py

import os
import pytest
from typing import Dict

# Define the file types and their corresponding prefixes
FILE_TYPES: Dict[str, str] = {
    '.py': 'script_',
    '.txt': 'data_',
    '.md': 'doc_'
}

# Define the expected files and their corresponding new names
EXPECTED_FILES: Dict[str, str] = {
    'file1.py': 'script_001.py',
    'file2.txt': 'data_001.txt',
    'file3.md': 'doc_001.md',
    'file4.py': 'script_002.py',
    'file5.txt': 'data_002.txt',
    'file6.md': 'doc_002.md'
}

def test_rename_log_file_exists():
    """Test that the rename log file exists."""
    log_file_path = '/home/user/rename_log.txt'
    assert os.path.exists(log_file_path), f"The rename log file {log_file_path} does not exist."

def test_rename_log_file_contents():
    """Test that the rename log file contains the correct contents."""
    log_file_path = '/home/user/rename_log.txt'
    with open(log_file_path, 'r') as f:
        log_file_contents = f.readlines()

    expected_log_file_contents = [
        f"{original_name} -> {new_name}\n"
        for original_name, new_name in EXPECTED_FILES.items()
    ]

    assert log_file_contents == expected_log_file_contents, (
        f"The rename log file {log_file_path} does not contain the correct contents. "
        f"Expected:\n{expected_log_file_contents}\nGot:\n{log_file_contents}"
    )

def test_deliverables_directory_contents():
    """Test that the deliverables directory contains the correct files."""
    deliverables_dir = '/home/user/deliverables'
    assert os.path.exists(deliverables_dir), f"The deliverables directory {deliverables_dir} does not exist."

    files_in_deliverables_dir = os.listdir(deliverables_dir)
    expected_files_in_deliverables_dir = list(EXPECTED_FILES.values())

    assert set(files_in_deliverables_dir) == set(expected_files_in_deliverables_dir), (
        f"The deliverables directory {deliverables_dir} does not contain the correct files. "
        f"Expected:\n{expected_files_in_deliverables_dir}\nGot:\n{files_in_deliverables_dir}"
    )

def test_file_types_and_prefixes():
    """Test that the file types and prefixes are correct."""
    for file_name, new_name in EXPECTED_FILES.items():
        file_extension = os.path.splitext(file_name)[1]
        prefix = FILE_TYPES.get(file_extension)
        assert new_name.startswith(prefix), (
            f"The file {file_name} has the wrong prefix. "
            f"Expected prefix: {prefix}, Got prefix: {new_name.split('_')[0]}"
        )

def test_unique_identifiers():
    """Test that the unique identifiers are correct."""
    unique_identifiers = []
    for new_name in EXPECTED_FILES.values():
        unique_identifier = new_name.split('_')[1].split('.')[0]
        unique_identifiers.append(unique_identifier)

    expected_unique_identifiers = ['001', '001', '001', '002', '002', '002']
    assert unique_identifiers == expected_unique_identifiers, (
        f"The unique identifiers are not correct. "
        f"Expected:\n{expected_unique_identifiers}\nGot:\n{unique_identifiers}"
    )
