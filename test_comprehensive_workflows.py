#!/usr/bin/env python3
"""
Comprehensive Workflow Testing Script
Tests all possible workflow patterns to identify result distribution issues
"""

import requests
import time
import json
import os
from pathlib import Path

# Configuration
MIDDLEWARE_URL = "http://localhost:8030"
TEST_FILE_PATH = "/home/anonymous/COLLEGE/ThreatFlow/test_samples/eicar_variant.txt"

def test_workflow_pattern(name, nodes, edges, expected_has_conditionals=False):
    """Test a specific workflow pattern"""
    print(f"\n{'='*60}")
    print(f"TESTING: {name}")
    print(f"{'='*60}")

    # Check if test file exists
    if not os.path.exists(TEST_FILE_PATH):
        print(f"❌ Test file not found: {TEST_FILE_PATH}")
        return False

    try:
        # Read file content first
        with open(TEST_FILE_PATH, 'rb') as f:
            file_content = f.read()

        # Prepare the request
        files = {'file': ('eicar_variant.txt', file_content, 'text/plain')}

        # Create workflow JSON
        workflow_json = json.dumps({'nodes': nodes, 'edges': edges})

        data = {
            'workflow_json': workflow_json
        }

        print(f"📋 Workflow structure:")
        print(f"  - Nodes: {len(nodes)} ({[n['type'] for n in nodes]})")
        print(f"  - Edges: {len(edges)}")
        print(f"  - Expected has_conditionals: {expected_has_conditionals}")

        # Submit workflow
        print("🚀 Submitting workflow...")
        response = requests.post(
            f"{MIDDLEWARE_URL}/api/execute",
            files=files,
            data=data,
            timeout=30
        )

        if response.status_code != 200:
            print(f"❌ Submission failed: {response.status_code} - {response.text}")
            return False

        result = response.json()
        print("✅ Workflow submitted successfully")
        print(f"  - Response: {result}")

        # Check has_conditionals flag
        actual_has_conditionals = result.get('has_conditionals', False)
        print(f"  - Actual has_conditionals: {actual_has_conditionals}")

        if actual_has_conditionals != expected_has_conditionals:
            print(f"❌ MISMATCH: Expected {expected_has_conditionals}, got {actual_has_conditionals}")
            return False

        # Get job ID
        job_id = result.get('job_id') or (result.get('job_ids') and result['job_ids'][0])
        if not job_id:
            print("❌ No job ID in response")
            return False

        print(f"  - Job ID: {job_id}")

        # Poll for completion
        print("⏳ Polling for completion...")
        max_attempts = 60
        for attempt in range(max_attempts):
            try:
                status_response = requests.get(f"{MIDDLEWARE_URL}/api/execute/status/{job_id}", timeout=10)
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    status = status_data.get('status')

                    if status == 'reported_without_fails':
                        print("✅ Workflow completed successfully")
                        print(f"  - Final status: {status_data}")

                        # Check final has_conditionals
                        final_has_conditionals = status_data.get('has_conditionals', False)
                        print(f"  - Final has_conditionals: {final_has_conditionals}")

                        if final_has_conditionals != expected_has_conditionals:
                            print(f"❌ FINAL MISMATCH: Expected {expected_has_conditionals}, got {final_has_conditionals}")
                            return False

                        return True
                    elif status in ['failed', 'killed']:
                        print(f"❌ Workflow failed with status: {status}")
                        return False

                time.sleep(2)

            except Exception as e:
                print(f"❌ Polling error: {e}")
                time.sleep(2)

        print("❌ Workflow timed out")
        return False

    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return False

