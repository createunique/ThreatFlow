#!/usr/bin/env python3
"""
Test script to check actual analyzer names in IntelOwl results
"""

import requests
import json
import time

API_BASE = "http://localhost:8030"

def test_analyzer_names():
    """Test to see what analyzer names are actually returned"""
    print("🧪 Testing Analyzer Names in Results...")

    # Load test workflow
    with open("/home/anonymous/COLLEGE/ThreatFlow/linear_test_workflow.json", "r") as f:
        workflow = json.load(f)

    # Load test file
    test_file_path = "/home/anonymous/COLLEGE/ThreatFlow/test_file.txt"

    # Execute workflow
    with open(test_file_path, "rb") as f:
        files = {"file": ("test_file.txt", f, "text/plain")}
        data = {"workflow_json": json.dumps(workflow)}

        response = requests.post(f"{API_BASE}/api/execute", files=files, data=data)
        print(f"Execute response: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            job_id = result.get("job_id")

            print(f"📋 Job ID: {job_id}")

            # Poll for completion
            for i in range(30):
                status_response = requests.get(f"{API_BASE}/api/status/{job_id}")
                if status_response.status_code == 200:
                    status_data = status_response.json()

                    if status_data.get("status") in ["reported_without_fails", "reported_with_fails"]:
                        print("✅ Job completed!")

                        results = status_data.get("results")
                        if results:
                            print("🔍 Analyzing results structure...")
                            print(f"📊 Full results: {json.dumps(results, indent=2)}")

                            # Check all keys in results
                            for key, value in results.items():
                                if isinstance(value, dict) and "analyzer_reports" in value:
                                    print(f"📊 Stage '{key}' has analyzer_reports:")
                                    for report in value["analyzer_reports"]:
                                        print(f"  - Name: '{report.get('name')}', Status: {report.get('status')}")
                                elif key == "analyzer_reports":
                                    print(f"📊 Root level analyzer_reports:")
                                    for report in value:
                                        print(f"  - Name: '{report.get('name')}', Status: {report.get('status')}")
                        else:
                            print("❌ No results in completed job")

                        break
                else:
                    print(f"❌ Status check failed: {status_response.status_code}")

                time.sleep(1)
        else:
            print(f"❌ Execution failed: {response.status_code} - {response.text}")

if __name__ == "__main__":
    print("🚀 Testing Analyzer Names")
    print("=" * 50)

    test_analyzer_names()

    print("\n✨ Testing complete!")