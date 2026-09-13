# test_final_state.py

import os
import csv
import pytest
from typing import List, Tuple

# Define the expected file paths
CV_RESULTS_FILE = "/home/user/experiments/cv_results.csv"
PREDICTIONS_FILE = "/home/user/experiments/predictions.txt"

# Define the expected header for the cv_results.csv file
CV_RESULTS_HEADER = ["degree", "alpha", "mean_mse"]

# Define the expected number of rows in the cv_results.csv file
EXPECTED_ROWS = 9

def read_csv_file(file_path: str) -> List[List[str]]:
    """
    Read a CSV file and return its contents as a list of lists.

    Args:
    file_path (str): The path to the CSV file.

    Returns:
    List[List[str]]: The contents of the CSV file.
    """
    with open(file_path, "r") as file:
        reader = csv.reader(file)
        contents = list(reader)
    return contents

def check_cv_results_file():
    """
    Check the cv_results.csv file for correctness.
    """
    # Check if the file exists
    assert os.path.exists(CV_RESULTS_FILE), f"The file {CV_RESULTS_FILE} does not exist."

    # Read the file contents
    contents = read_csv_file(CV_RESULTS_FILE)

    # Check the header
    assert contents[0] == CV_RESULTS_HEADER, f"The header of the {CV_RESULTS_FILE} file is incorrect."

    # Check the number of rows
    assert len(contents) == EXPECTED_ROWS + 1, f"The {CV_RESULTS_FILE} file has an incorrect number of rows."

    # Check the sorting of the rows
    mse_values = [float(row[2]) for row in contents[1:]]
    assert mse_values == sorted(mse_values), f"The rows in the {CV_RESULTS_FILE} file are not sorted correctly."

    # Check the precision of the MSE values
    for row in contents[1:]:
        mse_value = float(row[2])
        assert round(mse_value, 4) == mse_value, f"The MSE value {mse_value} in the {CV_RESULTS_FILE} file is not rounded to 4 decimal places."

def check_predictions_file():
    """
    Check the predictions.txt file for correctness.
    """
    # Check if the file exists
    assert os.path.exists(PREDICTIONS_FILE), f"The file {PREDICTIONS_FILE} does not exist."

    # Read the file contents
    with open(PREDICTIONS_FILE, "r") as file:
        predictions = [float(line.strip()) for line in file.readlines()]

    # Check the precision of the predictions
    for prediction in predictions:
        assert round(prediction, 4) == prediction, f"The prediction {prediction} in the {PREDICTIONS_FILE} file is not rounded to 4 decimal places."

def test_final_state():
    """
    Test the final state of the system.
    """
    check_cv_results_file()
    check_predictions_file()

if __name__ == "__main__":
    pytest.main([__file__])
