# IntelOwl Analyzer Response Reference

## Overview

This document contains the **verified field paths** for all tested IntelOwl analyzers, extracted from actual API responses during comprehensive testing. Use this reference when building conditional workflows or debugging condition evaluation.

**Test Date:** November 2025  
**IntelOwl Version:** 6.x with malware_tools_analyzers container  
**Total Analyzers Tested:** 18  

---

## Analyzer Response Structures

### 1. ClamAV (Antivirus Scanner)

**Purpose:** Detect known malware using signature-based scanning.

**Response Structure:**
```json
{
  "name": "ClamAV",
  "status": "SUCCESS",
  "report": {
    "detections": ["Eicar-Signature"],  // EMPTY ARRAY [] if clean
    "raw_report": "/tmp/file.exe: Eicar-Signature FOUND\n\n----------- SCAN SUMMARY -----------\nInfected files: 1"
  }
}
```

**Key Fields for Conditions:**
| Field Path | Type | Description | Malicious When |
|------------|------|-------------|----------------|
| `report.detections` | Array | Detection names | Length > 0 |
| `report.raw_report` | String | Raw scan output | Contains "FOUND" |

**Condition Examples:**
```python
# verdict_malicious
len(report.detections) > 0  # True if malware found

# verdict_clean
len(report.detections) == 0 and "FOUND" not in raw_report

# has_detections
len(report.detections) > 0
```

---

### 2. Yara (Pattern Matching)

**Purpose:** Match files against YARA rules from multiple rule sets.

**Response Structure:**
```json
{
  "name": "Yara",
  "status": "SUCCESS",
  "report": {
    "yara-rules_rules": [
      {
        "url": "https://github.com/Yara-Rules/rules.git",
        "meta": {"author": "..."},
        "path": "/opt/deploy/files_required/yara/yara-rules_rules/utils/domain.yar",
        "tags": [],
        "match": "domain",
        "strings": [{"plaintext": [...], "identifier": "$domain_regex"}]
      }
    ],
    "elastic_protections-artifacts": [],
    "advanced-threat-research_yara-rules": [],
    "neo23x0_signature-base": [],
    "bartblaze_yara-rules": [],
    "intezer_yara-rules": [],
    "inquest_yara-rules": [],
    // ... more rule sets
  },
  "data_model": {
    "evaluation": "malicious",  // or null for clean
    "signatures": [
      {
        "provider": "yara",
        "url": "...",
        "score": 1,
        "signature": {...}
      }
    ]
  }
}
```

**Key Fields for Conditions:**
| Field Path | Type | Description | Malicious When |
|------------|------|-------------|----------------|
| `data_model.evaluation` | String | Overall verdict | == "malicious" |
| `data_model.signatures` | Array | Matched signatures | Length > 0 |
| `report.<rule_set_name>` | Array | Per-rule-set matches | Contains non-utility rules |

**Available Rule Sets:**
- `yara-rules_rules` - Yara-Rules community rules
- `elastic_protections-artifacts` - Elastic security rules
- `advanced-threat-research_yara-rules` - McAfee ATR rules
- `neo23x0_signature-base` - Florian Roth rules
- `bartblaze_yara-rules`, `intezer_yara-rules`, `inquest_yara-rules`
- `reversinglabs_reversinglabs-yara-rules`, `mandiant_red_team_tool_countermeasures`
- `dr4k0nia_yara-rules`, `embee-research_yara`, `fboldewin_yara-rules`
- `jpcertcc_jpcert-yara`, `sbousseaden_yarahunts`, `strangerealintel_dailyioc`
- `stratosphereips_yara-rules`, `sifalcon_detection`, `elceef_yara-rulz`
- `yaraify-api.abuse.ch_yaraify-rules`

**Note:** Utility rules like `utils/domain.yar` and `utils/url.yar` match frequently but are NOT malware indicators. Filter these out for accurate malware detection.

---

### 3. File_Info (Metadata Analysis)

**Purpose:** Extract file metadata, hashes, and type information.

**Response Structure:**
```json
{
  "name": "File_Info",
  "status": "SUCCESS",
  "report": {
    "md5": "5b809b6590a7f01cf5fdb2bb7c3eb7b4",
    "sha1": "10516835b3e38226612cfd8675a157f9173d7fb8",
    "sha256": "499cdf27b38a63b855ba91550c4f694a228468cf3b1499257a93ec00947c897a",
    "tlsh": "TNULL",
    "ssdeep": "3:IFAF0GEALJn:gon",
    "magic": "ASCII text",
    "mimetype": "text/plain",
    "filetype": "TXT",
    "exiftool": {"ExifTool:ExifToolVersion": 13.29}
  }
}
```

**Key Fields for Conditions:**
| Field Path | Type | Description | Use Case |
|------------|------|-------------|----------|
| `report.mimetype` | String | MIME type | Route by file type |
| `report.filetype` | String | Short type name | Filter for PE, PDF, etc. |
| `report.magic` | String | Magic bytes description | Detect file type |

**Important:** File_Info is metadata-only and **cannot detect malware**. Always returns clean for `verdict_malicious`.

---

### 4. Doc_Info (Office Document Analysis)

