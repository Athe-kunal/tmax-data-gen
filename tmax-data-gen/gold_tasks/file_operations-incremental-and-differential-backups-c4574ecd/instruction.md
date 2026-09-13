As a researcher organizing datasets, I have a large collection of files that I need to back up regularly. I use a combination of full and incremental backups to save disk space. My backup system has completed an incremental backup, but due to a configuration error, it copied all files completely instead of creating hard links for the files that hadn't changed. I need to deduplicate the files in the incremental backup directory by creating hard links to the identical files in the base backup directory.

The metadata about the backups, including the paths to the base backup directory and the incremental backup directory, is stored in a JSON file at `/home/user/backups.json`. The format of the JSON file is as follows:
```json
{
    "base": "/home/user/base_backup",
    "inc": "/home/user/inc_backup"
}
```
A log file at `/home/user/sync.log` contains records of the files processed during the backup. Every record spans exactly three lines:
```
FILE: <filename>
SIZE: <bytes>
STATUS: <SUCCESS|FAILED>
```
My task is to write and execute a Rust program (using the Rust toolchain and cargo package manager) to perform the following operations:

1. Parse `/home/user/backups.json` to extract the paths for the base and incremental backup directories.
2. Parse `/home/user/sync.log` to identify all files that have `STATUS: SUCCESS`.
3. For every successfully processed file, check if it exists in both the base and incremental directories. If the contents are exactly identical, deduplicate it by deleting the copy in the incremental directory and creating a hard link to the file in the base directory.
4. Generate a CSV report at `/home/user/dedup_report.csv` with exactly two columns: `filename,saved_bytes`. Include only the files that were successfully hardlinked. The `saved_bytes` should be the size of the deduplicated file.
5. Create a symbolic link at `/home/user/latest_backup` pointing to the incremental backup directory.

To verify the correctness of the task, I will run `cargo test` to check if the generated CSV report matches the expected format and if the symbolic link points to the correct directory.

Please note that the Rust program should be executed in the `/home/user` directory, and the `cargo build` command should be used to build the program before running it.
