#!/usr/bin/env python3
"""
Create 18 SAFE test samples for IntelOwl analyzers:
- Floss (6 files, PE/COM)
- ELF_Info (6 files, ELF)
- DetectItEasy (6 files, mixed formats)
"""

import os
import struct
import zipfile
import json
from pathlib import Path

# ---------- CONFIG ----------
BASE_DIR = Path("/home/anonymous/COLLEGE/ThreatFlow/threatflow-middleware/app/intel_access/test_samples")
FLOSS_DIR = BASE_DIR / "floss_samples"
DIE_DIR = BASE_DIR / "detectiteasy_samples"
ELF_DIR = BASE_DIR / "elf_samples"


def ensure_dirs():
    for base in (FLOSS_DIR, DIE_DIR, ELF_DIR):
        (base / "safe").mkdir(parents=True, exist_ok=True)
        (base / "suspicious").mkdir(parents=True, exist_ok=True)


# ---------- FLOSS (PE) HELPERS ----------

def create_minimal_pe_with_strings(filepath: Path, strings_data: str):
    """Create a minimal PE-like file with embedded strings (good enough for Floss/DetectItEasy)."""
    filepath = Path(filepath)
    # Minimal DOS header
    dos_header = bytearray(64)
    dos_header[0:2] = b"MZ"
    dos_header[60:64] = struct.pack("<I", 64)  # e_lfanew

    # PE signature
    pe_signature = b"PE\x00\x00"

    # COFF header (20 bytes)
    coff_header = struct.pack(
        "<HHIIIHH",
        0x014C,  # i386
        1,       # sections
        0, 0, 0,
        224,     # size of optional header
        0x0102,  # executable
    )

    # Optional header (PE32, minimal)
    optional_header = bytearray(224)
    optional_header[0:2] = struct.pack("<H", 0x010B)  # PE32
    optional_header[16:20] = struct.pack("<I", 0x1000)   # BaseOfCode
    optional_header[20:24] = struct.pack("<I", 0x2000)   # BaseOfData
    optional_header[24:28] = struct.pack("<I", 0x400000) # ImageBase
    optional_header[28:32] = struct.pack("<I", 0x1000)   # SectionAlignment
    optional_header[32:36] = struct.pack("<I", 0x200)    # FileAlignment

    # Section header (.text)
    section_name = b".text\x00\x00\x00"
    section_data = strings_data.encode("utf-8", errors="ignore")
    virtual_size = len(section_data)

    section_header = struct.pack(
        "<8sIIIIIIHHI",
        section_name,
        virtual_size,          # VirtualSize
        0x1000,                # VirtualAddress
        len(section_data),     # SizeOfRawData
        0x200,                 # PointerToRawData
        0, 0, 0, 0,
        0x60000020,            # code | execute | read
    )

    pe_data = dos_header + pe_signature + coff_header + optional_header + section_header
    if len(pe_data) < 0x200:
        pe_data += b"\x00" * (0x200 - len(pe_data))
    pe_data += section_data

    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, "wb") as f:
        f.write(pe_data)
    return filepath


# ---------- ELF HELPERS ----------

