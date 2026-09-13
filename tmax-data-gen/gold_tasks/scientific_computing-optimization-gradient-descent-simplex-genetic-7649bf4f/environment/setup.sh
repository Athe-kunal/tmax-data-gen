#!/bin/bash

# Create the user directory
mkdir -p /home/user

# Create the sequences.fasta file
echo ">seq1
ATCG
>seq2
ATGC
>seq3
ACGT" > /home/user/sequences.fasta

# Create the model.py file
echo "import numpy as np
from scipy.optimize import fmin

def objective_function(params):
    alpha, beta, gamma = params
    return (alpha - 0.4)**2 + (beta - 0.2)**2 + (gamma - 0.1)**2

def optimize_sequence(sequence_id):
    initial_params = [0.5, 0.3, 0.2]
    optimized_params = fmin(objective_function, initial_params, maxiter=100, xtol=1e-6)
    return optimized_params

def main():
    sequences = []
    with open('/home/user/sequences.fasta', 'r') as f:
        lines = f.readlines()
        for i in range(0, len(lines), 2):
            sequence_id = lines[i].strip()[1:]
            sequences.append(sequence_id)

    with open('/home/user/results.txt', 'w') as f:
        f.write('sequence_id alpha beta gamma\n')
        for sequence_id in sequences:
            optimized_params = optimize_sequence(sequence_id)
            f.write(f'{sequence_id} {optimized_params[0]} {optimized_params[1]} {optimized_params[2]}\n')

    with open('/home/user/log.txt', 'w') as f:
        for sequence_id in sequences:
            optimized_params = optimize_sequence(sequence_id)
            f.write(f'Sequence ID: {sequence_id}\n')
            f.write(f'Optimized Parameters: alpha = {optimized_params[0]}, beta = {optimized_params[1]}, gamma = {optimized_params[2]}\n')

if __name__ == '__main__':
    main()" > /home/user/model.py

# Create the test.py file
echo "import numpy as np

def objective_function(alpha, beta, gamma):
    return (alpha - 0.4)**2 + (beta - 0.2)**2 + (gamma - 0.1)**2

def test_optimized_parameters():
    with open('/home/user/results.txt', 'r') as f:
        lines = f.readlines()[1:]
        for line in lines:
            sequence_id, alpha, beta, gamma = line.strip().split()
            assert np.isclose(float(alpha), 0.4)
            assert np.isclose(float(beta), 0.2)
            assert np.isclose(float(gamma), 0.1)

if __name__ == '__main__':
    test_optimized_parameters()" > /home/user/test.py

# Create the virtual environment
python3 -m venv /home/user/venv
/home/user/venv/bin/pip install scipy

# Change permissions
chmod -R 777 /home/user