**Purpose:** Analyze Microsoft Office documents for macros and suspicious content.

**Response Structure:**
```json
{
  "name": "Doc_Info",
  "status": "SUCCESS",
  "report": {
    "mraptor": "ok",  // or "suspicious" for malicious macros
    "olevba": {
      "xlm_macro": false,
      "macro_data": [
        {
          "filename": "/opt/deploy/files_required/...",
          "ole_path": null,
          "vba_code": null
        }
      ]
    },
    "msodde": "",
    "uris": [],
    "extracted_CVEs": []
  }
}
```

**Key Fields for Conditions:**
| Field Path | Type | Description | Malicious When |
|------------|------|-------------|----------------|
| `report.mraptor` | String | Macro security rating | == "suspicious" |
| `report.olevba.xlm_macro` | Boolean | XLM macro detected | == true |
| `report.uris` | Array | Extracted URIs | Contains suspicious URLs |
| `report.extracted_CVEs` | Array | CVE references | Length > 0 |

---

### 5. Strings_Info (String Extraction)

**Purpose:** Extract readable strings from binary files.

**Response Structure:**
```json
{
  "name": "Strings_Info",
  "status": "SUCCESS",
  "report": {
    "data": [
      "C:\\Windows\\System32\\cmd.exe /c powershell -enc",
      "http://malicious-c2-server.com/payload.exe",
      "...more strings..."
    ],
    "uris": [],
    "exceeded_max_number_of_strings": false
  }
}
```

**Key Fields for Conditions:**
| Field Path | Type | Description | Malicious When |
|------------|------|-------------|----------------|
| `report.data` | Array | Extracted strings | Contains suspicious patterns |
| `report.uris` | Array | Detected URIs | Contains malicious URLs |

**Suspicious Patterns to Check:**
- `powershell`, `cmd.exe`, `wscript`, `cscript`
- `malicious`, `exploit`, `payload`, `shellcode`
- `c2-server`, `backdoor`, `trojan`

---

### 6. Quark_Engine (Android Malware Scoring)

**Purpose:** Score Android APK files for malicious behaviors.

**Response Structure:**
```json
{
  "name": "Quark_Engine",
  "status": "SUCCESS",
  "report": {
    "md5": "57b97baedf98797a23321420a4bdbf24",
    "threat_level": "Low Risk",  // "Low Risk", "Medium Risk", "High Risk"
    "total_score": 0,  // 0-100
    "crimes": [],  // Detected malicious behaviors
    "size_bytes": 429,
    "apk_filename": "..."
  }
}
```

**Key Fields for Conditions:**
| Field Path | Type | Description | Malicious When |
|------------|------|-------------|----------------|
| `report.threat_level` | String | Risk classification | == "High Risk" or "Critical" |
| `report.total_score` | Number | Threat score 0-100 | > 50 |
| `report.crimes` | Array | Detected behaviors | Length > 0 |

**Threat Level Values:**
- `"Low Risk"` - Clean/Safe
- `"Medium Risk"` - Suspicious
- `"High Risk"` - Malicious
- `"Critical"` - Confirmed malware

---

### 7. APK_Artifacts (Android Permissions)

**Purpose:** Extract Android APK metadata and permissions.

**Response Structure:**
```json
{
  "name": "APK_Artifacts",
  "status": "SUCCESS",
  "report": {
    "permission": [
      "android.permission.INTERNET",
      "android.permission.READ_SMS"
    ],
    "intent": [
      "android.intent.action.MAIN",
      "android.intent.category.LAUNCHER"
    ],
    "application": ["com.malicious.trojan"]
  }
}
```

**Key Fields for Conditions:**
| Field Path | Type | Description | Malicious When |
|------------|------|-------------|----------------|
| `report.permission` | Array | Requested permissions | Contains dangerous permissions |
| `report.application` | Array | App identifiers | Contains suspicious package names |

**Dangerous Permissions:**
- `android.permission.READ_SMS`
- `android.permission.SEND_SMS`
- `android.permission.RECEIVE_SMS`
- `android.permission.READ_CONTACTS`
- `android.permission.CALL_PHONE`
- `android.permission.RECORD_AUDIO`
- `android.permission.CAMERA`
- `android.permission.READ_CALL_LOG`
- `android.permission.PROCESS_OUTGOING_CALLS`

---

### 8. APKiD (APK Identification)

**Purpose:** Identify Android APK compilers, packers, and obfuscators.

**Response Structure:**
```json
{
  "name": "APKiD",
  "status": "SUCCESS",
  "report": {
    "files": [],  // Empty if no packer detected
    "rules_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "apkid_version": "2.1.4"
  }
}
```

**Key Fields for Conditions:**
| Field Path | Type | Description | Suspicious When |
|------------|------|-------------|----------------|
| `report.files` | Array | Detected packers/obfuscators | Length > 0 |

---

### 9. Rtf_Info (RTF Analysis)

**Purpose:** Analyze Rich Text Format documents for embedded objects and exploits.

