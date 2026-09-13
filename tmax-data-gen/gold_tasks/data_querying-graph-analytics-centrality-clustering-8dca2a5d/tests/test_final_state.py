# test_final_state.py

import os
import json

def test_top_cited_paper():
    """
    Test that the contents of the /home/user/top_cited.txt file match the id of the paper with the highest in-degree.
    """
    # Define the truth data
    truth_data = [
        {"id": "paper1", "title": "Paper 1", "references": ["paper2", "paper3"]},
        {"id": "paper2", "title": "Paper 2", "references": ["paper1", "paper4"]},
        {"id": "paper3", "title": "Paper 3", "references": ["paper1", "paper2"]},
        {"id": "paper4", "title": "Paper 4", "references": ["paper2", "paper3"]},
    ]

    # Calculate the in-degrees of all papers
    in_degrees = {}
    for paper in truth_data:
        for reference in paper["references"]:
            if reference not in in_degrees:
                in_degrees[reference] = 1
            else:
                in_degrees[reference] += 1

    # Find the paper with the highest in-degree
    max_in_degree = max(in_degrees.values())
    most_cited_papers = [paper for paper, degree in in_degrees.items() if degree == max_in_degree]

    # Check the contents of the /home/user/top_cited.txt file
    top_cited_file = "/home/user/top_cited.txt"
    assert os.path.exists(top_cited_file), f"The file {top_cited_file} does not exist."

    with open(top_cited_file, "r") as f:
        top_cited_paper = f.read().strip()

    assert top_cited_paper in most_cited_papers, (
        f"The contents of the {top_cited_file} file do not match the id of the paper with the highest in-degree. "
        f"Expected one of {most_cited_papers}, but got {top_cited_paper}."
    )

def test_output_file_format():
    """
    Test that the output file /home/user/top_cited.txt contains only the id of the most cited paper, without any quotes or newlines.
    """
    top_cited_file = "/home/user/top_cited.txt"
    assert os.path.exists(top_cited_file), f"The file {top_cited_file} does not exist."

    with open(top_cited_file, "r") as f:
        top_cited_paper = f.read()

    assert top_cited_paper.strip() == top_cited_paper, "The output file contains trailing newlines."
    assert '"' not in top_cited_paper, "The output file contains quotes."
