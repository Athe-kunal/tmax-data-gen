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

---

# Example 2: multi-turn KG-generated task

Task: `file_operations-incremental-and-differential-backups-c4574ecd` (generated via KG retrieval, not a tmax seed)

## pass@4 for this specific task

| Variant | Attempts | Result |
|---|---|---|
| Original (fully-specified) | 4/4 passed | **100%** |
| Noisy rewrite | 0/4 passed | **0%** |

Same solving agent (DeepSeek-V4-Flash-0731), same environment/verifier/truth - a complete flip, full data on
both sides. (Aggregate across 10 multi-turn KG-generated tasks so far: 100% original vs. 60% noisy - see
`pass_at_4_rewrite_multiturn.png` in this folder.)

## Original (fully-specified)

> As a researcher organizing datasets, I have a large collection of files that I need to back up regularly. I use a combination of full and incremental backups to save disk space. My backup system has completed an incremental backup, but due to a configuration error, it copied all files completely instead of creating hard links for the files that hadn't changed. I need to deduplicate the files in the incremental backup directory by creating hard links to the identical files in the base backup directory.
>
> The metadata about the backups, including the paths to the base backup directory and the incremental backup directory, is stored in a JSON file at `/home/user/backups.json`. The format of the JSON file is as follows:
> ```json
> {
>     "base": "/home/user/base_backup",
>     "inc": "/home/user/inc_backup"
> }
> ```
> A log file at `/home/user/sync.log` contains records of the files processed during the backup. Every record spans exactly three lines:
> ```
> FILE: <filename>
> SIZE: <bytes>
> STATUS: <SUCCESS|FAILED>
> ```
> My task is to write and execute a Rust program (using the Rust toolchain and cargo package manager) to perform the following operations:
>
> 1. Parse `/home/user/backups.json` to extract the paths for the base and incremental backup directories.
> 2. Parse `/home/user/sync.log` to identify all files that have `STATUS: SUCCESS`.
> 3. For every successfully processed file, check if it exists in both the base and incremental directories. If the contents are exactly identical, deduplicate it by deleting the copy in the incremental directory and creating a hard link to the file in the base directory.
> 4. Generate a CSV report at `/home/user/dedup_report.csv` with exactly two columns: `filename,saved_bytes`. Include only the files that were successfully hardlinked. The `saved_bytes` should be the size of the deduplicated file.
> 5. Create a symbolic link at `/home/user/latest_backup` pointing to the incremental backup directory.
>
> To verify the correctness of the task, I will run `cargo test` to check if the generated CSV report matches the expected format and if the symbolic link points to the correct directory.
>
> Please note that the Rust program should be executed in the `/home/user` directory, and the `cargo build` command should be used to build the program before running it.

## Noisy rewrite

> I've got a backup system that's messed up - it copied all files instead of hardlinking the unchanged ones. I need a Rust program to fix this. The backup dirs and stuff are in a JSON file at `/home/user/backups.json`, and there's a log file `/home/user/sync.log` that says what files were processed. I just need to dedupe the files that were successfully backed up, and make a CSV report of what was saved. Oh, and create a symlink to the latest backup dir. The report should have two columns, `filename` and `saved_bytes`. I'll be running this in the `/home/user` dir, so make sure to build with `cargo build` before running. Can you help me out?

## What changed

- The exact JSON schema example (`{"base": ..., "inc": ...}`) and the exact 3-line log record format (`FILE:` / `SIZE:` / `STATUS:`) were both dropped entirely - the noisy version only says the log "says what files were processed," never specifying the record structure the agent has to parse.
- The numbered 5-step procedure collapsed into a run-on sentence of loosely-connected asks.
- Despite that, the destination paths, the CSV column names, and the `cargo build`-then-run instruction all survived.
- This is a case where the rewrite arguably crossed from "the good kind of vagueness" into dropping something that isn't really derivable by exploration (the exact log line format) - a useful failure case for tightening the rewriter's invariants further.
