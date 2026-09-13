As an integration developer, I am tasked with testing APIs to ensure they meet the required standards. I have a Python project located at `/home/user/project` that contains several APIs. The project uses the `requests` library to make API calls. I want to test the concurrency of these APIs using Go concurrency patterns.

The project has the following structure:
```
/home/user/project
|-- api
|   |-- __init__.py
|   |-- api1.py
|   |-- api2.py
|-- requirements.txt
|-- test_api.py
```
The `api1.py` and `api2.py` files contain functions that make API calls using the `requests` library. The `test_api.py` file contains test cases for these APIs.

I want you to write a Go program at `/home/user/concurrency_test.go` that uses Go concurrency patterns (goroutines and channels) to test the concurrency of the APIs. The program should:

1. Read the `requirements.txt` file and install the required packages using `pip`.
2. Run the `test_api.py` file using the `python` interpreter.
3. Use Go concurrency patterns to run the APIs in parallel and measure their response times.
4. Output the response times to a file named `/home/user/response_times.txt`.

The `response_times.txt` file should have the following format:
```
API1,RESPONSE_TIME1
API2,RESPONSE_TIME2
...
```
Where `API1`, `API2`, etc. are the names of the APIs, and `RESPONSE_TIME1`, `RESPONSE_TIME2`, etc. are their corresponding response times.

To verify the correctness of the program, I will run a test script that checks the contents of the `response_times.txt` file.

Note: You can use the `os/exec` package to run the `pip` and `python` commands from the Go program.
