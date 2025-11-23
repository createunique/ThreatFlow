"""
Comprehensive Test Suite for ThreatFlow Workflow Patterns
Tests all workflow combinations: linear, sequential, parallel, conditional
Author: Senior Architect (40 years experience)
Date: 2025-11-23
"""

import pytest
import json
from typing import Dict, List, Any
from unittest.mock import Mock, patch, AsyncMock
from app.services.workflow_parser import WorkflowParser
from app.services.intelowl_service import IntelOwlService
from app.models.workflow import WorkflowNode, WorkflowEdge, NodeType, ConditionType


class TestWorkflowPatterns:
    """Test suite for all workflow execution patterns"""
    
    def create_node(self, id: str, type: str, data: Dict[str, Any]) -> WorkflowNode:
        """Helper to create Pydantic WorkflowNode"""
        return WorkflowNode(
            id=id,
            type=NodeType(type),
            position={"x": 0, "y": 0},
            data=data
        )
    
    def create_edge(self, source: str, target: str, sourceHandle: str = None) -> WorkflowEdge:
        """Helper to create Pydantic WorkflowEdge"""
        edge_data = {
            "id": f"{source}-{target}",
            "source": source,
            "target": target
        }
        if sourceHandle:
            edge_data["sourceHandle"] = sourceHandle
        return WorkflowEdge(**edge_data)
    
    @pytest.fixture
    def parser(self):
        """Create workflow parser instance"""
        return WorkflowParser()
    
    @pytest.fixture
    def mock_intel_service(self):
        """Mock IntelOwl service"""
        service = Mock(spec=IntelOwlService)
        service.execute_workflow_with_conditionals = AsyncMock()
        return service
    
    # ==================== PATTERN 1: Simple Linear ====================
    
    def test_pattern_1_simple_linear(self, parser):
        """
        Test: File → Analyzer → Result
        Expected: 1 stage, 1 analyzer, 1 target result node
        """
        nodes = [
            self.create_node("file-1", "file", {"label": "File"}),
            self.create_node("analyzer-1", "analyzer", {"analyzer": "ClamAV"}),
            self.create_node("result-1", "result", {"label": "Result"})
        ]
        edges = [
            self.create_edge("file-1", "analyzer-1"),
            self.create_edge("analyzer-1", "result-1")
        ]
        
        parsed = parser.parse(nodes, edges)
        
        # Assertions
        assert parsed["has_conditionals"] == False
        assert len(parsed["stages"]) == 1
        
        stage_0 = parsed["stages"][0]
        assert stage_0["stage_id"] == 0
        assert stage_0["analyzers"] == ["ClamAV"]
        assert stage_0["depends_on"] is None
        assert "result-1" in stage_0.get("target_nodes", [])
        
        print("✅ PATTERN 1 (Simple Linear): PASSED")
    
    # ==================== PATTERN 2: Sequential Analyzers ====================
    
    def test_pattern_2_sequential_analyzers(self, parser):
        """
        Test: File → Analyzer1 → Analyzer2 → Result
        Expected: 2 stages, chained execution
        """
        workflow = {
            "nodes": [
                {"id": "file-1", "type": "file", "data": {}},
                {"id": "analyzer-1", "type": "analyzer", "data": {"analyzer": "ClamAV"}},
                {"id": "analyzer-2", "type": "analyzer", "data": {"analyzer": "PE_Info"}},
                {"id": "result-1", "type": "result", "data": {}}
            ],
            "edges": [
                {"source": "file-1", "target": "analyzer-1"},
                {"source": "analyzer-1", "target": "analyzer-2"},  # Chained
                {"source": "analyzer-2", "target": "result-1"}
            ]
        }
        
        parsed = parser.parse(workflow["nodes"], workflow["edges"])
        
        # Assertions
        assert len(parsed["stages"]) == 2
        
        stage_0 = parsed["stages"][0]
        assert stage_0["analyzers"] == ["ClamAV"]
        assert stage_0["depends_on"] is None
        
        stage_1 = parsed["stages"][1]
        assert stage_1["analyzers"] == ["PE_Info"]
        assert stage_1["depends_on"] is not None  # Depends on stage 0
        
        print("✅ PATTERN 2 (Sequential): PASSED")
    
    # ==================== PATTERN 3: Parallel Analyzers ====================
    
    def test_pattern_3_parallel_analyzers(self, parser):
        """
        Test: File → [Analyzer1 + Analyzer2] → Result
        Expected: 1 stage with multiple analyzers
        """
        workflow = {
            "nodes": [
                {"id": "file-1", "type": "file", "data": {}},
                {"id": "analyzer-1", "type": "analyzer", "data": {"analyzer": "ClamAV"}},
                {"id": "analyzer-2", "type": "analyzer", "data": {"analyzer": "PE_Info"}},
                {"id": "result-1", "type": "result", "data": {}}
            ],
            "edges": [
                {"source": "file-1", "target": "analyzer-1"},
                {"source": "file-1", "target": "analyzer-2"},  # Both from file
                {"source": "analyzer-1", "target": "result-1"},
                {"source": "analyzer-2", "target": "result-1"}
            ]
        }
        
        parsed = parser.parse(workflow["nodes"], workflow["edges"])
        
        # Assertions
        assert len(parsed["stages"]) == 1
        
        stage_0 = parsed["stages"][0]
        assert "ClamAV" in stage_0["analyzers"]
        assert "PE_Info" in stage_0["analyzers"]
        assert len(stage_0["analyzers"]) == 2
        
        print("✅ PATTERN 3 (Parallel): PASSED")
    
    # ==================== PATTERN 4: Conditional TRUE Branch ====================
    
    def test_pattern_4_conditional_true_branch(self, parser):
        """
        Test: File → Analyzer → Conditional → Result (TRUE branch)
        Expected: 2 stages (analyzer + true branch), false branch skipped
        """
        workflow = {
            "nodes": [
                {"id": "file-1", "type": "file", "data": {}},
                {"id": "analyzer-1", "type": "analyzer", "data": {"analyzer": "ClamAV"}},
                {"id": "conditional-1", "type": "conditional", "data": {
                    "conditionType": "verdict_malicious",
                    "sourceAnalyzer": "ClamAV"
                }},
                {"id": "result-true", "type": "result", "data": {}},
                {"id": "result-false", "type": "result", "data": {}}
            ],
            "edges": [
                {"source": "file-1", "target": "analyzer-1"},
                {"source": "analyzer-1", "target": "conditional-1"},
                {"source": "conditional-1", "target": "result-true", "sourceHandle": "true-output"},
                {"source": "conditional-1", "target": "result-false", "sourceHandle": "false-output"}
            ]
        }
        
        parsed = parser.parse(workflow["nodes"], workflow["edges"])
        
        # Assertions
        assert parsed["has_conditionals"] == True
        assert len(parsed["stages"]) == 3  # Initial + TRUE + FALSE
        
        # Stage 0: Initial analyzer
        stage_0 = parsed["stages"][0]
        assert stage_0["analyzers"] == ["ClamAV"]
        assert stage_0["condition"] is None
        
        # Stage 1: TRUE branch
        stage_1 = parsed["stages"][1]
        assert stage_1["condition"]["type"] == "verdict_malicious"
        assert stage_1["condition"]["source_analyzer"] == "ClamAV"
        assert "result-true" in stage_1["target_nodes"]
        
        # Stage 2: FALSE branch
        stage_2 = parsed["stages"][2]
        assert stage_2["condition"].get("negate") == True
        assert "result-false" in stage_2["target_nodes"]
        
        print("✅ PATTERN 4 (Conditional): PASSED")
    
    # ==================== PATTERN 5: Fan-Out to Multiple Results ====================
    
    def test_pattern_5_fan_out(self, parser):
        """
        Test: File → Analyzer → [Result1 + Result2]
        Expected: 1 stage with multiple target nodes
        """
        workflow = {
            "nodes": [
                {"id": "file-1", "type": "file", "data": {}},
                {"id": "analyzer-1", "type": "analyzer", "data": {"analyzer": "ClamAV"}},
                {"id": "result-1", "type": "result", "data": {}},
                {"id": "result-2", "type": "result", "data": {}}
            ],
            "edges": [
                {"source": "file-1", "target": "analyzer-1"},
                {"source": "analyzer-1", "target": "result-1"},
                {"source": "analyzer-1", "target": "result-2"}
            ]
        }
        
        parsed = parser.parse(workflow["nodes"], workflow["edges"])
        
        # Assertions
        assert len(parsed["stages"]) == 1
        
        stage_0 = parsed["stages"][0]
        assert "result-1" in stage_0["target_nodes"]
        assert "result-2" in stage_0["target_nodes"]
        
        print("✅ PATTERN 5 (Fan-Out): PASSED")
    
    # ==================== EDGE CASES ====================
    
    def test_edge_case_empty_workflow(self, parser):
        """Test: Empty workflow should fail gracefully"""
        with pytest.raises(ValueError, match="No file node found"):
            parser.parse([], [])
    
    def test_edge_case_no_analyzers(self, parser):
        """Test: File → Result (no analyzers) should fail"""
        workflow = {
            "nodes": [
                {"id": "file-1", "type": "file", "data": {}},
                {"id": "result-1", "type": "result", "data": {}}
            ],
            "edges": [
                {"source": "file-1", "target": "result-1"}
            ]
        }
        
        parsed = parser.parse(workflow["nodes"], workflow["edges"])
        assert len(parsed["stages"]) == 0  # No valid stages
    
    def test_edge_case_disconnected_analyzer(self, parser):
        """Test: Analyzer not connected to result should still execute"""
        workflow = {
            "nodes": [
                {"id": "file-1", "type": "file", "data": {}},
                {"id": "analyzer-1", "type": "analyzer", "data": {"analyzer": "ClamAV"}},
                {"id": "result-1", "type": "result", "data": {}}  # Not connected
            ],
            "edges": [
                {"source": "file-1", "target": "analyzer-1"}
                # No edge from analyzer to result
            ]
        }
        
        parsed = parser.parse(workflow["nodes"], workflow["edges"])
        
        # Analyzer should still be in stage
        assert len(parsed["stages"]) == 1
        assert parsed["stages"][0]["analyzers"] == ["ClamAV"]


