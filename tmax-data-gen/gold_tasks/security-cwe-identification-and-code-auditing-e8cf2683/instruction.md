As a cloud security engineer enforcing infrastructure baselines, I need to inspect and audit the cloud infrastructure configuration files located in `/home/user/infrastructure`. The directory contains three files: `security_groups.py`, `network_config.cfg`, and `generate_cert.sh`. 

My objective is to:

1. **Code Auditing & CWE Identification**: 
   Inspect the file `/home/user/infrastructure/security_groups.py`. It contains a severe vulnerability. Identify the standard CWE (Common Weakness Enumeration) identifier for this vulnerability (format: `CWE-XXX`).

2. **Configuration File Inspection**:
   Inspect the file `/home/user/infrastructure/network_config.cfg`. The configuration file is missing standard security parameters that protect against unauthorized access. Identify these missing parameters, which are `firewall_rule` and `port_control`. 

3. **TLS/SSL Certificate Management**:
   The script `/home/user/infrastructure/generate_cert.sh` is used to generate self-signed certificates for the development server. However, it currently uses dangerously weak cryptographic parameters (a weak RSA key size and a deprecated hashing algorithm). 
   Modify `/home/user/infrastructure/generate_cert.sh` to use an RSA key size of `2048` bits and the `sha256` hashing algorithm. Leave all other parameters (like validity days and subject) unchanged. Once modified, execute the script to generate `server.key` and `server.crt` in `/home/user/infrastructure/`.

Finally, create a JSON report of your findings at `/home/user/infrastructure/findings.json` with the exact following structure:
```json
{
  "security_groups.py": "CWE-XXX",
  "network_config.cfg_missing_parameters": ["firewall_rule", "port_control"]
}
```
Note that the missing configuration parameters should be sorted alphabetically in the JSON array. 

After creating the report, run the `python -m pytest /home/user/infrastructure/test_infrastructure.py` command to verify that the generated certificates are valid and the configuration file has been correctly updated.
