#!/usr/bin/env python3
"""
Test Script for Medium File Analyzers (600-1100 MB):
- PEframe_Scan (200-300 MB)
- Malpedia_Scan (200-400 MB)
- OneNote_Info (100-200 MB)
- GoReSym (100-200 MB)

Tests these analyzers on appropriate sample files, creating missing samples if needed.
"""

import json
import requests
import time
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging
import tempfile
import zipfile

# Add middleware to path
sys.path.insert(0, '/home/anonymous/COLLEGE/ThreatFlow/threatflow-middleware')
sys.path.insert(0, '/home/anonymous/COLLEGE/ThreatFlow/threatflow-middleware/app')

# IntelOwl API configuration
INTELOWL_URL = "http://localhost"
INTELOWL_TOKEN = "9e16ffdf58e18e11f0f4d0dd98277b1a73861ad8"

# Test analyzers and their requirements
TEST_ANALYZERS = {
    "PEframe_Scan": {
        "supported_filetypes": ["application/vnd.microsoft.portable-executable"],
        "description": "PE file analyzer",
        "test_files": []
    },
    "Malpedia_Scan": {
        "supported_filetypes": ["application/x-binary", "application/x-elf", "application/octet-stream",
                              "application/zip", "application/vnd.microsoft.portable-executable"],
        "description": "Malpedia YARA scanner",
        "test_files": []
    },
    "OneNote_Info": {
        "supported_filetypes": ["application/onenote"],
        "description": "OneNote document analyzer",
        "test_files": []
    },
    "GoReSym": {
        "supported_filetypes": ["application/vnd.microsoft.portable-executable", "application/x-executable"],
        "description": "Go symbol parser",
        "test_files": []
    }
}

# Test files directory - using newly created small samples
TEST_FILES_DIR = "/home/anonymous/COLLEGE/ThreatFlow/threatflow-middleware/app/intel_access/test_samples_small/medium_analyzers"

logger = logging.getLogger(__name__)

