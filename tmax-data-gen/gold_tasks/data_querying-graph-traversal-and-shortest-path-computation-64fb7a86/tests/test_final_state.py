# test_final_state.py

import os
import pytest

def test_output_file_exists():
    """Check if the output file exists and is not empty."""
    output_file = "/home/user/shortest_path.txt"
    assert os.path.exists(output_file), f"Output file {output_file} does not exist."
    assert os.path.getsize(output_file) > 0, f"Output file {output_file} is empty."

def test_output_file_contents():
    """Check if the output file contains the correct server IDs and total weight."""
    output_file = "/home/user/shortest_path.txt"
    expected_output = "Server1,Server2,Server3,Server4,10"
    with open(output_file, "r") as f:
        output = f.read().strip()
    assert output == expected_output, f"Output file {output_file} contains incorrect data. Expected {expected_output}, got {output}."

def test_log_file_exists():
    """Check if the log file exists."""
    log_file = "/home/user/pipeline.log"
    assert os.path.exists(log_file), f"Log file {log_file} does not exist."

def test_pipeline_execution():
    """Check if the pipeline executed correctly by checking the log file."""
    log_file = "/home/user/pipeline.log"
    with open(log_file, "r") as f:
        log_contents = f.read()
    assert "Error" not in log_contents, f"Pipeline execution failed. Log file {log_file} contains error messages."
    assert "Exception" not in log_contents, f"Pipeline execution failed. Log file {log_file} contains exception messages."

def test_run_pipeline_script():
    """Check if the run_pipeline.py script is executable."""
    script_file = "/home/user/run_pipeline.py"
    assert os.access(script_file, os.X_OK), f"Script file {script_file} is not executable."

def test_run_pipeline_output():
    """Check if the run_pipeline.py script produces the correct output."""
    # Run the script
    os.system("python3 /home/user/run_pipeline.py")
    # Check the output
    output_file = "/home/user/shortest_path.txt"
    expected_output = "Server1,Server2,Server3,Server4,10"
    with open(output_file, "r") as f:
        output = f.read().strip()
    assert output == expected_output, f"Script {script_file} produced incorrect output. Expected {expected_output}, got {output}."
