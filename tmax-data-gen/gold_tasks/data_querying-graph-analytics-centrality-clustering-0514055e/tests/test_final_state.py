# test_final_state.py

import json
import os
import pytest

def calculate_most_cited_paper():
    """
    Calculate the most cited paper by reading the JSONL file and calculating the in-degrees.
    """
    in_degrees = {}
    with open('/home/user/citation_graph/data/papers.jsonl', 'r') as f:
        for line in f:
            paper = json.loads(line)
            for reference in paper['references']:
                if reference in in_degrees:
                    in_degrees[reference] += 1
                else:
                    in_degrees[reference] = 1

    max_in_degree = 0
    most_cited_paper = None
    for paper_id, in_degree in in_degrees.items():
        if in_degree > max_in_degree:
            max_in_degree = in_degree
            most_cited_paper = paper_id

    return most_cited_paper

def test_most_cited_paper():
    """
    Test that the contents of the `/home/user/top_cited.txt` file match the expected output.
    """
    expected_output = calculate_most_cited_paper()
    with open('/home/user/top_cited.txt', 'r') as f:
        actual_output = f.read().strip()

    assert actual_output == expected_output, (
        f"Expected the contents of `/home/user/top_cited.txt` to be '{expected_output}', "
        f"but got '{actual_output}' instead."
    )

def test_output_file_exists():
    """
    Test that the `/home/user/top_cited.txt` file exists.
    """
    assert os.path.exists('/home/user/top_cited.txt'), (
        "The `/home/user/top_cited.txt` file does not exist."
    )

def test_output_file_is_not_empty():
    """
    Test that the `/home/user/top_cited.txt` file is not empty.
    """
    with open('/home/user/top_cited.txt', 'r') as f:
        contents = f.read().strip()
    assert contents, (
        "The `/home/user/top_cited.txt` file is empty."
    )

def test_output_file_contains_only_one_line():
    """
    Test that the `/home/user/top_cited.txt` file contains only one line.
    """
    with open('/home/user/top_cited.txt', 'r') as f:
        lines = f.readlines()
    assert len(lines) == 1, (
        f"Expected the `/home/user/top_cited.txt` file to contain only one line, "
        f"but got {len(lines)} lines instead."
    )

def test_output_file_does_not_contain_newlines():
    """
    Test that the `/home/user/top_cited.txt` file does not contain any newlines.
    """
    with open('/home/user/top_cited.txt', 'r') as f:
        contents = f.read()
    assert '\n' not in contents, (
        "The `/home/user/top_cited.txt` file contains a newline."
    )
