# test_final_state.py

import json
import os
import pytest

def calculate_in_degrees(papers):
    """
    Calculate the in-degrees of all nodes in the graph.

    Args:
    papers (list): A list of papers, each with 'id', 'title', and 'references'.

    Returns:
    dict: A dictionary where the keys are paper IDs and the values are their in-degrees.
    """
    in_degrees = {}
    for paper in papers:
        for reference in paper['references']:
            if reference in in_degrees:
                in_degrees[reference] += 1
            else:
                in_degrees[reference] = 1
    return in_degrees

def find_most_cited_paper(papers):
    """
    Find the paper with the highest in-degree.

    Args:
    papers (list): A list of papers, each with 'id', 'title', and 'references'.

    Returns:
    str: The ID of the most cited paper.
    """
    in_degrees = calculate_in_degrees(papers)
    most_cited_paper = max(in_degrees, key=in_degrees.get)
    return most_cited_paper

def read_papers_from_file(file_path):
    """
    Read papers from a JSONL file.

    Args:
    file_path (str): The path to the JSONL file.

    Returns:
    list: A list of papers, each with 'id', 'title', and 'references'.
    """
    papers = []
    with open(file_path, 'r') as file:
        for line in file:
            paper = json.loads(line)
            papers.append(paper)
    return papers

def test_final_state():
    # Read papers from the JSONL file
    papers_file_path = '/home/user/citation_graph/data/papers.jsonl'
    papers = read_papers_from_file(papers_file_path)

    # Find the most cited paper
    most_cited_paper = find_most_cited_paper(papers)

    # Check the contents of the /home/user/top_cited.txt file
    output_file_path = '/home/user/top_cited.txt'
    assert os.path.exists(output_file_path)
    with open(output_file_path, 'r') as file:
        output = file.read().strip()
        assert output == most_cited_paper

# Run the test
pytest.main([__file__])
