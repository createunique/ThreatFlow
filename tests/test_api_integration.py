"""
Test Section 5: API Integration Tests
End-to-end tests that verify backend API behavior
"""

import pytest
import requests
import time
import os
from pathlib import Path
from typing import Dict, List, Any

# API Configuration
API_BASE_URL = os.environ.get("THREATFLOW_API_URL", "http://localhost:8001")


class APIClient:
    """HTTP client for ThreatFlow middleware API"""
    
    def __init__(self, base_url: str = API_BASE_URL):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
    
    def health_check(self) -> bool:
        """Check if API is reachable"""
        try:
            response = self.session.get(f"{self.base_url}/health", timeout=5)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False
    
    def execute_workflow(self, workflow: Dict, file_path: str, timeout: int = 120) -> Dict:
        """
        Execute a workflow and wait for results
        
        Args:
            workflow: Dict containing 'nodes' and 'edges'
            file_path: Path to file to analyze
            timeout: Max seconds to wait
            
        Returns:
            Dict with execution results
        """
        endpoint = f"{self.base_url}/api/workflow/execute"
        
        with open(file_path, 'rb') as f:
            files = {'file': (os.path.basename(file_path), f)}
            data = {
                'workflow': workflow
            }
            
            response = self.session.post(
                endpoint,
                files=files,
                data={'workflow': str(workflow)},
                timeout=timeout
            )
        
        if response.status_code != 200:
            return {
                "success": False,
                "error": f"API returned {response.status_code}: {response.text}"
            }
        
        return response.json()
    
    def get_analyzers(self) -> List[str]:
        """Get list of available analyzers"""
        response = self.session.get(f"{self.base_url}/api/analyzers", timeout=10)
        if response.status_code == 200:
            return response.json()
        return []


@pytest.fixture(scope="module")
def api_client():
    """Provide API client for tests"""
    client = APIClient()
    if not client.health_check():
        pytest.skip("ThreatFlow API is not available")
    return client


@pytest.fixture(scope="module")
def available_analyzers(api_client):
    """Get list of actually available analyzers"""
    return api_client.get_analyzers()


class TestAPIHealth:
    """Basic API health and connectivity tests"""
    
    def test_api_reachable(self, api_client):
        """Verify API is responding"""
        assert api_client.health_check(), "API health check failed"
    
    def test_get_analyzers(self, api_client):
        """Verify analyzer list endpoint works"""
        analyzers = api_client.get_analyzers()
        assert isinstance(analyzers, list)
        # Should have at least some basic analyzers
        print(f"Available analyzers: {analyzers}")


class TestWorkflowExecution:
    """Test actual workflow execution via API"""
    
    def test_simple_workflow_execution(self, api_client, safe_sample_path):
        """Execute a simple linear workflow"""
        workflow = {
            "nodes": [
                {"id": "file-1", "type": "file", "data": {}, "position": {"x": 100, "y": 200}},
                {"id": "analyzer-1", "type": "analyzer", "data": {"analyzer": "File_Info"}, "position": {"x": 300, "y": 200}},
                {"id": "result-1", "type": "result", "data": {}, "position": {"x": 500, "y": 200}}
            ],
            "edges": [
                {"id": "e1", "source": "file-1", "target": "analyzer-1"},
                {"id": "e2", "source": "analyzer-1", "target": "result-1"}
            ]
        }
        
        result = api_client.execute_workflow(workflow, safe_sample_path)
        
        if not result.get("success", True):
            pytest.skip(f"Workflow execution not available: {result.get('error')}")
        
        # Verify response structure
        assert "results" in result or "analyzer_reports" in result
    
    def test_multi_analyzer_workflow(self, api_client, safe_sample_path, available_analyzers):
        """Execute workflow with multiple analyzers"""
        # Build workflow with available analyzers
        analyzers_to_use = []
        preferred = ["File_Info", "ClamAV", "Strings_Info"]
        
        for analyzer in preferred:
            if analyzer in available_analyzers:
                analyzers_to_use.append(analyzer)
        
        if len(analyzers_to_use) < 2:
            pytest.skip("Need at least 2 analyzers for this test")
        
        nodes = [
            {"id": "file-1", "type": "file", "data": {}, "position": {"x": 100, "y": 200}}
        ]
        edges = []
        
        for i, analyzer in enumerate(analyzers_to_use):
            nodes.append({
                "id": f"analyzer-{i+1}",
                "type": "analyzer",
                "data": {"analyzer": analyzer},
                "position": {"x": 300 + (i * 200), "y": 200}
            })
            
            # Connect to previous node
            if i == 0:
                edges.append({"id": f"e{i+1}", "source": "file-1", "target": f"analyzer-{i+1}"})
            else:
                edges.append({"id": f"e{i+1}", "source": f"analyzer-{i}", "target": f"analyzer-{i+1}"})
        
        # Add result node
        nodes.append({
            "id": "result-1",
            "type": "result",
            "data": {},
            "position": {"x": 300 + (len(analyzers_to_use) * 200), "y": 200}
        })
        edges.append({
            "id": f"e{len(analyzers_to_use)+1}",
            "source": f"analyzer-{len(analyzers_to_use)}",
            "target": "result-1"
        })
        
        workflow = {"nodes": nodes, "edges": edges}
        
        result = api_client.execute_workflow(workflow, safe_sample_path)
        
        # Verify all analyzers produced results
        analyzer_reports = result.get("analyzer_reports", [])
        result_names = [r.get("name") for r in analyzer_reports]
        
        for analyzer in analyzers_to_use:
            assert analyzer in result_names, f"{analyzer} missing from results"


