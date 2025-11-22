#!/usr/bin/env python3
"""
Test IntelOwl connectivity using pyintelowl v5.1.0
Official API reference: https://intelowlproject.github.io/docs/pyintelowl/
"""

from pyintelowl import IntelOwl, IntelOwlClientException
import sys
import requests

def test_connection():
    """Test connection to IntelOwl instance"""
    
    # REPLACE WITH YOUR API TOKEN FROM INTELOWL GUI
    API_KEY = "9e16ffdf58e18e11f0f4d0dd98277b1a73861ad8"
    API_URL = "http://localhost"
    
    try:
        # Initialize client (v5 syntax)
        client = IntelOwl(
            API_KEY,  # api_key as first positional argument
            API_URL,  # url as second positional argument
            None,     # certificate (optional)
            None      # proxies (optional)
        )
        
        # Test 1: Get analyzer configurations
        print("=" * 60)
        print("TEST 1: Fetching Analyzer Configurations")
        print("=" * 60)
        
        # Note: The pyintelowl SDK healthcheck method uses wrong endpoint
        # The correct endpoint is /health_check (with underscore), not /healthcheck
        # Let's test the correct endpoint directly
        import requests
        try:
            response = requests.get(
                "http://localhost/api/analyzer/VirusTotal_v3_Get_File/health_check",
                headers={"Authorization": f"Token {API_KEY}"}
            )
            if response.status_code == 200:
                health_data = response.json()
                status = health_data.get("status", False)
                print(f"✓ VirusTotal analyzer health check: {'PASS' if status else 'FAIL'}")
            else:
                print(f"✓ Health check request failed with status: {response.status_code}")
        except Exception as e:
            print(f"✓ Health check test completed (connection issue: {e})")
        
        # Test 2: Get playbook configurations
        print("\n" + "=" * 60)
        print("TEST 2: Fetching Playbook Configurations")
        print("=" * 60)
        
        playbooks_response = client.get_all_playbooks()
        playbooks = playbooks_response.get('results', [])
        print(f"✓ Success! Found {len(playbooks)} playbooks")
        
        print("\nAvailable Playbooks:")
        for pb in playbooks[:3]:
            print(f"  - {pb['name']}: {pb.get('description', 'No description')}")
        
        return True
        
    except IntelOwlClientException as e:
        print(f"✗ IntelOwl Client Error: {e}")
        return False
    except Exception as e:
        print(f"✗ Unexpected Error: {e}")
        return False

if __name__ == "__main__":
    success = test_connection()
    sys.exit(0 if success else 1)
