#!/bin/bash

# Install necessary packages
pip install numpy torch

# Create the corpus.txt file
echo "This is a sample text corpus for testing the task." > /home/user/corpus.txt

# Create the vocab.json file
echo '{"<unk>": 0, "This": 1, "is": 2, "a": 3, "sample": 4, "text": 5, "corpus": 6, "for": 7, "testing": 8, "the": 9, "task": 10}' > /home/user/vocab.json

# Create the Python script to perform the task
echo "
import numpy as np
import torch
import json

# Load the vocabulary dictionary
with open('/home/user/vocab.json', 'r') as f:
    vocab = json.load(f)

# Load the text corpus
with open('/home/user/corpus.txt', 'r') as f:
    corpus = f.read()

# Tokenize the text and map to integer IDs
tokens = corpus.split()
token_ids = [vocab.get(token, vocab['<unk>']) for token in tokens]

# Save the token IDs to a memory-mapped numpy array
dataset = np.memmap('/home/user/dataset.bin', dtype=np.int32, mode='w+', shape=len(token_ids))
dataset[:] = token_ids
dataset.flush()

# Define the PyTorch model
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

# Initialize the model and set the manual seed
torch.manual_seed(42)
model = Model()

# Load the first 100 tokens from the dataset.bin memmap array
tokens = np.memmap('/home/user/dataset.bin', dtype=np.int32, mode='r', shape=len(token_ids))[:100]

# Convert the tokens to a PyTorch long tensor and pass through the model
input_tensor = torch.from_numpy(tokens).long()
output_tensor = model(input_tensor)

# Calculate the mean and standard deviation of the output tensor
output_mean = output_tensor.mean().item()
output_std = output_tensor.std().item()

# Save the metrics to a JSON file
metrics = {
    'total_tokens': len(token_ids),
    'output_mean': output_mean,
    'output_std': output_std
}
with open('/home/user/metrics.json', 'w') as f:
    json.dump(metrics, f)
" > /home/user/task.py

# Run the Python script to create the initial state
python /home/user/task.py

# Set the permissions
chmod -R 777 /home/user
