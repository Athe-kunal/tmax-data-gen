#!/bin/bash

# Create the project directory
mkdir -p /home/user/project/api

# Create the __init__.py file
touch /home/user/project/api/__init__.py

# Create the api1.py file
echo "import requests

def api1():
    response = requests.get('https://api.example.com/api1')
    return response.json()" > /home/user/project/api/api1.py

# Create the api2.py file
echo "import requests

def api2():
    response = requests.get('https://api.example.com/api2')
    return response.json()" > /home/user/project/api/api2.py

# Create the requirements.txt file
echo "requests
pytest" > /home/user/project/requirements.txt

# Create the test_api.py file
echo "import pytest
from api.api1 import api1
from api.api2 import api2

def test_api1():
    response = api1()
    assert response['status'] == 200

def test_api2():
    response = api2()
    assert response['status'] == 200" > /home/user/project/test_api.py

# Create the response_times.txt file (empty for now)
touch /home/user/response_times.txt

# Create the concurrency_test.go file
echo "package main

import (
    \"fmt\"
    \"io/ioutil\"
    \"log\"
    \"os\"
    \"os/exec\"
    \"sync\"
    \"time\"
)

func main() {
    // Install required packages using pip
    cmd := exec.Command(\"pip\", \"install\", \"-r\", \"/home/user/project/requirements.txt\")
    output, err := cmd.CombinedOutput()
    if err != nil {
        log.Fatal(err)
    }
    fmt.Println(string(output))

    // Run test_api.py using python interpreter
    cmd = exec.Command(\"python\", \"/home/user/project/test_api.py\")
    output, err = cmd.CombinedOutput()
    if err != nil {
        log.Fatal(err)
    }
    fmt.Println(string(output))

    // Use Go concurrency patterns to run APIs in parallel and measure response times
    var wg sync.WaitGroup
    responseTimes := make(map[string]float64)

    apis := []string{\"api1\", \"api2\"}
    for _, api := range apis {
        wg.Add(1)
        go func(api string) {
            defer wg.Done()
            start := time.Now()
            // Make API call using requests library
            cmd := exec.Command(\"python\", \"-c\", \"from api.\"+api+\" import \"+api+\"; \"+api+\"()\")
            output, err := cmd.CombinedOutput()
            if err != nil {
                log.Fatal(err)
            }
            elapsed := time.Since(start)
            responseTimes[api] = elapsed.Seconds()
        }(api)
    }
    wg.Wait()

    // Output response times to response_times.txt file
    f, err := os.Create(\"/home/user/response_times.txt\")
    if err != nil {
        log.Fatal(err)
    }
    defer f.Close()
    for api, responseTime := range responseTimes {
        fmt.Fprintf(f, \"%s,%f\\n\", api, responseTime)
    }
}" > /home/user/concurrency_test.go

# Install required packages
pip install requests pytest

# Change permissions to allow execution
chmod -R 777 /home/user
