# Question-rewrite example: before vs. after

## pass@4 for this specific task

| Variant | Attempts | Result |
|---|---|---|
| Original (fully-specified) | 3/3 passed | **100%** |
| Noisy rewrite | 0/4 passed | **0%** |

Same solving agent (DeepSeek-V4-Flash-0731), same environment/verifier, same truth in both cases - only the
instruction text differs. (Original ran 3 of its planned 4 attempts - the 4th was cut when concurrency was
reduced mid-run. Aggregate pass@4 across all 10 seed tasks: 70% original vs. 50% noisy - see
`pass_at_4_rewrite.png` in this folder for the chart.)

---

Task: `data_processing-database-bulk-import-export-61f51f16` (from tmax's own RL-corpus seed tasks)

Same `truth`, same verifier, same environment in both cases — only the instruction text changed.
This particular task went from **solved (reward=1.0)** on the original phrasing to **failed (reward=0.0)**
on the noisy rewrite, in this session's pass@4 A/B test.

---

## Original (fully-specified, synthetic-pipeline style)

> You are a log analyst investigating performance patterns across multiple servers.
>
> You have been given a dataset `/home/user/server_logs.csv` containing performance metrics. The file has the following columns: `timestamp`, `server_id`, `cpu_usage`, and `log_message`.
>
> However, the current pipeline is dropping or mangling records. This is because some `log_message` fields are enclosed in double quotes and contain embedded newline characters. Furthermore, some `cpu_usage` values are missing (represented by empty strings) due to transient monitoring failures.
>
> Your task is to write a Python script `/home/user/analyze.py` that does the following:
> 1. Accurately parses `/home/user/server_logs.csv` without dropping rows containing embedded newlines in the `log_message` field.
> 2. Groups the records by `server_id`.
> 3. Processes each `server_id`'s data in parallel using Python's `multiprocessing` module.
> 4. For each `server_id`, sorts the records by `timestamp` (ascending).
> 5. Imputes any missing `cpu_usage` values using forward-fill (carry forward the last known value). If the very first value for a server is missing, default it to `0.0`.
> 6. Calculates a rolling 3-period moving average of the imputed `cpu_usage` (the average of the current measurement and the up to 2 previous measurements). For the first measurement, the average is just that measurement. For the second, it is the average of the first and second.
> 7. Writes the results to `/home/user/rolling_metrics.csv` with the exact columns: `timestamp,server_id,rolling_cpu`. The `rolling_cpu` values must be rounded to exactly 2 decimal places (e.g., `13.33`). The output must be sorted by `timestamp` ascending, then `server_id` ascending.
>
> Ensure your script runs successfully and produces the expected output.

**474 tokens** (cl100k_base)

---

## Noisy rewrite (how a real person would actually ask)

> I've got a log analysis task. I have a CSV file with server performance metrics, but the current pipeline is messing up some records. The file's at `/home/user/server_logs.csv` and has columns for `timestamp`, `server_id`, `cpu_usage`, and `log_message`. Some of these log messages have embedded newlines and are quoted, which is causing issues. Also, some `cpu_usage` values are missing due to monitoring failures.
>
> Can you write a Python script (`/home/user/analyze.py`) to fix this? I need it to:
> - Parse the CSV without dropping rows with newlines in `log_message`
> - Group by `server_id` and process each group in parallel
> - Sort by `timestamp` and impute missing `cpu_usage` values by carrying forward the last known value (or defaulting to `0.0` if the first value is missing)
> - Calculate a rolling 3-period moving average of `cpu_usage` and write the results to `/home/user/rolling_metrics.csv` with columns `timestamp`, `server_id`, and `rolling_cpu` (rounded to 2 decimal places). The output should be sorted by `timestamp` and then `server_id`.
>
> Make sure the script runs without errors and produces the expected output.

**229 tokens** (cl100k_base) — 52% shorter

---

## What changed

- Numbered step-by-step procedure collapsed into a bulleted "I need it to" list — no more narrating the implementation plan.
- Exact paths, exact column names, exact rounding (`.2f`), and the exact 3-period rolling-average definition all survived verbatim — these are load-bearing (the verifier checks them exactly).
- Tone is casual/conversational ("I've got a log analysis task", "Can you write... to fix this?") instead of a numbered engineering spec.
- Despite preserving every load-bearing detail, the solving agent (DeepSeek-V4-Flash-0731) that passed on the original phrasing failed on this rewrite — evidence the rewrite genuinely increases task difficulty, not just brevity.
