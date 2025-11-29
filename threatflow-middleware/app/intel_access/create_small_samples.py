#!/usr/bin/env python3
"""
Create SMALL, SAFE test samples for medium analyzers:
- PEframe_Scan (PE, Office-like)
- Malpedia_Scan (malware-like PE/bin)
- OneNote_Info (OneNote-like)
- GoReSym (Go-like binaries)

All files are a few KB each, not hundreds of MB.
"""

import os
import struct
import zipfile
from pathlib import Path
import json
import random

BASE_DIR = Path("/home/anonymous/COLLEGE/ThreatFlow/threatflow-middleware/app/intel_access/test_samples_small")
MEDIUM_ANALYZERS_DIR = BASE_DIR / "medium_analyzers"

PEFRAME_DIR = MEDIUM_ANALYZERS_DIR / "peframe_scan"
MALPEDIA_DIR = MEDIUM_ANALYZERS_DIR / "malpedia_scan"
ONENOTE_DIR = MEDIUM_ANALYZERS_DIR / "onenote_info"
GORESYM_DIR = MEDIUM_ANALYZERS_DIR / "gore_sym"


def ensure_dirs():
    for d in [PEFRAME_DIR, MALPEDIA_DIR, ONENOTE_DIR, GORESYM_DIR]:
        (d / "safe").mkdir(parents=True, exist_ok=True)
        (d / "suspicious").mkdir(parents=True, exist_ok=True)


# ---------- HELPERS ----------

def create_minimal_pe(filepath: Path, extra_strings: str = ""):
    """Very small PE-like file, good enough for PEframe + DetectItEasy."""
    filepath = Path(filepath)
    dos_header = b"MZ" + b"\x90" * 58 + struct.pack("<I", 0x40)
    pe_sig = b"PE\x00\x00"
    coff = struct.pack("<HHIIIHH", 0x014C, 1, 0, 0, 0, 0xE0, 0x0102)
    opt = bytearray(0xE0)
    opt[0:2] = struct.pack("<H", 0x010B)  # PE32
    section_name = b".text\x00\x00\x00"
    body = (b"LEGIT_APP" + extra_strings.encode("utf-8", errors="ignore"))
    sec = struct.pack(
        "<8sIIIIIIHHI",
        section_name,
        len(body),
        0x1000,
        len(body),
        0x200,
        0, 0, 0, 0,
        0x60000020,
    )
    pe = dos_header + pe_sig + coff + opt + sec
    if len(pe) < 0x200:
        pe += b"\x00" * (0x200 - len(pe))
    pe += body
    filepath.parent.mkdir(parents=True, exist_ok=True)
    filepath.write_bytes(pe)
    return filepath


