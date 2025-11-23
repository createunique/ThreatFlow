#!/usr/bin/env python3
"""
Comprehensive test script to analyze all 18 file analyzers and their report structures.
This will help identify patterns for fixing conditional logic evaluation.
"""

import asyncio
import json
import logging
import os
from pathlib import Path
from typing import Dict, Any, List

# Add the app directory to Python path
import sys
sys.path.append('/home/anonymous/COLLEGE/ThreatFlow/threatflow-middleware')

from app.services.intelowl_service import intel_service
from app.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_all_file_analyzers():
    """
    Test all available file analyzers on a sample file to analyze their report structures.
    This will help identify patterns for conditional logic evaluation.
    """

    # Use the EICAR test file we created earlier
    test_file_path = "/home/anonymous/COLLEGE/ThreatFlow/eicar_test.txt"

    if not os.path.exists(test_file_path):
        logger.error(f"Test file not found: {test_file_path}")
        return

    logger.info("Starting comprehensive analyzer report structure analysis...")

    # Get all available file analyzers
    try:
        analyzers_data = await intel_service.get_available_analyzers(analyzer_type="file")
        available_analyzers = analyzers_data.get("available", [])
        logger.info(f"Found {len(available_analyzers)} available file analyzers")
    except Exception as e:
        logger.error(f"Failed to get analyzers: {e}")
        return

    # Test specific analyzers that should work with EICAR
    test_analyzers = ["File_Info", "ClamAV", "Doc_Info", "Strings_Info", "YARA_Scan"]
    available_analyzers = [a for a in available_analyzers if a["name"] in test_analyzers]
    
    # Test each analyzer individually
    results = {}

    for analyzer in available_analyzers:
        analyzer_name = analyzer["name"]
        logger.info(f"Testing analyzer: {analyzer_name}")

        try:
            # Submit analysis
            job_id = await intel_service.submit_file_analysis(
                file_path=test_file_path,
                analyzers=[analyzer_name],
                file_name="test_file.txt",
                tlp="CLEAR"
            )

            logger.info(f"Submitted job {job_id} for {analyzer_name}")

            # Wait for completion
            job_results = await intel_service.wait_for_completion(job_id, timeout=120)

            # Extract analyzer report
            analyzer_reports = job_results.get("analyzer_reports", [])
            if analyzer_reports:
                report = analyzer_reports[0]  # Should be the only one
                results[analyzer_name] = {
                    "status": report.get("status"),
                    "report": report.get("report", {}),
                    "errors": report.get("errors", []),
                    "job_id": job_id
                }

                # Analyze report structure
                report_data = report.get("report", {})
                logger.info(f"{analyzer_name} report structure:")
                logger.info(f"  - Keys: {list(report_data.keys())}")
                if "verdict" in report_data:
                    logger.info(f"  - verdict: {report_data['verdict']}")
                if "detections" in report_data:
                    logger.info(f"  - detections: {report_data['detections']}")
                if "raw_report" in report_data:
                    raw_preview = str(report_data['raw_report'])[:200]
                    logger.info(f"  - raw_report preview: {raw_preview}...")

            else:
                logger.warning(f"No reports found for {analyzer_name}")
                results[analyzer_name] = {"error": "No reports found"}

        except Exception as e:
            logger.error(f"Failed to test {analyzer_name}: {e}")
            results[analyzer_name] = {"error": str(e)}

    # Save results to file
    output_file = "/home/anonymous/COLLEGE/ThreatFlow/analyzer_report_analysis.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)

    logger.info(f"Analysis complete. Results saved to {output_file}")

    # Analyze patterns for conditional logic
    analyze_report_patterns(results)

def analyze_report_patterns(results: Dict[str, Any]):
    """
    Analyze the report structures to identify patterns for conditional logic.
    """
    logger.info("\n" + "="*60)
    logger.info("ANALYZING REPORT PATTERNS FOR CONDITIONAL LOGIC")
    logger.info("="*60)

    patterns = {
        "has_verdict_field": [],
        "has_detections_array": [],
        "has_raw_report": [],
        "clamav_style_infection": [],
        "success_status": [],
        "failure_status": []
    }

    for analyzer_name, data in results.items():
        if "error" in data:
            continue

        report = data.get("report", {})
        status = data.get("status")

        if "verdict" in report:
            patterns["has_verdict_field"].append(analyzer_name)
            logger.info(f"✓ {analyzer_name} has verdict field: {report['verdict']}")

        if isinstance(report.get("detections"), list) and report["detections"]:
            patterns["has_detections_array"].append(analyzer_name)
            logger.info(f"✓ {analyzer_name} has detections array: {report['detections']}")

        if "raw_report" in report:
            patterns["has_raw_report"].append(analyzer_name)
            raw_report = str(report["raw_report"]).lower()
            if "infected files:" in raw_report and "1" in raw_report:
                patterns["clamav_style_infection"].append(analyzer_name)
                logger.info(f"✓ {analyzer_name} has ClamAV-style infection indicator")

        if status == "SUCCESS":
            patterns["success_status"].append(analyzer_name)
        elif status and status != "SUCCESS":
            patterns["failure_status"].append(analyzer_name)

    logger.info("\n" + "="*60)
    logger.info("SUMMARY OF PATTERNS FOUND:")
    logger.info("="*60)

    for pattern, analyzers in patterns.items():
        logger.info(f"{pattern}: {len(analyzers)} analyzers")
        if analyzers:
            logger.info(f"  - {', '.join(analyzers)}")

    logger.info("\n" + "="*60)
    logger.info("RECOMMENDATIONS FOR CONDITIONAL LOGIC:")
    logger.info("="*60)

    if patterns["has_verdict_field"]:
        logger.info("✓ verdict_malicious condition should work for: " +
                   ", ".join(patterns["has_verdict_field"]))

    if patterns["has_detections_array"]:
        logger.info("✓ verdict_malicious condition should work for detections: " +
                   ", ".join(patterns["has_detections_array"]))

    if patterns["clamav_style_infection"]:
        logger.info("✓ verdict_malicious condition should work for ClamAV-style: " +
                   ", ".join(patterns["clamav_style_infection"]))

    # Identify analyzers that won't work with current logic
    all_tested = set(results.keys())
    working_analyzers = set(patterns["has_verdict_field"] +
                           patterns["has_detections_array"] +
                           patterns["clamav_style_infection"])

    broken_analyzers = all_tested - working_analyzers - {"error"}
    if broken_analyzers:
        logger.warning(f"⚠ verdict_malicious condition WON'T work for: {', '.join(broken_analyzers)}")
        logger.warning("  These analyzers need custom evaluation logic based on their report structures")

if __name__ == "__main__":
    asyncio.run(test_all_file_analyzers())