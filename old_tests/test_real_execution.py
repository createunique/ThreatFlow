#!/usr/bin/env python3
"""
Test the actual workflow execution with the middleware
"""

import json
import asyncio
import sys
import os
sys.path.append('/home/anonymous/COLLEGE/ThreatFlow/threatflow-middleware')

from app.services.workflow_parser import workflow_parser
from app.services.intelowl_service import intel_service

async def test_workflow_execution():
    """Test the workflow execution with a clean file"""

    # Load the test workflow
    with open('/home/anonymous/COLLEGE/ThreatFlow/test_workflow.json', 'r') as f:
        workflow_data = json.load(f)

    print("=== Testing Workflow Execution ===")
    print("Workflow nodes:", len(workflow_data['nodes']))
    print("Workflow edges:", len(workflow_data['edges']))

    # Convert dict nodes to WorkflowNode objects
    from app.models.workflow import WorkflowNode, WorkflowEdge, NodeType

    nodes = []
    for node_dict in workflow_data['nodes']:
        node = WorkflowNode(
            id=node_dict['id'],
            type=NodeType(node_dict['type']),
            position=node_dict['position'],
            data=node_dict['data']
        )
        nodes.append(node)

    edges = []
    for edge_dict in workflow_data['edges']:
        edge = WorkflowEdge(
            id=edge_dict['id'],
            source=edge_dict['source'],
            target=edge_dict['target'],
            sourceHandle=edge_dict.get('sourceHandle')
        )
        edges.append(edge)

    # Parse the workflow
    execution_plan = workflow_parser.parse(nodes, edges)
    print("\nExecution plan:")
    print(json.dumps(execution_plan, indent=2))

    # Test file path
    test_file = "/home/anonymous/COLLEGE/ThreatFlow/test_clean_file.txt"

    if not os.path.exists(test_file):
        print(f"Test file {test_file} does not exist")
        return

    print(f"\nTest file: {test_file} ({os.path.getsize(test_file)} bytes)")

    # Execute the workflow
    stages = execution_plan.get("stages", [])
    print(f"\nExecuting {len(stages)} stages...")

    try:
        result = await intel_service.execute_workflow_with_conditionals(
            file_path=test_file,
            stages=stages,
            file_name="test_clean_file.txt"
        )

        print("\nExecution result:")
        print(f"Job IDs: {result['job_ids']}")
        print(f"Executed stages: {result['executed_stages']}")
        print(f"Skipped stages: {result['skipped_stages']}")
        print(f"Total stages executed: {result['total_stages_executed']}")

        print("\nStage results:")
        for stage_key, stage_data in result['all_results'].items():
            print(f"  {stage_key}:")
            if isinstance(stage_data, dict):
                if stage_data.get('type') == 'result_only':
                    print(f"    Type: result_only")
                    print(f"    Target nodes: {stage_data.get('target_nodes', [])}")
                elif 'analyzer_reports' in stage_data:
                    reports = stage_data['analyzer_reports']
                    print(f"    Analyzer reports: {len(reports)}")
                    for report in reports:
                        print(f"      - {report.get('name')}: {report.get('status')}")
                else:
                    print(f"    Data: {stage_data}")

        # Check what would be sent to frontend
        stage_routing = []
        for stage in stages:
            stage_routing.append({
                "stage_id": stage["stage_id"],
                "target_nodes": stage.get("target_nodes", []),
                "executed": stage["stage_id"] in result["executed_stages"],
                "analyzers": stage.get("analyzers", [])
            })

        print("\nStage routing for frontend:")
        for routing in stage_routing:
            print(f"  Stage {routing['stage_id']}: executed={routing['executed']}, analyzers={routing['analyzers']}, targets={routing['target_nodes']}")

    except Exception as e:
        print(f"Execution failed: {e}")
        import traceback
        traceback.print_exc()

async def main():
    await test_workflow_execution()

if __name__ == "__main__":
    asyncio.run(main())