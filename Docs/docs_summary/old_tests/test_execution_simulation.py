#!/usr/bin/env python3
"""
Test script to simulate the full conditional workflow execution
and identify where the FALSE branch analyzers are not running
"""

import json
import asyncio
import sys
import os
sys.path.append('/home/anonymous/COLLEGE/ThreatFlow/threatflow-middleware')

from app.services.workflow_parser import workflow_parser
from app.services.intelowl_service import intel_service
from app.models.workflow import WorkflowNode, WorkflowEdge, NodeType

def create_test_workflow():
    """Create a test workflow with conditional branching"""
    nodes = [
        WorkflowNode(
            id="file-1",
            type=NodeType.FILE,
            position={"x": 100, "y": 100},
            data={
                "filename": "test_file.txt",
                "fileSize": 1024
            }
        ),
        WorkflowNode(
            id="clamav-1",
            type=NodeType.ANALYZER,
            position={"x": 300, "y": 100},
            data={
                "analyzer": "ClamAV"
            }
        ),
        WorkflowNode(
            id="conditional-1",
            type=NodeType.CONDITIONAL,
            position={"x": 500, "y": 100},
            data={
                "conditionType": "verdict_malicious",
                "sourceAnalyzer": "ClamAV"
            }
        ),
        WorkflowNode(
            id="fileinfo-true",
            type=NodeType.ANALYZER,
            position={"x": 700, "y": 50},
            data={
                "analyzer": "File_Info"
            }
        ),
        WorkflowNode(
            id="stringsinfo-false",
            type=NodeType.ANALYZER,
            position={"x": 700, "y": 150},
            data={
                "analyzer": "Strings_Info"
            }
        ),
        WorkflowNode(
            id="results-clamav",
            type=NodeType.RESULT,
            position={"x": 450, "y": 200},
            data={}
        ),
        WorkflowNode(
            id="results-true",
            type=NodeType.RESULT,
            position={"x": 900, "y": 50},
            data={}
        ),
        WorkflowNode(
            id="results-false",
            type=NodeType.RESULT,
            position={"x": 900, "y": 150},
            data={}
        )
    ]

    edges = [
        # File -> ClamAV
        WorkflowEdge(id="e1", source="file-1", target="clamav-1"),
        # ClamAV -> Conditional
        WorkflowEdge(id="e2", source="clamav-1", target="conditional-1"),
        # Conditional TRUE -> File Info
        WorkflowEdge(id="e3", source="conditional-1", target="fileinfo-true", sourceHandle="true-output"),
        # Conditional FALSE -> Strings Info
        WorkflowEdge(id="e4", source="conditional-1", target="stringsinfo-false", sourceHandle="false-output"),
        # ClamAV -> Results (before conditional)
        WorkflowEdge(id="e5", source="clamav-1", target="results-clamav"),
        # File Info -> Results (TRUE branch)
        WorkflowEdge(id="e6", source="fileinfo-true", target="results-true"),
        # Strings Info -> Results (FALSE branch)
        WorkflowEdge(id="e7", source="stringsinfo-false", target="results-false")
    ]

    return nodes, edges

