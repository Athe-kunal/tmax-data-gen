#!/bin/bash

# Install necessary packages
pip install torch numpy

# Create the corpus.txt file with some sample text data
echo "This is a sample text corpus with multiple words and sentences. This corpus will be used for tokenization and storage." > /home/user/corpus.txt

# Create the vocab.json file with a sample vocabulary dictionary
echo '{"word1": 0, "word2": 1, "word3": 2, "word4": 3, "word5": 4, "<unk>": 5}' > /home/user/vocab.json

# Create a Python script to perform tokenization and storage
echo "
import json
import numpy as np

with open('/home/user/corpus.txt', 'r') as f:
    text = f.read()

with open('/home/user/vocab.json', 'r') as f:
    vocab = json.load(f)

tokens = text.split()
token_ids = []
for token in tokens:
    if token in vocab:
        token_ids.append(vocab[token])
    else:
        token_ids.append(vocab['<unk>'])

arr = np.memmap('/home/user/dataset.bin', dtype='int32', mode='w+', shape=(len(token_ids),))
arr[:] = token_ids
arr.flush()
" > /home/user/tokenize.py

# Run the Python script to perform tokenization and storage
python /home/user/tokenize.py

# Create a Python script to define the PyTorch model and perform numerical accuracy testing and inference
echo "
import torch
import torch.nn as nn
import numpy as np
import json

# Set the PyTorch manual seed
torch.manual_seed(42)

# Define the PyTorch model
class Model(nn.Module):
    def __init__(self):
        super(Model, self).__init__()
        self.embedding = nn.Embedding(len(json.load(open('/home/user/vocab.json', 'r'))), 16)
        self.linear = nn.Linear(16, 8)

    def forward(self, x):
        x = self.embedding(x)
        x = self.linear(x)
        x = torch.relu(x)
        return x

# Initialize the model
model = Model()

# Load the first 100 tokens from the dataset.bin memmap array
arr = np.memmap('/home/user/dataset.bin', dtype='int32', mode='r', shape=(-1,))
input_tensor = torch.from_numpy(arr[:100]).long()

# Pass the tensor through the initialized model to get an output tensor
output_tensor = model(input_tensor)

# Calculate the mean and standard deviation of the output tensor
mean = output_tensor.mean().item()
std = output_tensor.std(unbiased=True).item()

# Create a JSON file with the total number of tokens, mean, and standard deviation
metrics = {
    'total_tokens': len(arr),
    'output_mean': mean,
    'output_std': std
}
with open('/home/user/metrics.json', 'w') as f:
    json.dump(metrics, f)
" > /home/user/inference.py

# Run the Python script to define the PyTorch model and perform numerical accuracy testing and inference
python /home/user/inference.py

# Set the permissions
chmod -R 777 /home/user
