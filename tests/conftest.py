"""
ThreatFlow Test Configuration
Provides fixtures and utilities for comprehensive workflow testing
"""

import pytest
import requests
import json
import os
import time
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass

# Configuration
MIDDLEWARE_URL = os.getenv("MIDDLEWARE_URL", "http://localhost:8030")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

# Test sample paths
TEST_SAMPLES_DIR = Path(__file__).parent.parent / "testing_responses" / "Malware safe Malware samples"
SAFE_SAMPLES_DIR = TEST_SAMPLES_DIR / "safe"
MALICIOUS_SAMPLES_DIR = TEST_SAMPLES_DIR / "malicious"


@dataclass
class WorkflowResult:
    """Result of a workflow execution test"""
    success: bool
    job_id: Optional[int]
    has_conditionals: bool
    executed_stages: List[int]
    skipped_stages: List[int]
    stage_routing: List[Dict]
    results: Optional[Dict]
    error: Optional[str]
    
    def get_result_node_analyzers(self, result_node_id: str) -> List[str]:
        """
        Get the list of analyzer names that should be displayed in a result node.
        Uses stage_routing to determine which analyzers were routed to which nodes.
        
        Args:
            result_node_id: The ID of the result node
            
        Returns:
            List of analyzer names that were routed to this result node
        """
        analyzer_names = []
        
        # Check stage_routing for analyzers routed to this result node
        for stage in self.stage_routing:
            target_nodes = stage.get('target_nodes', [])
            if result_node_id in target_nodes:
                analyzers = stage.get('analyzers', [])
                analyzer_names.extend(analyzers)
        
        # Also check results if available
        if self.results and 'analyzer_reports' in self.results:
            reports = self.results['analyzer_reports']
            if isinstance(reports, list):
                for report in reports:
                    analyzer_name = report.get('name')
                    if analyzer_name and analyzer_name not in analyzer_names:
                        analyzer_names.append(analyzer_name)
        
        return analyzer_names


class WorkflowBuilder:
    """
    Helper class to build workflow node/edge structures
    Mimics how the frontend creates workflows
    """
    
    def __init__(self):
        self.nodes = []
        self.edges = []
        self.node_counter = 0
        self.edge_counter = 0
    
    def add_file_node(self, x: float = 100, y: float = 200) -> str:
        """Add a file input node"""
        node_id = f"file-{self.node_counter}"
        self.node_counter += 1
        
        self.nodes.append({
            "id": node_id,
            "type": "file",
            "position": {"x": x, "y": y},
            "data": {
                "label": "File Upload",
                "file": None,
                "fileName": "",
                "fileSize": 0
            }
        })
        return node_id
    
    def add_analyzer_node(self, analyzer: str, x: float = 300, y: float = 200) -> str:
        """Add an analyzer node"""
        node_id = f"analyzer-{self.node_counter}"
        self.node_counter += 1
        
        self.nodes.append({
            "id": node_id,
            "type": "analyzer",
            "position": {"x": x, "y": y},
            "data": {
                "label": "Analyzer",
                "analyzer": analyzer,
                "analyzerType": "file",
                "description": f"{analyzer} analyzer"
            }
        })
        return node_id
    
    def add_conditional_node(
        self,
        condition_type: str,
        source_analyzer: str,
        field_path: str = None,
        expected_value: Any = None,
        x: float = 500,
        y: float = 200
    ) -> str:
        """Add a conditional branching node"""
        node_id = f"conditional-{self.node_counter}"
        self.node_counter += 1
        
        data = {
            "label": "Conditional",
            "conditionType": condition_type,
            "sourceAnalyzer": source_analyzer
        }
        
        if field_path:
            data["fieldPath"] = field_path
        if expected_value is not None:
            data["expectedValue"] = expected_value
        
        self.nodes.append({
            "id": node_id,
            "type": "conditional",
            "position": {"x": x, "y": y},
            "data": data
        })
        return node_id
    
    def add_result_node(self, x: float = 700, y: float = 200, label: str = "Results") -> str:
        """Add a result display node"""
        node_id = f"result-{self.node_counter}"
        self.node_counter += 1
        
        self.nodes.append({
            "id": node_id,
            "type": "result",
            "position": {"x": x, "y": y},
            "data": {
                "label": label,
                "jobId": None,
                "status": "idle",
                "results": None,
                "error": None
            }
        })
        return node_id
    
    def connect(self, source_id: str, target_id: str, source_handle: str = None, target_handle: str = None) -> str:
        """Connect two nodes with an edge"""
        edge_id = f"edge-{self.edge_counter}"
        self.edge_counter += 1
        
        edge = {
            "id": edge_id,
            "source": source_id,
            "target": target_id
        }
        
        if source_handle:
            edge["sourceHandle"] = source_handle
        if target_handle:
            edge["targetHandle"] = target_handle
        
        self.edges.append(edge)
        return edge_id
    
    def get_workflow(self) -> Tuple[List[Dict], List[Dict]]:
        """Get the workflow nodes and edges"""
        return self.nodes, self.edges
    
    def reset(self):
        """Reset the builder"""
        self.nodes = []
        self.edges = []
        self.node_counter = 0
        self.edge_counter = 0