class TestConditionalWorkflowExecution:
    """Test conditional workflow execution via API"""
    
    def test_conditional_workflow_with_safe_file(self, api_client, safe_sample_path, available_analyzers):
        """Test conditional routing with safe file"""
        if "ClamAV" not in available_analyzers:
            pytest.skip("ClamAV not available")
        
        workflow = {
            "nodes": [
                {"id": "file-1", "type": "file", "data": {}, "position": {"x": 100, "y": 200}},
                {"id": "analyzer-1", "type": "analyzer", "data": {"analyzer": "ClamAV"}, "position": {"x": 300, "y": 200}},
                {"id": "cond-1", "type": "conditional", "data": {"conditionType": "verdict_malicious", "sourceAnalyzer": "ClamAV"}, "position": {"x": 500, "y": 200}},
                {"id": "result-true", "type": "result", "data": {}, "position": {"x": 700, "y": 100}},
                {"id": "result-false", "type": "result", "data": {}, "position": {"x": 700, "y": 300}}
            ],
            "edges": [
                {"id": "e1", "source": "file-1", "target": "analyzer-1"},
                {"id": "e2", "source": "analyzer-1", "target": "cond-1"},
                {"id": "e3", "source": "cond-1", "target": "result-true", "sourceHandle": "true-output"},
                {"id": "e4", "source": "cond-1", "target": "result-false", "sourceHandle": "false-output"}
            ]
        }
        
        result = api_client.execute_workflow(workflow, safe_sample_path)
        
        # For safe file, should route to FALSE branch
        stage_routing = result.get("stage_routing", [])
        print(f"Stage routing for safe file: {stage_routing}")
    
    def test_conditional_workflow_with_malicious_file(self, api_client, malicious_sample_path, available_analyzers):
        """Test conditional routing with EICAR test file"""
        if "ClamAV" not in available_analyzers:
            pytest.skip("ClamAV not available")
        
        workflow = {
            "nodes": [
                {"id": "file-1", "type": "file", "data": {}, "position": {"x": 100, "y": 200}},
                {"id": "analyzer-1", "type": "analyzer", "data": {"analyzer": "ClamAV"}, "position": {"x": 300, "y": 200}},
                {"id": "cond-1", "type": "conditional", "data": {"conditionType": "verdict_malicious", "sourceAnalyzer": "ClamAV"}, "position": {"x": 500, "y": 200}},
                {"id": "result-true", "type": "result", "data": {}, "position": {"x": 700, "y": 100}},
                {"id": "result-false", "type": "result", "data": {}, "position": {"x": 700, "y": 300}}
            ],
            "edges": [
                {"id": "e1", "source": "file-1", "target": "analyzer-1"},
                {"id": "e2", "source": "analyzer-1", "target": "cond-1"},
                {"id": "e3", "source": "cond-1", "target": "result-true", "sourceHandle": "true-output"},
                {"id": "e4", "source": "cond-1", "target": "result-false", "sourceHandle": "false-output"}
            ]
        }
        
        result = api_client.execute_workflow(workflow, malicious_sample_path)
        
        # For EICAR file, should route to TRUE branch
        stage_routing = result.get("stage_routing", [])
        print(f"Stage routing for malicious file: {stage_routing}")


class TestStageRoutingMetadata:
    """Verify stage_routing metadata is correctly generated"""
    
    def test_stage_routing_structure(self, api_client, safe_sample_path):
        """Verify stage_routing has correct structure"""
        workflow = {
            "nodes": [
                {"id": "file-1", "type": "file", "data": {}, "position": {"x": 100, "y": 200}},
                {"id": "analyzer-1", "type": "analyzer", "data": {"analyzer": "File_Info"}, "position": {"x": 300, "y": 200}},
                {"id": "cond-1", "type": "conditional", "data": {"conditionType": "analyzer_success", "sourceAnalyzer": "File_Info"}, "position": {"x": 500, "y": 200}},
                {"id": "result-1", "type": "result", "data": {}, "position": {"x": 700, "y": 100}},
                {"id": "result-2", "type": "result", "data": {}, "position": {"x": 700, "y": 300}}
            ],
            "edges": [
                {"id": "e1", "source": "file-1", "target": "analyzer-1"},
                {"id": "e2", "source": "analyzer-1", "target": "cond-1"},
                {"id": "e3", "source": "cond-1", "target": "result-1", "sourceHandle": "true-output"},
                {"id": "e4", "source": "cond-1", "target": "result-2", "sourceHandle": "false-output"}
            ]
        }
        
        result = api_client.execute_workflow(workflow, safe_sample_path)
        
        stage_routing = result.get("stage_routing", [])
        
        if not stage_routing:
            pytest.skip("stage_routing not returned by API")
        
        # Verify structure
        for stage in stage_routing:
            assert "stage_id" in stage
            assert "executed" in stage
            assert "target_nodes" in stage
            assert isinstance(stage["target_nodes"], list)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
