# test_final_state.py

import pytest
import numpy as np
import torch
import json
import os

def test_dataset_bin_exists():
    """Test if the dataset.bin file exists"""
    assert os.path.exists('/home/user/dataset.bin')

def test_dataset_bin_shape_and_dtype():
    """Test if the dataset.bin file has the correct shape and data type"""
    dataset = np.memmap('/home/user/dataset.bin', dtype=np.int32, mode='r')
    with open('/home/user/vocab.json', 'r') as f:
        vocab = json.load(f)
    with open('/home/user/corpus.txt', 'r') as f:
        corpus = f.read()
    tokens = corpus.split()
    token_ids = [vocab.get(token, vocab['<unk>']) for token in tokens]
    assert dataset.shape == (len(token_ids),)
    assert dataset.dtype == np.int32

def test_metrics_json_exists():
    """Test if the metrics.json file exists"""
    assert os.path.exists('/home/user/metrics.json')

def test_metrics_json_contents():
    """Test if the metrics.json file has the correct contents"""
    with open('/home/user/metrics.json', 'r') as f:
        metrics = json.load(f)
    with open('/home/user/vocab.json', 'r') as f:
        vocab = json.load(f)
    with open('/home/user/corpus.txt', 'r') as f:
        corpus = f.read()
    tokens = corpus.split()
    token_ids = [vocab.get(token, vocab['<unk>']) for token in tokens]
    dataset = np.memmap('/home/user/dataset.bin', dtype=np.int32, mode='r', shape=len(token_ids))[:100]
    input_tensor = torch.from_numpy(dataset).long()
    torch.manual_seed(42)
    class Model(torch.nn.Module):
        def __init__(self):
            super(Model, self).__init__()
            self.embedding = torch.nn.Embedding(len(vocab), 16)
            self.linear = torch.nn.Linear(16, 8)

        def forward(self, x):
            x = self.embedding(x)
            x = self.linear(x)
            x = torch.relu(x)
            return x
    model = Model()
    output_tensor = model(input_tensor)
    output_mean = output_tensor.mean().item()
    output_std = output_tensor.std().item()
    assert metrics['total_tokens'] == len(token_ids)
    assert np.isclose(metrics['output_mean'], output_mean)
    assert np.isclose(metrics['output_std'], output_std)

def test_model_definition():
    """Test if the PyTorch model is defined correctly"""
    torch.manual_seed(42)
    class Model(torch.nn.Module):
        def __init__(self):
            super(Model, self).__init__()
            with open('/home/user/vocab.json', 'r') as f:
                vocab = json.load(f)
            self.embedding = torch.nn.Embedding(len(vocab), 16)
            self.linear = torch.nn.Linear(16, 8)

        def forward(self, x):
            x = self.embedding(x)
            x = self.linear(x)
            x = torch.relu(x)
            return x
    model = Model()
    assert isinstance(model.embedding, torch.nn.Embedding)
    assert isinstance(model.linear, torch.nn.Linear)
    assert model.embedding.num_embeddings == len(json.load(open('/home/user/vocab.json', 'r')))
    assert model.embedding.embedding_dim == 16
    assert model.linear.in_features == 16
    assert model.linear.out_features == 8

def test_numerical_accuracy_testing():
    """Test if the numerical accuracy testing and inference are performed correctly"""
    torch.manual_seed(42)
    class Model(torch.nn.Module):
        def __init__(self):
            super(Model, self).__init__()
            with open('/home/user/vocab.json', 'r') as f:
                vocab = json.load(f)
            self.embedding = torch.nn.Embedding(len(vocab), 16)
            self.linear = torch.nn.Linear(16, 8)

        def forward(self, x):
            x = self.embedding(x)
            x = self.linear(x)
            x = torch.relu(x)
            return x
    model = Model()
    dataset = np.memmap('/home/user/dataset.bin', dtype=np.int32, mode='r')
    input_tensor = torch.from_numpy(dataset[:100]).long()
    output_tensor = model(input_tensor)
    output_mean = output_tensor.mean().item()
    output_std = output_tensor.std().item()
    assert not np.isnan(output_mean)
    assert not np.isnan(output_std)
