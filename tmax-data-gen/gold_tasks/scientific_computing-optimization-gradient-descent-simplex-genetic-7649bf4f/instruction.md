As a bioinformatics analyst, I need to optimize the parameters of a complex biological system using the Simplex optimization algorithm. The system is modeled by a Python program located at `/home/user/model.py`, which calculates the objective function and its partial derivatives. The objective function is defined as a function of three parameters: `alpha`, `beta`, and `gamma`, which represent the frequencies of three different types of mutations in a genetic sequence.

My task has three parts:

1. **Implement Simplex Optimization:** 
   I need to implement a Simplex optimization algorithm in the `model.py` file. The algorithm should minimize the objective function using the Simplex method with a initial simplex size of `1.0`. The initial values of `alpha`, `beta`, and `gamma` should be `0.5`, `0.3`, and `0.2`, respectively.

2. **Run the Optimization:**
   I have a set of genetic sequences in `/home/user/sequences.fasta`. For each sequence in the file, I need to run the Simplex optimization algorithm to find the optimal values of `alpha`, `beta`, and `gamma` that minimize the objective function. The optimization should run for a maximum of `100` iterations or until the simplex size is smaller than `1e-6`.

3. **Store the Results:**
   I need to store the optimized parameters in a file located at `/home/user/results.txt`. The file should contain four columns, `sequence_id`, `alpha`, `beta`, and `gamma`, separated by a space. Each row should correspond to the optimized parameters for each sequence in the `sequences.fasta` file.

To verify the results, I will use a test script located at `/home/user/test.py`. The script will check if the optimized parameters are close to the expected values. I expect the optimized parameters to be close to the values that minimize the objective function.

To run the `model.py` file, I will use the Python interpreter. I will also use the `scipy` library, which is installed in the `/home/user/venv` virtual environment. Please optimize the parameters of the system and store the results in the `results.txt` file.

After running the optimization, please create a log file at `/home/user/log.txt` with the following format:
```
Sequence ID: <sequence_id>
Optimized Parameters: alpha = <alpha>, beta = <beta>, gamma = <gamma>
```
This will help me verify the results and track the optimization process.
