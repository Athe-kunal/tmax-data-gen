# test_final_state.py

import os
import pytest
import re
import statistics

# Constants
BENCHMARKS_FILE = '/home/user/benchmarks.csv'
CORRELATION_FILE = '/home/user/correlation.txt'
TASK_LOG_FILE = '/home/user/task.log'

def calculate_pearson_correlation(benchmarks_file):
    """
    Calculate the Pearson correlation coefficient between the valid `inference_ms` values and the `confidence_score` values.

    Args:
        benchmarks_file (str): Path to the benchmarks.csv file.

    Returns:
        float: The Pearson correlation coefficient rounded to 3 decimal places.
    """
    # Read the benchmarks.csv file
    with open(benchmarks_file, 'r') as f:
        lines = f.readlines()[1:]  # Ignore the header row

    # Filter out any rows where `inference_ms` is not a valid non-negative number
    valid_lines = []
    for line in lines:
        values = line.strip().split(',')
        if len(values) == 3:
            try:
                inference_ms = float(values[1])
                if inference_ms >= 0:
                    valid_lines.append((inference_ms, float(values[2])))
            except ValueError:
                pass

    # Calculate the Pearson correlation coefficient
    if len(valid_lines) < 2:
        return 0.0  # Not enough data to calculate correlation

    inference_ms_values = [x[0] for x in valid_lines]
    confidence_score_values = [x[1] for x in valid_lines]

    mean_inference_ms = statistics.mean(inference_ms_values)
    mean_confidence_score = statistics.mean(confidence_score_values)

    numerator = sum((x - mean_inference_ms) * (y - mean_confidence_score) for x, y in valid_lines)
    denominator = (sum((x - mean_inference_ms) ** 2 for x in inference_ms_values) * sum((y - mean_confidence_score) ** 2 for y in confidence_score_values)) ** 0.5

    correlation_coefficient = numerator / denominator if denominator != 0 else 0.0

    return round(correlation_coefficient, 3)

def test_correlation_file_contents():
    """
    Test that the /home/user/correlation.txt file contains a single number, which is the rounded Pearson correlation coefficient.
    """
    if not os.path.exists(CORRELATION_FILE):
        pytest.fail(f"The {CORRELATION_FILE} file does not exist.")

    with open(CORRELATION_FILE, 'r') as f:
        contents = f.read().strip()

    if not re.match(r'^-?\d+\.\d{3}$', contents):
        pytest.fail(f"The {CORRELATION_FILE} file does not contain a valid correlation coefficient.")

    expected_correlation_coefficient = calculate_pearson_correlation(BENCHMARKS_FILE)
    if float(contents) != expected_correlation_coefficient:
        pytest.fail(f"The correlation coefficient in the {CORRELATION_FILE} file is incorrect. Expected {expected_correlation_coefficient}, but got {contents}.")

def test_task_log_file_contents():
    """
    Test that the /home/user/task.log file contains a record of the task execution, including any errors or warnings that occurred during the process.
    """
    if not os.path.exists(TASK_LOG_FILE):
        pytest.fail(f"The {TASK_LOG_FILE} file does not exist.")

    with open(TASK_LOG_FILE, 'r') as f:
        contents = f.read()

    if not contents:
        pytest.fail(f"The {TASK_LOG_FILE} file is empty.")
