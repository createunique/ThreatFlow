#!/usr/bin/env python3
"""
Test script to verify conditional workflow logic works correctly
"""

import asyncio
import json
import logging
from pathlib import Path

# Add the app directory to Python path
import sys
sys.path.append('/home/anonymous/COLLEGE/ThreatFlow/threatflow-middleware')

from app.services.intelowl_service import intel_service

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_conditional_workflow():
    """
    Test the conditional workflow logic
    """

    # Load the test workflow stages directly
    with open('/home/anonymous/COLLEGE/ThreatFlow/test_conditional_workflow.json', 'r') as f:
        workflow_data = json.load(f)

    stages = workflow_data["stages"]

    logger.info(f"Loaded workflow with {len(stages)} stages")

    # Test file
    test_file_path = "/home/anonymous/COLLEGE/ThreatFlow/eicar_test.txt"

    # Execute the workflow
    results = await intel_service.execute_workflow_with_conditionals(
        file_path=test_file_path,
        stages=stages,
        file_name="eicar_test.txt",
        tlp="CLEAR"
    )

    logger.info("Workflow execution completed")
    logger.info(f"Job IDs: {results['job_ids']}")
    logger.info(f"Executed stages: {results['executed_stages']}")
    logger.info(f"Skipped stages: {results['skipped_stages']}")

    # Analyze results
    all_results = results['all_results']

    # Stage 0 should always execute
    assert 0 in results['executed_stages'], "Stage 0 should always execute"
    assert 'stage_0' in all_results, "Stage 0 results should be present"

    # Stage 1 should be skipped (File_Info is not malicious)
    assert 1 in results['skipped_stages'], "Stage 1 should be skipped (File_Info not malicious)"
    assert 'stage_1' not in all_results, "Stage 1 should not have results"

    # Stage 2 should execute (File_Info succeeded)
    assert 2 in results['executed_stages'], "Stage 2 should execute (File_Info succeeded)"
    assert 'stage_2' in all_results, "Stage 2 results should be present"

    logger.info("✅ Conditional logic test PASSED!")
    logger.info("  - Stage 0 (File_Info): EXECUTED ✓")
    logger.info("  - Stage 1 (Strings_Info, condition: verdict_malicious): SKIPPED ✓")
    logger.info("  - Stage 2 (Doc_Info, condition: analyzer_success): EXECUTED ✓")

    return results

if __name__ == "__main__":
    asyncio.run(test_conditional_workflow())