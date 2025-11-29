#!/usr/bin/env python3
"""
Test Script for Floss, DetectItEasy, and ELF_Info Analyzers
Tests these specific analyzers on safe sample files
"""

import json
import requests
import time
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging

# Add middleware to path
sys.path.insert(0, '/home/anonymous/COLLEGE/ThreatFlow/threatflow-middleware')
sys.path.insert(0, '/home/anonymous/COLLEGE/ThreatFlow/threatflow-middleware/app')

# IntelOwl API configuration
INTELOWL_URL = "http://localhost"
INTELOWL_TOKEN = "9e16ffdf58e18e11f0f4d0dd98277b1a73861ad8"

# Test analyzers
TEST_ANALYZERS = ["Floss", "DetectItEasy", "ELF_Info"]

# Test files directory - using newly created samples
TEST_FILES_DIR = "/home/anonymous/COLLEGE/ThreatFlow/threatflow-middleware/app/intel_access/test_samples"

logger = logging.getLogger(__name__)

class AnalyzerTester:
    """Test specific analyzers on sample files"""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Token {INTELOWL_TOKEN}",
            # Remove Content-Type header - let requests set it correctly for multipart
        })

    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        """Make API request with error handling"""
        url = f"{INTELOWL_URL}{endpoint}"

        try:
            if method.upper() == "GET":
                response = self.session.get(url)
            elif method.upper() == "POST":
                response = self.session.post(url, json=data)
            elif method.upper() == "DELETE":
                response = self.session.delete(url)
            else:
                raise ValueError(f"Unsupported method: {method}")

            response.raise_for_status()
            return response.json() if response.content else {}

        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP Error {e.response.status_code}: {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Request failed: {e}")
            raise

    def submit_test_file(self, file_path: str, analyzers: List[str]) -> Optional[int]:
        """Submit a test file for analysis"""
        if not os.path.exists(file_path):
            logger.error(f"Test file not found: {file_path}")
            return None

        try:
            # Prepare multipart form data as expected by FileJobSerializer
            with open(file_path, 'rb') as f:
                files = {'file': (os.path.basename(file_path), f, 'application/octet-stream')}
                data = {
                    'analyzers_requested': analyzers,  # Send as list, not JSON string
                    'file_name': os.path.basename(file_path),
                    'is_sample': 'true',
                    'tlp': 'CLEAR'
                }

                response = self.session.post(
                    f"{INTELOWL_URL}/api/analyze_file",
                    files=files,
                    data=data
                )

            response.raise_for_status()
            result = response.json()

            # Check if result is a dict with job_id or a list
            if isinstance(result, dict) and 'job_id' in result:
                job_id = result['job_id']
            elif isinstance(result, dict) and 'results' in result:
                # Multiple jobs response
                jobs = result['results']
                if jobs and len(jobs) > 0:
                    job_id = jobs[0].get('job_id')
                else:
                    logger.error("No jobs in response")
                    return None
            else:
                logger.error(f"Unexpected response format: {result}")
                return None

            if job_id:
                logger.info(f"✅ Submitted test file, Job ID: {job_id}")
                return job_id
            else:
                logger.error("❌ No job ID in response")
                return None

        except requests.exceptions.HTTPError as e:
            logger.error(f"❌ Failed to submit test file: {e}")
            logger.error(f"Response text: {e.response.text}")
            return None
        except Exception as e:
            logger.error(f"❌ Failed to submit test file: {e}")
            return None

    def wait_for_job_completion(self, job_id: int, timeout: int = 120) -> Dict[str, Any]:
        """Wait for job to complete"""
        start_time = time.time()

        while time.time() - start_time < timeout:
            try:
                response = self.session.get(f"{INTELOWL_URL}/api/jobs/{job_id}")
                response.raise_for_status()
                job_data = response.json()

                status = job_data.get('status')
                logger.info(f"Job {job_id} status: {status}")

                if status in ['reported_without_fails', 'reported_with_fails', 'failed']:
                    return job_data

                time.sleep(5)

            except Exception as e:
                logger.error(f"Error checking job status: {e}")
                time.sleep(5)

        raise TimeoutError(f"Job {job_id} did not complete within {timeout} seconds")

    def test_analyzer_on_file(self, analyzer: str, file_path: str) -> Dict[str, Any]:
        """Test a single analyzer on a single file"""
        logger.info(f"🧪 Testing {analyzer} on {os.path.basename(file_path)}")

        # Submit test file
        job_id = self.submit_test_file(file_path, [analyzer])
        if not job_id:
            return {
                "analyzer": analyzer,
                "file": os.path.basename(file_path),
                "success": False,
                "error": "Failed to submit job"
            }

        # Wait for completion
        try:
            job_result = self.wait_for_job_completion(job_id, timeout=180)  # Longer timeout for these analyzers

            # Check if analyzer ran
            reports = job_result.get('analyzer_reports', [])
            logger.info(f"Job {job_id} has {len(reports)} analyzer reports")

            analyzer_report = None
            for report in reports:
                if report.get('name') == analyzer:
                    analyzer_report = report
                    break

            if not analyzer_report:
                return {
                    "analyzer": analyzer,
                    "file": os.path.basename(file_path),
                    "job_id": job_id,
                    "success": False,
                    "error": f"Analyzer {analyzer} did not run",
                    "job_result": job_result
                }

            # Check report status
            report_status = analyzer_report.get('status')
            if report_status == 'SUCCESS':
                return {
                    "analyzer": analyzer,
                    "file": os.path.basename(file_path),
                    "job_id": job_id,
                    "success": True,
                    "report_status": report_status,
                    "has_errors": bool(analyzer_report.get('errors')),
                    "report": analyzer_report.get('report', {})
                }
            else:
                return {
                    "analyzer": analyzer,
                    "file": os.path.basename(file_path),
                    "job_id": job_id,
                    "success": False,
                    "error": f"Report status: {report_status}",
                    "errors": analyzer_report.get('errors'),
                    "report": analyzer_report.get('report', {})
                }

        except TimeoutError as e:
            return {
                "analyzer": analyzer,
                "file": os.path.basename(file_path),
                "job_id": job_id,
                "success": False,
                "error": str(e)
            }
        except Exception as e:
            return {
                "analyzer": analyzer,
                "file": os.path.basename(file_path),
                "job_id": job_id,
                "success": False,
                "error": str(e)
            }

    def get_suitable_test_files(self) -> Dict[str, List[str]]:
        """Get suitable test files for each analyzer from newly created samples"""
        files = {}

        # Floss: works on PE files and COM files
        files["Floss"] = [
            os.path.join(TEST_FILES_DIR, "floss_samples/safe/sample1_simple_app.exe"),
            os.path.join(TEST_FILES_DIR, "floss_samples/safe/sample2_webservice.exe"),
            os.path.join(TEST_FILES_DIR, "floss_samples/safe/sample3_logger.exe"),
            os.path.join(TEST_FILES_DIR, "floss_samples/suspicious/eicar_test.com"),
            os.path.join(TEST_FILES_DIR, "floss_samples/suspicious/sample2_commandline.exe"),
            os.path.join(TEST_FILES_DIR, "floss_samples/suspicious/sample3_network.exe")
        ]

        # DetectItEasy: works on any file type
        files["DetectItEasy"] = [
            os.path.join(TEST_FILES_DIR, "detectiteasy_samples/safe/sample1_document.txt"),
            os.path.join(TEST_FILES_DIR, "detectiteasy_samples/safe/sample2_archive.zip"),
            os.path.join(TEST_FILES_DIR, "detectiteasy_samples/safe/sample3_config.json"),
            os.path.join(TEST_FILES_DIR, "detectiteasy_samples/suspicious/sample1_eicar.exe"),
            os.path.join(TEST_FILES_DIR, "detectiteasy_samples/suspicious/sample2_script.bat"),
            os.path.join(TEST_FILES_DIR, "detectiteasy_samples/suspicious/sample3_encoded.py")
        ]

        # ELF_Info: needs actual ELF files
        files["ELF_Info"] = [
            os.path.join(TEST_FILES_DIR, "elf_samples/safe/sample1_hello_world"),
            os.path.join(TEST_FILES_DIR, "elf_samples/safe/sample2_library.so"),
            os.path.join(TEST_FILES_DIR, "elf_samples/safe/sample3_utility"),
            os.path.join(TEST_FILES_DIR, "elf_samples/suspicious/sample1_dropper"),
            os.path.join(TEST_FILES_DIR, "elf_samples/suspicious/sample2_rootkit.so"),
            os.path.join(TEST_FILES_DIR, "elf_samples/suspicious/sample3_backdoor")
        ]

        # Filter to only existing files
        for analyzer in files:
            files[analyzer] = [f for f in files[analyzer] if os.path.exists(f)]

        return files

def main():
    """Main test function"""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    tester = AnalyzerTester()

    print("🔬 TESTING FLOSS, DETECTITEASY, AND ELF_INFO ANALYZERS")
    print("   Using newly created test samples")
    print("=" * 60)

    # Get suitable test files
    test_files = tester.get_suitable_test_files()
    print(f"📁 Test files directory: {TEST_FILES_DIR}")
    print(f"📋 Available test files per analyzer: {test_files}")
    print()

    all_results = []

    # Test each analyzer
    for analyzer in TEST_ANALYZERS:
        print(f"🧪 Testing {analyzer}...")
        print("-" * 40)

        files_to_test = test_files.get(analyzer, [])
        if not files_to_test:
            print(f"❌ No suitable test files found for {analyzer}")
            continue

        analyzer_results = []

        for file_path in files_to_test:
            result = tester.test_analyzer_on_file(analyzer, file_path)
            analyzer_results.append(result)

            status = "✅ SUCCESS" if result['success'] else "❌ FAILED"
            print(f"  {os.path.basename(file_path)}: {status}")
            if not result['success']:
                print(f"    Error: {result.get('error', 'Unknown')}")

        # Summary for this analyzer
        successful = sum(1 for r in analyzer_results if r['success'])
        total = len(analyzer_results)
        print(f"  {analyzer} Summary: {successful}/{total} tests passed")
        print()

        all_results.extend(analyzer_results)

    # Overall summary
    print("=" * 60)
    print("📊 OVERALL TEST SUMMARY")
    print("=" * 60)

    successful_tests = sum(1 for r in all_results if r['success'])
    total_tests = len(all_results)

    print(f"Total tests run: {total_tests}")
    print(f"Successful tests: {successful_tests}")
    print(f"Failed tests: {total_tests - successful_tests}")

    # Per-analyzer summary
    print("\n📈 Per-Analyzer Results:")
    for analyzer in TEST_ANALYZERS:
        analyzer_tests = [r for r in all_results if r['analyzer'] == analyzer]
        if analyzer_tests:
            successful = sum(1 for r in analyzer_tests if r['success'])
            total = len(analyzer_tests)
            success_rate = (successful / total * 100) if total > 0 else 0
            status = "✅ WORKING" if successful > 0 else "❌ NOT WORKING"
            print(f"  {analyzer}: {successful}/{total} ({success_rate:.1f}%) - {status}")

    # Save detailed results
    results_file = "/home/anonymous/COLLEGE/ThreatFlow/threatflow-middleware/app/intel_access/analyzer_test_results.json"
    with open(results_file, 'w') as f:
        json.dump({
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "analyzers_tested": TEST_ANALYZERS,
            "test_files": test_files,
            "results": all_results,
            "summary": {
                "total_tests": total_tests,
                "successful_tests": successful_tests,
                "failed_tests": total_tests - successful_tests
            }
        }, f, indent=2, default=str)

    print(f"\n📄 Detailed results saved to: {results_file}")

    print("\n" + "=" * 60)
    print("TESTING COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    main()