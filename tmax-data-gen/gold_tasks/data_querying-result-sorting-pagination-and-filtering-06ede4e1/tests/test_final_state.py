# test_final_state.py

import json
import os
import pytest
import sqlite3

# Constants
DATA_DB = '/home/user/data.db'
INTERACTIONS_JSON = '/home/user/interactions.json'
OUTPUT_PAGE3_JSON = '/home/user/output_page3.json'

# Load truth data
def load_truth_data():
    # Load users from SQLite database
    users = []
    with sqlite3.connect(DATA_DB) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT id, name, department FROM users')
        for row in cursor.fetchall():
            users.append({'id': row[0], 'name': row[1], 'department': row[2]})

    # Load interactions from JSON file
    interactions = []
    with open(INTERACTIONS_JSON, 'r') as f:
        interactions = json.load(f)

    return users, interactions

# Calculate weighted degree centrality
def calculate_centrality(users, interactions):
    centrality = {user['id']: 0 for user in users}
    for interaction in interactions:
        centrality[interaction['src']] += interaction['weight']
        centrality[interaction['dst']] += interaction['weight']
    return centrality

# Filter and sort users by centrality
def filter_and_sort_users(users, centrality):
    filtered_users = [user for user in users if centrality[user['id']] >= 10]
    sorted_users = sorted(filtered_users, key=lambda user: (-centrality[user['id']], user['name']))
    return sorted_users

# Paginate sorted users
def paginate_users(sorted_users, page_size, page_number):
    start_index = (page_number - 1) * page_size
    end_index = start_index + page_size
    return sorted_users[start_index:end_index]

# Load expected output
def load_expected_output():
    with open(OUTPUT_PAGE3_JSON, 'r') as f:
        return json.load(f)

# Test final state
def test_final_state():
    # Load truth data
    users, interactions = load_truth_data()

    # Calculate weighted degree centrality
    centrality = calculate_centrality(users, interactions)

    # Filter and sort users by centrality
    sorted_users = filter_and_sort_users(users, centrality)

    # Paginate sorted users
    page_size = 3
    page_number = 3
    paginated_users = paginate_users(sorted_users, page_size, page_number)

    # Load expected output
    expected_output = load_expected_output()

    # Assert paginated users match expected output
    assert len(paginated_users) == len(expected_output)
    for i in range(len(paginated_users)):
        assert paginated_users[i]['id'] == expected_output[i]['id']
        assert paginated_users[i]['name'] == expected_output[i]['name']
        assert centrality[paginated_users[i]['id']] == expected_output[i]['centrality']

# Run test
pytest.main([__file__])