def create_minimal_elf(filepath: Path, is_shared_lib: bool = False):
    """Create a minimal 64‑bit ELF binary (enough for ELF_Info)."""
    filepath = Path(filepath)

    elf_header = bytearray(64)
    elf_header[0:4] = b"\x7fELF"
    elf_header[4] = 2  # 64-bit
    elf_header[5] = 1  # little endian
    elf_header[6] = 1  # version

    # e_type
    elf_header[16:18] = struct.pack("<H", 3 if is_shared_lib else 2)  # DYN or EXEC
    # e_machine: x86-64
    elf_header[18:20] = struct.pack("<H", 0x3E)
    # e_version
    elf_header[20:24] = struct.pack("<I", 1)
    # e_entry
    elf_header[24:32] = struct.pack("<Q", 0x400000 if not is_shared_lib else 0)
    # e_phoff
    elf_header[32:40] = struct.pack("<Q", 64)
    # e_shoff
    elf_header[40:48] = struct.pack("<Q", 64 + 56)
    # e_ehsize
    elf_header[52:54] = struct.pack("<H", 64)
    # e_phentsize / e_phnum
    elf_header[54:56] = struct.pack("<H", 56)
    elf_header[56:58] = struct.pack("<H", 1)
    # e_shentsize / e_shnum / e_shstrndx
    elf_header[58:60] = struct.pack("<H", 64)
    elf_header[60:62] = struct.pack("<H", 3)
    elf_header[62:64] = struct.pack("<H", 2)

    # Program header
    ph = bytearray(56)
    ph[0:4] = struct.pack("<I", 1)  # PT_LOAD
    ph[4:8] = struct.pack("<I", 5)  # R|X
    ph[8:16] = struct.pack("<Q", 0)         # offset
    ph[16:24] = struct.pack("<Q", 0x400000) # vaddr
    ph[24:32] = struct.pack("<Q", 0x400000) # paddr
    ph[32:40] = struct.pack("<Q", 0x1000)   # filesz
    ph[40:48] = struct.pack("<Q", 0x1000)   # memsz
    ph[48:56] = struct.pack("<Q", 0x1000)   # align

    # Section headers (3)
    sh = bytearray()
    sh += bytearray(64)  # NULL

    # .text
    text = bytearray(64)
    text[0:4] = struct.pack("<I", 1)    # name offset
    text[4:8] = struct.pack("<I", 1)    # PROGBITS
    text[8:16] = struct.pack("<Q", 6)   # ALLOC|EXEC
    text[16:24] = struct.pack("<Q", 0x400000)
    text[24:32] = struct.pack("<Q", 0x1000)
    text[32:40] = struct.pack("<Q", 100)
    sh += text

    # .shstrtab
    shstr = bytearray(64)
    shstr[0:4] = struct.pack("<I", 7)
    shstr[4:8] = struct.pack("<I", 3)  # STRTAB
    shstr[24:32] = struct.pack("<Q", 64 + 56 + 192)
    shstr[32:40] = struct.pack("<Q", 20)
    sh += shstr

    string_table = b"\x00.text\x00.shstrtab\x00"

    data = elf_header + ph + sh + string_table
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, "wb") as f:
        f.write(data)
    os.chmod(filepath, 0o755)
    return filepath


# ---------- CREATE ALL SAMPLES ----------

def create_floss_samples():
    # SAFE 1
    s1 = """
Application Name: MyTestApp v1.0
Copyright 2024 Test
License: MIT
Configuration loaded successfully
Connecting to database...
User authentication complete
Processing data records
Operation completed successfully
"""
    create_minimal_pe_with_strings(FLOSS_DIR / "safe" / "sample1_simple_app.exe", s1)

    # SAFE 2
    s2 = """
https://api.example.com/v1/
https://www.example.com/login
GET /api/users HTTP/1.1
POST /api/data HTTP/1.1
Content-Type: application/json
Authorization: Bearer token
Server starting on port 8080
Health check endpoint active
"""
    create_minimal_pe_with_strings(FLOSS_DIR / "safe" / "sample2_webservice.exe", s2)

    # SAFE 3
    s3 = """
[INFO] Application initialized
[DEBUG] Loading configuration from config.ini
[INFO] Starting service worker threads
[WARNING] Retry limit set to 3 attempts
[INFO] Monitoring filesystem events
[INFO] Ready to accept connections
[INFO] Graceful shutdown initiated
"""
    create_minimal_pe_with_strings(FLOSS_DIR / "safe" / "sample3_logger.exe", s3)

    # SUSPICIOUS 1 – EICAR (safe industry test)
    eicar = b"X5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*"
    with open(FLOSS_DIR / "suspicious" / "eicar_test.com", "wb") as f:
        f.write(eicar)

    # SUSPICIOUS 2
    s4 = """
cmd.exe /c powershell.exe
net user administrator /active:yes
reg add HKLM\\Software\\Microsoft\\Windows\\CurrentVersion\\Run
schtasks /create /tn UpdateTask
C:\\Windows\\System32\\
download http://127.0.0.1:8080/payload
execute_shellcode
bypass_amsi
disable_defender
"""
    create_minimal_pe_with_strings(FLOSS_DIR / "suspicious" / "sample2_commandline.exe", s4)

    # SUSPICIOUS 3
    s5 = """
192.168.1.100:4444
10.0.0.50:8888
http://malicious-domain-test.local/gate.php
/admin/panel/upload.php
POST /c2/beacon HTTP/1.1
User-Agent: Mozilla/5.0 (Windows NT 10.0)
X-Session-ID: ABCD1234567890
heartbeat_interval=60
exfiltrate_data
reverse_shell_port=4444
persistence_registry_key
"""
    create_minimal_pe_with_strings(FLOSS_DIR / "suspicious" / "sample3_network.exe", s5)


