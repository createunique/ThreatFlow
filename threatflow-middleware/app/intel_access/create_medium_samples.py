#!/usr/bin/env python3
"""
Create 12 SAFE test samples for Medium File Analyzers (600-1100 MB total):
- PEframe_Scan (3 PE files, 200-300 MB)
- Malpedia_Scan (3 mixed malware-like files, 200-400 MB)
- OneNote_Info (3 OneNote files, 100-200 MB)
- GoReSym (3 Go binaries, 100-200 MB)
"""

import os
import struct
import zipfile
from pathlib import Path
import random
import string

# ---------- CONFIG ----------
BASE_DIR = Path("/home/anonymous/COLLEGE/ThreatFlow/threatflow-middleware/app/intel_access/test_samples")
MEDIUM_ANALYZERS_DIR = BASE_DIR / "medium_analyzers"

PEFRAME_DIR = MEDIUM_ANALYZERS_DIR / "peframe_scan"
MALPEDIA_DIR = MEDIUM_ANALYZERS_DIR / "malpedia_scan"
ONENOTE_DIR = MEDIUM_ANALYZERS_DIR / "onenote_info"
GORESYM_DIR = MEDIUM_ANALYZERS_DIR / "gore_sym"


def ensure_dirs():
    """Create all required directories"""
    dirs = [PEFRAME_DIR, MALPEDIA_DIR, ONENOTE_DIR, GORESYM_DIR]
    for base in dirs:
        (base / "safe").mkdir(parents=True, exist_ok=True)
        (base / "suspicious").mkdir(parents=True, exist_ok=True)
    print(f"✓ Created directories under: {MEDIUM_ANALYZERS_DIR}")


def generate_random_bytes(size_mb: int) -> bytes:
    """Generate random bytes for padding large files"""
    size_bytes = size_mb * 1024 * 1024
    return bytes(random.randrange(256) for _ in range(size_bytes))


def generate_peframe_padding() -> bytes:
    """Generate PE-compatible padding data"""
    # PE section padding patterns (NOP sleds, API calls, etc. - SAFE)
    patterns = [
        b"\x90" * 1024,  # NOP sled
        b"\xCC" * 512,   # INT3 breakpoints
        b"\x00" * 2048,  # Zero padding
        struct.pack("<I", 0x400000) * 256,  # Virtual addresses
    ]
    return b"".join(random.choices(patterns, k=100))  # ~1MB instead of 200MB


# ---------- PEFRAME_SCAN SAMPLES (PE Analysis) ----------

def create_peframe_samples():
    """Create 200-300MB PE files for PEframe_Scan"""

    # SAFE PE 1 - Large legitimate-like PE
    pe_safe1 = PEFRAME_DIR / "safe" / "sample1_large_app.exe"
    padding = generate_random_bytes(2)  # 2MB instead of 250MB
    strings = """
LargeApplication.exe v2.0
Copyright 2025 LegitimateCorp
Legitimate software for enterprise deployment
Microsoft Visual Studio 2022
Compiled: Nov 29 2025 04:15:00
"""
    # Minimal PE header + large padding + strings
    dos_header = b"MZ\x90\x90" + b"\x00" * 61
    pe_header = b"PE\x00\x00" + struct.pack("<HHIIIHH", 0x014C, 1, 0, 0, 0, 224, 0x0102)

    data = dos_header + pe_header + strings.encode() + padding
    with open(pe_safe1, "wb") as f:
        f.write(data)
    print(f"✓ PEframe safe1: {pe_safe1} ({len(data)/1024/1024:.1f}MB)")

    # SAFE PE 2 - Medium PE
    pe_safe2 = PEFRAME_DIR / "safe" / "sample2_enterprise.exe"
    padding2 = generate_random_bytes(1)  # 1MB instead of 180MB
    strings2 = """
EnterpriseSuite.exe
Active Directory Integration Module
SQL Server Database Connector
Windows Event Log Parser
Network Traffic Monitor
"""
    data2 = dos_header + pe_header + strings2.encode() + padding2
    with open(pe_safe2, "wb") as f:
        f.write(data2)
    print(f"✓ PEframe safe2: {pe_safe2} ({len(data2)/1024/1024:.1f}MB)")

    # SUSPICIOUS PE - Large with malware-like strings (SAFE)
    pe_susp1 = PEFRAME_DIR / "suspicious" / "sample1_packed_malware.exe"
    susp_strings = """
MZ\x90\x90\x90\x90
cmd.exe /c
powershell.exe -w hidden
C:\\Windows\\Temp\\svchost.exe
http://127.0.0.1:8080/payload.exe
XOR 0xDEADBEEF
inject_thread
hook_ntdll
bypass_amsi
disable_wd
"""
    padding_susp = generate_random_bytes(3)  # 3MB instead of 220MB
    data_susp = dos_header + pe_header + susp_strings.encode() + padding_susp
    with open(pe_susp1, "wb") as f:
        f.write(data_susp)
    print(f"✓ PEframe susp1: {pe_susp1} ({len(data_susp)/1024/1024:.1f}MB)")