class WorkflowTester:
    """
    Executes workflows against the middleware and validates results
    """
    
    def __init__(self, middleware_url: str = MIDDLEWARE_URL):
        self.middleware_url = middleware_url
        self.session = requests.Session()
    
    def execute_workflow(
        self,
        nodes: List[Dict],
        edges: List[Dict],
        file_path: str,
        timeout: int = 300,
        poll_interval: int = 5
    ) -> WorkflowResult:
        """
        Execute a workflow and wait for completion
        
        Args:
            nodes: Workflow nodes
            edges: Workflow edges
            file_path: Path to the file to analyze
            timeout: Maximum wait time in seconds
            poll_interval: Time between status checks
        
        Returns:
            WorkflowResult with execution details
        """
        try:
            # Read file
            if not os.path.exists(file_path):
                return WorkflowResult(
                    success=False,
                    job_id=None,
                    has_conditionals=False,
                    executed_stages=[],
                    skipped_stages=[],
                    stage_routing=[],
                    results=None,
                    error=f"File not found: {file_path}"
                )
            
            with open(file_path, 'rb') as f:
                file_content = f.read()
            
            file_name = os.path.basename(file_path)
            
            # Prepare request
            files = {'file': (file_name, file_content, 'application/octet-stream')}
            workflow_json = json.dumps({'nodes': nodes, 'edges': edges})
            data = {'workflow_json': workflow_json}
            
            # Submit workflow
            response = self.session.post(
                f"{self.middleware_url}/api/execute",
                files=files,
                data=data,
                timeout=30
            )
            
            if response.status_code != 200:
                return WorkflowResult(
                    success=False,
                    job_id=None,
                    has_conditionals=False,
                    executed_stages=[],
                    skipped_stages=[],
                    stage_routing=[],
                    results=None,
                    error=f"Submission failed: {response.status_code} - {response.text}"
                )
            
            result = response.json()
            job_id = result.get('job_id') or (result.get('job_ids') and result['job_ids'][0])
            has_conditionals = result.get('has_conditionals', False)
            stage_routing = result.get('stage_routing', [])
            
            if not job_id:
                return WorkflowResult(
                    success=False,
                    job_id=None,
                    has_conditionals=has_conditionals,
                    executed_stages=result.get('executed_stages', []),
                    skipped_stages=result.get('skipped_stages', []),
                    stage_routing=stage_routing,
                    results=None,
                    error="No job ID in response"
                )
            
            # Poll for completion
            max_attempts = timeout // poll_interval
            for attempt in range(max_attempts):
                try:
                    status_response = self.session.get(
                        f"{self.middleware_url}/api/status/{job_id}",
                        timeout=10
                    )
                    
                    if status_response.status_code == 200:
                        status_data = status_response.json()
                        status = status_data.get('status')
                        
                        if status in ['reported_without_fails', 'reported_with_fails']:
                            return WorkflowResult(
                                success=True,
                                job_id=job_id,
                                has_conditionals=has_conditionals,
                                executed_stages=result.get('executed_stages', []),
                                skipped_stages=result.get('skipped_stages', []),
                                stage_routing=stage_routing,
                                results=status_data.get('results'),
                                error=None
                            )
                        elif status == 'failed':
                            return WorkflowResult(
                                success=False,
                                job_id=job_id,
                                has_conditionals=has_conditionals,
                                executed_stages=result.get('executed_stages', []),
                                skipped_stages=result.get('skipped_stages', []),
                                stage_routing=stage_routing,
                                results=status_data.get('results'),
                                error="Analysis failed"
                            )
                except Exception as e:
                    pass  # Continue polling
                
                time.sleep(poll_interval)
            
            return WorkflowResult(
                success=False,
                job_id=job_id,
                has_conditionals=has_conditionals,
                executed_stages=result.get('executed_stages', []),
                skipped_stages=result.get('skipped_stages', []),
                stage_routing=stage_routing,
                results=None,
                error=f"Timeout after {timeout}s"
            )
            
        except Exception as e:
            return WorkflowResult(
                success=False,
                job_id=None,
                has_conditionals=False,
                executed_stages=[],
                skipped_stages=[],
                stage_routing=[],
                results=None,
                error=str(e)
            )
    
    def health_check(self) -> bool:
        """Check if middleware is running"""
        try:
            response = self.session.get(f"{self.middleware_url}/health/", timeout=5)
            return response.status_code == 200
        except:
            return False


# Pytest fixtures

@pytest.fixture(scope="session")
def workflow_tester():
    """Provide a workflow tester instance"""
    tester = WorkflowTester()
    if not tester.health_check():
        pytest.skip("Middleware not available")
    return tester


@pytest.fixture
def workflow_builder():
    """Provide a fresh workflow builder"""
    return WorkflowBuilder()


@pytest.fixture
def safe_sample_path():
    """Provide path to a safe test file"""
    path = SAFE_SAMPLES_DIR / "test.txt"
    if not path.exists():
        # Create a simple test file
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("This is a safe test file.")
    return str(path)


@pytest.fixture
def malicious_sample_path():
    """Provide path to an EICAR test file"""
    path = MALICIOUS_SAMPLES_DIR / "eicar.com"
    if not path.exists():
        # Create EICAR test file
        path.parent.mkdir(parents=True, exist_ok=True)
        eicar = r"X5O!P%@AP[4\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*"
        path.write_text(eicar)
    return str(path)


@pytest.fixture
def pdf_safe_path():
    """Path to safe PDF sample"""
    return str(SAFE_SAMPLES_DIR / "safe.pdf")


@pytest.fixture
def pdf_malicious_path():
    """Path to malicious PDF sample"""
    return str(MALICIOUS_SAMPLES_DIR / "malicious.pdf")
