#!/bin/bash

# Create the user's home directory
mkdir -p /home/user

# Create the logs directory
mkdir -p /home/user/logs

# Create the log file with the specified contents
cat > /home/user/logs/config.log << EOF
2022-01-01 12:00:00 INFO This is a single-line log message
2022-01-01 12:00:01 ERROR This is a multi-line log message
that spans multiple lines
2022-01-01 12:00:02 WARNING Another single-line log message
EOF

# Create the expected output file
cat > /home/user/expected_output.txt << EOF
2022-01-01 12:00:00 INFO This is a single-line log message

2022-01-01 12:00:01 ERROR This is a multi-line log message
that spans multiple lines

2022-01-01 12:00:02 WARNING Another single-line log message
EOF

# Create the log parser directory
mkdir -p /home/user/log_parser

# Create the main.go file with the test
cat > /home/user/log_parser/main.go << EOF
package main

import (
	"bufio"
	"fmt"
	"os"
)

func main() {
	// Open the log file
	logFile, err := os.Open("/home/user/logs/config.log")
	if err != nil {
		fmt.Println(err)
		return
	}
	defer logFile.Close()

	// Open the extracted logs file
	extractedLogsFile, err := os.Create("/home/user/extracted_config_logs.txt")
	if err != nil {
		fmt.Println(err)
		return
	}
	defer extractedLogsFile.Close()

	// Read the log file line by line
	scanner := bufio.NewScanner(logFile)
	var record string
	for scanner.Scan() {
		line := scanner.Text()
		// Check if the line starts with a timestamp and log level
		if len(line) > 20 && line[4] == '-' && line[7] == '-' && line[10] == ' ' && line[13] == ':' && line[16] == ':' && line[19] == ' ' {
			// If we have a record, write it to the extracted logs file
			if record != "" {
				fmt.Fprintln(extractedLogsFile, record)
				fmt.Fprintln(extractedLogsFile)
			}
			// Start a new record
			record = line
		} else {
			// Add the line to the current record
			record += "\n" + line
		}
	}

	// Write the last record to the extracted logs file
	if record != "" {
		fmt.Fprintln(extractedLogsFile, record)
	}
}
EOF

# Create the test file
cat > /home/user/log_parser/log_parser_test.go << EOF
package log_parser

import (
	"io/ioutil"
	"testing"
)

func TestExtractLogs(t *testing.T) {
	// Read the expected output from a file
	expectedOutput, err := ioutil.ReadFile("/home/user/expected_output.txt")
	if err != nil {
		t.Fatal(err)
	}

	// Run the main program to extract the logs
	cmd := "go run /home/user/log_parser/main.go"
	output, err := exec.Command("sh", "-c", cmd).Output()
	if err != nil {
		t.Fatal(err)
	}

	// Read the extracted logs from a file
	extractedLogs, err := ioutil.ReadFile("/home/user/extracted_config_logs.txt")
	if err != nil {
		t.Fatal(err)
	}

	// Compare the extracted logs with the expected output
	if string(extractedLogs) != string(expectedOutput) {
		t.Errorf("Extracted logs do not match expected output")
	}
}
EOF

# Change the ownership of the files to the user
chown -R user:user /home/user

# Make the files readable, writable, and executable by everyone
chmod -R 777 /home/user
