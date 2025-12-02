#!/usr/bin/env python3
"""
Test script to verify frontend receives correct stagerouting data
"""

import requests
import json
import time

API_BASE = "http://localhost:8030"

def test_status_polling():
    """Test that status polling returns stagerouting"""
    print("🧪 Testing Status Polling with StageRouting...")

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
            print(f"📋 Initial stagerouting: {result.get('stagerouting')}")

            # Poll for status multiple times
            for i in range(10):
                status_response = requests.get(f"{API_BASE}/api/status/{job_id}")
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    stagerouting = status_data.get("stagerouting")

                    print(f"🔄 Poll {i+1} - Status: {status_data.get('status')}")
                    if stagerouting:
                        print(f"✅ Stage routing in poll {i+1}: {len(stagerouting)} stages")
                        for stage in stagerouting:
                            print(f"  - Stage {stage['stage_id']}: executed={stage['executed']}, analyzers={stage['analyzers']}")
                    else:
                        print(f"❌ No stagerouting in poll {i+1}")

                    if status_data.get("status") in ["reported_without_fails", "reported_with_fails"]:
                        print("✅ Job completed!")
                        break
                else:
                    print(f"❌ Status check failed: {status_response.status_code}")

                time.sleep(1)
        else:
            print(f"❌ Execution failed: {response.status_code} - {response.text}")

if __name__ == "__main__":
    print("🚀 Testing Frontend Data Reception")
    print("=" * 50)

    test_status_polling()

    print("\n✨ Testing complete!")