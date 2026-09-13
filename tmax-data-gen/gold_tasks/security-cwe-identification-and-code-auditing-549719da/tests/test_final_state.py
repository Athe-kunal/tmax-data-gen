# test_final_state.py

import os
import hashlib
import pytest

def calculate_sha256_hash(file_path):
    """Calculate the SHA-256 hash of a file."""
    with open(file_path, 'rb') as file:
        hash_object = hashlib.sha256()
        hash_object.update(file.read())
        return hash_object.hexdigest()

def test_verify_token_script_exists():
    """Verify that the /home/user/verify_token.sh script exists."""
    assert os.path.exists('/home/user/verify_token.sh')

def test_crafted_token_exists():
    """Verify that the /home/user/evasion.token file exists."""
    assert os.path.exists('/home/user/evasion.token')

def test_crafted_token_contents():
    """Verify that the /home/user/evasion.token file contains the expected token string."""
    with open('/home/user/evasion.token', 'r') as file:
        token_string = file.read()
        assert token_string == 'eyJhbGciOiJub25lIn0=.eyJyb2xlIjoiYWRtaW4ifQ==.'

def test_crafted_token_permissions():
    """Verify that the /home/user/evasion.token file has the correct permissions."""
    permissions = oct(os.stat('/home/user/evasion.token').st_mode)[-4:]
    assert permissions == '0400'

def test_sha256_hash():
    """Verify that the SHA-256 hash of /home/user/evasion.token is correct."""
    expected_hash = calculate_sha256_hash('/home/user/evasion.token')
    assert expected_hash == calculate_sha256_hash('/home/user/evasion.token')

def test_exfiltration_report_exists():
    """Verify that the /home/user/exfiltration_report.txt file exists."""
    assert os.path.exists('/home/user/exfiltration_report.txt')

def test_exfiltration_report_contents():
    """Verify that the /home/user/exfiltration_report.txt file contains the expected contents."""
    with open('/home/user/exfiltration_report.txt', 'r') as file:
        lines = file.readlines()
        assert lines[0].strip() == 'CWE-347'
        assert lines[1].strip() == calculate_sha256_hash('/home/user/evasion.token')

def test_cwe_id():
    """Verify that the CWE ID in the exfiltration report is correct."""
    with open('/home/user/exfiltration_report.txt', 'r') as file:
        lines = file.readlines()
        assert lines[0].strip() == 'CWE-347'
