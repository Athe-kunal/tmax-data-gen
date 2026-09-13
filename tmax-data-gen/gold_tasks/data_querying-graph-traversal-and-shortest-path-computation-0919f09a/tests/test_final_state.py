# test_final_state.py

import os
import pytest

# Ground-truth alignment (principled tests)
def test_output_file_exists():
    """Check if the output file exists and is not empty"""
    output_file = "/home/user/shortest_path.txt"
    assert os.path.exists(output_file) and os.path.getsize(output_file) > 0, \
        f"Output file {output_file} is empty or does not exist"

def test_output_file_contents():
    """Check if the output file contains the correct device IDs and total weight"""
    output_file = "/home/user/shortest_path.txt"
    with open(output_file, 'r') as f:
        output = f.read().strip()
    expected_output = "Device1,Device2,Device3,Device4,10"
    assert output == expected_output, \
        f"Output file {output_file} contains incorrect data: {output} != {expected_output}"

def test_output_file_format():
    """Check if the output file format is correct"""
    output_file = "/home/user/shortest_path.txt"
    with open(output_file, 'r') as f:
        output = f.read().strip()
    parts = output.split(',')
    assert len(parts) == 5, \
        f"Output file {output_file} has incorrect format: {output}"
    device_ids = parts[:-1]
    total_weight = parts[-1]
    assert all(device_id.startswith('Device') for device_id in device_ids), \
        f"Output file {output_file} contains incorrect device IDs: {device_ids}"
    assert total_weight.isdigit(), \
        f"Output file {output_file} contains incorrect total weight: {total_weight}"

# Run tests
pytest.main([__file__])
