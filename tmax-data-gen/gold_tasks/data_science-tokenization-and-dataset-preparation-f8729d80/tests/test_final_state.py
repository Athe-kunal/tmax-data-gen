# test_final_state.py

import pytest
import os
import numpy as np
import json
import torch

# Ground-truth alignment
def load_vocab(vocab_path):
    with open(vocab_path, 'r') as f:
        vocab = json.load(f)
    return vocab

def load_corpus(corpus_path):
    with open(corpus_path, 'r') as f:
        corpus = f.read()
    return corpus

def tokenize_corpus(corpus, vocab):
    tokens = corpus.split()
    token_ids = []
    for token in tokens:
        if token in vocab:
            token_ids.append(vocab[token])
        else:
            token_ids.append(vocab['<unk>'])
    return token_ids

def create_memmap(token_ids, memmap_path):
    memmap = np.memmap(memmap_path, dtype='int32', mode='w+', shape=(len(token_ids),))
    memmap[:] = token_ids
    return memmap

def define_model(vocab):
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

    return Model()

def perform_inference(model, memmap_path):
    torch.manual_seed(42)
    memmap = np.memmap(memmap_path, dtype='int32', mode='r', shape=(10000,))
    input_tensor = torch.from_numpy(memmap[:100]).long()
    output_tensor = model(input_tensor)
    mean = torch.mean(output_tensor)
    std = torch.std(output_tensor, unbiased=True)
    return mean, std

def create_metrics_file(metrics_path, total_tokens, mean, std):
    metrics = {
        "total_tokens": total_tokens,
        "output_mean": mean.item(),
        "output_std": std.item()
    }
    with open(metrics_path, 'w') as f:
        json.dump(metrics, f)

def test_final_state():
    corpus_path = '/home/user/corpus.txt'
    vocab_path = '/home/user/vocab.json'
    memmap_path = '/home/user/dataset.bin'
    metrics_path = '/home/user/metrics.json'

    # Check if files exist
    assert os.path.exists(corpus_path)
    assert os.path.exists(vocab_path)
    assert os.path.exists(memmap_path)
    assert os.path.exists(metrics_path)

    # Load vocab and corpus
    vocab = load_vocab(vocab_path)
    corpus = load_corpus(corpus_path)

    # Tokenize corpus
    token_ids = tokenize_corpus(corpus, vocab)

    # Create memmap
    memmap = create_memmap(token_ids, memmap_path)

    # Define model
    model = define_model(vocab)

    # Perform inference
    mean, std = perform_inference(model, memmap_path)

    # Create metrics file
    create_metrics_file(metrics_path, len(token_ids), mean, std)

    # Check metrics file contents
    with open(metrics_path, 'r') as f:
        metrics = json.load(f)
    assert metrics['total_tokens'] == len(token_ids)
    assert np.isclose(metrics['output_mean'], mean.item())
    assert np.isclose(metrics['output_std'], std.item())

    # Check memmap contents
    memmap = np.memmap(memmap_path, dtype='int32', mode='r', shape=(len(token_ids),))
    assert np.array_equal(memmap, token_ids)

# Run the test
test_final_state()
