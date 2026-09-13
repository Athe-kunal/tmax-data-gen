# test_final_state.py

import os
import json
import pytest

def test_security_groups_vulnerability():
    """Test that the security groups vulnerability is correctly identified"""
    findings_path = "/home/user/infrastructure/findings.json"
    assert os.path.exists(findings_path)
    with open(findings_path, "r") as f:
        findings = json.load(f)
    assert findings["security_groups.py"] == "CWE-522"

def test_network_config_missing_parameters():
    """Test that the missing network config parameters are correctly identified"""
    findings_path = "/home/user/infrastructure/findings.json"
    assert os.path.exists(findings_path)
    with open(findings_path, "r") as f:
        findings = json.load(f)
    assert findings["network_config.cfg_missing_parameters"] == ["firewall_rule", "port_control"]

def test_generate_cert_script():
    """Test that the generate cert script has been modified to use strong cryptographic parameters"""
    script_path = "/home/user/infrastructure/generate_cert.sh"
    assert os.path.exists(script_path)
    with open(script_path, "r") as f:
        script_content = f.read()
    expected_command = "openssl req -x509 -newkey rsa:2048 -nodes -keyout server.key -out server.crt -days 365 -subj \"/C=US/ST=State/L=Locality/O=Organization/CN=www.example.com\" -sha256"
    assert expected_command in script_content

def test_generated_certificates():
    """Test that the generated certificates exist and are in the correct location"""
    key_path = "/home/user/infrastructure/server.key"
    crt_path = "/home/user/infrastructure/server.crt"
    assert os.path.exists(key_path)
    assert os.path.exists(crt_path)

def test_findings_json_structure():
    """Test that the findings.json file has the correct structure"""
    findings_path = "/home/user/infrastructure/findings.json"
    assert os.path.exists(findings_path)
    with open(findings_path, "r") as f:
        findings = json.load(f)
    assert "security_groups.py" in findings
    assert "network_config.cfg_missing_parameters" in findings
    assert isinstance(findings["network_config.cfg_missing_parameters"], list)

def test_findings_json_content():
    """Test that the findings.json file contains the correct content"""
    findings_path = "/home/user/infrastructure/findings.json"
    assert os.path.exists(findings_path)
    with open(findings_path, "r") as f:
        findings = json.load(f)
    expected_content = {
        "security_groups.py": "CWE-522",
        "network_config.cfg_missing_parameters": ["firewall_rule", "port_control"]
    }
    assert findings == expected_content
