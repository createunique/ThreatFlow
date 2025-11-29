#!/usr/bin/env python3
# SAFE test script for DetectItEasy
import base64, zlib
encoded = base64.b64encode(b'Hello World Test String').decode()
compressed = zlib.compress(b'Sample data for compression testing')
payload = 'test_payload_string'
shellcode = bytes([0x90, 0x90, 0x90, 0x90])
c2_server = '127.0.0.1:8080'
print('SAFE test script for malware analysis training')
print('Encoded:', encoded)
