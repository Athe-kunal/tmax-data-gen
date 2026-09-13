As an incident responder investigating a recent security breach, I need to analyze the web server access logs and a raw data dump left by the attacker to identify the perpetrator and prepare the exfiltrated data for legal evidence. The access log is located at `/home/user/access.log`, and the data dump is at `/home/user/compromised_db_dump.csv`. My goal is to redact sensitive Personally Identifiable Information (PII) from the data dump and create a forensics report.

To begin, I need to analyze the access log to identify the IP address and timestamp of the successful SQL injection attack. The log contains both normal traffic and malicious attempts, so I must carefully inspect the entries to find the one with an HTTP status code of `200` and a request URI containing standard SQL injection keywords like `UNION` or `SELECT`.

Once I have identified the attacker's IP address and the attack timestamp, I need to create a redacted version of the data dump at `/home/user/redacted_evidence.csv`. The original data dump contains columns for `id`, `name`, `email`, `ssn`, and `cc_number`. I must replace all Social Security Numbers (in the format `ddd-dd-dddd`) with `XXX-XX-XXXX` and all Credit Card Numbers (in the format `dddd-dddd-dddd-dddd`) with `XXXX-XXXX-XXXX-XXXX`, leaving the header and all other data unchanged.

Finally, I need to create a summary report at `/home/user/forensics_report.txt` with the attacker's IP address, the attack timestamp, and the total number of data rows redacted (excluding the header). The report must be in the following format:

```
Attacker IP: [Insert Attacker IP here]
Attack Timestamp: [Insert Timestamp here, e.g., 10/Oct/2023:13:55:36 +0000]
Redacted Records: [Insert the total number of data rows redacted, excluding the header]
```

I will use standard Linux command-line tools to perform these tasks. My Python environment is set up with the necessary packages, and I can use the Python 3 interpreter to execute any necessary scripts. I will also use `pip` as my package manager and `python -m compileall .` to build my code. To verify my results, I can run `python -m pytest` to execute any test cases.

Please help me complete these tasks and create the redacted evidence file and forensics report.
