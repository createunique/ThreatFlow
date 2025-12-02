#!/usr/bin/env python3
"""
Test script to verify conditional workflow execution fix.
Tests the complete flow: File -> ClamAV -> Conditional -> TRUE: File Info, FALSE: Strings Info
"""

import json
import requests
import time
import sys
import os

# API configuration
API_BASE_URL = "http://localhost:8030"

def test_conditional_workflow():
    """Test conditional workflow execution with clean file (should trigger FALSE branch)"""

    # Test workflow: File -> ClamAV -> Conditional -> TRUE: File Info, FALSE: Strings Info
    workflow = {
        "nodes": [
            {
                "id": "file_1",
                "type": "file",
                "data": {}
            },
            {
                "id": "clamav_1",
                "type": "analyzer",
                "data": {
                    "analyzer": "ClamAV"
                }
            },
            {
                "id": "conditional_1",
                "type": "conditional",
                "data": {
                    "conditionType": "analyzer_success",
                    "sourceAnalyzer": "ClamAV",
                    "field_path": "success",
                    "expected_value": True
                }
            },
            {
                "id": "fileinfo_1",
                "type": "analyzer",
                "data": {
                    "analyzer": "FileInfo"
                }
            },
            {
                "id": "strings_1",
                "type": "analyzer",
                "data": {
                    "analyzer": "Strings_Info"
                }
            },
            {
                "id": "result_true",
                "type": "result",
                "data": {}
            },
            {
                "id": "result_false",
                "type": "result",
                "data": {}
            }
        ],
        "edges": [
            {"id": "edge_1", "source": "file_1", "target": "clamav_1"},
            {"id": "edge_2", "source": "clamav_1", "target": "conditional_1"},
            {"id": "edge_3", "source": "conditional_1", "target": "fileinfo_1", "sourceHandle": "true-output"},
            {"id": "edge_4", "source": "conditional_1", "target": "strings_1", "sourceHandle": "false-output"},
            {"id": "edge_5", "source": "fileinfo_1", "target": "result_true"},
            {"id": "edge_6", "source": "strings_1", "target": "result_false"}
        ]
    }

    print("🚀 Testing conditional workflow execution...")
    print("Workflow: File -> ClamAV -> Conditional -> TRUE: File Info, FALSE: Strings Info")
    print("Test file: EICAR test file (should be detected as malicious by ClamAV)")
    print("=" * 60)

    try:
        # Read the test file
        file_path = "/home/anonymous/COLLEGE/ThreatFlow/test_samples/eicar_standard.txt"
        if not os.path.exists(file_path):
            print(f"❌ Test file not found: {file_path}")
            return False

        with open(file_path, 'rb') as f:
            file_data = f.read()

        # Execute workflow using multipart form data
        with open(file_path, 'rb') as f:
            response = requests.post(
                f"{API_BASE_URL}/api/execute",
                data={
                    'workflow_json': json.dumps(workflow)
                },
                files={
                    'file': ('eicar_standard.txt', f, 'application/octet-stream')
                }
            )

        if response.status_code != 200:
            print(f"❌ Workflow execution failed: {response.status_code}")
            print(response.text)
            return False

        result = response.json()
        print("✅ Workflow execution initiated")
        print(f"Response has conditionals: {result.get('has_conditionals', False)}")

        if result.get('has_conditionals'):
            # Conditional workflow - results should be included immediately
            if 'results' in result:
                print("✅ Results included in response (conditional workflow)")
                all_results = result['results']
                print(f"Results structure: {list(all_results.keys())}")

                # Check stage execution
                stage_routing = result.get('stage_routing', [])
                print(f"Stage routing: {len(stage_routing)} stages")

                for stage in stage_routing:
                    print(f"  Stage {stage['stage']}: executed={stage['executed']}, analyzers={stage['analyzers']}")

                # Check if Strings Info executed (should be TRUE for malicious file)
                strings_executed = any(
                    stage['executed'] and 'Strings_Info' in stage['analyzers']
                    for stage in stage_routing
                )

                if strings_executed:
                    print("✅ Strings Info analyzer executed (FALSE branch)")
                    return True
                else:
                    print("❌ Strings Info analyzer did not execute")
                    return False
            else:
                print("❌ No results in conditional workflow response")
                return False
        else:
            print("ℹ️ Non-conditional workflow - would need to poll for results")
            return True

    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        return False

if __name__ == "__main__":
    success = test_conditional_workflow()
    sys.exit(0 if success else 1)