class TestConditionEvaluation:
    """Test suite for condition evaluation logic"""
    
    @pytest.fixture
    def intel_service(self):
        return IntelOwlService()
    
    def test_condition_verdict_malicious_true(self, intel_service):
        """Test: verdict_malicious condition with malicious result"""
        condition = {
            "type": "verdict_malicious",
            "source_analyzer": "ClamAV"
        }
        
        all_results = {
            "stage_0": {
                "analyzer_reports": [
                    {
                        "name": "ClamAV",
                        "report": {
                            "classification": "malicious"
                        }
                    }
                ]
            }
        }
        
        result = intel_service._evaluate_condition(condition, all_results)
        assert result == True
        print("✅ Condition Evaluation (Malicious): PASSED")
    
    def test_condition_verdict_malicious_false(self, intel_service):
        """Test: verdict_malicious condition with clean result"""
        condition = {
            "type": "verdict_malicious",
            "source_analyzer": "ClamAV"
        }
        
        all_results = {
            "stage_0": {
                "analyzer_reports": [
                    {
                        "name": "ClamAV",
                        "report": {
                            "classification": "clean"
                        }
                    }
                ]
            }
        }
        
        result = intel_service._evaluate_condition(condition, all_results)
        assert result == False
        print("✅ Condition Evaluation (Clean): PASSED")
    
    def test_condition_negation(self, intel_service):
        """Test: negate flag inverts condition result"""
        condition = {
            "type": "verdict_malicious",
            "source_analyzer": "ClamAV",
            "negate": True  # Should invert result
        }
        
        all_results = {
            "stage_0": {
                "analyzer_reports": [
                    {
                        "name": "ClamAV",
                        "report": {
                            "classification": "malicious"
                        }
                    }
                ]
            }
        }
        
        result = intel_service._evaluate_condition(condition, all_results)
        assert result == False  # Negated: True → False
        print("✅ Condition Negation: PASSED")