def create_minimal_elf(filepath: Path, is_shared_lib: bool = False):
    """Very small 64‑bit ELF (good for ELF_Info / Malpedia context)."""
    filepath = Path(filepath)
    elf = bytearray(64)
    elf[0:4] = b"\x7fELF"
    elf[4] = 2  # 64-bit
    elf[5] = 1  # LE
    elf[6] = 1
    elf[16:18] = struct.pack("<H", 3 if is_shared_lib else 2)  # DYN/EXEC
    elf[18:20] = struct.pack("<H", 0x3E)  # x86-64
    elf[20:24] = struct.pack("<I", 1)
    elf[24:32] = struct.pack("<Q", 0x400000 if not is_shared_lib else 0)
    elf[32:40] = struct.pack("<Q", 64)       # phoff
    elf[40:48] = struct.pack("<Q", 64 + 56)  # shoff
    elf[52:54] = struct.pack("<H", 64)
    elf[54:56] = struct.pack("<H", 56)
    elf[56:58] = struct.pack("<H", 1)
    elf[58:60] = struct.pack("<H", 64)
    elf[60:62] = struct.pack("<H", 3)
    elf[62:64] = struct.pack("<H", 2)

    ph = bytearray(56)
    ph[0:4] = struct.pack("<I", 1)   # PT_LOAD
    ph[4:8] = struct.pack("<I", 5)   # R|X
    ph[8:16] = struct.pack("<Q", 0)
    ph[16:24] = struct.pack("<Q", 0x400000)
    ph[24:32] = struct.pack("<Q", 0x400000)
    ph[32:40] = struct.pack("<Q", 0x200)
    ph[40:48] = struct.pack("<Q", 0x200)
    ph[48:56] = struct.pack("<Q", 0x1000)

    sh = bytearray()
    sh += bytearray(64)
    text = bytearray(64)
    text[0:4] = struct.pack("<I", 1)
    text[4:8] = struct.pack("<I", 1)    # PROGBITS
    text[8:16] = struct.pack("<Q", 6)   # ALLOC|EXEC
    text[16:24] = struct.pack("<Q", 0x400000)
    text[24:32] = struct.pack("<Q", 0x200)
    text[32:40] = struct.pack("<Q", 64)
    sh += text
    shstr = bytearray(64)
    shstr[0:4] = struct.pack("<I", 7)
    shstr[4:8] = struct.pack("<I", 3)
    shstr[24:32] = struct.pack("<Q", 64 + 56 + 192)
    shstr[32:40] = struct.pack("<Q", 20)
    sh += shstr

    strtab = b"\x00.text\x00.shstrtab\x00"
    body = b"echo 'hello from tiny elf'\n"
    data = elf + ph + sh + strtab + body
    filepath.parent.mkdir(parents=True, exist_ok=True)
    filepath.write_bytes(data)
    os.chmod(filepath, 0o755)
    return filepath


def random_bytes(n: int) -> bytes:
    return os.urandom(n)


# ---------- PEFRAME_Scan (3 small PE/Office-like) ----------

def create_peframe_small():
    # Safe PE
    create_minimal_pe(
        PEFRAME_DIR / "safe" / "peframe_safe_app.exe",
        extra_strings="""
DocumentProcessor
OfficeCompatibility
StaticAnalysisTest
"""
    )
    # Suspicious PE (safe, only strings)
    create_minimal_pe(
        PEFRAME_DIR / "suspicious" / "peframe_susp_maldoc.exe",
        extra_strings="""
Word.Document.8
AutoOpen
powershell.exe -ExecutionPolicy Bypass
hxxp://example[.]local/maldoc
"""
    )
    # Small Office-like doc (for Office path in PEframe_Scan) [web:1]
    doc_path = PEFRAME_DIR / "suspicious" / "sample_macro.doc"
    content = (
        "DOCFILE TEST\n"
        "Sub AutoOpen()\n"
        "   Shell \"cmd.exe /c calc.exe\"\n"
        "End Sub\n"
    )
    doc_path.write_bytes(content.encode("utf-8") + random_bytes(2048))


# ---------- Malpedia_Scan (3 small malware-like bins) ----------

def create_malpedia_small():
    # PE with family-like strings (safe)
    create_minimal_pe(
        MALPEDIA_DIR / "suspicious" / "malpedia_emotet_like.exe",
        extra_strings="""
EmotetLoader
C2_Server=127.0.0.1:443
InjectExplorer
"""
    )
    # ELF with family-like strings
    elf_path = MALPEDIA_DIR / "suspicious" / "malpedia_linus_backdoor"
    create_minimal_elf(elf_path, is_shared_lib=False)
    elf_path.write_bytes(elf_path.read_bytes() + b"\nBackdoorSample\nSSHKeySteal\n")

    # Safe archive with mixed benign files
    zip_path = MALPEDIA_DIR / "safe" / "malpedia_legit_bundle.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("readme.txt", "Legitimate bundle for Malpedia_Scan testing only.\n")
        zf.writestr("config.json", json.dumps({"family": "test", "type": "benign"}, indent=2))
        zf.writestr("dummy.bin", random_bytes(4096))


# ---------- OneNote_Info (3 small OneNote-like) ----------

