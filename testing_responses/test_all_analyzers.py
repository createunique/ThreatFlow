#!/usr/bin/env python3
"""
Comprehensive IntelOwl Analyzer Testing Script
Tests all 18 analyzers on safe and malicious samples
Collects and analyzes responses for different scenarios
"""

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Any
import logging

# Add the middleware app to path
sys.path.insert(0, '/home/anonymous/COLLEGE/ThreatFlow/threatflow-middleware')
sys.path.insert(0, '/home/anonymous/COLLEGE/ThreatFlow/threatflow-middleware/app')

# Load environment variables
import os
os.environ['INTELOWL_API_KEY'] = '9e16ffdf58e18e11f0f4d0dd98277b1a73861ad8'
os.environ['INTELOWL_URL'] = 'http://localhost'

from app.services.intelowl_service import IntelOwlService
from app.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Define the 18 analyzers to test
ANALYZERS = [
    "File_Info", "ClamAV", "PE_Info", "Capa_Info", "Capa_Info_Shellcode",
    "Flare_Capa", "Yara", "Signature_Info", "Doc_Info", "PDF_Info",
    "Xlm_Macro_Deobfuscator", "Rtf_Info", "Strings_Info", "BoxJS",
    "Androguard", "APKiD", "APK_Artifacts", "Quark_Engine"
]

