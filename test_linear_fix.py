#!/usr/bin/env python3
"""
Test script to verify linear workflow stage_routing fix
"""

import requests
import json
import time
import sys
import os

MIDDLEWARE_URL = "http://localhost:8030"

def test_linear_workflow():
    """Test that linear workflows return stage_routing"""

    # Load test workflow
    with open("linear_test_workflow.json", "r") as f:
        workflow = json.load(f)

    # Load test file
    test_file_path = "threatflow-middleware/test_file.txt"
    if not os.path.exists(test_file_path):
        print(f"❌ Test file not found: {test_file_path}")
        return False

    # Prepare request
    files = {'file': open(test_file_path, 'rb')}
    workflow_json = json.dumps(workflow)
    data = {'workflow_json': workflow_json}

    print("📤 Submitting linear workflow...")
    print(f"   Nodes: {len(workflow['nodes'])}")
    print(f"   Edges: {len(workflow['edges'])}")
    print(f"   Analyzers: ClamAV, File_Info")

    # Submit workflow
    response = requests.post(
        f"{MIDDLEWARE_URL}/api/execute",
        files=files,
        data=data,
        timeout=30
    )

    if response.status_code != 200:
        print(f"❌ Submission failed: {response.status_code}")
        print(response.text)
        return False

    result = response.json()
    print("✅ Workflow submitted successfully")
    print(f"   Job ID: {result.get('job_id')}")
    print(f"   Has conditionals: {result.get('has_conditionals')}")
    print(f"   Stage routing present: {'stage_routing' in result}")

    if 'stage_routing' in result:
        stage_routing = result['stage_routing']
        print(f"   Stage routing: {stage_routing}")

        # Check if stage 0 has target_nodes
        if stage_routing and len(stage_routing) > 0:
            stage_0 = stage_routing[0]
            target_nodes = stage_0.get('target_nodes', [])
            analyzers = stage_0.get('analyzers', [])
            executed = stage_0.get('executed', False)

            print(f"   Stage 0 analyzers: {analyzers}")
            print(f"   Stage 0 target_nodes: {target_nodes}")
            print(f"   Stage 0 executed: {executed}")

            if len(analyzers) == 2 and len(target_nodes) >= 1 and executed:
                print("✅ Stage routing looks correct!")
                return True
            else:
                print("❌ Stage routing incomplete")
                return False
    else:
        print("❌ No stage_routing in response")
        return False

if __name__ == "__main__":
    print("🧪 Testing linear workflow stage_routing fix...")
    success = test_linear_workflow()
    sys.exit(0 if success else 1)