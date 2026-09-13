# test_final_state.py

import os
import csv
import pytest

# Define the expected values
EXPECTED_REDACTED_DATA = [
    ["id", "username", "email", "password_hash", "access_level"],
    ["1", "user1", "user1@example.com", "XXXXXX", "REDACTED"],
    ["2", "user2", "user2@example.com", "XXXXXX", "REDACTED"],
    ["3", "user3", "user3@example.com", "XXXXXX", "REDACTED"],
]

EXPECTED_AUDIT_REPORT = [
    "Admin Users: 2",
    "Suspicious Activity: 1",
    "Redacted Records: 3",
]

# Define the paths to the files
LOG_FILE = "/home/user/audit.log"
DATA_DUMP = "/home/user/data_dump.csv"
REDACTED_DATA = "/home/user/redacted_data.csv"
AUDIT_REPORT = "/home/user/audit_report.txt"

def test_redacted_data():
    # Check if the redacted data file exists
    assert os.path.exists(REDACTED_DATA), f"Redacted data file {REDACTED_DATA} does not exist"

    # Read the redacted data file
    with open(REDACTED_DATA, "r") as file:
        reader = csv.reader(file)
        data = list(reader)

    # Check if the redacted data matches the expected values
    assert data == EXPECTED_REDACTED_DATA, f"Redacted data {data} does not match expected values {EXPECTED_REDACTED_DATA}"

def test_audit_report():
    # Check if the audit report file exists
    assert os.path.exists(AUDIT_REPORT), f"Audit report file {AUDIT_REPORT} does not exist"

    # Read the audit report file
    with open(AUDIT_REPORT, "r") as file:
        report = file.readlines()

    # Check if the audit report matches the expected values
    assert [line.strip() for line in report] == EXPECTED_AUDIT_REPORT, f"Audit report {report} does not match expected values {EXPECTED_AUDIT_REPORT}"

def test_log_file():
    # Check if the log file exists
    assert os.path.exists(LOG_FILE), f"Log file {LOG_FILE} does not exist"

    # Read the log file
    with open(LOG_FILE, "r") as file:
        log_entries = file.readlines()

    # Check if the log file contains the expected entries
    expected_log_entries = [
        "10.0.0.1 - - [10/Oct/2023:13:55:36 +0000] \"GET /admin HTTP/1.1\" 200\n",
        "10.0.0.2 - - [10/Oct/2023:13:56:00 +0000] \"GET /user HTTP/1.1\" 200\n",
        "10.0.0.3 - - [10/Oct/2023:13:57:00 +0000] \"GET /admin HTTP/1.1\" 401\n",
    ]
    assert log_entries == expected_log_entries, f"Log file {log_entries} does not match expected entries {expected_log_entries}"

def test_data_dump():
    # Check if the data dump file exists
    assert os.path.exists(DATA_DUMP), f"Data dump file {DATA_DUMP} does not exist"

    # Read the data dump file
    with open(DATA_DUMP, "r") as file:
        reader = csv.reader(file)
        data = list(reader)

    # Check if the data dump matches the expected values
    expected_data = [
        ["id", "username", "email", "password_hash", "access_level"],
        ["1", "user1", "user1@example.com", "abc123", "admin"],
        ["2", "user2", "user2@example.com", "def456", "user"],
        ["3", "user3", "user3@example.com", "ghi789", "admin"],
    ]
    assert data == expected_data, f"Data dump {data} does not match expected values {expected_data}"

def test_admin_users():
    # Read the data dump file
    with open(DATA_DUMP, "r") as file:
        reader = csv.reader(file)
        data = list(reader)

    # Count the number of admin users
    admin_users = sum(1 for row in data[1:] if row[4] == "admin")

    # Check if the number of admin users matches the expected value
    assert admin_users == 2, f"Number of admin users {admin_users} does not match expected value 2"

def test_suspicious_activity():
    # Read the log file
    with open(LOG_FILE, "r") as file:
        log_entries = file.readlines()

    # Count the number of suspicious activity
    suspicious_activity = sum(1 for entry in log_entries if "401" in entry)

    # Check if the number of suspicious activity matches the expected value
    assert suspicious_activity == 1, f"Number of suspicious activity {suspicious_activity} does not match expected value 1"

def test_redacted_records():
    # Read the data dump file
    with open(DATA_DUMP, "r") as file:
        reader = csv.reader(file)
        data = list(reader)

    # Count the number of redacted records
    redacted_records = len(data) - 1

    # Check if the number of redacted records matches the expected value
    assert redacted_records == 3, f"Number of redacted records {redacted_records} does not match expected value 3"
