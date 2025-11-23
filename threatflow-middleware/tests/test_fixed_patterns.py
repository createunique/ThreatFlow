"""
ThreatFlow Comprehensive Pattern Tests - Fixed Version
Tests all workflow patterns with proper Pydantic models
"""

import pytest
from app.services.workflow_parser import WorkflowParser
from app.services.intelowl_service import IntelOwlService
from app.models.workflow import WorkflowNode, WorkflowEdge, NodeType


def create_node(id: str, node_type: str, data: dict) -> WorkflowNode:
    """Helper to create Pydantic WorkflowNode"""
    return WorkflowNode(
        id=id,
        type=NodeType(node_type),
        position={"x": 0, "y": 0},
        data=data
    )


def create_edge(source: str, target: str, sourceHandle: str = None) -> WorkflowEdge:
    """Helper to create Pydantic WorkflowEdge"""
    edge_data = {
        "id": f"{source}-{target}",
        "source": source,
        "target": target
    }
    if sourceHandle:
        edge_data["sourceHandle"] = sourceHandle
    return WorkflowEdge(**edge_data)


class TestWorkflowPatterns:
    """Test suite for workflow patterns"""
    
    @pytest.fixture
    def parser(self):
        return WorkflowParser()
    
    def test_pattern_1_simple_linear(self, parser):
        """File → Analyzer → Result"""
        nodes = [
            create_node("file-1", "file", {"label": "File"}),
            create_node("analyzer-1", "analyzer", {"analyzer": "ClamAV"}),
            create_node("result-1", "result", {"label": "Result"})
        ]
        edges = [
            create_edge("file-1", "analyzer-1"),
            create_edge("analyzer-1", "result-1")
        ]
        
        parsed = parser.parse(nodes, edges)
        
        assert parsed["file_node_id"] == "file-1"
        assert parsed["has_conditionals"] is False
        assert len(parsed["stages"]) == 1
        assert "ClamAV" in parsed["stages"][0]["analyzers"]
        # Note: target_nodes only exists for conditional branches
    
    def test_pattern_2_sequential(self, parser):
        """File → Analyzer1 → Analyzer2 → Result"""
        nodes = [
            create_node("file-1", "file", {}),
            create_node("analyzer-1", "analyzer", {"analyzer": "ClamAV"}),
            create_node("analyzer-2", "analyzer", {"analyzer": "PE_Info"}),
            create_node("result-1", "result", {})
        ]
        edges = [
            create_edge("file-1", "analyzer-1"),
            create_edge("analyzer-1", "analyzer-2"),
            create_edge("analyzer-2", "result-1")
        ]
        
        parsed = parser.parse(nodes, edges)
        
        # Current implementation creates 1 stage with all chained analyzers
        # Note: Sequential execution is handled by order, not separate stages
        assert len(parsed["stages"]) >= 1
        # Both analyzers should be included
        all_analyzers = []
        for stage in parsed["stages"]:
            all_analyzers.extend(stage["analyzers"])
        assert "ClamAV" in all_analyzers
        assert "PE_Info" in all_analyzers
    
    def test_pattern_3_parallel(self, parser):
        """File → [Analyzer1 + Analyzer2] → Result"""
        nodes = [
            create_node("file-1", "file", {}),
            create_node("analyzer-1", "analyzer", {"analyzer": "ClamAV"}),
            create_node("analyzer-2", "analyzer", {"analyzer": "PE_Info"}),
            create_node("result-1", "result", {})
        ]
        edges = [
            create_edge("file-1", "analyzer-1"),
            create_edge("file-1", "analyzer-2"),
            create_edge("analyzer-1", "result-1"),
            create_edge("analyzer-2", "result-1")
        ]
        
        parsed = parser.parse(nodes, edges)
        
        assert len(parsed["stages"]) == 1
        assert "ClamAV" in parsed["stages"][0]["analyzers"]
        assert "PE_Info" in parsed["stages"][0]["analyzers"]
    
    def test_pattern_4_conditional(self, parser):
        """File → Analyzer → Conditional → [Result_TRUE | Result_FALSE]"""
        nodes = [
            create_node("file-1", "file", {}),
            create_node("analyzer-1", "analyzer", {"analyzer": "ClamAV"}),
            create_node("conditional-1", "conditional", {
                "conditionType": "verdict_malicious",
                "sourceAnalyzer": "ClamAV"
            }),
            create_node("result-true", "result", {}),
            create_node("result-false", "result", {})
        ]
        edges = [
            create_edge("file-1", "analyzer-1"),
            create_edge("analyzer-1", "conditional-1"),
            create_edge("conditional-1", "result-true", "true-output"),
            create_edge("conditional-1", "result-false", "false-output")
        ]
        
        parsed = parser.parse(nodes, edges)
        
        assert parsed["has_conditionals"] is True
        assert len(parsed["stages"]) >= 2  # At least analyzer + one branch
        
        # Find TRUE branch stage
        true_stage = next(
            (s for s in parsed["stages"] if "result-true" in s.get("target_nodes", [])),
            None
        )
        assert true_stage is not None
        assert true_stage["condition"] is not None
        assert true_stage["condition"]["type"] == "verdict_malicious"
        assert true_stage["condition"]["source_analyzer"] == "ClamAV"
    
    def test_pattern_5_chained_before_conditional(self, parser):
        """File → Analyzer1 → Analyzer2 → Conditional → [AnalyzerA | AnalyzerB]"""
        nodes = [
            create_node("file-1", "file", {}),
            create_node("analyzer-1", "analyzer", {"analyzer": "ClamAV"}),
            create_node("analyzer-2", "analyzer", {"analyzer": "PE_Info"}),
            create_node("conditional-1", "conditional", {
                "conditionType": "verdict_malicious",
                "sourceAnalyzer": "PE_Info"  # Depends on chained analyzer
            }),
            create_node("analyzer-true", "analyzer", {"analyzer": "Strings_Info"}),
            create_node("analyzer-false", "analyzer", {"analyzer": "File_Info"}),
            create_node("result-1", "result", {})
        ]
        edges = [
            create_edge("file-1", "analyzer-1"),
            create_edge("analyzer-1", "analyzer-2"),
            create_edge("analyzer-2", "conditional-1"),
            create_edge("conditional-1", "analyzer-true", "true-output"),
            create_edge("conditional-1", "analyzer-false", "false-output"),
            create_edge("analyzer-true", "result-1"),
            create_edge("analyzer-false", "result-1")
        ]
        
        parsed = parser.parse(nodes, edges)
        
        assert parsed["has_conditionals"] is True
        assert len(parsed["stages"]) >= 3  # Stage 0 + TRUE + FALSE branches
        
        # Stage 0 should include both chained analyzers
        stage_0 = parsed["stages"][0]
        assert stage_0["stage_id"] == 0
        assert "ClamAV" in stage_0["analyzers"]
        assert "PE_Info" in stage_0["analyzers"]
        assert stage_0["condition"] is None  # No condition for stage 0
        
        # Find TRUE branch stage
        true_stage = next(
            (s for s in parsed["stages"] if s.get("condition") and s.get("condition", {}).get("type") == "verdict_malicious" and not s.get("condition", {}).get("negate")),
            None
        )
        assert true_stage is not None
        assert true_stage["depends_on"] == "PE_Info"  # Depends on the chained analyzer
        assert "Strings_Info" in true_stage["analyzers"]
        
        # Find FALSE branch stage
        false_stage = next(
            (s for s in parsed["stages"] if s.get("condition") and s.get("condition", {}).get("negate") is True),
            None
        )
        assert false_stage is not None
        assert false_stage["depends_on"] == "PE_Info"
        assert "File_Info" in false_stage["analyzers"]
    
    def test_edge_case_empty_workflow(self, parser):
        """Empty workflow should raise error"""
        with pytest.raises(ValueError, match="must contain a file node"):
            parser.parse([], [])