class TestExecutionFlow:
    """Integration tests for full execution flow"""
    
    @pytest.mark.asyncio
    async def test_execution_skip_empty_analyzer_stage(self):
        """Test: Stages with empty analyzers should be skipped"""
        from app.services.intelowl_service import IntelOwlService
        
        service = IntelOwlService()
        
        stages = [
            {
                "stage_id": 0,
                "analyzers": ["ClamAV"],
                "target_nodes": [],
                "condition": None
            },
            {
                "stage_id": 1,
                "analyzers": [],  # Empty - should skip
                "target_nodes": ["result-1"],
                "condition": {"type": "verdict_malicious", "source_analyzer": "ClamAV"}
            }
        ]
        
        # Mock the IntelOwl submission
        with patch.object(service, 'submit_file_analysis', new=AsyncMock(return_value=123)):
            with patch.object(service, 'wait_for_completion', new=AsyncMock(return_value={})):
                result = await service.execute_workflow_with_conditionals(
                    file_path="/tmp/test.exe",
                    stages=stages,
                    file_name="test.exe"
                )
        
        # Stage 1 should be in executed_stages (result-only stage)
        assert 1 in result["executed_stages"]
        print("✅ Empty Analyzer Stage Handling: PASSED")


def run_all_tests():
    """Run all test suites"""
    print("\n" + "="*80)
    print("THREATFLOW WORKFLOW TEST SUITE")
    print("="*80)
    
    pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "--color=yes"
    ])


if __name__ == "__main__":
    run_all_tests()
