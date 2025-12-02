#!/usr/bin/env python3
"""
Test script to verify the conditional workflow routing fix
"""

import requests
import json
import time

API_BASE = "http://localhost:8030"

def test_conditional_routing_fix():
    """Test that conditional workflow routing is now correct"""
    print("🧪 Testing Conditional Workflow Routing Fix...")

    # Load the conditional workflow
    with open("/home/anonymous/COLLEGE/ThreatFlow/test_workflow.json", "r") as f:
        workflow = json.load(f)

    # Load test file
    test_file_path = "/home/anonymous/COLLEGE/ThreatFlow/test_file.txt"

    # Execute workflow
    with open(test_file_path, "rb") as f:
        files = {"file": ("test_file.txt", f, "text/plain")}
        data = {"workflow_json": json.dumps(workflow)}

        response = requests.post(f"{API_BASE}/api/execute", files=files, data=data)

        if response.status_code == 200:
            result = response.json()
            job_ids = result.get("job_ids", [])
            stagerouting = result.get("stagerouting")

            print(f"📊 Backend stagerouting: {stagerouting}")

            # Extract all result nodes from workflow
            all_result_nodes = [node['id'] for node in workflow['nodes'] if node['type'] == 'result']
            print(f"🎯 All Result nodes in workflow: {all_result_nodes}")

            # Analyze the routing
            if stagerouting and len(stagerouting) > 0:
                print("\n📋 Routing Analysis:")
                for routing in stagerouting:
                    stage_id = routing['stage_id']
                    executed = routing['executed']
                    target_nodes = routing.get('target_nodes', [])
                    analyzers = routing.get('analyzers', [])
                    
                    status = "✅ EXECUTED" if executed else "⏭️ SKIPPED"
                    print(f"  Stage {stage_id}: {status}")
                    print(f"    Target nodes: {target_nodes}")
                    print(f"    Analyzers: {analyzers}")

                # Check Stage 0 (pre-conditional) targets all result nodes
                stage_0 = next((r for r in stagerouting if r['stage_id'] == 0), None)
                if stage_0:
                    stage_0_targets = set(stage_0.get('target_nodes', []))
                    all_result_set = set(all_result_nodes)
                    
                    if stage_0_targets == all_result_set:
                        print("✅ Stage 0 correctly targets ALL result nodes")
                    else:
                        print(f"❌ Stage 0 targets {stage_0_targets}, should target {all_result_set}")
                
                # Check executed stages
                executed_stages = [r for r in stagerouting if r['executed']]
                print(f"\n🎯 Executed stages: {len(executed_stages)}")
                
                # Simulate frontend Strategy 1
                executed_leaves = set()
                for routing in stagerouting:
                    if routing.get("executed"):
                        target_nodes = routing.get("target_nodes", [])
                        executed_leaves.update(target_nodes)

                executed_leaves = list(executed_leaves)
                print(f"✅ Strategy 1 - Executed leaves: {executed_leaves}")
                
                # Check that all result nodes are accounted for
                non_executed_leaves = set(all_result_nodes) - set(executed_leaves)
                if non_executed_leaves:
                    print(f"ℹ️ Non-executed leaves: {list(non_executed_leaves)} (expected in conditional workflows)")
                else:
                    print("ℹ️ All result nodes have execution paths")

                print("\n🎉 Conditional routing analysis complete!")
        else:
            print(f"❌ Execution failed: {response.status_code} - {response.text}")

if __name__ == "__main__":
    print("🚀 Testing Conditional Workflow Routing Fix")
    print("=" * 60)

    test_conditional_routing_fix()

    print("\n✨ Testing complete!")