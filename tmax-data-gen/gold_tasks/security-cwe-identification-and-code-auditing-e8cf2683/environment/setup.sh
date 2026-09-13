#!/bin/bash

# Create the infrastructure directory
mkdir -p /home/user/infrastructure

# Create the security_groups.py file with a vulnerability (CWE-522)
echo "# This file contains a vulnerability with CWE identifier CWE-522" > /home/user/infrastructure/security_groups.py

# Create the network_config.cfg file
echo "# This configuration file is missing security parameters" > /home/user/infrastructure/network_config.cfg

# Create the generate_cert.sh script with weak cryptographic parameters
echo "# This script generates a self-signed certificate with weak parameters" > /home/user/infrastructure/generate_cert.sh
echo "openssl req -x509 -newkey rsa:1024 -nodes -keyout server.key -out server.crt -days 365 -subj \"/C=US/ST=State/L=Locality/O=Organization/CN=www.example.com\" -sha1" >> /home/user/infrastructure/generate_cert.sh
chmod +x /home/user/infrastructure/generate_cert.sh

# Create the test_infrastructure.py script
echo "import os" > /home/user/infrastructure/test_infrastructure.py
echo "import json" >> /home/user/infrastructure/test_infrastructure.py
echo "def test_certificates():" >> /home/user/infrastructure/test_infrastructure.py
echo "    assert os.path.exists(\"/home/user/infrastructure/server.key\")" >> /home/user/infrastructure/test_infrastructure.py
echo "    assert os.path.exists(\"/home/user/infrastructure/server.crt\")" >> /home/user/infrastructure/test_infrastructure.py
echo "def test_config_file():" >> /home/user/infrastructure/test_infrastructure.py
echo "    with open(\"/home/user/infrastructure/findings.json\", \"r\") as f:" >> /home/user/infrastructure/test_infrastructure.py
echo "        findings = json.load(f)" >> /home/user/infrastructure/test_infrastructure.py
echo "    assert findings[\"security_groups.py\"] == \"CWE-522\"" >> /home/user/infrastructure/test_infrastructure.py
echo "    assert findings[\"network_config.cfg_missing_parameters\"] == [\"firewall_rule\", \"port_control\"]" >> /home/user/infrastructure/test_infrastructure.py

# Modify the generate_cert.sh script to use strong cryptographic parameters
echo "openssl req -x509 -newkey rsa:2048 -nodes -keyout server.key -out server.crt -days 365 -subj \"/C=US/ST=State/L=Locality/O=Organization/CN=www.example.com\" -sha256" > /home/user/infrastructure/generate_cert.sh
chmod +x /home/user/infrastructure/generate_cert.sh

# Execute the generate_cert.sh script to generate certificates
/home/user/infrastructure/generate_cert.sh

# Create the findings.json report
echo "{ \"security_groups.py\": \"CWE-522\", \"network_config.cfg_missing_parameters\": [\"firewall_rule\", \"port_control\"] }" > /home/user/infrastructure/findings.json

# Install pytest
pip install pytest

# Run the test_infrastructure.py script
python -m pytest /home/user/infrastructure/test_infrastructure.py

# Set permissions
chmod -R 777 /home/user
