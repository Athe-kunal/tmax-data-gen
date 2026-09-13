# test_final_state.py

import os
import json
import csv
import pytest

# Define the paths to the base backup directory, incremental backup directory, and log file
base_backup_dir = "/home/user/base_backup"
inc_backup_dir = "/home/user/inc_backup"
log_file = "/home/user/sync.log"
backups_json = "/home/user/backups.json"
dedup_report_csv = "/home/user/dedup_report.csv"
latest_backup_link = "/home/user/latest_backup"

def test_backups_json():
    # Check if the backups.json file exists and has the correct contents
    assert os.path.exists(backups_json)
    with open(backups_json, "r") as f:
        data = json.load(f)
        assert data["base"] == base_backup_dir
        assert data["inc"] == inc_backup_dir

def test_sync_log():
    # Check if the sync.log file exists and has the correct contents
    assert os.path.exists(log_file)
    with open(log_file, "r") as f:
        lines = f.readlines()
        assert len(lines) == 9
        assert lines[0].strip() == "FILE: file1.txt"
        assert lines[1].strip() == "SIZE: 1024"
        assert lines[2].strip() == "STATUS: SUCCESS"
        assert lines[3].strip() == "FILE: file2.txt"
        assert lines[4].strip() == "SIZE: 2048"
        assert lines[5].strip() == "STATUS: SUCCESS"
        assert lines[6].strip() == "FILE: file3.txt"
        assert lines[7].strip() == "SIZE: 4096"
        assert lines[8].strip() == "STATUS: FAILED"

def test_dedup_report_csv():
    # Check if the dedup_report.csv file exists and has the correct contents
    assert os.path.exists(dedup_report_csv)
    with open(dedup_report_csv, "r") as f:
        reader = csv.reader(f)
        rows = list(reader)
        assert len(rows) == 3
        assert rows[0] == ["filename", "saved_bytes"]
        assert rows[1] == ["file1.txt", "1024"]
        assert rows[2] == ["file2.txt", "2048"]

def test_latest_backup_link():
    # Check if the latest_backup link exists and points to the correct directory
    assert os.path.islink(latest_backup_link)
    assert os.readlink(latest_backup_link) == inc_backup_dir

def test_base_backup_dir_unchanged():
    # Check if the contents of the base backup directory remain unchanged
    assert os.path.exists(base_backup_dir)
    assert os.path.isdir(base_backup_dir)
    # Add additional assertions here to check the contents of the base backup directory

def test_inc_backup_dir():
    # Check if the incremental backup directory exists and contains the expected files
    assert os.path.exists(inc_backup_dir)
    assert os.path.isdir(inc_backup_dir)
    # Add additional assertions here to check the contents of the incremental backup directory

def test_hardlinks():
    # Check if the files in the incremental backup directory are hardlinked to the base backup directory
    for filename in ["file1.txt", "file2.txt"]:
        base_file_path = os.path.join(base_backup_dir, filename)
        inc_file_path = os.path.join(inc_backup_dir, filename)
        assert os.path.exists(base_file_path)
        assert os.path.exists(inc_file_path)
        assert os.path.samefile(base_file_path, inc_file_path)

# Run the tests
pytest.main([__file__])