def main():
    """Run comprehensive workflow tests"""
    print("🔬 COMPREHENSIVE WORKFLOW TESTING")
    print("Testing all possible workflow patterns to identify result distribution issues")

    # Test Pattern 1: Simple linear (File -> Analyzer -> Result)
    pattern1_nodes = [
        {'id': 'file-1', 'type': 'file', 'data': {}},
        {'id': 'analyzer-1', 'type': 'analyzer', 'data': {'analyzer': 'ClamAV'}},
        {'id': 'result-1', 'type': 'result', 'data': {}}
    ]
    pattern1_edges = [
        {'id': 'e1', 'source': 'file-1', 'target': 'analyzer-1'},
        {'id': 'e2', 'source': 'analyzer-1', 'target': 'result-1'}
    ]

    # Test Pattern 2: File -> Analyzer -> Conditional -> Result (TRUE) + Result (FALSE)
    pattern2_nodes = [
        {'id': 'file-1', 'type': 'file', 'data': {}},
        {'id': 'analyzer-1', 'type': 'analyzer', 'data': {'analyzer': 'ClamAV'}},
        {'id': 'conditional-1', 'type': 'conditional', 'data': {'conditionType': 'verdict_malicious', 'sourceAnalyzer': 'ClamAV'}},
        {'id': 'result-true', 'type': 'result', 'data': {}},
        {'id': 'result-false', 'type': 'result', 'data': {}}
    ]
    pattern2_edges = [
        {'id': 'e1', 'source': 'file-1', 'target': 'analyzer-1'},
        {'id': 'e2', 'source': 'analyzer-1', 'target': 'conditional-1'},
        {'id': 'e3', 'source': 'conditional-1', 'target': 'result-true', 'sourceHandle': 'true-output'},
        {'id': 'e4', 'source': 'conditional-1', 'target': 'result-false', 'sourceHandle': 'false-output'}
    ]

    # Test Pattern 3: File -> Analyzer -> Conditional -> Analyzer -> Result (TRUE) + Result (FALSE)
    pattern3_nodes = [
        {'id': 'file-1', 'type': 'file', 'data': {}},
        {'id': 'analyzer-1', 'type': 'analyzer', 'data': {'analyzer': 'ClamAV'}},
        {'id': 'conditional-1', 'type': 'conditional', 'data': {'conditionType': 'verdict_malicious', 'sourceAnalyzer': 'ClamAV'}},
        {'id': 'analyzer-2', 'type': 'analyzer', 'data': {'analyzer': 'YARA'}},
        {'id': 'result-true', 'type': 'result', 'data': {}},
        {'id': 'result-false', 'type': 'result', 'data': {}}
    ]
    pattern3_edges = [
        {'id': 'e1', 'source': 'file-1', 'target': 'analyzer-1'},
        {'id': 'e2', 'source': 'analyzer-1', 'target': 'conditional-1'},
        {'id': 'e3', 'source': 'conditional-1', 'target': 'analyzer-2', 'sourceHandle': 'true-output'},
        {'id': 'e4', 'source': 'analyzer-2', 'target': 'result-true'},
        {'id': 'e5', 'source': 'conditional-1', 'target': 'result-false', 'sourceHandle': 'false-output'}
    ]

    # Test Pattern 4: Multiple analyzers -> Result (no conditional)
    pattern4_nodes = [
        {'id': 'file-1', 'type': 'file', 'data': {}},
        {'id': 'analyzer-1', 'type': 'analyzer', 'data': {'analyzer': 'ClamAV'}},
        {'id': 'analyzer-2', 'type': 'analyzer', 'data': {'analyzer': 'YARA'}},
        {'id': 'result-1', 'type': 'result', 'data': {}}
    ]
    pattern4_edges = [
        {'id': 'e1', 'source': 'file-1', 'target': 'analyzer-1'},
        {'id': 'e2', 'source': 'file-1', 'target': 'analyzer-2'},
        {'id': 'e3', 'source': 'analyzer-1', 'target': 'result-1'},
        {'id': 'e4', 'source': 'analyzer-2', 'target': 'result-1'}
    ]

    # Test Pattern 5: Parallel branches with conditional
    pattern5_nodes = [
        {'id': 'file-1', 'type': 'file', 'data': {}},
        {'id': 'analyzer-1', 'type': 'analyzer', 'data': {'analyzer': 'ClamAV'}},
        {'id': 'conditional-1', 'type': 'conditional', 'data': {'conditionType': 'verdict_malicious', 'sourceAnalyzer': 'ClamAV'}},
        {'id': 'analyzer-2', 'type': 'analyzer', 'data': {'analyzer': 'YARA'}},
        {'id': 'analyzer-3', 'type': 'analyzer', 'data': {'analyzer': 'Strings'}},
        {'id': 'result-1', 'type': 'result', 'data': {}},
        {'id': 'result-2', 'type': 'result', 'data': {}}
    ]
    pattern5_edges = [
        {'id': 'e1', 'source': 'file-1', 'target': 'analyzer-1'},
        {'id': 'e2', 'source': 'analyzer-1', 'target': 'conditional-1'},
        {'id': 'e3', 'source': 'conditional-1', 'target': 'analyzer-2', 'sourceHandle': 'true-output'},
        {'id': 'e4', 'source': 'conditional-1', 'target': 'analyzer-3', 'sourceHandle': 'false-output'},
        {'id': 'e5', 'source': 'analyzer-2', 'target': 'result-1'},
        {'id': 'e6', 'source': 'analyzer-3', 'target': 'result-2'}
    ]

    # Run all tests
    test_results = []

    test_results.append(("Pattern 1: File -> Analyzer -> Result", test_workflow_pattern(
        "Pattern 1: File -> Analyzer -> Result",
        pattern1_nodes, pattern1_edges, expected_has_conditionals=False
    )))

    test_results.append(("Pattern 2: File -> Analyzer -> Conditional -> Result + Result", test_workflow_pattern(
        "Pattern 2: File -> Analyzer -> Conditional -> Result + Result",
        pattern2_nodes, pattern2_edges, expected_has_conditionals=True
    )))

    test_results.append(("Pattern 3: File -> Analyzer -> Conditional -> Analyzer -> Result + Result", test_workflow_pattern(
        "Pattern 3: File -> Analyzer -> Conditional -> Analyzer -> Result + Result",
        pattern3_nodes, pattern3_edges, expected_has_conditionals=True
    )))

    test_results.append(("Pattern 4: Multiple Analyzers -> Result", test_workflow_pattern(
        "Pattern 4: Multiple Analyzers -> Result",
        pattern4_nodes, pattern4_edges, expected_has_conditionals=False
    )))

    test_results.append(("Pattern 5: Parallel branches with conditional", test_workflow_pattern(
        "Pattern 5: Parallel branches with conditional",
        pattern5_nodes, pattern5_edges, expected_has_conditionals=True
    )))

    # Summary
    print(f"\n{'='*60}")
    print("TEST SUMMARY")
    print(f"{'='*60}")

    passed = 0
    total = len(test_results)

    for name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {name}")
        if result:
            passed += 1

    print(f"\nResults: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed!")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")

if __name__ == "__main__":
    main()