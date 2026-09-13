# test_final_state.py

import json
import numpy as np
import os
import pytest
import torch
from torch import nn

# Constants
CORPUS_FILE = '/home/user/corpus.txt'
VOCAB_FILE = '/home/user/vocab.json'
DATASET_FILE = '/home/user/dataset.bin'
METRICS_FILE = '/home/user/metrics.json'

# Load vocabulary dictionary
with open(VOCAB_FILE, 'r') as f:
    vocab = json.load(f)

# Load raw text corpus
with open(CORPUS_FILE, 'r') as f:
    corpus = f.read()

# Tokenize text corpus
tokens = corpus.split()
token_ids = [vocab.get(token, vocab['<unk>']) for token in tokens]

# Calculate total number of tokens
total_tokens = len(token_ids)

# Create memory-mapped numpy array
memmap = np.memmap(DATASET_FILE, dtype='int32', mode='w+', shape=(total_tokens,))

# Populate memory-mapped numpy array
memmap[:] = token_ids

# Define PyTorch model
class Model(nn.Module):
    def __init__(self):
        super(Model, self).__init__()
        self.embedding = nn.Embedding(num_embeddings=len(vocab), embedding_dim=16)
        self.linear = nn.Linear(16, 8)

    def forward(self, x):
        x = self.embedding(x)
        x = self.linear(x)
        x = torch.relu(x)
        return x

# Set PyTorch manual seed
torch.manual_seed(42)

# Initialize model
model = Model()

# Load first 100 tokens from memory-mapped numpy array
tokens = np.memmap(DATASET_FILE, dtype='int32', mode='r', shape=(total_tokens,))[:100]

# Convert tokens to PyTorch long tensor
tensor = torch.from_numpy(tokens).long()

# Pass tensor through model to get output tensor
output = model(tensor)

# Calculate mean and standard deviation of output tensor
output_mean = output.mean().item()
output_std = output.std(unbiased=True).item()

# Load metrics from metrics.json file
with open(METRICS_FILE, 'r') as f:
    metrics = json.load(f)

# Test total number of tokens
def test_total_tokens():
    assert metrics['total_tokens'] == total_tokens, f"Expected total tokens to be {total_tokens}, but got {metrics['total_tokens']}"

# Test mean of output tensor
def test_output_mean():
    assert np.isclose(metrics['output_mean'], output_mean), f"Expected output mean to be {output_mean}, but got {metrics['output_mean']}"

# Test standard deviation of output tensor
def test_output_std():
    assert np.isclose(metrics['output_std'], output_std), f"Expected output standard deviation to be {output_std}, but got {metrics['output_std']}"

# Test existence of required files
def test_file_existence():
    assert os.path.exists(CORPUS_FILE), f"Expected {CORPUS_FILE} to exist"
    assert os.path.exists(VOCAB_FILE), f"Expected {VOCAB_FILE} to exist"
    assert os.path.exists(DATASET_FILE), f"Expected {DATASET_FILE} to exist"
    assert os.path.exists(METRICS_FILE), f"Expected {METRICS_FILE} to exist"

# Test format of metrics.json file
def test_metrics_format():
    assert isinstance(metrics, dict), f"Expected metrics to be a dictionary, but got {type(metrics)}"
    assert 'total_tokens' in metrics, f"Expected metrics to contain 'total_tokens', but got {metrics.keys()}"
    assert 'output_mean' in metrics, f"Expected metrics to contain 'output_mean', but got {metrics.keys()}"
    assert 'output_std' in metrics, f"Expected metrics to contain 'output_std', but got {metrics.keys()}"
