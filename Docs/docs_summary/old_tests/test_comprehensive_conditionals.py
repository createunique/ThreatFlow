#!/usr/bin/env python3
"""
Comprehensive test script for conditional logic with different analyzers and conditions
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

async def test_comprehensive_conditionals():
    """
    Test conditional logic with various analyzers and condition types
    """

    test_file_path = "/home/anonymous/COLLEGE/ThreatFlow/eicar_test.txt"

    # Test Case 1: File_Info with verdict_malicious (should be False)
    logger.info("="*60)
    logger.info("TEST CASE 1: File_Info verdict_malicious condition")
    logger.info("="*60)

    stages_1 = [
        {
            "stage_id": 0,
            "depends_on": None,
            "condition": None,
            "analyzers": ["File_Info"]
        },
        {
            "stage_id": 1,
            "depends_on": 0,
            "condition": {
                "type": "verdict_malicious",
                "source_analyzer": "File_Info"
            },
            "analyzers": ["Strings_Info"]
        }
    ]

    results_1 = await intel_service.execute_workflow_with_conditionals(
        file_path=test_file_path,
        stages=stages_1,
        file_name="eicar_test.txt",
        tlp="CLEAR"
    )

    assert 0 in results_1['executed_stages'], "Stage 0 should execute"
    assert 1 in results_1['skipped_stages'], "Stage 1 should be skipped (File_Info not malicious)"
    logger.info("✅ PASSED: File_Info verdict_malicious correctly evaluates to False")

    # Test Case 2: File_Info with analyzer_success (should be True)
    logger.info("="*60)
    logger.info("TEST CASE 2: File_Info analyzer_success condition")
    logger.info("="*60)

    stages_2 = [
        {
            "stage_id": 0,
            "depends_on": None,
            "condition": None,
            "analyzers": ["File_Info"]
        },
        {
            "stage_id": 1,
            "depends_on": 0,
            "condition": {
                "type": "analyzer_success",
                "source_analyzer": "File_Info"
            },
            "analyzers": ["Doc_Info"]
        }
    ]

    results_2 = await intel_service.execute_workflow_with_conditionals(
        file_path=test_file_path,
        stages=stages_2,
        file_name="eicar_test.txt",
        tlp="CLEAR"
    )

    assert 0 in results_2['executed_stages'], "Stage 0 should execute"
    assert 1 in results_2['executed_stages'], "Stage 1 should execute (File_Info succeeded)"
    logger.info("✅ PASSED: File_Info analyzer_success correctly evaluates to True")

    # Test Case 3: ClamAV with verdict_malicious (should be False for EICAR with outdated sigs)
    logger.info("="*60)
    logger.info("TEST CASE 3: ClamAV verdict_malicious condition")
    logger.info("="*60)

    stages_3 = [
        {
            "stage_id": 0,
            "depends_on": None,
            "condition": None,
            "analyzers": ["ClamAV"]
        },
        {
            "stage_id": 1,
            "depends_on": 0,
            "condition": {
                "type": "verdict_malicious",
                "source_analyzer": "ClamAV"
            },
            "analyzers": ["Strings_Info"]
        }
    ]

    results_3 = await intel_service.execute_workflow_with_conditionals(
        file_path=test_file_path,
        stages=stages_3,
        file_name="eicar_test.txt",
        tlp="CLEAR"
    )

    assert 0 in results_3['executed_stages'], "Stage 0 should execute"
    # ClamAV doesn't detect EICAR with outdated signatures, so verdict_malicious should be False
    assert 1 in results_3['skipped_stages'], "Stage 1 should be skipped (ClamAV no detection)"
    logger.info("✅ PASSED: ClamAV verdict_malicious correctly evaluates to False (no EICAR detection)")

    # Test Case 4: NOT condition
    logger.info("="*60)
    logger.info("TEST CASE 4: NOT condition (File_Info verdict_malicious)")
    logger.info("="*60)

    stages_4 = [
        {
            "stage_id": 0,
            "depends_on": None,
            "condition": None,
            "analyzers": ["File_Info"]
        },
        {
            "stage_id": 1,
            "depends_on": 0,
            "condition": {
                "type": "NOT",
                "inner": {
                    "type": "verdict_malicious",
                    "source_analyzer": "File_Info"
                }
            },
            "analyzers": ["Strings_Info"]
        }
    ]

    results_4 = await intel_service.execute_workflow_with_conditionals(
        file_path=test_file_path,
        stages=stages_4,
        file_name="eicar_test.txt",
        tlp="CLEAR"
    )

    assert 0 in results_4['executed_stages'], "Stage 0 should execute"
    assert 1 in results_4['executed_stages'], "Stage 1 should execute (NOT verdict_malicious = True)"
    logger.info("✅ PASSED: NOT condition correctly inverts verdict_malicious")

    logger.info("="*60)
    logger.info("🎉 ALL CONDITIONAL LOGIC TESTS PASSED!")
    logger.info("="*60)

if __name__ == "__main__":
    asyncio.run(test_comprehensive_conditionals())