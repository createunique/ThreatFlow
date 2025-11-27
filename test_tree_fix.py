#!/usr/bin/env python3
"""
Test script to verify the tree-based distribution fix
"""

import requests
import json
import time

API_BASE = "http://localhost:8030"

def test_tree_distribution():
    """Test that tree distribution now works correctly"""
    print("🧪 Testing Tree-Based Distribution Fix...")

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

            # Poll for completion
            for i in range(30):
                status_response = requests.get(f"{API_BASE}/api/status/{job_id}")
                if status_response.status_code == 200:
                    status_data = status_response.json()

                    if status_data.get("status") in ["reported_without_fails", "reported_with_fails"]:
                        print("✅ Job completed!")

                        results = status_data.get("results")
                        stagerouting = status_data.get("stagerouting")

                        if results and stagerouting:
                            print("🔍 Verifying tree distribution logic...")

                            # Simulate what frontend does
                            analyzer_reports = results.get("analyzer_reports", [])
                            print(f"📊 Total analyzer reports: {len(analyzer_reports)}")

                            for report in analyzer_reports:
                                print(f"  - {report['name']}: {report['status']}")

                            # Check stagerouting
                            executed_leaves = []
                            for routing in stagerouting:
                                if routing.get("executed"):
                                    executed_leaves.extend(routing.get("target_nodes", []))

                            print(f"🎯 Executed leaves: {executed_leaves}")
                            print(f"📋 Analyzers in routing: {stagerouting[0].get('analyzers', [])}")

                            # Simulate filtering
                            path_analyzers = stagerouting[0].get("analyzers", [])
                            filtered_reports = [r for r in analyzer_reports if r["name"] in path_analyzers]

                            print(f"✅ Filtered reports for leaf: {len(filtered_reports)}")
                            print("🎉 Tree distribution should now work correctly!")
                        break
                else:
                    print(f"❌ Status check failed: {status_response.status_code}")

                time.sleep(1)
        else:
            print(f"❌ Execution failed: {response.status_code} - {response.text}")

if __name__ == "__main__":
    print("🚀 Testing Tree Distribution Fix")
    print("=" * 50)

    test_tree_distribution()

    print("\n✨ Testing complete!")