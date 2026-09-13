#!/bin/bash

# Create the /home/user directory and set its permissions
mkdir -p /home/user
chmod 755 /home/user

# Create the /home/user/verify_token.sh script
echo "#!/bin/bash" > /home/user/verify_token.sh
echo "echo 'Vulnerability: CWE-347'" >> /home/user/verify_token.sh
chmod 755 /home/user/verify_token.sh

# Create the /home/user/evasion.token file with the crafted token string
echo -n "eyJhbGciOiJub25lIn0=.eyJyb2xlIjoiYWRtaW4ifQ==." > /home/user/evasion.token

# Set the permissions of the /home/user/evasion.token file to 0400
chmod 0400 /home/user/evasion.token

# Create the /home/user/exfiltration_report.txt file
echo "CWE-347" > /home/user/exfiltration_report.txt
sha256sum /home/user/evasion.token | cut -d' ' -f1 >> /home/user/exfiltration_report.txt

# Install required packages using pip
pip3 install pytest

# Set the permissions of all files in /home/user to 777
chmod -R 777 /home/user
