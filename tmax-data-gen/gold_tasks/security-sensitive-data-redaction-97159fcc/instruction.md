As a security auditor checking permissions, I need to analyze a log file and a data dump to identify potential security vulnerabilities and prepare the data for further analysis. The log file is located at `/home/user/audit.log`, and the data dump is at `/home/user/data_dump.csv`. My goal is to redact sensitive information from the data dump and create a report summarizing my findings.

To begin, I need to analyze the log file to identify any potential security issues. The log contains information about user access, including IP addresses, timestamps, and actions performed. I need to inspect the log to find any entries that indicate unauthorized access or suspicious activity.

Once I have analyzed the log, I need to create a redacted version of the data dump at `/home/user/redacted_data.csv`. The original data dump contains columns for `id`, `username`, `email`, `password_hash`, and `access_level`. I must replace all password hashes with `XXXXXX` and all access levels with `REDACTED`, leaving the header and all other data unchanged.

Finally, I need to create a summary report at `/home/user/audit_report.txt` with the following information:
- The total number of users with admin access
- The number of users with suspicious activity in the log
- The number of data rows redacted

The report must be in the following format:
```
Admin Users: [Insert number of admin users here]
Suspicious Activity: [Insert number of users with suspicious activity here]
Redacted Records: [Insert number of data rows redacted, excluding the header]
```
I will use standard Linux command-line tools to perform these tasks. My bash environment is set up with the necessary tools, and I can use the bash shell to execute any necessary commands. I will also use `apt` as my package manager and `bash -n` to build my scripts. To verify my results, I can run `bash` to execute any test cases.

Please help me complete these tasks and create the redacted data file and audit report.
