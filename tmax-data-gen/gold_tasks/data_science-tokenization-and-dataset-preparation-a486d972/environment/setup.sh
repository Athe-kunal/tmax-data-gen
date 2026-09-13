#!/bin/bash

# Install necessary packages
pip install numpy torch

# Create the directory for the user
mkdir -p /home/user

# Create the corpus.txt file with some sample text data
echo "This is a sample text corpus with multiple words and sentences. The corpus will be used for text data processing and PyTorch model evaluation." > /home/user/corpus.txt

# Create the vocab.json file with a sample vocabulary dictionary
echo '{"word1": 1, "word2": 2, "word3": 3, "<unk>": 0}' > /home/user/vocab.json

# Create the Python script to process the text data and define the PyTorch model
echo "
import json
import numpy as np
import torch
import torch.nn as nn

# Load the vocabulary dictionary
with open('/home/user/vocab.json', 'r') as f:
    vocab = json.load(f)

# Load the raw text corpus
with open('/home/user/corpus.txt', 'r') as f:
    corpus = f.read()

# Tokenize the text by splitting on single spaces
tokens = corpus.split()

# Map each word to its integer ID using the vocabulary
integer_sequence = []
for token in tokens:
    if token in vocab:
        integer_sequence.append(vocab[token])
    else:
        integer_sequence.append(vocab['<unk>'])

# Save the integer sequence to a memory-mapped numpy array
memmap = np.memmap('/home/user/dataset.bin', dtype=np.int32, mode='w+', shape=len(integer_sequence))
memmap[:] = integer_sequence
memmap.flush()

# Define the PyTorch model
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

# Set the PyTorch manual seed
torch.manual_seed(42)

# Initialize the model
model = MyModel()

# Load the first 100 tokens from the dataset.bin memmap array
memmap = np.memmap('/home/user/dataset.bin', dtype=np.int32, mode='r')
tokens = memmap[:100]

# Convert the tokens to a PyTorch long tensor
tensor = torch.from_numpy(tokens).long()

# Pass the tensor through the model
output = model(tensor)

# Calculate the mean and standard deviation of the output tensor
mean = output.mean().item()
std = output.std().item()

# Create the metrics.json file
metrics = {
    'total_tokens': len(memmap),
    'output_mean': mean,
    'output_std': std
}

with open('/home/user/metrics.json', 'w') as f:
    import json
    json.dump(metrics, f)
" > /home/user/script.py

# Run the Python script to process the text data and define the PyTorch model
python /home/user/script.py

# Change the permissions of the user directory
chmod -R 777 /home/user
