As a configuration manager, I need to track changes to a log file and extract specific records for auditing purposes. The log file is located at `/home/user/logs/config.log` and contains multi-line log records. Each record starts with a timestamp and a log level (e.g., INFO, ERROR, WARNING), followed by a message that may span multiple lines. My task is to write a Go program that can parse this log file, extract the records, and save them to a new file named `/home/user/extracted_config_logs.txt`. The extracted records should be in the same format as the original log file, but with each record separated by a blank line for easier reading.

The log file has the following format:
```
2022-01-01 12:00:00 INFO This is a single-line log message
2022-01-01 12:00:01 ERROR This is a multi-line log message
that spans multiple lines
2022-01-01 12:00:02 WARNING Another single-line log message
```
I want the extracted records to be saved in the same format, but with a blank line between each record:
```
2022-01-01 12:00:00 INFO This is a single-line log message

2022-01-01 12:00:01 ERROR This is a multi-line log message
that spans multiple lines

2022-01-01 12:00:02 WARNING Another single-line log message
```
To verify the correctness of the extracted logs, I need to compare the output with a golden standard. Please use the `go test` command to verify that the extracted logs match the expected output.

Please write a Go program that can accomplish this task and save it to `/home/user/log_parser/main.go`. Then, build and run the program using the `go build` and `go run` commands, respectively. Finally, verify the correctness of the extracted logs using the `go test` command.