async def simulate_execution():
    """Simulate the full execution flow"""
    print("=== Simulating Full Execution Flow ===")

    nodes, edges = create_test_workflow()
    execution_plan = workflow_parser.parse(nodes, edges)
    stages = execution_plan["stages"]

    print(f"Parsed {len(stages)} stages")

    # Mock results after Stage 0 (ClamAV clean)
    mock_results = {
        "stage_0": {
            "job_id": 123,
            "status": "reported_without_fails",
            "analyzer_reports": [
                {
                    "name": "ClamAV",
                    "status": "SUCCESS",
                    "report": {
                        "detections": [],  # Clean file
                        "raw_report": "Infected files: 0"
                    }
                }
            ]
        }
    }

    executed_stages = []
    skipped_stages = []

    print("\nSimulating stage execution:")
    for stage in stages:
        stage_id = stage["stage_id"]
        depends_on = stage.get("depends_on")
        condition = stage.get("condition")
        analyzers = stage["analyzers"]
        target_nodes = stage.get("target_nodes", [])

        # Check if stage should execute
        if depends_on is None:
            should_execute = True
            reason = "Initial stage"
        else:
            should_execute = intel_service._evaluate_condition(condition, mock_results)
            cond_type = condition.get('type', 'unknown')
            negate = condition.get('negate', False)
            reason = f"Condition '{cond_type}'{' (negated)' if negate else ''} = {should_execute}"

        print(f"Stage {stage_id}: {reason}")
        print(f"  Analyzers: {analyzers}")
        print(f"  Target nodes: {target_nodes}")
        print(f"  Should execute: {should_execute}")

        if should_execute:
            if not analyzers:
                print(f"  -> Result-only stage (no analyzers to run)")
                mock_results[f"stage_{stage_id}"] = {
                    "stage_id": stage_id,
                    "type": "result_only",
                    "target_nodes": target_nodes,
                    "message": "Routing to result nodes based on condition"
                }
            else:
                print(f"  -> Would execute analyzers: {analyzers}")
                # Simulate successful execution
                mock_results[f"stage_{stage_id}"] = {
                    "job_id": 124 + stage_id,
                    "status": "reported_without_fails",
                    "analyzer_reports": [
                        {
                            "name": analyzer,
                            "status": "SUCCESS",
                            "report": {"mock": "data"}
                        } for analyzer in analyzers
                    ]
                }
            executed_stages.append(stage_id)
        else:
            print(f"  -> SKIPPED")
            skipped_stages.append(stage_id)

        print()

    # Simulate result distribution
    print("=== Simulating Result Distribution ===")

    # Create stage routing like the backend does
    stage_routing = []
    for stage in stages:
        stage_routing.append({
            "stage_id": stage["stage_id"],
            "target_nodes": stage.get("target_nodes", []),
            "executed": stage["stage_id"] in executed_stages,
            "analyzers": stage.get("analyzers", [])
        })

    print("Stage routing:")
    for routing in stage_routing:
        print(f"  Stage {routing['stage_id']}: executed={routing['executed']}, analyzers={routing['analyzers']}, targets={routing['target_nodes']}")

    # Simulate frontend result distribution
    result_nodes = ["results-clamav", "results-true", "results-false"]
    result_updates = {}

    for result_node in result_nodes:
        result_updates[result_node] = {
            "should_update": False,
            "analyzers": [],
            "error": "Branch not executed (condition not met)"
        }

    # Process routing
    for routing in stage_routing:
        is_executed = routing["executed"]
        stage_analyzers = routing["analyzers"] or []
        target_nodes = routing["target_nodes"] or []

        for node_id in target_nodes:
            if node_id in result_updates:
                current = result_updates[node_id]
                if is_executed:
                    current["should_update"] = True
                    current["analyzers"].extend(stage_analyzers)
                    current["error"] = None
                # If not executed, keep the error message

    print("\nResult node updates:")
    for node_id, update in result_updates.items():
        print(f"  {node_id}: {update}")

    return {
        "execution_plan": execution_plan,
        "executed_stages": executed_stages,
        "skipped_stages": skipped_stages,
        "stage_routing": stage_routing,
        "result_updates": result_updates
    }

async def main():
    """Main test function"""
    print("Testing Conditional Workflow Execution - Full Simulation")
    print("=" * 60)

    results = await simulate_execution()

    print("\n=== Final Analysis ===")
    executed = results["executed_stages"]
    skipped = results["skipped_stages"]
    routing = results["stage_routing"]
    result_updates = results["result_updates"]

    print(f"Executed stages: {executed}")
    print(f"Skipped stages: {skipped}")

    print("\nResult node status:")
    for node_id, update in result_updates.items():
        if update["should_update"]:
            print(f"  ✅ {node_id}: Would receive results from {update['analyzers']}")
        else:
            print(f"  ❌ {node_id}: {update['error']}")

    # Check for the issue
    false_result = result_updates.get("results-false", {})
    if false_result.get("should_update") and "Strings_Info" in false_result.get("analyzers", []):
        print("\n✅ FALSE branch should work correctly - Strings_Info analyzer executed")
    else:
        print("\n❌ ISSUE FOUND: FALSE branch not working - Strings_Info analyzer not executed")
        print("This would cause '0 analyzers executed' in the FALSE result node")

if __name__ == "__main__":
    asyncio.run(main())