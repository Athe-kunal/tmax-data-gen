As a release archivist packaging deliverables, I have a large collection of log files that need to be parsed to extract relevant information. The log files are stored in the /home/user/logs directory, and each log file contains multiple lines of log records. Each log record spans multiple lines and is in the following format:
```
YYYY-MM-DD HH:MM:SS,mmm [THREAD] LEVEL MESSAGE
  KEY1=VALUE1
  KEY2=VALUE2
  ...
```
I need help writing a script to parse these log files and extract the log records into new files. The new files should have the same name as the original log files but with a ".parsed" extension. The extracted log records should be in the following format:
```
YYYY-MM-DD HH:MM:SS,mmm [THREAD] LEVEL MESSAGE
KEY1=VALUE1
KEY2=VALUE2
...
```
The script should be able to handle log files with varying numbers of log records and varying lengths of log records. To verify the correctness of the script, I will check the contents of the parsed log files against the expected output. I will also check that the script does not modify the original log files.

Please help me write a script to parse the log files and extract the log records into new files. The script should be able to handle the log files in the /home/user/logs directory and produce the parsed log files in the same directory.

The script should be written in Bash and should be efficient in terms of memory and CPU usage. I will be using the Bash shell to run the script, and I expect the script to be challenging to solve but easy to verify.

To verify the correctness of the script, please create a log file named "test.log" in the /home/user/logs directory with the following contents:
```
2022-01-01 12:00:00,000 [THREAD1] INFO MESSAGE1
  KEY1=VALUE1
  KEY2=VALUE2
2022-01-01 12:00:01,000 [THREAD2] ERROR MESSAGE2
  KEY3=VALUE3
  KEY4=VALUE4
```
The expected output file should be named "test.log.parsed" and should have the following contents:
```
2022-01-01 12:00:00,000 [THREAD1] INFO MESSAGE1
KEY1=VALUE1
KEY2=VALUE2
2022-01-01 12:00:01,000 [THREAD2] ERROR MESSAGE2
KEY3=VALUE3
KEY4=VALUE4
```
Please ensure that the script produces the correct output file and does not modify the original log file.

Once the script is complete, please run it against the log files in the /home/user/logs directory and verify that the parsed log files are correct. You can use the `bash -n` command to check the script for syntax errors and the `bash` command to run the script.

After the script is complete, please create a log file named "verification.log" in the /home/user/logs directory with the contents of the parsed log files. This will be used to verify the correctness of the script.
