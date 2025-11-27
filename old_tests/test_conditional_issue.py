#!/usr/bin/env python3
"""
Test script to reproduce the conditional workflow issue
where analyzers on FALSE branches don't execute
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

async def test_workflow_parsing():
    """Test the workflow parsing logic"""
    print("=== Testing Workflow Parsing ===")

    nodes, edges = create_test_workflow()
    execution_plan = workflow_parser.parse(nodes, edges)

    print("Execution Plan:")
    print(json.dumps(execution_plan, indent=2))

    return execution_plan

async def test_conditional_evaluation():
    """Test conditional evaluation with mock results"""
    print("\n=== Testing Conditional Evaluation ===")

    # Mock results for ClamAV (clean file - should trigger FALSE branch)
    mock_results = {
        "stage_0": {
            "analyzer_reports": [
                {
                    "name": "ClamAV",
                    "status": "SUCCESS",
                    "report": {
                        "detections": [],  # Empty = clean
                        "raw_report": "Infected files: 0"
                    }
                }
            ]
        }
    }

    # Test condition evaluation
    stages = [
        {
            "stage_id": 0,
            "analyzers": ["ClamAV"],
            "depends_on": None,
            "condition": None
        },
        {
            "stage_id": 1,
            "analyzers": ["File_Info"],
            "depends_on": "ClamAV",
            "condition": {
                "type": "verdict_malicious",
                "source_analyzer": "ClamAV"
            },
            "target_nodes": ["results-true"]
        },
        {
            "stage_id": 2,
            "analyzers": ["Strings_Info"],
            "depends_on": "ClamAV",
            "condition": {
                "type": "verdict_malicious",
                "source_analyzer": "ClamAV",
                "negate": True  # FALSE branch
            },
            "target_nodes": ["results-false"]
        }
    ]

    print("Testing stage evaluation:")
    for stage in stages:
        if stage["condition"]:
            should_execute = intel_service._evaluate_condition(stage["condition"], mock_results)
            print(f"Stage {stage['stage_id']}: {should_execute} (analyzers: {stage['analyzers']})")
        else:
            print(f"Stage {stage['stage_id']}: Always execute (analyzers: {stage['analyzers']})")

async def main():
    """Main test function"""
    print("Testing Conditional Workflow Execution Issue")
    print("=" * 50)

    # Test parsing
    execution_plan = await test_workflow_parsing()

    # Test evaluation
    await test_conditional_evaluation()

    print("\n=== Analysis ===")
    print("If ClamAV returns clean (no detections), the condition 'verdict_malicious' should be False.")
    print("This means the TRUE branch (File_Info) should be skipped.")
    print("The FALSE branch (Strings_Info) should execute because condition is negated (negate=True).")
    print("\nThe issue might be in:")
    print("1. Workflow parsing - are FALSE branches being created correctly?")
    print("2. Condition evaluation - is negate=True working properly?")
    print("3. Stage execution - are negated conditions being evaluated correctly?")

if __name__ == "__main__":
    asyncio.run(main())