As an MLOps engineer, I am tasked with tracking experiment artifacts and analyzing the inference performance benchmarks stored in the CSV file at `/home/user/benchmarks.csv`. The file contains three columns: `model_id`, `inference_ms`, and `confidence_score`. However, the logging system had some bugs, resulting in invalid `inference_ms` values. My goal is to calculate the Pearson correlation coefficient between the valid `inference_ms` values and the `confidence_score` values.

To accomplish this, I need to:
1. Read the `/home/user/benchmarks.csv` file, ignoring the header row.
2. Filter out any rows where `inference_ms` is not a valid non-negative number.
3. Calculate the Pearson correlation coefficient between the valid `inference_ms` values and the `confidence_score` values using standard Linux command-line tools like `awk`, `sed`, `grep`, `bc`, etc.
4. Round the final correlation coefficient to 3 decimal places and save it to exactly `/home/user/correlation.txt`.

The `/home/user/correlation.txt` file should contain only the rounded correlation coefficient, with no additional text or formatting. I will use this value to further analyze the inference performance benchmarks.

Please create a log file at `/home/user/task.log` to record any important events or errors during the task execution. This will help me diagnose any issues that may arise.

The `benchmarks.csv` file has the following format:
```csv
model_id,inference_ms,confidence_score
1,10.5,0.8
2,-5.2,0.7
3,abc,0.9
4,20.1,0.6
...
```
Note that the `inference_ms` column may contain invalid values such as negative numbers or non-numeric strings.

To verify the correctness of the task, I expect the `/home/user/correlation.txt` file to contain a single number, which is the Pearson correlation coefficient rounded to 3 decimal places. The `/home/user/task.log` file should contain a record of the task execution, including any errors or warnings that occurred during the process.
