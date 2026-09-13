# test_final_state.py

import json
import os
import pytest
import csv

# Ground-truth data
TRUTH_BACKUPS_JSON = {
    "base": "/home/user/base_backup",
    "inc": "/home/user/inc_backup"
}

TRUTH_SYNC_LOG = [
    {"filename": "file1.txt", "size": 1024, "status": "SUCCESS"},
    {"filename": "file2.txt", "size": 2048, "status": "SUCCESS"},
    {"filename": "file3.txt", "size": 4096, "status": "FAILED"}
]

TRUTH_BASE_BACKUP_FILES = {
    "file1.txt": 1024,
    "file2.txt": 2048
}

TRUTH_INC_BACKUP_FILES = {
    "file1.txt": 1024,
    "file2.txt": 2048,
    "file3.txt": 4096
}

TRUTH_DEDUP_REPORT_CSV = [
    {"filename": "file1.txt", "saved_bytes": 1024},
    {"filename": "file2.txt", "saved_bytes": 2048}
]

TRUTH_LATEST_BACKUP_LINK = "/home/user/inc_backup"

def test_backups_json():
    """Test if the backups.json file contains the correct metadata"""
    with open("/home/user/backups.json", "r") as f:
        backups_json = json.load(f)
    assert backups_json == TRUTH_BACKUPS_JSON

def test_sync_log():
    """Test if the sync.log file contains the correct records"""
    sync_log_records = []
    with open("/home/user/sync.log", "r") as f:
        lines = f.readlines()
        for i in range(0, len(lines), 3):
            filename = lines[i].strip().split(": ")[1]
            size = int(lines[i+1].strip().split(": ")[1])
            status = lines[i+2].strip().split(": ")[1]
            sync_log_records.append({"filename": filename, "size": size, "status": status})
    assert sync_log_records == TRUTH_SYNC_LOG

def test_base_backup_files():
    """Test if the base backup directory contains the correct files"""
    base_backup_files = {}
    for filename in os.listdir(TRUTH_BACKUPS_JSON["base"]):
        file_path = os.path.join(TRUTH_BACKUPS_JSON["base"], filename)
        if os.path.isfile(file_path):
            base_backup_files[filename] = os.path.getsize(file_path)
    assert base_backup_files == TRUTH_BASE_BACKUP_FILES

def test_inc_backup_files():
    """Test if the incremental backup directory contains the correct files"""
    inc_backup_files = {}
    for filename in os.listdir(TRUTH_BACKUPS_JSON["inc"]):
        file_path = os.path.join(TRUTH_BACKUPS_JSON["inc"], filename)
        if os.path.isfile(file_path):
            inc_backup_files[filename] = os.path.getsize(file_path)
    assert inc_backup_files == TRUTH_INC_BACKUP_FILES

def test_dedup_report_csv():
    """Test if the dedup_report.csv file contains the correct records"""
    dedup_report_csv_records = []
    with open("/home/user/dedup_report.csv", "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            dedup_report_csv_records.append({"filename": row["filename"], "saved_bytes": int(row["saved_bytes"])})
    assert dedup_report_csv_records == TRUTH_DEDUP_REPORT_CSV

def test_latest_backup_link():
    """Test if the latest_backup link points to the correct directory"""
    latest_backup_link = os.readlink("/home/user/latest_backup")
    assert latest_backup_link == TRUTH_LATEST_BACKUP_LINK

def test_hardlinks():
    """Test if the files in the incremental backup directory are hardlinks to the base backup directory"""
    for filename in TRUTH_BASE_BACKUP_FILES:
        base_file_path = os.path.join(TRUTH_BACKUPS_JSON["base"], filename)
        inc_file_path = os.path.join(TRUTH_BACKUPS_JSON["inc"], filename)
        assert os.path.islink(inc_file_path) == False  # Check if it's a hardlink
        assert os.stat(base_file_path).st_ino == os.stat(inc_file_path).st_ino  # Check if it's the same file
