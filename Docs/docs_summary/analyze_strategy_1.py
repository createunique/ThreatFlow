#!/usr/bin/env python3
"""
Test script to analyze Strategy 1 logic in detail
"""

import requests
import json
import time

API_BASE = "http://localhost:8030"

def test_strategy_1_logic():
    """Test Strategy 1: Backend tells which leaves executed"""
    print("🧪 Testing Strategy 1 Logic in Detail...")

    # Test 1: Linear Workflow
    print("\n📋 Test 1: Linear Workflow")
    print("-" * 40)

    with open("/home/anonymous/COLLEGE/ThreatFlow/linear_test_workflow.json", "r") as f:
        workflow = json.load(f)

    test_file_path = "/home/anonymous/COLLEGE/ThreatFlow/test_file.txt"

    with open(test_file_path, "rb") as f:
        files = {"file": ("test_file.txt", f, "text/plain")}
        data = {"workflow_json": json.dumps(workflow)}

        response = requests.post(f"{API_BASE}/api/execute", files=files, data=data)

        if response.status_code == 200:
            result = response.json()
            job_id = result.get("job_id")
            stagerouting = result.get("stagerouting")

            print(f"📊 Backend stagerouting: {stagerouting}")

            # Extract all result nodes from workflow
            all_result_nodes = [node['id'] for node in workflow['nodes'] if node['type'] == 'result']
            print(f"🎯 All Result nodes in workflow: {all_result_nodes}")

            # Simulate Strategy 1 logic
            if stagerouting and len(stagerouting) > 0:
                executed_leaves = set()
                for routing in stagerouting:
                    if routing.get("executed"):
                        target_nodes = routing.get("target_nodes", [])
                        executed_leaves.update(target_nodes)

                executed_leaves = list(executed_leaves)
                print(f"✅ Strategy 1 - Executed leaves: {executed_leaves}")

                # Check if all result nodes are executed (should be for linear)
                missing_leaves = set(all_result_nodes) - set(executed_leaves)
                if missing_leaves:
                    print(f"❌ MISSING leaves: {list(missing_leaves)}")
                else:
                    print("✅ All Result nodes correctly identified as executed")
            else:
                print("❌ No stagerouting received")

    # Test 2: Conditional Workflow
    print("\n📋 Test 2: Conditional Workflow")
    print("-" * 40)

    with open("/home/anonymous/COLLEGE/ThreatFlow/test_workflow.json", "r") as f:
        workflow = json.load(f)

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

            # Simulate Strategy 1 logic
            if stagerouting and len(stagerouting) > 0:
                executed_leaves = set()
                for routing in stagerouting:
                    if routing.get("executed"):
                        target_nodes = routing.get("target_nodes", [])
                        executed_leaves.update(target_nodes)

                executed_leaves = list(executed_leaves)
                print(f"✅ Strategy 1 - Executed leaves: {executed_leaves}")

                # For conditional workflows, some leaves might not execute
                non_executed_leaves = set(all_result_nodes) - set(executed_leaves)
                if non_executed_leaves:
                    print(f"ℹ️  Non-executed leaves (expected in conditional): {list(non_executed_leaves)}")
                else:
                    print("ℹ️  All Result nodes executed (possible in this test case)")
            else:
                print("❌ No stagerouting received")

def analyze_current_logic():
    """Analyze the current Strategy 1 logic in detail"""
    print("\n🔍 Analysis of Current Strategy 1 Logic")
    print("=" * 50)

    print("""
🎯 STRATEGY 1: Backend tells which Result leaves executed

CURRENT LOGIC:
```typescript
const getExecutedLeaves = (stageRouting: StageRouting[] | undefined, allLeaves: string[]): string[] => {
  if (!stageRouting?.length) return allLeaves; // Fallback: assume all executed
  
  const executed = new Set<string>();
  stageRouting.forEach(routing => {
    if (routing.executed) {
      (routing.target_nodes || []).forEach(nodeId => executed.add(nodeId));
    }
  });
  return Array.from(executed);
};
```

📋 LOGIC FLOW:
1. If no stagerouting provided → assume ALL leaves executed (fallback)
2. For each routing entry where executed=true → collect target_nodes
3. Return unique list of executed leaf node IDs

✅ STRENGTHS:
- Handles duplicates automatically (Set)
- Clear separation of concerns with Strategy 2
- Works for both linear and conditional workflows
- Fallback for backwards compatibility

🤔 POTENTIAL ISSUES TO ANALYZE:

1. **Missing Result Nodes**: What if a Result node exists in workflow but isn't targeted by any routing?
   - Current: Won't be executed → shows "Branch not executed" error
   - Linear: This shouldn't happen (backend routes to all)
   - Conditional: This is correct behavior

2. **Empty target_nodes**: What if executed stage has no target_nodes?
   - Current: Ignores the stage (no nodes added)
   - This might be correct for "result-only" stages

3. **Multiple stages targeting same node**: What if multiple executed stages target the same Result node?
   - Current: Set handles duplicates correctly
   - This is the expected behavior

4. **Workflow structure validation**: Should frontend validate that all Result nodes are accounted for?
   - Current: No validation, trusts backend routing
   - This is correct - backend knows execution details

🎯 CONCLUSION:
The current Strategy 1 logic appears CORRECT and ROBUST for its intended purpose.
It correctly identifies which Result nodes should display results based on backend execution decisions.
""")

if __name__ == "__main__":
    test_strategy_1_logic()
    analyze_current_logic()

    print("\n✨ Analysis complete!")