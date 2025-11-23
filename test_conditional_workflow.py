#!/usr/bin/env python3
"""
Test script for conditional workflow with sample files
"""

import requests
import json
import time
import os

API_BASE = "http://localhost:8030"

def test_file_with_workflow(file_path, expected_malicious=False):
    """Test a file with the conditional workflow"""
    
    print(f"\n{'='*60}")
    print(f"Testing: {os.path.basename(file_path)}")
    print(f"Expected malicious: {expected_malicious}")
    print(f"{'='*60}")
    
    # Load workflow
    with open("test_workflow_reliable.json", "r") as f:
        workflow_data = json.load(f)
    
    # Prepare file
    with open(file_path, "rb") as f:
        files = {"file": (os.path.basename(file_path), f, "application/octet-stream")}
        data = {"workflow_json": json.dumps(workflow_data)}
        
        # Submit workflow
        print("Submitting workflow...")
        response = requests.post(f"{API_BASE}/api/execute", files=files, data=data)
        
        if response.status_code != 200:
            print(f"❌ Submission failed: {response.status_code}")
            print(response.text)
            return
        
        result = response.json()
        print(f"✅ Submission successful: {result.get('message', '')}")
        
        # Get job IDs (conditional workflows return multiple)
        job_ids = result.get("job_ids", [])
        if not job_ids:
            print("❌ No job IDs returned")
            return
        
        print(f"Job IDs: {job_ids}")
        
        # Wait for all jobs to complete
        all_analyzer_reports = []
        for job_id in job_ids:
            print(f"Waiting for job {job_id}...")
            max_attempts = 30
            for attempt in range(max_attempts):
                time.sleep(2)
                
                status_response = requests.get(f"{API_BASE}/api/status/{job_id}")
                if status_response.status_code != 200:
                    print(f"❌ Status check failed for job {job_id}: {status_response.status_code}")
                    continue
                    
                status_data = status_response.json()
                current_status = status_data.get("status", "unknown")
                
                if status_data.get("results"):
                    # Analysis complete
                    results = status_data["results"]
                    analyzer_reports = results.get("analyzer_reports", [])
                    all_analyzer_reports.extend(analyzer_reports)
                    print(f"✅ Job {job_id} completed with {len(analyzer_reports)} analyzers")
                    break
        
        print(f"✅ Analysis complete!")
        print(f"Total analyzers run: {len(all_analyzer_reports)}")
        
        # Check which analyzers ran
        analyzers_run = [r["name"] for r in all_analyzer_reports]
        print(f"Analyzers executed: {analyzers_run}")
        
        # Check File_Info result
        fileinfo_report = next((r for r in all_analyzer_reports if r["name"] == "File_Info"), None)
        if fileinfo_report:
            status = fileinfo_report.get("status")
            is_success = status == "SUCCESS"
            print(f"File_Info status: {status} -> {is_success}")
            
            if is_success:
                print("✅ File_Info succeeded")
            else:
                print("❌ File_Info failed")
        
        # Show conditional execution
        if "Strings_Info" in analyzers_run and "Yara" in analyzers_run:
            print("✅ Conditional TRUE: Deep analysis executed (Strings + YARA)")
        elif "PE_Info" in analyzers_run:
            print("✅ Conditional FALSE: PE analysis executed")
        else:
            print("❓ Conditional logic unclear")
        
        return True
        
        print("❌ Analysis timed out")
        return False

def main():
    """Test all sample files"""
    
    if not os.path.exists("test_workflow_reliable.json"):
        print("❌ test_workflow_reliable.json not found")
        return
    
    # Test files - all should trigger File_Info success
    test_cases = [
        ("test_samples/eicar_variant.txt", True),      # Should succeed
        ("test_samples/suspicious_strings.txt", True), # Should succeed
        ("test_samples/fake_malware.bat", True),       # Should succeed
        ("test_samples/simple_webshell.php", True),    # Should succeed
    ]
    
    print("Testing Conditional Workflow Logic")
    print("Workflow: File_Info → Conditional → (Success: Strings+YARA) OR (Fail: PE_Info)")
    
    for file_path, expected_malicious in test_cases:
        if os.path.exists(file_path):
            test_file_with_workflow(file_path, expected_malicious)
        else:
            print(f"❌ Test file not found: {file_path}")
    
    print(f"\n{'='*60}")
    print("Testing complete!")
    print("Check the results above to verify conditional logic is working.")

if __name__ == "__main__":
    main()
