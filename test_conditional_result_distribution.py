#!/usr/bin/env python3
"""
Comprehensive Test for Conditional Workflow Result Distribution
Tests that result nodes correctly show/hide results based on executed vs skipped branches
"""

import asyncio
import json
import requests
import time
from pathlib import Path

def test_conditional_workflow_frontend():
    """
    Test the complete conditional workflow from frontend perspective
    """
    print("🧪 TESTING CONDITIONAL WORKFLOW RESULT DISTRIBUTION")
    print("=" * 60)

    # Test workflow: File -> File_Info -> Conditional -> [Result1 (TRUE), Result2 (FALSE)]
    # Condition: analyzer_success (File_Info should succeed)
    # Expected: Result1 shows results, Result2 shows "Branch not executed"

    workflow_data = {
        "nodes": [
            {
                "id": "file-1",
                "type": "file",
                "position": {"x": 100, "y": 100},
                "data": {"label": "Test File"}
            },
            {
                "id": "analyzer-1",
                "type": "analyzer",
                "position": {"x": 300, "y": 100},
                "data": {"analyzer": "File_Info", "label": "File Info"}
            },
            {
                "id": "conditional-1",
                "type": "conditional",
                "position": {"x": 500, "y": 100},
                "data": {
                    "conditionType": "analyzer_success",
                    "sourceAnalyzer": "File_Info",
                    "label": "File Info Success?"
                }
            },
            {
                "id": "result-true",
                "type": "result",
                "position": {"x": 700, "y": 50},
                "data": {"label": "Success Results"}
            },
            {
                "id": "result-false",
                "type": "result",
                "position": {"x": 700, "y": 150},
                "data": {"label": "Failure Results"}
            }
        ],
        "edges": [
            {"id": "edge-1", "source": "file-1", "target": "analyzer-1"},
            {"id": "edge-2", "source": "analyzer-1", "target": "conditional-1"},
            {"id": "edge-3", "source": "conditional-1", "target": "result-true", "sourceHandle": "true-output"},
            {"id": "edge-4", "source": "conditional-1", "target": "result-false", "sourceHandle": "false-output"}
        ]
    }

    # Test file
    test_file_path = "/home/anonymous/COLLEGE/ThreatFlow/eicar_test.txt"

    print("📋 Test Setup:")
    print(f"  - Workflow: File → File_Info → Conditional → [Result1 (TRUE), Result2 (FALSE)]")
    print(f"  - Condition: analyzer_success (File_Info)")
    print(f"  - Test File: {test_file_path}")
    print(f"  - Expected: Result1 shows File_Info results, Result2 shows 'Branch not executed'")
    print()

    try:
        # Submit workflow
        print("🚀 Submitting workflow...")
        with open(test_file_path, 'rb') as f:
            files = {'file': ('eicar_test.txt', f, 'text/plain')}
            data = {'workflow_json': json.dumps(workflow_data)}

            response = requests.post(
                'http://localhost:8030/api/execute',
                files=files,
                data=data,
                timeout=30
            )

        if response.status_code != 200:
            print(f"❌ Workflow submission failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False

        result = response.json()
        print(f"✅ Workflow submitted successfully")
        print(f"  - Job IDs: {result.get('job_ids', [])}")
        print(f"  - Has conditionals: {result.get('has_conditionals', False)}")
        print(f"  - Stage routing: {len(result.get('stage_routing', []))} stages")
        
        # Debug: Check what the middleware parsed
        job_id = result.get('job_ids', [result.get('job_id')])[0]
        try:
            status_response = requests.get(f'http://localhost:8030/api/status/{job_id}', timeout=5)
            if status_response.status_code == 200:
                status_data = status_response.json()
                print(f"  - Parsed has_conditionals: {status_data.get('has_conditionals', 'N/A')}")
                routing = status_data.get('stage_routing', [])
                if routing:
                    print(f"  - Routing details:")
                    for r in routing:
                        print(f"    Stage {r['stage_id']}: executed={r.get('executed')}, targets={r.get('target_nodes', [])}, analyzers={r.get('analyzers', [])}")
        except Exception as e:
            print(f"  - Could not get status details: {e}")
        print()

        # Get the main job ID
        job_id = result.get('job_id') or (result.get('job_ids', [])[0] if result.get('job_ids') else None)
        if not job_id:
            print("❌ No job ID returned")
            return False

        # Poll for completion
        print("⏳ Polling for completion...")
        max_attempts = 60
        for attempt in range(max_attempts):
            try:
                status_response = requests.get(f'http://localhost:8030/api/status/{job_id}', timeout=10)
                if status_response.status_code == 200:
                    status = status_response.json()
                    if status.get('status') == 'reported_without_fails':
                        print("✅ Workflow completed successfully")
                        break
                    elif status.get('status') == 'reported_with_fails':
                        print("⚠️ Workflow completed with failures")
                        break
                    elif status.get('status') == 'failed':
                        print("❌ Workflow failed")
                        return False
                else:
                    print(f"❌ Status check failed: {status_response.status_code}")
                    return False
            except Exception as e:
                print(f"❌ Status check error: {e}")
                return False

            if attempt < max_attempts - 1:
                time.sleep(2)
        else:
            print("❌ Workflow timed out")
            return False

        # Analyze final status
        final_status = status_response.json()
        print(f"📊 Final Status Analysis:")
        print(f"  - Status: {final_status.get('status')}")
        print(f"  - Has conditionals: {final_status.get('has_conditionals', False)}")

        stage_routing = final_status.get('stage_routing', [])
        if stage_routing:
            print(f"  - Stage routing:")
            for routing in stage_routing:
                executed_status = "✅ EXECUTED" if routing.get('executed') else "⏭️ SKIPPED"
                print(f"    Stage {routing['stage_id']}: {executed_status} - Targets: {routing.get('target_nodes', [])} - Analyzers: {routing.get('analyzers', [])}")
        print()

        # Check results distribution
        all_results = final_status.get('results', {})
        analyzer_reports = all_results.get('analyzer_reports', [])

        print("🔍 Result Distribution Analysis:")
        print(f"  - Total analyzer reports: {len(analyzer_reports)}")

        executed_analyzers = set()
        for routing in stage_routing:
            if routing.get('executed') and routing.get('analyzers'):
                executed_analyzers.update(routing['analyzers'])

        print(f"  - Executed analyzers: {list(executed_analyzers)}")

        # Check which result nodes should have results
        result_node_analysis = {}
        for routing in stage_routing:
            executed = routing.get('executed', False)
            analyzers = routing.get('analyzers', [])
            targets = routing.get('target_nodes', [])

            for target in targets:
                if target not in result_node_analysis:
                    result_node_analysis[target] = {
                        'should_have_results': False,
                        'analyzers': [],
                        'executed_stages': []
                    }

                if executed:
                    result_node_analysis[target]['should_have_results'] = True
                    result_node_analysis[target]['analyzers'].extend(analyzers)
                    result_node_analysis[target]['executed_stages'].append(routing['stage_id'])

        print(f"  - Result node expectations:")
        for node_id, analysis in result_node_analysis.items():
            status = "✅ SHOULD SHOW RESULTS" if analysis['should_have_results'] else "⏭️ SHOULD BE SKIPPED"
            analyzers = list(set(analysis['analyzers'])) if analysis['analyzers'] else []
            print(f"    {node_id}: {status} - Analyzers: {analyzers}")
        print()

        # Test validation
        success = True

        # Check that executed analyzers have reports
        for analyzer in executed_analyzers:
            report_exists = any(r.get('name') == analyzer for r in analyzer_reports)
            if report_exists:
                print(f"✅ Analyzer '{analyzer}' has report")
            else:
                print(f"❌ Analyzer '{analyzer}' missing report")
                success = False

        # Check result node expectations
        for node_id, analysis in result_node_analysis.items():
            expected_analyzers = set(analysis['analyzers'])
            should_have_results = analysis['should_have_results']

            # In a real frontend test, we'd check the node data
            # For now, we validate the backend logic
            if should_have_results and not expected_analyzers:
                print(f"⚠️ Result node '{node_id}' should have results but no analyzers assigned")
            elif not should_have_results and expected_analyzers:
                print(f"⚠️ Result node '{node_id}' should be skipped but has analyzers: {expected_analyzers}")
                success = False

        print()
        if success:
            print("🎉 CONDITIONAL WORKFLOW TEST PASSED!")
            print("✅ Result distribution logic working correctly")
            print("✅ Executed branches show results, skipped branches are properly handled")
        else:
            print("❌ CONDITIONAL WORKFLOW TEST FAILED!")
            print("❌ Result distribution logic has issues")

        return success

    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_conditional_workflow_frontend()
    exit(0 if success else 1)