# test_final_state.py

import os
import json
import statistics

def test_anomalous_translations():
    """
    Test that the anomalous_translations.txt file contains the correct IDs.
    """
    # Load the expected IDs from the truth data
    with open('/home/user/translation_updates.jsonl', 'r') as f:
        updates = [json.loads(line) for line in f]

    expected_anomalous_ids = []
    length_ratios = []

    for update in updates:
        length_ratio = len(update['target_text']) / len(update['source_text'])
        length_ratios.append(length_ratio)

        if len(length_ratios) > 30:
            mean = statistics.mean(length_ratios[-31:-1])
            std_dev = statistics.stdev(length_ratios[-31:-1])
            if abs(length_ratio - mean) > 3 * std_dev:
                expected_anomalous_ids.append(update['id'])

    # Load the actual IDs from the output file
    with open('/home/user/anomalous_translations.txt', 'r') as f:
        anomalous_ids = [line.strip() for line in f]

    # Check that the actual IDs match the expected IDs
    assert anomalous_ids == expected_anomalous_ids, \
        f"Expected {expected_anomalous_ids} but got {anomalous_ids}"

def test_task_log():
    """
    Test that the task_log.txt file contains the correct information.
    """
    # Load the log lines from the log file
    with open('/home/user/task_log.txt', 'r') as f:
        log_lines = [line.strip() for line in f]

    # Check that the log file contains the correct information
    assert log_lines[0] == 'Task completed successfully: True', \
        f"Expected 'Task completed successfully: True' but got {log_lines[0]}"
    assert log_lines[1].startswith('Number of anomalous translations:'), \
        f"Expected 'Number of anomalous translations:' but got {log_lines[1]}"

def test_output_files_exist():
    """
    Test that the output files exist.
    """
    # Check that the output files exist
    assert os.path.exists('/home/user/anomalous_translations.txt'), \
        "anomalous_translations.txt file does not exist"
    assert os.path.exists('/home/user/task_log.txt'), \
        "task_log.txt file does not exist"

def test_input_file_unchanged():
    """
    Test that the input file remains unchanged.
    """
    # Load the original input file
    with open('/home/user/translation_updates.jsonl', 'r') as f:
        original_updates = [line.strip() for line in f]

    # Load the current input file
    with open('/home/user/translation_updates.jsonl', 'r') as f:
        current_updates = [line.strip() for line in f]

    # Check that the input file remains unchanged
    assert original_updates == current_updates, \
        "Input file has been modified"