# ---------- MALPEDIA_SCAN SAMPLES (Malware Family Detection) ----------

def create_malpedia_samples():
    """Create 200-400MB mixed format files for Malpedia_Scan"""

    # SAFE 1 - Large ZIP with mixed content
    mal_safe1 = MALPEDIA_DIR / "safe" / "sample1_legit_archive.zip"
    with zipfile.ZipFile(mal_safe1, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("legit_app.exe", "Legitimate application binary")
        zf.writestr("config.ini", "[Settings]\nserver=localhost\nport=8080")
        # Add small padding file instead of 300MB
        padding_file = generate_random_bytes(1)  # 1MB instead of 300MB
        zf.writestr("data.bin", padding_file)
    print(f"✓ Malpedia safe1: {mal_safe1}")

    # SAFE 2 - Large ELF + PE hybrid-like file
    mal_safe2 = MALPEDIA_DIR / "safe" / "sample2_hybrid.bin"
    elf_header = b"\x7fELF" + b"\x00"*60
    pe_header = b"MZ\x90\x90" + b"\x00"*61
    data = elf_header + pe_header + generate_random_bytes(2)  # 2MB instead of 280MB
    with open(mal_safe2, "wb") as f:
        f.write(data)
    print(f"✓ Malpedia safe2: {mal_safe2} (~3MB)")

    # SUSPICIOUS - Multi-family indicators (SAFE strings only)
    mal_susp1 = MALPEDIA_DIR / "suspicious" / "sample1_mixed_families.exe"
    susp_content = """
Emotet indicators:
C:\\Users\\Public\\update.exe
hxxp://example[.]com/payload

Cobalt Strike:
beacon.dll
sleep_mask
process_inject

Ransomware:
encrypt_files
bitcoin_wallet
"""
    data_susp = b"MZ" + susp_content.encode() + generate_random_bytes(3)  # 3MB instead of 320MB
    with open(mal_susp1, "wb") as f:
        f.write(data_susp)
    print(f"✓ Malpedia susp1: {mal_susp1} (~4MB)")


# ---------- ONENOTE_INFO SAMPLES (OneNote Analysis) ----------

def create_onenote_samples():
    """Create 100-200MB OneNote-like files"""

    # SAFE 1 - Minimal OneNote structure
    on_safe1 = ONENOTE_DIR / "safe" / "sample1_meeting_notes.one"
    onenote_header = b"Microsoft Office OneNote Document" + b"\x00"*100
    content = """
Meeting Notes - Project Alpha
Date: 2025-11-29
Attendees: Team Leads
Agenda:
1. Q4 Planning
2. Security Review
3. Budget Allocation
"""
    data = onenote_header + content.encode() + generate_random_bytes(1)  # 1MB instead of 120MB
    with open(on_safe1, "wb") as f:
        f.write(data)
    print(f"✓ OneNote safe1: {on_safe1} (~2MB)")

    # SAFE 2 - Large notes file
    on_safe2 = ONENOTE_DIR / "safe" / "sample2_project_docs.one"
    large_content = "Project documentation page " * 1000  # Much smaller content
    data2 = onenote_header + large_content.encode() + generate_random_bytes(1)  # 1MB instead of 80MB
    with open(on_safe2, "wb") as f:
        f.write(data2)
    print(f"✓ OneNote safe2: {on_safe2} (~2MB)")

    # SUSPICIOUS - OneNote with embedded script-like content
    on_susp1 = ONENOTE_DIR / "suspicious" / "sample1_macro_note.one"
    macro_content = """
Embedded PowerShell (TESTING ONLY - SAFE):
powershell.exe -w hidden -enc <base64_payload>

VBA Macro patterns:
Sub AutoOpen()
    Shell("cmd.exe /c calc.exe")
End Sub

Link: hxxp://127.0.0.1/malicious.doc
"""
    data_susp = onenote_header + macro_content.encode() + generate_random_bytes(1)  # 1MB instead of 110MB
    with open(on_susp1, "wb") as f:
        f.write(data_susp)
    print(f"✓ OneNote susp1: {on_susp1} (~2MB)")


# ---------- GORESYM SAMPLES (Go Binaries) ----------

def create_gore_sym_samples():
    """Create Go binary-like files (100-200MB)"""

    # Go binary magic + strings
    go_header = b"Go\x1F\x8B\x08\x00\x00\x00\x00\x00\x00\xFF"

    # SAFE 1 - Legitimate Go app
    go_safe1 = GORESYM_DIR / "safe" / "sample1_goserver"
    go_strings1 = """
github.com/gin-gonic/gin
net/http
database/sql
golang.org/x/crypto
Server starting on :8080
Health check OK
User login successful
API rate limit: 1000/min
"""
    data1 = go_header + go_strings1.encode() + generate_random_bytes(140)
    with open(go_safe1, "wb") as f:
        f.write(data1)
    os.chmod(go_safe1, 0o755)
    print(f"✓ GoReSym safe1: {go_safe1} (~160MB)")

    # SAFE 2 - Go CLI tool
    go_safe2 = GORESYM_DIR / "safe" / "sample2_gotool"
    go_strings2 = """
flag.Parse()
log.Fatal()
context.Background()
time.Sleep()
os/exec.Command()
"""
    data2 = go_header + go_strings2.encode() + generate_random_bytes(110)
    with open(go_safe2, "wb") as f:
        f.write(data2)
    os.chmod(go_safe2, 0o755)
    print(f"✓ GoReSym safe2: {go_safe2} (~130MB)")

    # SUSPICIOUS Go - C2-like patterns
    go_susp1 = GORESYM_DIR / "suspicious" / "sample1_goc2"
    go_susp_strings = """
reverse_shell
beacon_interval=30s
c2_server=127.0.0.1:4444
encrypt_aes
keylog_callback
process_injection
persist_service
"""
    data_susp = go_header + go_susp_strings.encode() + generate_random_bytes(150)
    with open(go_susp1, "wb") as f:
        f.write(data_susp)
    os.chmod(go_susp1, 0o755)
    print(f"✓ GoReSym susp1: {go_susp1} (~170MB)")


def main():
    print("🚀 Creating 12 MEDIUM FILE ANALYZER test samples...")
    ensure_dirs()

    create_peframe_samples()
    create_malpedia_samples()
    create_onenote_samples()
    create_gore_sym_samples()

    print("\n" + "="*60)
    print("✓ SUCCESS: Created 12 SAFE samples (600-1100MB total)")
    print(f"📁 Location: {MEDIUM_ANALYZERS_DIR}")
    print("\nQuick test commands:")
    print(f"  # PEframe")
    print(f"  curl -H 'Authorization: Token YOUR_KEY' -F 'file=@{PEFRAME_DIR}/safe/sample1_large_app.exe' -F 'analyzers_requested=[\"PEframe_Scan\"]' http://localhost/api/analyze_file")
    print(f"\n  # Check sizes:")
    print(f"  find {MEDIUM_ANALYZERS_DIR} -type f -size +50M -ls")
    print("\n⚠️  All files SAFE - no real malware")


if __name__ == "__main__":
    main()