def create_onenote_small():
    header = b"Microsoft Office OneNote Document" + b"\x00" * 32

    # Safe note
    (ONENOTE_DIR / "safe").mkdir(parents=True, exist_ok=True)
    (ONENOTE_DIR / "suspicious").mkdir(parents=True, exist_ok=True)

    safe1 = ONENOTE_DIR / "safe" / "onenote_meeting.one"
    text1 = (
        "Meeting Notes\n"
        "Date: 2025-11-29\n"
        "Topic: IntelOwl testing\n"
    )
    safe1.write_bytes(header + text1.encode() + random_bytes(1024))

    # Suspicious note (macro-like text, but safe)
    susp1 = ONENOTE_DIR / "suspicious" / "onenote_macro_like.one"
    text2 = (
        "EmbeddedScript (TEST ONLY)\n"
        "powershell.exe -w hidden -enc AAAA...\n"
        "Sub AutoOpen()\n"
        "   ' test macro text\n"
        "End Sub\n"
    )
    susp1.write_bytes(header + text2.encode() + random_bytes(2048))

    # Another safe note
    safe2 = ONENOTE_DIR / "safe" / "onenote_docs.one"
    text3 = "Project documentation and task list.\n"
    safe2.write_bytes(header + text3.encode() + random_bytes(1024))


# ---------- GoReSym (3 small Go-like bins) ----------

def create_gore_sym_small():
    # Fake Go header + strings (good enough for GoReSym expectations) [web:56]
    go_hdr = b"\x7fELFGO"  # not real, but distinctive

    safe1 = GORESYM_DIR / "safe" / "goserver_small"
    body1 = (
        "main.main\n"
        "net/http\n"
        "github.com/gin-gonic/gin\n"
    ).encode()
    safe1.write_bytes(go_hdr + body1 + random_bytes(2048))
    os.chmod(safe1, 0o755)

    susp1 = GORESYM_DIR / "suspicious" / "goc2_small"
    body2 = (
        "reverse_shell\n"
        "c2=127.0.0.1:4444\n"
        "beacon_interval=30s\n"
    ).encode()
    susp1.write_bytes(go_hdr + body2 + random_bytes(4096))
    os.chmod(susp1, 0o755)

    # Another safe Go-style binary
    safe2 = GORESYM_DIR / "safe" / "gotool_small"
    body3 = (
        "flag.Parse\n"
        "log.Fatal\n"
        "context.Background\n"
    ).encode()
    safe2.write_bytes(go_hdr + body3 + random_bytes(2048))
    os.chmod(safe2, 0o755)


def main():
    ensure_dirs()
    create_peframe_small()
    create_malpedia_small()
    create_onenote_small()
    create_gore_sym_small()

    print(f"✓ Created small test set under: {MEDIUM_ANALYZERS_DIR}")
    print("\nCheck sizes (all well under 30–40MB total):")
    print(f"  du -sh {BASE_DIR}")
    print("\nExample IntelOwl calls:")
    print(f"  # PEframe_Scan")
    print(f"  curl -H 'Authorization: Token YOUR_KEY' "
          f"-F 'file=@{PEFRAME_DIR}/suspicious/peframe_susp_maldoc.exe' "
          f"-F 'analyzers_requested=[\"PEframe_Scan\"]' "
          f"http://localhost/api/analyze_file")
    print(f"\n  # Malpedia_Scan")
    print(f"  curl -H 'Authorization: Token YOUR_KEY' "
          f"-F 'file=@{MALPEDIA_DIR}/suspicious/malpedia_emotet_like.exe' "
          f"-F 'analyzers_requested=[\"Malpedia_Scan\"]' "
          f"http://localhost/api/analyze_file")
    print(f"\n  # OneNote_Info")
    print(f"  curl -H 'Authorization: Token YOUR_KEY' "
          f"-F 'file=@{ONENOTE_DIR}/suspicious/onenote_macro_like.one' "
          f"-F 'analyzers_requested=[\"OneNote_Info\"]' "
          f"http://localhost/api/analyze_file")
    print(f"\n  # GoReSym")
    print(f"  curl -H 'Authorization: Token YOUR_KEY' "
          f"-F 'file=@{GORESYM_DIR}/suspicious/goc2_small' "
          f"-F 'analyzers_requested=[\"GoReSym\"]' "
          f"http://localhost/api/analyze_file")


if __name__ == "__main__":
    main()