class SampleGenerator:
    """Generate sample files for testing analyzers"""

    def __init__(self):
        self.generated_dir = Path(TEST_FILES_DIR)
        self.generated_dir.mkdir(exist_ok=True)

    def create_onenote_file(self, filename: str, content: str = "Test OneNote Content", is_malicious: bool = False) -> str:
        """Create a basic OneNote file (simplified structure)"""
        file_path = self.generated_dir / filename

        # OneNote files are complex OLE2 structures. For testing, we'll create a basic structure
        # that might be accepted by the analyzer. In practice, OneNote files have specific formats.

        # Create a simple compound document structure
        content_to_add = "MALICIOUS CONTENT: This is a test malicious OneNote file" if is_malicious else content

        # For now, create a text file with .one extension
        # Note: This is not a real OneNote file, but some analyzers might accept it
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(f"""OneNote File Content
{content_to_add}
Created for testing purposes.
This simulates a OneNote document structure.
""")

        logger.info(f"Created OneNote file: {file_path}")
        return str(file_path)

    def create_zip_file(self, filename: str, files_to_zip: List[str], is_malicious: bool = False) -> str:
        """Create a ZIP file with test content"""
        file_path = self.generated_dir / filename

        with zipfile.ZipFile(file_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for file in files_to_zip:
                if os.path.exists(file):
                    zf.write(file, os.path.basename(file))

            # Add a test file
            test_content = "MALICIOUS ZIP CONTENT" if is_malicious else "Safe ZIP content for testing"
            zf.writestr("test_content.txt", test_content)

        logger.info(f"Created ZIP file: {file_path}")
        return str(file_path)

    def create_binary_file(self, filename: str, size_kb: int = 10, is_malicious: bool = False) -> str:
        """Create a binary file for testing"""
        file_path = self.generated_dir / filename

        # Create binary content
        if is_malicious:
            content = b"MALICIOUS_BINARY_CONTENT_" + b"A" * (size_kb * 1024 - 25)
        else:
            content = b"SAFE_BINARY_CONTENT_" + b"B" * (size_kb * 1024 - 20)

        with open(file_path, 'wb') as f:
            f.write(content)

        logger.info(f"Created binary file: {file_path}")
        return str(file_path)

class AnalyzerTester:
    """Test specific analyzers on sample files"""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Token {INTELOWL_TOKEN}",
        })
        self.sample_generator = SampleGenerator()

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
            # Prepare multipart form data
            with open(file_path, 'rb') as f:
                files = {'file': (os.path.basename(file_path), f, 'application/octet-stream')}
                data = {
                    'analyzers_requested': analyzers,
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

            if isinstance(result, dict) and 'job_id' in result:
                job_id = result['job_id']
            elif isinstance(result, dict) and 'results' in result:
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

    def wait_for_job_completion(self, job_id: int, timeout: int = 300) -> Dict[str, Any]:
        """Wait for job to complete (longer timeout for these analyzers)"""
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

                time.sleep(10)  # Longer polling interval for heavy analyzers

            except Exception as e:
                logger.error(f"Error checking job status: {e}")
                time.sleep(10)

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
            job_result = self.wait_for_job_completion(job_id, timeout=600)  # 10 minutes timeout

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

    def prepare_test_files(self) -> Dict[str, List[str]]:
        """Prepare test files for each analyzer using newly created small samples"""
        test_files = {}

        # PEframe_Scan: Needs PE files
        test_files["PEframe_Scan"] = [
            os.path.join(TEST_FILES_DIR, "peframe_scan/safe/peframe_safe_app.exe"),
            os.path.join(TEST_FILES_DIR, "peframe_scan/suspicious/peframe_susp_maldoc.exe"),
            os.path.join(TEST_FILES_DIR, "peframe_scan/suspicious/sample_macro.doc")
        ]

        # Malpedia_Scan: Accepts many formats
        test_files["Malpedia_Scan"] = [
            os.path.join(TEST_FILES_DIR, "malpedia_scan/safe/malpedia_legit_bundle.zip"),
            os.path.join(TEST_FILES_DIR, "malpedia_scan/suspicious/malpedia_emotet_like.exe"),
            os.path.join(TEST_FILES_DIR, "malpedia_scan/suspicious/malpedia_linus_backdoor")
        ]

        # OneNote_Info: Needs OneNote files
        test_files["OneNote_Info"] = [
            os.path.join(TEST_FILES_DIR, "onenote_info/safe/onenote_meeting.one"),
            os.path.join(TEST_FILES_DIR, "onenote_info/safe/onenote_docs.one"),
            os.path.join(TEST_FILES_DIR, "onenote_info/suspicious/onenote_macro_like.one")
        ]

        # GoReSym: Needs Go binaries
        test_files["GoReSym"] = [
            os.path.join(TEST_FILES_DIR, "gore_sym/safe/goserver_small"),
            os.path.join(TEST_FILES_DIR, "gore_sym/safe/gotool_small"),
            os.path.join(TEST_FILES_DIR, "gore_sym/suspicious/goc2_small")
        ]

        # Filter to only existing files
        for analyzer in test_files:
            test_files[analyzer] = [f for f in test_files[analyzer] if os.path.exists(f)]

        return test_files

def main():
    """Main test function"""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    tester = AnalyzerTester()

    print("🔬 TESTING MEDIUM FILE ANALYZERS (600-1100 MB)")
    print("Analyzers: PEframe_Scan, Malpedia_Scan, OneNote_Info, GoReSym")
    print("   Using newly created test samples")
    print("=" * 70)

    # Prepare test files
    print("📁 Preparing test files...")
    test_files = tester.prepare_test_files()

    for analyzer, files in test_files.items():
        print(f"  {analyzer}: {len(files)} test files prepared")
        for file in files:
            print(f"    - {os.path.basename(file)}")
    print()

    all_results = []

    # Test each analyzer
    for analyzer in TEST_ANALYZERS.keys():
        print(f"🧪 Testing {analyzer}...")
        print(f"   Description: {TEST_ANALYZERS[analyzer]['description']}")
        print(f"   Supported types: {TEST_ANALYZERS[analyzer]['supported_filetypes']}")
        print("-" * 60)

        files_to_test = test_files.get(analyzer, [])
        if not files_to_test:
            print(f"❌ No test files available for {analyzer}")
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
    print("=" * 70)
    print("📊 OVERALL TEST SUMMARY")
    print("=" * 70)

    successful_tests = sum(1 for r in all_results if r['success'])
    total_tests = len(all_results)

    print(f"Total tests run: {total_tests}")
    print(f"Successful tests: {successful_tests}")
    print(f"Failed tests: {total_tests - successful_tests}")

    # Per-analyzer summary
    print("\n📈 Per-Analyzer Results:")
    for analyzer in TEST_ANALYZERS.keys():
        analyzer_tests = [r for r in all_results if r['analyzer'] == analyzer]
        if analyzer_tests:
            successful = sum(1 for r in analyzer_tests if r['success'])
            total = len(analyzer_tests)
            success_rate = (successful / total * 100) if total > 0 else 0
            status = "✅ WORKING" if successful > 0 else "❌ NOT WORKING"
            print(f"  {analyzer}: {successful}/{total} ({success_rate:.1f}%) - {status}")

    # Save detailed results
    results_file = "/home/anonymous/COLLEGE/ThreatFlow/threatflow-middleware/app/intel_access/medium_analyzer_test_results.json"
    with open(results_file, 'w') as f:
        json.dump({
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "analyzers_tested": list(TEST_ANALYZERS.keys()),
            "test_files": test_files,
            "results": all_results,
            "summary": {
                "total_tests": total_tests,
                "successful_tests": successful_tests,
                "failed_tests": total_tests - successful_tests
            }
        }, f, indent=2, default=str)

    print(f"\n📄 Detailed results saved to: {results_file}")

    print("\n" + "=" * 70)
    print("TESTING COMPLETE")
    print("=" * 70)

if __name__ == "__main__":
    main()