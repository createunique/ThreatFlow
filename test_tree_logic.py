#!/usr/bin/env python3
"""
Test script to verify tree-based result distribution is working
Tests both linear and conditional workflows
"""

import requests
import json
import time
import os

API_BASE = "http://localhost:8030"

def test_linear_workflow():
    """Test linear workflow execution"""
    print("🧪 Testing Linear Workflow...")

    # Load test workflow
    with open("/home/anonymous/COLLEGE/ThreatFlow/linear_test_workflow.json", "r") as f:
        workflow = json.load(f)

    # Load test file
    test_file_path = "/home/anonymous/COLLEGE/ThreatFlow/test_file.txt"

    # Prepare form data
    with open(test_file_path, "rb") as f:
        files = {"file": ("test_file.txt", f, "text/plain")}
        data = {"workflow_json": json.dumps(workflow)}

        # Execute workflow
        response = requests.post(f"{API_BASE}/api/execute", files=files, data=data)
        print(f"Execute response: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print(f"✅ Execution successful: {result.get('message', '')}")

            job_id = result.get("job_id")
            if job_id:
                print(f"📋 Job ID: {job_id}")

                # Poll for status
                for i in range(30):  # Poll for up to 30 seconds
                    status_response = requests.get(f"{API_BASE}/api/status/{job_id}")
                    if status_response.status_code == 200:
                        status_data = status_response.json()
                        print(f"🔄 Status: {status_data.get('status')}")

                        # Check for stagerouting
                        stagerouting = status_data.get("stagerouting")
                        if stagerouting:
                            print(f"✅ Stage routing found: {len(stagerouting)} stages")
                            for stage in stagerouting:
                                print(f"  - Stage {stage['stage_id']}: executed={stage['executed']}, analyzers={stage['analyzers']}")
                        else:
                            print("❌ No stagerouting in status response")

                        if status_data.get("status") in ["reported_without_fails", "reported_with_fails"]:
                            print("✅ Job completed!")
                            results = status_data.get("results")
                            if results:
                                analyzer_reports = results.get("analyzer_reports", [])
                                print(f"📊 Results: {len(analyzer_reports)} analyzer reports")
                                for report in analyzer_reports:
                                    print(f"  - {report.get('name')}: {report.get('status')}")
                            else:
                                print("❌ No results in completed job")
                            break
                    else:
                        print(f"❌ Status check failed: {status_response.status_code}")

                    time.sleep(2)
                else:
                    print("⏰ Job did not complete within timeout")
            else:
                print("❌ No job_id in response")
        else:
            print(f"❌ Execution failed: {response.status_code} - {response.text}")

def test_conditional_workflow():
    """Test conditional workflow execution"""
    print("\n🧪 Testing Conditional Workflow...")

    # Load test workflow
    with open("/home/anonymous/COLLEGE/ThreatFlow/test_workflow.json", "r") as f:
        workflow = json.load(f)

    # Load test file
    test_file_path = "/home/anonymous/COLLEGE/ThreatFlow/test_file.txt"

    # Prepare form data
    with open(test_file_path, "rb") as f:
        files = {"file": ("test_file.txt", f, "text/plain")}
        data = {"workflow_json": json.dumps(workflow)}

        # Execute workflow
        response = requests.post(f"{API_BASE}/api/execute", files=files, data=data)
        print(f"Execute response: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print(f"✅ Execution successful: {result.get('message', '')}")

            job_ids = result.get("job_ids", [])
            if job_ids:
                print(f"📋 Job IDs: {job_ids}")

                # For conditional workflows, check the first job
                job_id = job_ids[0]

                # Poll for status
                for i in range(30):  # Poll for up to 30 seconds
                    status_response = requests.get(f"{API_BASE}/api/status/{job_id}")
                    if status_response.status_code == 200:
                        status_data = status_response.json()
                        print(f"🔄 Status: {status_data.get('status')}")

                        # Check for stagerouting
                        stagerouting = status_data.get("stagerouting")
                        if stagerouting:
                            print(f"✅ Stage routing found: {len(stagerouting)} stages")
                            for stage in stagerouting:
                                print(f"  - Stage {stage['stage_id']}: executed={stage['executed']}, target_nodes={stage['target_nodes']}, analyzers={stage.get('analyzers', [])}")
                        else:
                            print("❌ No stagerouting in status response")

                        if status_data.get("status") in ["reported_without_fails", "reported_with_fails"]:
                            print("✅ Job completed!")
                            results = status_data.get("results")
                            if results:
                                analyzer_reports = results.get("analyzer_reports", [])
                                print(f"📊 Results: {len(analyzer_reports)} analyzer reports")
                                for report in analyzer_reports:
                                    print(f"  - {report.get('name')}: {report.get('status')}")
                            else:
                                print("❌ No results in completed job")
                            break
                    else:
                        print(f"❌ Status check failed: {status_response.status_code}")

                    time.sleep(2)
                else:
                    print("⏰ Job did not complete within timeout")
            else:
                print("❌ No job_ids in response")
        else:
            print(f"❌ Execution failed: {response.status_code} - {response.text}")

if __name__ == "__main__":
    print("🚀 Testing Tree-Based Result Distribution")
    print("=" * 50)

    # Test linear workflow
    test_linear_workflow()

    # Test conditional workflow
    test_conditional_workflow()

    print("\n✨ Testing complete!")