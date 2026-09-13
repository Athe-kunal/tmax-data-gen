#!/bin/bash

# Install necessary packages
pip install torch numpy

# Create the corpus.txt file with 10000 tokens
echo "Creating corpus.txt file..."
for i in {1..10000}; do
  echo -n "word$(($RANDOM%10)) "
done > /home/user/corpus.txt

# Create the vocab.json file with 10 words
echo "Creating vocab.json file..."
vocab='{"<unk>": 0, '
for i in {1..10}; do
  vocab+="\"word$i\": $i, "
done
vocab=${vocab%,*}"}"
echo "$vocab" > /home/user/vocab.json

# Create the dataset.bin file with 10000 tokens
echo "Creating dataset.bin file..."
python -c "import numpy as np; import json; with open('/home/user/vocab.json') as f: vocab = json.load(f); tokens = open('/home/user/corpus.txt').read().split(); token_ids = [vocab.get(token, vocab['<unk>']) for token in tokens]; np.memmap('/home/user/dataset.bin', dtype='int32', mode='w+', shape=len(token_ids)).flush()" > /dev/null

# Create a placeholder metrics.json file
echo "Creating metrics.json file..."
echo "{}" > /home/user/metrics.json

# Create a Python script to define the PyTorch model and perform numerical accuracy testing
echo "Creating model.py file..."
cat > /home/user/model.py <<EOF
import torch
import torch.nn as nn
import numpy as np
import json

class Model(nn.Module):
    def __init__(self, vocab_size):
        super(Model, self).__init__()
        self.embedding = nn.Embedding(vocab_size, 16)
        self.linear = nn.Linear(16, 8)

    def forward(self, x):
        x = self.embedding(x)
        x = self.linear(x)
        return torch.relu(x)

def main():
    torch.manual_seed(42)
    vocab_size = len(json.load(open('/home/user/vocab.json')))
    model = Model(vocab_size)
    dataset = np.memmap('/home/user/dataset.bin', dtype='int32', mode='r')
    input_tensor = torch.from_numpy(dataset[:100]).long()
    output_tensor = model(input_tensor)
    mean = output_tensor.mean().item()
    std = output_tensor.std(unbiased=True).item()
    metrics = {
        "total_tokens": len(dataset),
        "output_mean": mean,
        "output_std": std
    }
    with open('/home/user/metrics.json', 'w') as f:
        json.dump(metrics, f)

if __name__ == '__main__':
    main()
EOF

# Make the script executable and run it
chmod +x /home/user/model.py
/home/user/model.py > /dev/null

# Set permissions
chmod -R 777 /home/user