class AnalyzerTester:
    def __init__(self):
        self.service = IntelOwlService()
        self.samples_dir = Path("/home/anonymous/COLLEGE/ThreatFlow/testing_responses/Malware safe Malware samples")
        self.responses_dir = Path("/home/anonymous/COLLEGE/ThreatFlow/testing_responses/responses")
        self.responses_dir.mkdir(exist_ok=True)

    async def test_analyzer_on_file(self, analyzer: str, file_path: Path, category: str) -> Dict[str, Any]:
        """Test a single analyzer on a single file"""
        try:
            logger.info(f"Testing {analyzer} on {category}/{file_path.name}")

            # Submit analysis
            job_id = await self.service.submit_file_analysis(
                file_path=str(file_path),
                analyzers=[analyzer],
                file_name=file_path.name,
                tlp="CLEAR"
            )

            # Wait for completion
            result = await self.service.wait_for_completion(job_id, timeout=60)

            return {
                "analyzer": analyzer,
                "file": file_path.name,
                "category": category,
                "job_id": job_id,
                "success": True,
                "result": result
            }

        except Exception as e:
            logger.error(f"Failed {analyzer} on {file_path.name}: {e}")
            return {
                "analyzer": analyzer,
                "file": file_path.name,
                "category": category,
                "success": False,
                "error": str(e)
            }

    async def test_all_analyzers_on_category(self, category: str) -> List[Dict[str, Any]]:
        """Test all analyzers on all files in a category (safe/malicious)"""
        category_dir = self.samples_dir / category
        results = []

        if not category_dir.exists():
            logger.error(f"Category directory {category_dir} does not exist")
            return results

        files = list(category_dir.glob("*"))
        # Filter out directories
        files = [f for f in files if f.is_file()]

        logger.info(f"Testing {len(ANALYZERS)} analyzers on {len(files)} {category} files")

        for file_path in files:
            for analyzer in ANALYZERS:
                # Skip analyzers that don't make sense for certain file types
                if not self._should_test_analyzer(analyzer, file_path):
                    continue

                result = await self.test_analyzer_on_file(analyzer, file_path, category)
                results.append(result)

                # Small delay to avoid overwhelming the service
                await asyncio.sleep(0.5)

        return results

    def _should_test_analyzer(self, analyzer: str, file_path: Path) -> bool:
        """Determine if an analyzer should be tested on a file type"""
        ext = file_path.suffix.lower()
        name = file_path.name.lower()

        # File_Info works on everything
        if analyzer == "File_Info":
            return True

        # ClamAV works on most files
        if analyzer == "ClamAV":
            return True

        # PE analyzers only on .exe files
        if analyzer in ["PE_Info", "Capa_Info", "Flare_Capa", "Signature_Info"]:
            return ext in ['.exe', '.dll']

        # Shellcode analyzer on .bin files
        if analyzer == "Capa_Info_Shellcode":
            return ext == '.bin' or 'shellcode' in name

        # Document analyzers
        if analyzer == "Doc_Info":
            return ext in ['.doc', '.docx']
        if analyzer == "PDF_Info":
            return ext == '.pdf'
        if analyzer == "Xlm_Macro_Deobfuscator":
            return ext in ['.xls', '.xlsx', '.csv'] or 'xlm' in name
        if analyzer == "Rtf_Info":
            return ext == '.rtf'

        # Strings analyzer on text files
        if analyzer == "Strings_Info":
            return ext in ['.txt', '.js', '.py', '.sh']

        # BoxJS on JavaScript
        if analyzer == "BoxJS":
            return ext == '.js'

        # Android analyzers on APK files
        if analyzer in ["Androguard", "APKiD", "APK_Artifacts", "Quark_Engine"]:
            return ext == '.apk'

        # Yara on everything
        if analyzer == "Yara":
            return True

        return False

    async def run_comprehensive_tests(self) -> Dict[str, Any]:
        """Run all tests and collect results"""
        logger.info("Starting comprehensive analyzer testing")

        all_results = {
            "metadata": {
                "analyzers_tested": ANALYZERS,
                "categories": ["safe", "malicious"],
                "timestamp": "2025-11-26"
            },
            "results": []
        }

        # Test safe samples
        logger.info("Testing SAFE samples...")
        safe_results = await self.test_all_analyzers_on_category("safe")
        all_results["results"].extend(safe_results)

        # Test malicious samples
        logger.info("Testing MALICIOUS samples...")
        malicious_results = await self.test_all_analyzers_on_category("malicious")
        all_results["results"].extend(malicious_results)

        return all_results

    def save_results(self, results: Dict[str, Any]):
        """Save results to JSON file"""
        output_file = self.responses_dir / "comprehensive_test_results.json"
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        logger.info(f"Results saved to {output_file}")

    def analyze_results(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze the test results and provide summary"""
        analysis = {
            "summary": {
                "total_tests": len(results["results"]),
                "successful_tests": 0,
                "failed_tests": 0,
                "analyzers_coverage": {}
            },
            "analyzer_performance": {},
            "file_type_analysis": {},
            "error_analysis": []
        }

        for result in results["results"]:
            analyzer = result["analyzer"]
            success = result["success"]

            if success:
                analysis["summary"]["successful_tests"] += 1
            else:
                analysis["summary"]["failed_tests"] += 1
                analysis["error_analysis"].append({
                    "analyzer": analyzer,
                    "file": result["file"],
                    "error": result.get("error", "Unknown")
                })

            # Track analyzer coverage
            if analyzer not in analysis["summary"]["analyzers_coverage"]:
                analysis["summary"]["analyzers_coverage"][analyzer] = {"tested": 0, "successful": 0}

            analysis["summary"]["analyzers_coverage"][analyzer]["tested"] += 1
            if success:
                analysis["summary"]["analyzers_coverage"][analyzer]["successful"] += 1

            # Analyze results for successful tests
            if success and "result" in result:
                self._analyze_successful_result(result, analysis)

        return analysis

    def _analyze_successful_result(self, result: Dict[str, Any], analysis: Dict[str, Any]):
        """Analyze a successful test result"""
        analyzer = result["analyzer"]
        file_name = result["file"]
        category = result["category"]

        if analyzer not in analysis["analyzer_performance"]:
            analysis["analyzer_performance"][analyzer] = {
                "safe_files": [],
                "malicious_files": [],
                "response_formats": []
            }

        # Categorize by safety
        if category == "safe":
            analysis["analyzer_performance"][analyzer]["safe_files"].append(file_name)
        else:
            analysis["analyzer_performance"][analyzer]["malicious_files"].append(file_name)

        # Extract response format info
        if "result" in result and result["result"]:
            response_info = self._extract_response_info(result["result"])
            analysis["analyzer_performance"][analyzer]["response_formats"].append(response_info)

    def _extract_response_info(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Extract key information from analyzer response"""
        info = {
            "has_report": "report" in str(result),
            "has_errors": "errors" in str(result) or "error" in str(result),
            "has_success": "success" in str(result),
            "response_keys": list(result.keys()) if isinstance(result, dict) else []
        }

        # Try to extract verdict if present
        if isinstance(result, dict):
            for key, value in result.items():
                if isinstance(value, dict) and "report" in value:
                    report = value["report"]
                    if isinstance(report, dict):
                        if "verdict" in report:
                            info["verdict"] = report["verdict"]

        return info

    def save_analysis(self, analysis: Dict[str, Any]):
        """Save analysis to JSON file"""
        output_file = self.responses_dir / "test_analysis.json"
        with open(output_file, 'w') as f:
            json.dump(analysis, f, indent=2, default=str)
        logger.info(f"Analysis saved to {output_file}")

async def main():
    """Main testing function"""
    tester = AnalyzerTester()

    # Run comprehensive tests
    results = await tester.run_comprehensive_tests()

    # Save raw results
    tester.save_results(results)

    # Analyze results
    analysis = tester.analyze_results(results)

    # Save analysis
    tester.save_analysis(analysis)

    # Print summary
    print("\n" + "="*50)
    print("COMPREHENSIVE ANALYZER TESTING COMPLETE")
    print("="*50)
    print(f"Total tests run: {analysis['summary']['total_tests']}")
    print(f"Successful: {analysis['summary']['successful_tests']}")
    print(f"Failed: {analysis['summary']['failed_tests']}")
    print("\nAnalyzer Coverage:")
    for analyzer, stats in analysis['summary']['analyzers_coverage'].items():
        success_rate = (stats['successful'] / stats['tested'] * 100) if stats['tested'] > 0 else 0
        print(".1f")

    if analysis['error_analysis']:
        print(f"\nErrors encountered ({len(analysis['error_analysis'])}):")
        for error in analysis['error_analysis'][:5]:  # Show first 5
            print(f"  {error['analyzer']} on {error['file']}: {error['error']}")

if __name__ == "__main__":
    asyncio.run(main())