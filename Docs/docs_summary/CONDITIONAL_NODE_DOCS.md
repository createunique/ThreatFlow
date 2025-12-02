# Enhanced Conditional Node Documentation

## Overview
The ThreatFlow conditional node has been significantly enhanced to support all 18 IntelOwl analyzers with comprehensive condition types. Previously limited to basic `verdict_malicious` checks, it now supports 11 different condition types for flexible workflow branching.

## Supported Condition Types

### Verdict-Based Conditions
- **`verdict_malicious`**: Checks if analyzer detected malware/viruses
- **`verdict_suspicious`**: Checks for suspicious activity indicators
- **`verdict_clean`**: Checks if file is deemed safe/clean

### Field-Based Conditions
- **`field_equals`**: Exact match of a field value (e.g., `pe_info.signature.valid == true`)
- **`field_contains`**: Check if field contains a substring or list item contains value
- **`field_greater_than`**: Numeric comparison (field > value)
- **`field_less_than`**: Numeric comparison (field < value)

### Analyzer-Specific Conditions
- **`yara_rule_match`**: Checks if YARA analyzer found rule matches
- **`capability_detected`**: Checks if analyzer detected specific capabilities (e.g., "packer", "obfuscation")
- **`has_detections`**: Generic check for any detections/signatures/rules
- **`has_errors`**: Checks if analyzer encountered errors

### Status Conditions
- **`analyzer_success`**: Checks if analyzer completed successfully
- **`analyzer_failed`**: Checks if analyzer failed to complete

## Usage Examples

### Basic Malware Detection
```
Condition: verdict_malicious from ClamAV
If TRUE: Run advanced analysis (VirusTotal, Sandbox)
If FALSE: Run file type analysis only
```

### PE File Signature Validation
```
Condition: field_equals from File_Info
Field Path: pe_info.signature.valid
Expected Value: true
If TRUE: Trust the file signature
If FALSE: Flag for manual review
```

### YARA Rule Matching
```
Condition: yara_rule_match from YARA
If TRUE: High-priority threat response
If FALSE: Continue with standard analysis
```

### Capability Detection
```
Condition: capability_detected from PEiD
Expected Value: packer
If TRUE: Run unpacker analyzers
If FALSE: Skip unpacking steps
```

### File Size Thresholds
```
Condition: field_greater_than from File_Info
Field Path: size
Expected Value: 1000000
If TRUE: Run large file analyzers
If FALSE: Use standard analysis
```

## Field Path Navigation

Field paths use dot notation to navigate JSON structures:
- `verdict` - Top-level verdict field
- `pe_info.signature.valid` - Nested PE signature validation
- `detections[0].name` - First detection name (array indexing supported)
- `capabilities` - List of detected capabilities

## Frontend Configuration

The PropertiesPanel now provides:
- **Condition Type Dropdown**: Select from all 11 condition types
- **Source Analyzer Dropdown**: Choose which analyzer to evaluate
- **Field Path Input**: Specify JSON path for field-based conditions
- **Expected Value Input**: Set comparison value
- **Visual Indicators**: Icons and labels show condition type at a glance

## Backend Implementation

The enhanced `_evaluate_condition` method in `intelowl_service.py`:
- Supports all 11 condition types
- Handles complex JSON path navigation
- Provides detailed logging for debugging
- Supports array indexing and nested object traversal
- Includes analyzer-specific logic optimizations

## Testing

Comprehensive test suite (`test_conditionals.py`) validates:
- All condition types work correctly
- Field path navigation functions properly
- Analyzer-specific patterns are detected
- Edge cases are handled gracefully

## Compatibility

✅ **All 18 IntelOwl Analyzers Supported**
- File analysis tools (File_Info, Strings_Info, Doc_Info, etc.)
- Malware scanners (ClamAV, VirusTotal, etc.)
- PE analyzers (PEiD, PEframe, etc.)
- Signature-based detectors (YARA, Suricata, etc.)
- Behavioral analyzers (Cuckoo, Sandbox, etc.)

The conditional node now provides the flexibility needed for complex threat analysis workflows with intelligent branching based on any analyzer output.