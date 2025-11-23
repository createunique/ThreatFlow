"""
Workflow Validation Framework
Pre-execution validation for workflows and conditions
"""

from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import logging
from app.models.workflow import WorkflowNode, WorkflowEdge, NodeType
from app.services.analyzer_schema import schema_manager

logger = logging.getLogger(__name__)


class ValidationSeverity(Enum):
    """Validation issue severity levels"""
    ERROR = "error"  # Blocks execution
    WARNING = "warning"  # Should be addressed but doesn't block
    INFO = "info"  # Best practice suggestions


@dataclass
class ValidationIssue:
    """Represents a validation issue"""
    severity: ValidationSeverity
    message: str
    node_id: Optional[str] = None
    field: Optional[str] = None
    suggestions: List[str] = None
    auto_fix: Optional[Dict[str, Any]] = None  # Automatic fix suggestion
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "severity": self.severity.value,
            "message": self.message,
            "node_id": self.node_id,
            "field": self.field,
            "suggestions": self.suggestions or [],
            "auto_fix": self.auto_fix
        }


class WorkflowValidator:
    """
    Comprehensive workflow validation
    Checks structure, conditions, dependencies, and analyzer compatibility
    """
    
    @classmethod
    def validate_workflow(
        cls,
        nodes: List[WorkflowNode],
        edges: List[WorkflowEdge]
    ) -> List[ValidationIssue]:
        """
        Validate entire workflow before execution
        
        Returns list of validation issues sorted by severity
        """
        issues = []
        
        # 1. Structural validation
        issues.extend(cls._validate_structure(nodes, edges))
        
        # 2. Condition validation
        issues.extend(cls._validate_conditions(nodes))
        
        # 3. Dependency validation
        issues.extend(cls._validate_dependencies(nodes, edges))
        
        # 4. Analyzer compatibility
        issues.extend(cls._validate_analyzer_compatibility(nodes))
        
        # Sort by severity (errors first, then warnings, then info)
        severity_order = {ValidationSeverity.ERROR: 0, ValidationSeverity.WARNING: 1, ValidationSeverity.INFO: 2}
        issues.sort(key=lambda x: severity_order[x.severity])
        
        return issues
    
    @classmethod
    def _validate_structure(
        cls,
        nodes: List[WorkflowNode],
        edges: List[WorkflowEdge]
    ) -> List[ValidationIssue]:
        """Validate workflow structure"""
        issues = []
        
        # Must have exactly one file node
        file_nodes = [n for n in nodes if n.type == NodeType.FILE]
        if len(file_nodes) == 0:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                message="Workflow must have a file input node",
                suggestions=["Add a File node from the Node Palette"]
            ))
        elif len(file_nodes) > 1:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                message=f"Workflow has {len(file_nodes)} file nodes, only 1 allowed",
                suggestions=["Remove extra file nodes, keeping only one"]
            ))
        
        # Must have at least one analyzer
        analyzer_nodes = [n for n in nodes if n.type == NodeType.ANALYZER]
        if len(analyzer_nodes) == 0:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                message="Workflow must have at least one analyzer",
                suggestions=["Add analyzers from the Node Palette"]
            ))
        
        # Check for disconnected nodes
        node_ids = {n.id for n in nodes}
        connected_nodes = set()
        for edge in edges:
            connected_nodes.add(edge.source)
            connected_nodes.add(edge.target)
        
        disconnected = node_ids - connected_nodes
        if disconnected:
            for node_id in disconnected:
                node = next((n for n in nodes if n.id == node_id), None)
                if node and node.type != NodeType.FILE:
                    issues.append(ValidationIssue(
                        severity=ValidationSeverity.WARNING,
                        message=f"Node '{node.data.get('label', node_id)}' is not connected to workflow",
                        node_id=node_id,
                        suggestions=["Connect this node to the workflow or remove it"]
                    ))
        
        # Check for circular dependencies
        if cls._has_circular_dependency(nodes, edges):
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                message="Workflow contains circular dependencies",
                suggestions=["Remove edges that create cycles in the workflow"]
            ))
        
        return issues
    
    @classmethod
    def _validate_conditions(cls, nodes: List[WorkflowNode]) -> List[ValidationIssue]:
        """Validate conditional nodes"""
        issues = []
        
        conditional_nodes = [n for n in nodes if n.type == NodeType.CONDITIONAL]
        
        for cond_node in conditional_nodes:
            node_data = cond_node.data
            
            # Check if condition type is set
            if not node_data.get("conditionType"):
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    message=f"Conditional node '{node_data.get('label', cond_node.id)}' has no condition type",
                    node_id=cond_node.id,
                    field="conditionType",
                    suggestions=["Open node properties and select a condition type"]
                ))
                continue
            
            # Check if source analyzer is set
            if not node_data.get("sourceAnalyzer"):
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    message=f"Conditional node '{node_data.get('label', cond_node.id)}' has no source analyzer",
                    node_id=cond_node.id,
                    field="sourceAnalyzer",
                    suggestions=["Select which analyzer's output to evaluate"]
                ))
                continue
            
            # Validate using schema manager
            condition = {
                "type": node_data.get("conditionType"),
                "source_analyzer": node_data.get("sourceAnalyzer"),
                "field_path": node_data.get("fieldPath"),
                "expected_value": node_data.get("expectedValue")
            }
            
            is_valid, errors = schema_manager.validate_condition(condition)
            if not is_valid:
                for error in errors:
                    issues.append(ValidationIssue(
                        severity=ValidationSeverity.ERROR,
                        message=f"Conditional node validation failed: {error}",
                        node_id=cond_node.id,
                        suggestions=["Check condition configuration in node properties"]
                    ))
            
            # Check if field path is valid for field-based conditions
            cond_type = node_data.get("conditionType")
            if cond_type in ["field_equals", "field_contains", "field_greater_than", "field_less_than"]:
                field_path = node_data.get("fieldPath")
                source_analyzer = node_data.get("sourceAnalyzer")
                
                if field_path and source_analyzer:
                    is_valid, msg = schema_manager.validate_field_path(source_analyzer, field_path)
                    if not is_valid:
                        # Suggest alternatives
                        suggestions_list = schema_manager.suggest_field_paths(source_analyzer, field_path)
                        
                        issues.append(ValidationIssue(
                            severity=ValidationSeverity.WARNING,
                            message=f"Field path '{field_path}' may not exist in {source_analyzer} output: {msg}",
                            node_id=cond_node.id,
                            field="fieldPath",
                            suggestions=[f"Try: {s}" for s in suggestions_list[:3]] if suggestions_list else []
                        ))
        
        return issues
    
    @classmethod
    def _validate_dependencies(
        cls,
        nodes: List[WorkflowNode],
        edges: List[WorkflowEdge]
    ) -> List[ValidationIssue]:
        """Validate node dependencies"""
        issues = []
        
        # Build dependency map
        node_map = {n.id: n for n in nodes}
        dependencies = {n.id: [] for n in nodes}
        
        for edge in edges:
            if edge.target in dependencies:
                dependencies[edge.target].append(edge.source)
        
        # Check conditional nodes have proper input
        conditional_nodes = [n for n in nodes if n.type == NodeType.CONDITIONAL]
        for cond_node in conditional_nodes:
            source_analyzer = cond_node.data.get("sourceAnalyzer")
            if not source_analyzer:
                continue
            
            # Check if source analyzer is in the workflow
            analyzer_in_workflow = any(
                n.type == NodeType.ANALYZER and n.data.get("analyzer") == source_analyzer
                for n in nodes
            )
            
            if not analyzer_in_workflow:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    message=f"Conditional node references analyzer '{source_analyzer}' which is not in the workflow",
                    node_id=cond_node.id,
                    suggestions=[
                        f"Add {source_analyzer} analyzer to the workflow",
                        "Change sourceAnalyzer to an analyzer that exists in the workflow"
                    ]
                ))
            
            # Check if conditional node is connected to the source analyzer
            deps = dependencies.get(cond_node.id, [])
            has_analyzer_input = any(
                node_map.get(dep) and 
                node_map[dep].type == NodeType.ANALYZER and
                node_map[dep].data.get("analyzer") == source_analyzer
                for dep in deps
            )
            
            if not has_analyzer_input:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    message=f"Conditional node is not connected to its source analyzer '{source_analyzer}'",
                    node_id=cond_node.id,
                    suggestions=[
                        f"Connect {source_analyzer} output to this conditional node input"
                    ]
                ))
        
        return issues
    
    @classmethod
    def _validate_analyzer_compatibility(cls, nodes: List[WorkflowNode]) -> List[ValidationIssue]:
        """Validate analyzer compatibility and availability"""
        issues = []
        
        analyzer_nodes = [n for n in nodes if n.type == NodeType.ANALYZER]
        
        for analyzer_node in analyzer_nodes:
            analyzer_name = analyzer_node.data.get("analyzer")
            if not analyzer_name:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    message=f"Analyzer node '{analyzer_node.data.get('label', analyzer_node.id)}' has no analyzer selected",
                    node_id=analyzer_node.id,
                    suggestions=["Select an analyzer from the dropdown"]
                ))
                continue
            
            # Check if analyzer exists in schema
            if analyzer_name not in schema_manager.get_all_analyzers():
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    message=f"Analyzer '{analyzer_name}' is not in the known analyzer schema",
                    node_id=analyzer_node.id,
                    suggestions=["Analyzer may be unavailable or schema needs updating"]
                ))
        
        return issues
    
    @classmethod
    def _has_circular_dependency(
        cls,
        nodes: List[WorkflowNode],
        edges: List[WorkflowEdge]
    ) -> bool:
        """Check for circular dependencies using DFS"""
        # Build adjacency list
        graph = {n.id: [] for n in nodes}
        for edge in edges:
            graph[edge.source].append(edge.target)
        
        visited = set()
        rec_stack = set()
        
        def has_cycle(node_id: str) -> bool:
            visited.add(node_id)
            rec_stack.add(node_id)
            
            for neighbor in graph.get(node_id, []):
                if neighbor not in visited:
                    if has_cycle(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True
            
            rec_stack.remove(node_id)
            return False
        
        for node in nodes:
            if node.id not in visited:
                if has_cycle(node.id):
                    return True
        
        return False


# Global validator instance
workflow_validator = WorkflowValidator()