def create_elf_samples():
    # SAFE
    create_minimal_elf(ELF_DIR / "safe" / "sample1_hello_world", is_shared_lib=False)
    create_minimal_elf(ELF_DIR / "safe" / "sample2_library.so", is_shared_lib=True)
    create_minimal_elf(ELF_DIR / "safe" / "sample3_utility", is_shared_lib=False)

    # SUSPICIOUS (names only, all safe)
    create_minimal_elf(ELF_DIR / "suspicious" / "sample1_dropper", is_shared_lib=False)
    create_minimal_elf(ELF_DIR / "suspicious" / "sample2_rootkit.so", is_shared_lib=True)
    create_minimal_elf(ELF_DIR / "suspicious" / "sample3_backdoor", is_shared_lib=False)


def create_die_samples():
    # SAFE 1 – text
    p1 = DIE_DIR / "safe" / "sample1_document.txt"
    p1.parent.mkdir(parents=True, exist_ok=True)
    p1.write_text(
        "This is a sample text document for testing DetectItEasy file type detection.\n"
        "The tool should identify this as a plain text file.\n"
    )

    # SAFE 2 – zip
    p2 = DIE_DIR / "safe" / "sample2_archive.zip"
    with zipfile.ZipFile(p2, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("readme.txt", "This is a test ZIP archive\n")
        zf.writestr("data/config.ini", "[Settings]\nport=8080\n")
        zf.writestr("data/sample.log", "INFO: Application started\n")

    # SAFE 3 – json
    p3 = DIE_DIR / "safe" / "sample3_config.json"
    cfg = {
        "application": "TestApp",
        "version": "1.0.0",
        "server": {"host": "localhost", "port": 8080},
        "database": {"type": "postgresql", "connection": "postgresql://localhost:5432/testdb"},
    }
    p3.write_text(json.dumps(cfg, indent=2))

    # SUSPICIOUS 1 – PE + EICAR
    s = """
EICAR Test File - Safe malware signature
X5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*
This file contains the EICAR test signature for AV testing.
"""
    create_minimal_pe_with_strings(DIE_DIR / "suspicious" / "sample1_eicar.exe", s)

    # SUSPICIOUS 2 – batch
    p4 = DIE_DIR / "suspicious" / "sample2_script.bat"
    p4.write_text(
        "@echo off\n"
        "REM SAFE test file with suspicious-looking patterns\n"
        "echo cmd.exe /c dir\n"
        "echo powershell.exe -ExecutionPolicy Bypass\n"
        "echo reg add HKLM\\Software\\Test\n"
        "echo schtasks /create /tn TestTask\n"
        "echo This file is for TESTING ONLY\n"
    )

    # SUSPICIOUS 3 – python
    p5 = DIE_DIR / "suspicious" / "sample3_encoded.py"
    p5.write_text(
        "#!/usr/bin/env python3\n"
        "# SAFE test script for DetectItEasy\n"
        "import base64, zlib\n"
        "encoded = base64.b64encode(b'Hello World Test String').decode()\n"
        "compressed = zlib.compress(b'Sample data for compression testing')\n"
        "payload = 'test_payload_string'\n"
        "shellcode = bytes([0x90, 0x90, 0x90, 0x90])\n"
        "c2_server = '127.0.0.1:8080'\n"
        "print('SAFE test script for malware analysis training')\n"
        "print('Encoded:', encoded)\n"
    )
    os.chmod(p5, 0o755)


def main():
    ensure_dirs()
    create_floss_samples()
    create_elf_samples()
    create_die_samples()

    print(f"✓ Created 18 SAFE samples under: {BASE_DIR}")
    print("\nQuick check:")
    print(f"  find {BASE_DIR} -type f | sort")
    print("\nExample IntelOwl call (Floss):")
    print(
        f'  curl -H "Authorization: Token YOUR_API_KEY" '
        f'-F "file=@{FLOSS_DIR / "safe" / "sample1_simple_app.exe"}" '
        f'-F \'analyzers_requested=["Floss"]\' http://localhost/api/analyze_file'
    )


if __name__ == "__main__":
    main()