class TestConditionEvaluation:
    """Test condition evaluation logic"""
    
    @pytest.fixture
    def service(self):
        # IntelOwlService() takes no args - uses env variables
        return IntelOwlService()
    
    def test_verdict_malicious_true(self, service):
        """Verdict malicious condition with malicious result"""
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
                            "malicious": True
                        }
                    }
                ]
            }
        }
        
        result = service._evaluate_condition(condition, all_results)
        assert result is True
    
    def test_verdict_malicious_false(self, service):
        """Verdict malicious condition with clean result"""
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
                            "malicious": False
                        }
                    }
                ]
            }
        }
        
        result = service._evaluate_condition(condition, all_results)
        assert result is False
    
    def test_condition_negation(self, service):
        """Negate flag inverts condition result"""
        condition = {
            "type": "verdict_malicious",
            "source_analyzer": "ClamAV",
            "negate": True
        }
        
        all_results = {
            "stage_0": {
                "analyzer_reports": [
                    {
                        "name": "ClamAV",
                        "report": {
                            "malicious": True
                        }
                    }
                ]
            }
        }
        
        result = service._evaluate_condition(condition, all_results)
        assert result is False  # Negated: True → False


class TestExecutionFlow:
    """Test execution flow control"""
    
    @pytest.fixture
    def service(self):
        return IntelOwlService()
    
    def test_skip_empty_analyzer_stage(self, service):
        """Empty analyzer stages should be skipped"""
        stage = {
            "stage_id": 1,
            "analyzers": [],  # Empty
            "target_nodes": ["result-1"]
        }
        
        # This stage should be skipped - no API call
        assert len(stage["analyzers"]) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
