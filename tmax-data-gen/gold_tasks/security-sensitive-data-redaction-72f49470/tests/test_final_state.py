# test_final_state.py

import pytest
import os
import csv
import re

# Define the expected values based on the truth data
expected_attacker_ip = "192.168.1.100"
expected_attack_timestamp = "10/Oct/2023:13:55:36 +0000"
expected_redacted_records = 3

# Define the expected redacted evidence file contents
expected_redacted_evidence = [
    ["id", "name", "email", "ssn", "cc_number"],
    ["1", "John Doe", "johndoe@example.com", "XXX-XX-XXXX", "XXXX-XXXX-XXXX-XXXX"],
    ["2", "Jane Doe", "janedoe@example.com", "XXX-XX-XXXX", "XXXX-XXXX-XXXX-XXXX"],
    ["3", "Bob Smith", "bobsmith@example.com", "XXX-XX-XXXX", "XXXX-XXXX-XXXX-XXXX"]
]

# Define the expected forensics report contents
expected_forensics_report = f"""
Attacker IP: {expected_attacker_ip}
Attack Timestamp: {expected_attack_timestamp}
Redacted Records: {expected_redacted_records}
"""

def test_access_log():
    # Check if the access log file exists
    assert os.path.exists("/home/user/access.log")

    # Read the access log file and find the entry with the successful SQL injection attack
    with open("/home/user/access.log", "r") as f:
        log_entries = f.readlines()

    # Find the entry with the HTTP status code 200 and the request URI containing standard SQL injection keywords
    for entry in log_entries:
        if "200" in entry and ("UNION" in entry or "SELECT" in entry):
            # Extract the IP address and timestamp from the entry
            ip_address = entry.split("- -")[0].strip()
            timestamp = entry.split("[")[1].split("]")[0].strip()

            # Check if the IP address and timestamp match the expected values
            assert ip_address == expected_attacker_ip
            assert timestamp == expected_attack_timestamp

def test_redacted_evidence():
    # Check if the redacted evidence file exists
    assert os.path.exists("/home/user/redacted_evidence.csv")

    # Read the redacted evidence file and check its contents
    with open("/home/user/redacted_evidence.csv", "r") as f:
        reader = csv.reader(f)
        rows = list(reader)

    # Check if the number of rows matches the expected number of redacted records
    assert len(rows) == expected_redacted_records + 1  # +1 for the header row

    # Check if the header row matches the expected header
    assert rows[0] == expected_redacted_evidence[0]

    # Check if the data rows match the expected redacted evidence
    for i in range(1, len(rows)):
        assert rows[i] == expected_redacted_evidence[i]

def test_forensics_report():
    # Check if the forensics report file exists
    assert os.path.exists("/home/user/forensics_report.txt")

    # Read the forensics report file and check its contents
    with open("/home/user/forensics_report.txt", "r") as f:
        report = f.read()

    # Check if the report matches the expected forensics report
    assert report.strip() == expected_forensics_report.strip()

def test_ssn_redaction():
    # Check if the SSN values in the redacted evidence file are redacted correctly
    with open("/home/user/redacted_evidence.csv", "r") as f:
        reader = csv.reader(f)
        next(reader)  # Skip the header row
        for row in reader:
            ssn = row[3]
            assert re.match(r"XXX-XX-XXXX", ssn)

def test_cc_number_redaction():
    # Check if the CC Number values in the redacted evidence file are redacted correctly
    with open("/home/user/redacted_evidence.csv", "r") as f:
        reader = csv.reader(f)
        next(reader)  # Skip the header row
        for row in reader:
            cc_number = row[4]
            assert re.match(r"XXXX-XXXX-XXXX-XXXX", cc_number)
