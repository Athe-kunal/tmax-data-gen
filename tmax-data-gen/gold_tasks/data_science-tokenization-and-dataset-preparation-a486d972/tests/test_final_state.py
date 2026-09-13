# test_final_state.py

import json
import numpy as np
import os
import pytest
import torch
import torch.nn as nn

def test_dataset_bin_exists():
    """Check if the dataset.bin file exists."""
    assert os.path.exists('/home/user/dataset.bin')

def test_dataset_bin_contents():
    """Check the contents of the dataset.bin file."""
    with open('/home/user/vocab.json', 'r') as f:
        vocab = json.load(f)

    with open('/home/user/corpus.txt', 'r') as f:
        corpus = f.read()

    tokens = corpus.split()
    token_ids = []
    for token in tokens:
        token_ids.append(vocab.get(token, vocab['<unk>']))

    memmap = np.memmap('/home/user/dataset.bin', dtype=np.int32, mode='r')
    assert len(memmap) == len(token_ids)
    assert np.array_equal(memmap, token_ids)

def test_metrics_json_exists():
    """Check if the metrics.json file exists."""
    assert os.path.exists('/home/user/metrics.json')

def test_metrics_json_contents():
    """Check the contents of the metrics.json file."""
    with open('/home/user/vocab.json', 'r') as f:
        vocab = json.load(f)

    class MyModel(nn.Module):
        def __init__(self):
            super(MyModel, self).__init__()
            self.embedding = nn.Embedding(len(vocab), 16)
            self.linear = nn.Linear(16, 8)
            self.relu = nn.ReLU()

        def forward(self, x):
            x = self.embedding(x)
            x = self.linear(x)
            x = self.relu(x)
            return x

    torch.manual_seed(42)
    model = MyModel()

    memmap = np.memmap('/home/user/dataset.bin', dtype=np.int32, mode='r')
    tokens = memmap[:100]
    tensor = torch.from_numpy(tokens).long()
    output = model(tensor)
    mean = output.mean().item()
    std = output.std(unbiased=True).item()

    expected_metrics = {
        'total_tokens': len(memmap),
        'output_mean': mean,
        'output_std': std
    }

    with open('/home/user/metrics.json', 'r') as f:
        actual_metrics = json.load(f)

    assert actual_metrics == expected_metrics

def test_pytorch_model_definition():
    """Check the definition of the PyTorch model."""
    with open('/home/user/vocab.json', 'r') as f:
        vocab = json.load(f)

    class MyModel(nn.Module):
        def __init__(self):
            super(MyModel, self).__init__()
            self.embedding = nn.Embedding(len(vocab), 16)
            self.linear = nn.Linear(16, 8)
            self.relu = nn.ReLU()

        def forward(self, x):
            x = self.embedding(x)
            x = self.linear(x)
            x = self.relu(x)
            return x

    model = MyModel()
    assert isinstance(model.embedding, nn.Embedding)
    assert model.embedding.num_embeddings == len(vocab)
    assert model.embedding.embedding_dim == 16
    assert isinstance(model.linear, nn.Linear)
    assert model.linear.in_features == 16
    assert model.linear.out_features == 8
    assert isinstance(model.relu, nn.ReLU)

def test_numerical_accuracy_testing_and_inference():
    """Check the numerical accuracy testing and inference."""
    with open('/home/user/vocab.json', 'r') as f:
        vocab = json.load(f)

    class MyModel(nn.Module):
        def __init__(self):
            super(MyModel, self).__init__()
            self.embedding = nn.Embedding(len(vocab), 16)
            self.linear = nn.Linear(16, 8)
            self.relu = nn.ReLU()

        def forward(self, x):
            x = self.embedding(x)
            x = self.linear(x)
            x = self.relu(x)
            return x

    torch.manual_seed(42)
    model = MyModel()

    memmap = np.memmap('/home/user/dataset.bin', dtype=np.int32, mode='r')
    tokens = memmap[:100]
    tensor = torch.from_numpy(tokens).long()
    output = model(tensor)
    mean = output.mean().item()
    std = output.std(unbiased=True).item()

    assert not np.isnan(mean)
    assert not np.isnan(std)
