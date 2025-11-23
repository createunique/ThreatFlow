"""
Enhanced workflow parser with conditional logic support (Phase 4)
Converts React Flow JSON to multi-stage IntelOwl execution plan
"""

from typing import Dict, List, Any, Optional, Set
from app.models.workflow import WorkflowNode, WorkflowEdge, NodeType, ConditionType
import logging

logger = logging.getLogger(__name__)

class WorkflowParser:
    """
    Translates visual workflow (nodes + edges) into executable plan
    Now supports conditional logic and multi-stage execution
    """
    
    def parse(self, nodes: List[WorkflowNode], edges: List[WorkflowEdge]) -> Dict[str, Any]:
        """
        Parse workflow and generate execution plan with stages
        
        Args:
            nodes: List of workflow nodes
            edges: List of connections between nodes
        
        Returns:
            Execution plan with stages:
            {
                "file_node_id": "file-1",
                "file_data": {...},
                "has_conditionals": bool,
                "stages": [
                    {
                        "stage_id": 0,
                        "analyzers": ["ClamAV", "File_Info"],
                        "depends_on": None,
                        "condition": None
                    },
                    {
                        "stage_id": 1,
                        "analyzers": ["PE_Info", "Capa_Info"],
                        "depends_on": "ClamAV",
                        "condition": {
                            "type": "verdict_malicious",
                            "source_analyzer": "ClamAV"
                        }
                    }
                ]
            }
        """
        node_map = {node.id: node for node in nodes}
        edge_map = self._build_edge_map(edges)
        
        # Find file source node
        file_node = next(
            (n for n in nodes if n.type == NodeType.FILE),
            None
        )
        
        if not file_node:
            raise ValueError("Workflow must contain a file node")
        
        # Check for conditional nodes
        conditional_nodes = [n for n in nodes if n.type == NodeType.CONDITIONAL]
        has_conditionals = len(conditional_nodes) > 0
        
        if not has_conditionals:
            # Simple linear workflow (Phase 3 behavior)
            return self._parse_linear_workflow(file_node, nodes, edges, node_map, edge_map)
        
        # Complex workflow with conditionals (Phase 4)
        return self._parse_conditional_workflow(
            file_node, nodes, edges, node_map, edge_map, conditional_nodes
        )
    
    def _parse_linear_workflow(
        self,
        file_node: WorkflowNode,
        nodes: List[WorkflowNode],
        edges: List[WorkflowEdge],
        node_map: Dict[str, WorkflowNode],
        edge_map: Dict[str, List[str]]
    ) -> Dict[str, Any]:
        """Parse simple workflow without conditionals (backwards compatible)"""
        
        analyzers = self._get_all_analyzers_in_workflow(file_node.id, node_map, edge_map)
        
        if not analyzers:
            raise ValueError("No analyzers connected to file node")
        
        logger.info(f"Parsed linear workflow: {len(analyzers)} analyzers")
        
        return {
            "file_node_id": file_node.id,
            "file_data": file_node.data,
            "has_conditionals": False,
            "stages": [
                {
                    "stage_id": 0,
                    "analyzers": analyzers,
                    "depends_on": None,
                    "condition": None
                }
            ]
        }
    
    def _parse_conditional_workflow(
        self,
        file_node: WorkflowNode,
        nodes: List[WorkflowNode],
        edges: List[WorkflowEdge],
        node_map: Dict[str, WorkflowNode],
        edge_map: Dict[str, List[str]],
        conditional_nodes: List[WorkflowNode]
    ) -> Dict[str, Any]:
        """Parse complex workflow with conditional branches"""
        
        stages = []
        
        # Stage 0: Direct analyzers from file (always execute first)
        stage_0_analyzers = self._get_direct_analyzers(file_node.id, node_map, edge_map, edges)
        
        if stage_0_analyzers:
            stages.append({
                "stage_id": 0,
                "analyzers": stage_0_analyzers,
                "depends_on": None,
                "condition": None,
                "description": "Initial analysis"
            })
        
        # Process conditional nodes
        for cond_node in conditional_nodes:
            # Find input edge (which analyzer feeds this conditional)
            input_edges = [e for e in edges if e.target == cond_node.id]
            if not input_edges:
                logger.warning(f"Conditional node {cond_node.id} has no input")
                continue
            
            source_node_id = input_edges[0].source
            source_node = node_map.get(source_node_id)
            
            if not source_node or source_node.type != NodeType.ANALYZER:
                logger.warning(f"Conditional node {cond_node.id} input is not an analyzer")
                continue
            
            source_analyzer = source_node.data.get("analyzer")
            if not source_analyzer:
                continue
            
            # Find output edges (true/false branches)
            output_edges = [e for e in edges if e.source == cond_node.id]
            
            true_analyzers = []
            false_analyzers = []
            true_result_nodes = []  # NEW: Track result node targets
            false_result_nodes = []  # NEW: Track result node targets
            
            for edge in output_edges:
                target_node = node_map.get(edge.target)
                
                if not target_node:
                    continue
                
                # Determine which branch based on sourceHandle
                is_true_branch = edge.sourceHandle == "true-output"
                is_false_branch = edge.sourceHandle == "false-output"
                
                if target_node.type == NodeType.ANALYZER:
                    analyzer_name = target_node.data.get("analyzer")
                    if not analyzer_name:
                        continue
                    
                    if is_true_branch:
                        true_analyzers.append(analyzer_name)
                    elif is_false_branch:
                        false_analyzers.append(analyzer_name)
                    else:
                        # Default: assume true branch if not specified
                        true_analyzers.append(analyzer_name)
                
                # NEW: Handle result node targets
                elif target_node.type == NodeType.RESULT:
                    if is_true_branch:
                        true_result_nodes.append(edge.target)
                    elif is_false_branch:
                        false_result_nodes.append(edge.target)
            
            # Extract condition from node data
            if cond_node.conditional_data:
                # Convert ConditionalData object to dict
                condition_config = {
                    "type": cond_node.conditional_data.condition_type,
                    "source_analyzer": cond_node.conditional_data.source_analyzer,
                }
                if cond_node.conditional_data.field_path:
                    condition_config["field_path"] = cond_node.conditional_data.field_path
                if cond_node.conditional_data.expected_value:
                    condition_config["expected_value"] = cond_node.conditional_data.expected_value
            else:
                # Fallback to data dict (for backwards compatibility)
                # Check for frontend format: conditionType, sourceAnalyzer
                frontend_condition_type = cond_node.data.get("conditionType")
                frontend_source_analyzer = cond_node.data.get("sourceAnalyzer")

                if frontend_condition_type:
                    condition_config = {
                        "type": frontend_condition_type,
                        "source_analyzer": frontend_source_analyzer or source_analyzer
                    }
                else:
                    condition_config = cond_node.data.get("condition")
            
            if not condition_config:
                # Default condition: check if malicious
                condition_config = {
                    "type": "verdict_malicious",
                    "source_analyzer": source_analyzer
                }
            elif isinstance(condition_config, dict) and "source_analyzer" not in condition_config:
                condition_config["source_analyzer"] = source_analyzer
            
            # Create stage for TRUE branch
            if true_analyzers or true_result_nodes:
                stages.append({
                    "stage_id": len(stages),
                    "analyzers": true_analyzers,
                    "depends_on": source_analyzer,
                    "condition": condition_config,
                    "target_nodes": true_result_nodes,  # NEW: Include result node targets
                    "description": f"If {source_analyzer} condition is TRUE"
                })
                logger.debug(f"Created TRUE branch stage: analyzers={true_analyzers}, target_nodes={true_result_nodes}")
            
            # Create stage for FALSE branch
            if false_analyzers or false_result_nodes:
                # Create negated condition that preserves source_analyzer
                false_condition = dict(condition_config)  # Copy the original condition
                false_condition["negate"] = True  # Add negate flag instead of wrapping
                
                stages.append({
                    "stage_id": len(stages),
                    "analyzers": false_analyzers,
                    "depends_on": source_analyzer,
                    "condition": false_condition,  # Negated version preserving source_analyzer
                    "target_nodes": false_result_nodes,  # NEW: Include result node targets
                    "description": f"If {source_analyzer} condition is FALSE"
                })
                logger.debug(f"Created FALSE branch stage: analyzers={false_analyzers}, target_nodes={false_result_nodes}")
        
        logger.info(f"Parsed conditional workflow: {len(stages)} stages")
        
        return {
            "file_node_id": file_node.id,
            "file_data": file_node.data,
            "has_conditionals": True,
            "stages": stages
        }
    
    def _build_edge_map(self, edges: List[WorkflowEdge]) -> Dict[str, List[str]]:
        """Build adjacency map from edges"""
        edge_map = {}
        for edge in edges:
            if edge.source not in edge_map:
                edge_map[edge.source] = []
            edge_map[edge.source].append(edge.target)
        return edge_map
    
    def _get_direct_analyzers(
        self, 
        source_id: str, 
        node_map: Dict[str, WorkflowNode],
        edge_map: Dict[str, List[str]],
        edges: List[WorkflowEdge]
    ) -> List[str]:
        """Get analyzers directly connected to source node (skip conditionals)"""
        analyzers = []
        target_ids = edge_map.get(source_id, [])
        
        for target_id in target_ids:
            target_node = node_map.get(target_id)
            
            if not target_node:
                continue
            
            # Only include analyzer nodes (skip conditional nodes)
            if target_node.type == NodeType.ANALYZER:
                analyzer_name = target_node.data.get("analyzer")
                if analyzer_name:
                    analyzers.append(analyzer_name)
        
        return analyzers
    
    def _get_all_analyzers_in_workflow(
        self,
        file_node_id: str,
        node_map: Dict[str, WorkflowNode],
        edge_map: Dict[str, List[str]]
    ) -> List[str]:
        """Get all analyzers reachable from file node (for linear workflows)"""
        analyzers = []
        visited = set()
        
        def traverse_from_node(node_id: str):
            if node_id in visited:
                return
            visited.add(node_id)
            
            node = node_map.get(node_id)
            if not node:
                return
            
            # If this is an analyzer, add it
            if node.type == NodeType.ANALYZER:
                analyzer_name = node.data.get("analyzer")
                if analyzer_name and analyzer_name not in analyzers:
                    analyzers.append(analyzer_name)
            
            # Continue to connected nodes (unless it's a result node)
            if node.type != NodeType.RESULT:
                for target_id in edge_map.get(node_id, []):
                    traverse_from_node(target_id)
        
        traverse_from_node(file_node_id)
        return analyzers

# Global parser instance
workflow_parser = WorkflowParser()