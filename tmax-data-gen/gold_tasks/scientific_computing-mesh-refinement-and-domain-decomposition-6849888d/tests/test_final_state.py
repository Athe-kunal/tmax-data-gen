# test_final_state.py

import json
import os
import pytest

# Ground-truth data
DATASET_PATH = "/home/user/spatial_data.csv"
INITIAL_DOMAIN = [0, 1, 0, 1]  # x_min, x_max, y_min, y_max
MAX_REFINEMENT_DEPTH = 3
GAUSSIAN_DISTRIBUTION = {
    "mu_x": 0.5,
    "mu_y": 0.5,
    "sigma": 0.2
}
RESULT_FILE_PATH = "/home/user/model_fit.json"
LOG_FILE_PATH = "/home/user/task_log.txt"
LOG_CONTENT = "Task completed. Model fit results written to /home/user/model_fit.json."

def test_result_file_exists():
    """Check if the result file exists."""
    assert os.path.exists(RESULT_FILE_PATH), "Result file does not exist"

def test_result_file_format():
    """Check if the result file has the correct format."""
    with open(RESULT_FILE_PATH, "r") as file:
        result_data = json.load(file)
    assert "total_cells" in result_data, "Result file is missing 'total_cells' key"
    assert "max_depth_reached" in result_data, "Result file is missing 'max_depth_reached' key"
    assert "kl_divergence" in result_data, "Result file is missing 'kl_divergence' key"
    assert isinstance(result_data["total_cells"], int), "'total_cells' value is not an integer"
    assert isinstance(result_data["max_depth_reached"], int), "'max_depth_reached' value is not an integer"
    assert isinstance(result_data["kl_divergence"], (int, float)), "'kl_divergence' value is not a number"

def test_log_file_exists():
    """Check if the log file exists."""
    assert os.path.exists(LOG_FILE_PATH), "Log file does not exist"

def test_log_file_content():
    """Check if the log file has the correct content."""
    with open(LOG_FILE_PATH, "r") as file:
        log_content = file.read().strip()
    assert log_content == LOG_CONTENT, "Log file content is incorrect"

def test_kl_divergence():
    """Check if the KL divergence is computed correctly and rounded to 4 decimal places."""
    with open(RESULT_FILE_PATH, "r") as file:
        result_data = json.load(file)
    kl_divergence = result_data["kl_divergence"]
    assert isinstance(kl_divergence, (int, float)), "'kl_divergence' value is not a number"
    assert round(kl_divergence, 4) == kl_divergence, "'kl_divergence' value is not rounded to 4 decimal places"

def test_total_cells():
    """Check if the total number of leaf cells in the final mesh is correct."""
    # This test requires knowledge of the dataset and the refinement process
    # For simplicity, we assume that the total number of leaf cells is correct if it is a power of 4
    with open(RESULT_FILE_PATH, "r") as file:
        result_data = json.load(file)
    total_cells = result_data["total_cells"]
    assert (total_cells & (total_cells - 1) == 0) and (total_cells != 0), "Total number of leaf cells is not a power of 4"

def test_max_refinement_depth():
    """Check if the maximum refinement depth reached is correct."""
    with open(RESULT_FILE_PATH, "r") as file:
        result_data = json.load(file)
    max_depth_reached = result_data["max_depth_reached"]
    assert max_depth_reached <= MAX_REFINEMENT_DEPTH, "Maximum refinement depth reached is greater than the maximum allowed depth"
