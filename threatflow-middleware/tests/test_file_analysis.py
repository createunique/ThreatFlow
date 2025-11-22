#!/usr/bin/env python3
"""
Test file analysis submission to IntelOwl
Uses EICAR test file (safe malware signature)
"""

from pyintelowl import IntelOwl, IntelOwlClientException
import time
import os

# EICAR test string (safe malware signature)
EICAR_STRING = b'X5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*'

def test_file_analysis():
    """Submit EICAR file and retrieve results"""
    
    API_KEY = "9e16ffdf58e18e11f0f4d0dd98277b1a73861ad8"
    API_URL = "http://localhost"
    
    try:
        client = IntelOwl(API_KEY, API_URL, None, None)
        
        # Create EICAR test file
        test_file_path = "/tmp/eicar_test.txt"
        with open(test_file_path, "wb") as f:
            f.write(EICAR_STRING)
        
        print("=" * 60)
        print("Submitting EICAR test file to IntelOwl")
        print("=" * 60)
        
        # Submit file analysis (v5 API)
        # Read file content as bytes
        with open(test_file_path, "rb") as f:
            file_binary = f.read()
        
        result = client.send_file_analysis_request(
            filename="eicar_test.txt",
            binary=file_binary,
            analyzers_requested=["File_Info", "ClamAV", "VirusTotal_v3_Get_File"],
            tlp="CLEAR",
            runtime_configuration={},
            tags_labels=["test"]
        )
        
        job_id = result["job_id"]
        print(f"✓ Analysis submitted! Job ID: {job_id}")
        
        # Poll for results (max 2 minutes)
        print("\nWaiting for analysis to complete...")
        max_attempts = 24
        attempt = 0
        
        while attempt < max_attempts:
            attempt += 1
            time.sleep(5)
            
            # Get job status
            job = client.get_job_by_id(job_id)
            status = job["status"]
            
            print(f"Attempt {attempt}/24 - Status: {status}")
            
            if status in ["reported_without_fails", "reported_with_fails"]:
                print(f"\n✓ Analysis Complete!")
                print(f"Status: {status}")
                print(f"Analyzers ran: {len(job.get('analyzer_reports', []))}")
                
                # Display analyzer results
                for report in job.get("analyzer_reports", []):
                    analyzer_name = report["name"]
                    success = report["status"] == "SUCCESS"
                    verdict = report.get("report", {}).get("verdict", "N/A")
                    print(f"  - {analyzer_name}: {'✓' if success else '✗'} (Verdict: {verdict})")
                
                # Cleanup
                os.remove(test_file_path)
                return True
        
        print("✗ Timeout: Analysis took too long")
        return False
        
    except IntelOwlClientException as e:
        print(f"✗ Error: {e}")
        return False

if __name__ == "__main__":
    import sys
    sys.exit(0 if test_file_analysis() else 1)
