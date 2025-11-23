#!/usr/bin/env python3
"""
Test script for enhanced conditional node functionality in ThreatFlow.

This script tests the new condition types that support all 18 IntelOwl analyzers:
- verdict_malicious, verdict_suspicious, verdict_clean
- field_equals, field_contains, field_greater_than, field_less_than
- yara_rule_match, capability_detected
- has_detections, has_errors
- analyzer_success, analyzer_failed
"""

import json
import sys
import os

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.services.intelowl_service import IntelOwlService

def create_mock_analyzer_report(analyzer_name: str, report_data: dict, status: str = "SUCCESS") -> dict:
    """Create a mock analyzer report for testing"""
    return {
        "name": analyzer_name,
        "status": status,
        "report": report_data
    }

def test_condition_evaluation():
    """Test various condition types with mock analyzer reports"""

    # Initialize the service (we'll only use the condition evaluation method)
    service = IntelOwlService()

    # Mock results from previous stages
    mock_results = {
        "stage_0": {
            "analyzer_reports": [
                # ClamAV with detections
                create_mock_analyzer_report("ClamAV", {
                    "detections": ["Win.Malware.Generic-123"],
                    "verdict": "malicious"
                }),
                # YARA with matches
                create_mock_analyzer_report("YARA", {
                    "matches": [
                        {"rule": "malware_rule_1", "strings": ["malicious_string"]},
                        {"rule": "suspicious_rule_2", "strings": ["suspicious_pattern"]}
                    ]
                }),
                # PEiD with capabilities
                create_mock_analyzer_report("PEiD", {
                    "capabilities": ["packer", "obfuscation", "anti_debug"]
                }),
                # File Info with metadata
                create_mock_analyzer_report("File_Info", {
                    "pe_info": {
                        "signature": {
                            "valid": True,
                            "signer": "Microsoft Corporation"
                        }
                    },
                    "size": 1024,
                    "mime_type": "application/x-executable"
                }),
                # Strings analyzer with URLs
                create_mock_analyzer_report("Strings_Info", {
                    "urls": ["http://malicious-domain.com", "https://legit-site.com"]
                }),
                # Failed analyzer
                create_mock_analyzer_report("Failed_Analyzer", {}, "FAILED")
            ]
        }
    }

    # Test cases for different condition types
    test_cases = [
        # Basic verdict conditions
        {
            "name": "verdict_malicious - ClamAV",
            "condition": {"type": "verdict_malicious", "source_analyzer": "ClamAV"},
            "expected": True
        },
        {
            "name": "verdict_clean - File_Info",
            "condition": {"type": "verdict_clean", "source_analyzer": "File_Info"},
            "expected": False  # File info doesn't have verdict
        },

        # Field-based conditions
        {
            "name": "field_equals - PE signature valid",
            "condition": {
                "type": "field_equals",
                "source_analyzer": "File_Info",
                "field_path": "pe_info.signature.valid",
                "expected_value": True
            },
            "expected": True
        },
        {
            "name": "field_contains - URLs contain malicious domain",
            "condition": {
                "type": "field_contains",
                "source_analyzer": "Strings_Info",
                "field_path": "urls",
                "expected_value": "malicious-domain.com"
            },
            "expected": True
        },
        {
            "name": "field_greater_than - File size > 1000",
            "condition": {
                "type": "field_greater_than",
                "source_analyzer": "File_Info",
                "field_path": "size",
                "expected_value": 1000
            },
            "expected": True  # 1024 > 1000
        },
        {
            "name": "field_less_than - File size < 2000",
            "condition": {
                "type": "field_less_than",
                "source_analyzer": "File_Info",
                "field_path": "size",
                "expected_value": 2000
            },
            "expected": True
        },

        # Analyzer-specific conditions
        {
            "name": "yara_rule_match - YARA has matches",
            "condition": {"type": "yara_rule_match", "source_analyzer": "YARA"},
            "expected": True
        },
        {
            "name": "capability_detected - PEiD has packer",
            "condition": {
                "type": "capability_detected",
                "source_analyzer": "PEiD",
                "expected_value": "packer"
            },
            "expected": True
        },

        # Status conditions
        {
            "name": "analyzer_success - File_Info",
            "condition": {"type": "analyzer_success", "source_analyzer": "File_Info"},
            "expected": True
        },
        {
            "name": "analyzer_failed - Failed_Analyzer",
            "condition": {"type": "analyzer_failed", "source_analyzer": "Failed_Analyzer"},
            "expected": True
        },

        # Detection conditions
        {
            "name": "has_detections - ClamAV",
            "condition": {"type": "has_detections", "source_analyzer": "ClamAV"},
            "expected": True
        },
        {
            "name": "has_detections - File_Info (no detections)",
            "condition": {"type": "has_detections", "source_analyzer": "File_Info"},
            "expected": False
        },

        # NOT condition
        {
            "name": "NOT verdict_malicious - File_Info",
            "condition": {
                "type": "NOT",
                "inner": {"type": "verdict_malicious", "source_analyzer": "File_Info"}
            },
            "expected": True
        }
    ]

    print("Testing Enhanced Conditional Node Logic")
    print("=" * 50)

    passed = 0
    failed = 0

    for test_case in test_cases:
        try:
            result = service._evaluate_condition(test_case["condition"], mock_results)
            expected = test_case["expected"]

            if result == expected:
                status = "✓ PASS"
                passed += 1
            else:
                status = "✗ FAIL"
                failed += 1

            print(f"{status} {test_case['name']}")
            print(f"    Expected: {expected}, Got: {result}")
            print(f"    Condition: {test_case['condition']}")
            print()

        except Exception as e:
            print(f"✗ ERROR {test_case['name']}: {e}")
            failed += 1
            print()

    print("=" * 50)
    print(f"Results: {passed} passed, {failed} failed")

    if failed == 0:
        print("🎉 All tests passed! Enhanced conditional logic is working correctly.")
        return True
    else:
        print("❌ Some tests failed. Please check the implementation.")
        return False

if __name__ == "__main__":
    success = test_condition_evaluation()
    sys.exit(0 if success else 1)