**Response Structure:**
```json
{
  "name": "Rtf_Info",
  "status": "SUCCESS",
  "report": {
    "rtfobj": {
      "ole_objects": []  // Embedded OLE objects
    },
    "follina": []  // CVE-2022-30190 exploit indicators
  }
}
```

**Key Fields for Conditions:**
| Field Path | Type | Description | Malicious When |
|------------|------|-------------|----------------|
| `report.rtfobj.ole_objects` | Array | Embedded objects | Length > 0 |
| `report.follina` | Array | Follina exploit | Length > 0 |

---

### 10. BoxJS (JavaScript Analysis)

**Purpose:** Deobfuscate and analyze JavaScript files.

**Response Structure:**
```json
{
  "name": "BoxJS",
  "status": "SUCCESS",
  "report": {
    "uris": [],
    "IOC.json": [
      {"type": "Sample Name", "value": {...}}
    ],
    "analysis.log": [],
    "snippets.json": {"uuid.js": {"as": "eval'd JS"}}
  }
}
```

**Key Fields for Conditions:**
| Field Path | Type | Description | Malicious When |
|------------|------|-------------|----------------|
| `report.IOC.json` | Array | Indicators of compromise | Contains non-metadata IOCs |
| `report.snippets.json` | Object | Deobfuscated code | Contains suspicious code |

**Note:** `IOC.json` often contains just sample metadata ("Sample Name" type). Filter for actual threat indicators.

---

## Condition Type Reference

### Verdict-Based Conditions

| Condition Type | Description | Evaluation Logic |
|----------------|-------------|------------------|
| `verdict_malicious` | File is definitively malware | Analyzer-specific malware indicators present |
| `verdict_suspicious` | File has concerning characteristics | Moderate risk indicators present |
| `verdict_clean` | File verified as safe | No malware indicators, analyzer succeeded |

### Detection-Based Conditions

| Condition Type | Description | Evaluation Logic |
|----------------|-------------|------------------|
| `has_detections` | Any detections present | Analyzer's detection fields not empty |
| `yara_rule_match` | YARA rules matched | `data_model.signatures` or rule set arrays have matches |
| `capability_detected` | Specific capability found | Check `report.capabilities` array |

### Field-Based Conditions

| Condition Type | Description | Example |
|----------------|-------------|---------|
| `field_equals` | Field exactly equals value | `report.threat_level` == "High Risk" |
| `field_contains` | Field contains substring/item | "powershell" in `report.data` |
| `field_greater_than` | Numeric comparison | `report.total_score` > 50 |
| `field_less_than` | Numeric comparison | `report.total_score` < 10 |

### Status-Based Conditions

| Condition Type | Description | Evaluation Logic |
|----------------|-------------|------------------|
| `analyzer_success` | Analyzer completed successfully | `status` == "SUCCESS" |
| `analyzer_failed` | Analyzer failed | `status` != "SUCCESS" |

---

## Common Patterns

### Checking for Malware (Multi-Analyzer)

```python
# ClamAV detections
condition = {"type": "verdict_malicious", "source_analyzer": "ClamAV"}
# Evaluates: len(report.detections) > 0

# Yara rule matches
condition = {"type": "yara_rule_match", "source_analyzer": "Yara"}
# Evaluates: data_model.signatures has items OR rule sets have security-relevant matches

# Doc_Info suspicious macros
condition = {"type": "field_equals", "source_analyzer": "Doc_Info", 
             "field_path": "report.mraptor", "expected_value": "suspicious"}
```

### Checking for Clean Files

```python
# ClamAV clean
condition = {"type": "verdict_clean", "source_analyzer": "ClamAV"}
# Evaluates: len(report.detections) == 0 AND "FOUND" not in raw_report

# Quark_Engine low risk
condition = {"type": "field_equals", "source_analyzer": "Quark_Engine",
             "field_path": "report.threat_level", "expected_value": "Low Risk"}
```

### Routing by File Type

```python
# Route PE files to PE analyzers
condition = {"type": "field_equals", "source_analyzer": "File_Info",
             "field_path": "report.filetype", "expected_value": "PE"}

# Route PDFs to PDF analyzer
condition = {"type": "field_contains", "source_analyzer": "File_Info",
             "field_path": "report.mimetype", "expected_value": "pdf"}
```

---

## Troubleshooting

### Common Issues

1. **Condition always returns False**
   - Check if the field path is correct (use this reference)
   - Verify the analyzer completed successfully (`status` == "SUCCESS")
   - For Yara, remember utility rules are filtered out

2. **File_Info never shows malware**
   - Expected behavior - File_Info is metadata-only
   - Use ClamAV, Yara, or other detection analyzers

3. **Yara matches on clean files**
   - Some rule sets (like `domain.yar`, `url.yar`) match patterns, not malware
   - The system filters utility rules for `verdict_malicious`

4. **APK analyzers fail**
   - Ensure the file is a valid APK
   - Some analyzers (Androguard) require specific APK structure

### Debug Logging

Enable debug logging to see condition evaluation:
```python
import logging
logging.getLogger("app.services.intelowl_service").setLevel(logging.DEBUG)
```

This will show:
- Which field paths are being checked
- Actual values found in the report
- Which evaluation strategy was used (primary, schema, generic, safe_default)
