As a storage administrator managing disk space, I am facing an issue with a legacy backup process that has crashed halfway through archiving system logs. The process has left behind a multi-part, gzip-compressed tar archive in the directory `/home/user/backup_data/`. The files are named `system_logs.tar.gz.00`, `system_logs.tar.gz.01`, and `system_logs.tar.gz.02`. 

My objective is to extract specific error logs from this split archive using stream processing, rename them, and organize them using hard links so the monitoring system can ingest them.

I need to achieve the following:
1. **Stream Processing & Archive Handling:** Read the multi-part archive directly and extract *only* the files that end with `.err.log`. Do not write the recombined `.tar.gz` file to disk (process it as a stream to save space).
2. **Bulk Renaming:** As you extract these files, place them into `/home/user/extracted_errors/`. You must rename them during or immediately after extraction so that the `.log` extension is removed (e.g., `application.err.log` becomes `application.err`). Flatten the directory structure (put all extracted files directly in `/home/user/extracted_errors/`, ignoring their original directories inside the tarball).
3. **Link Management:** For every file you place in `/home/user/extracted_errors/`, create a **hard link** in the directory `/home/user/important_errors/`. The hard link must be named by prepending `CRITICAL_` to the new filename (e.g., `CRITICAL_application.err`).

To verify the successful completion of this task, I expect to see the extracted error logs in `/home/user/extracted_errors/` and their corresponding hard links in `/home/user/important_errors/`. Additionally, I want a log file named `extraction_log.txt` in the `/home/user/logs` directory, which should contain the list of extracted files and their corresponding hard links.

Please create the `/home/user/extracted_errors/` and `/home/user/important_errors/` directories yourself and ensure that the files in both directories share the exact same inodes. Also, create the `/home/user/logs` directory and the `extraction_log.txt` file as required.
