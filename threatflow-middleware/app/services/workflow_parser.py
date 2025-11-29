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
        
        # Find all result nodes in the workflow
        result_nodes = [node.id for node in nodes if node.type == NodeType.RESULT]
        
        logger.info(f"Parsed linear workflow: {len(analyzers)} analyzers, {len(result_nodes)} result nodes")
        
        return {
            "file_node_id": file_node.id,
            "file_data": file_node.data,
            "has_conditionals": False,
            "stages": [
                {
                    "stage_id": 0,
                    "analyzers": analyzers,
                    "depends_on": None,
                    "condition": None,
                    "target_nodes": result_nodes  # All analyzers route to all result nodes
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
        """Parse complex workflow with conditional branches and chained conditionals"""
        
        stages = []
        processed_nodes = set()
        
        # Stage 0: ALL analyzers that can execute before any conditional evaluation
        stage_0_analyzers = self._get_preconditional_analyzers(
            file_node.id, conditional_nodes, node_map, edge_map
        )
        
        if stage_0_analyzers:
            # For pre-conditional stage, target ALL result nodes in the workflow
            # since these analyzers provide baseline analysis for all branches
            all_result_nodes = [node.id for node in node_map.values() if node.type == NodeType.RESULT]
            
            stages.append({
                "stage_id": 0,
                "analyzers": stage_0_analyzers,
                "depends_on": None,
                "condition": None,
                "target_nodes": all_result_nodes,  # ALL result nodes get pre-conditional analysis
                "description": "Pre-conditional analysis"
            })
            # Mark these analyzers as processed
            for analyzer in stage_0_analyzers:
                processed_nodes.add(analyzer)
        
        # Build conditional dependency graph and process chained conditionals
        conditional_stages = self._build_conditional_stages(
            conditional_nodes, node_map, edges, processed_nodes
        )
        stages.extend(conditional_stages)
        
        # Assign temporary unique IDs for dependency ordering
        for i, stage in enumerate(stages):
            if stage["stage_id"] == -1:
                stage["stage_id"] = 1000 + i  # Temporary unique ID
        
        # Ensure proper stage ordering (topological sort by dependencies)
        stages = self._order_stages_by_dependencies(stages)
        
        # Reassign stage IDs after ordering
        for i, stage in enumerate(stages):
            stage["stage_id"] = i
        
        logger.info(f"Parsed conditional workflow with chained conditionals: {len(stages)} stages")
        
        return {
            "file_node_id": file_node.id,
            "file_data": file_node.data,
            "has_conditionals": True,
            "stages": stages
        }
    
    def _build_conditional_stages(
        self,
        conditional_nodes: List[WorkflowNode],
        node_map: Dict[str, WorkflowNode],
        edges: List[WorkflowEdge],
        processed_nodes: set
    ) -> List[Dict[str, Any]]:
        """Build stages for conditional branches, handling chained conditionals recursively"""
        stages = []
        
        # Process each top-level conditional
        for cond_node in conditional_nodes:
            # Find input analyzer
            input_edges = [e for e in edges if e.target == cond_node.id]
            if not input_edges:
                continue
                
            source_node = node_map.get(input_edges[0].source)
            if not source_node or source_node.type != NodeType.ANALYZER:
                continue
                
            source_analyzer = source_node.data.get("analyzer")
            if not source_analyzer:
                continue
            
            # Get condition configuration
            condition_config = self._extract_condition_config(cond_node, source_analyzer)
            
            # Process TRUE and FALSE branches
            output_edges = [e for e in edges if e.source == cond_node.id]
            
            for is_true_branch in [True, False]:
                branch_analyzers = []
                branch_result_nodes = []
                
                branch_condition = dict(condition_config)
                if not is_true_branch:
                    branch_condition["negate"] = True
                
                # Collect analyzers and result nodes for this branch
                for edge in output_edges:
                    target_node = node_map.get(edge.target)
                    if not target_node:
                        continue
                    
                    # Check if this edge belongs to the current branch
                    if is_true_branch:
                        branch_type = edge.sourceHandle == "true-output"
                    else:
                        branch_type = edge.sourceHandle == "false-output"
                    
                    if target_node.type == NodeType.ANALYZER:
                        analyzer_name = target_node.data.get("analyzer")
                        if analyzer_name and branch_type:
                            branch_analyzers.append(analyzer_name)
                    elif target_node.type == NodeType.RESULT and branch_type:
                        branch_result_nodes.append(edge.target)
                
                # Find result nodes connected to the analyzers in this branch
                analyzer_result_nodes = self._find_result_nodes_for_analyzers(
                    branch_analyzers, node_map, edges
                )
                branch_result_nodes.extend(analyzer_result_nodes)
                branch_result_nodes = list(set(branch_result_nodes))  # Remove duplicates
                
                # Fallback: if stage has analyzers but no target_nodes, target all result nodes
                if branch_analyzers and not branch_result_nodes:
                    all_result_nodes = [node.id for node in node_map.values() if node.type == NodeType.RESULT]
                    branch_result_nodes = all_result_nodes
                    logger.warning(f"Conditional branch with analyzers {branch_analyzers} has no target nodes, falling back to all result nodes")
                
                # Create stage for this branch if it has analyzers or result nodes
                if branch_analyzers or branch_result_nodes:
                    branch_type_str = "TRUE" if is_true_branch else "FALSE"
                    logger.info(
                        f"📍 Building {branch_type_str} branch stage: "
                        f"analyzers={branch_analyzers}, target_nodes={branch_result_nodes}, "
                        f"condition={branch_condition.get('type', 'unknown')}"
                    )
                    
                    stage = {
                        "stage_id": -1,  # Will be reassigned
                        "analyzers": branch_analyzers,
                        "depends_on": source_analyzer,
                        "condition": branch_condition,
                        "target_nodes": branch_result_nodes,
                        "description": f"Conditional branch: {branch_condition.get('type', 'unknown')} {'(negated)' if not is_true_branch else ''}"
                    }
                    stages.append(stage)
                    
                    # Mark analyzers as processed
                    for analyzer in branch_analyzers:
                        processed_nodes.add(analyzer)
                    
                    # Check if any of these analyzers lead to more conditionals
                    for analyzer in branch_analyzers:
                        analyzer_node = None
                        for node in node_map.values():
                            if node.type == NodeType.ANALYZER and node.data.get("analyzer") == analyzer:
                                analyzer_node = node
                                break
                        
                        if analyzer_node:
                            # Find conditionals that depend on this analyzer
                            downstream_conditionals = []
                            for edge in edges:
                                if edge.source == analyzer_node.id:
                                    target_node = node_map.get(edge.target)
                                    if target_node and target_node.type == NodeType.CONDITIONAL:
                                        downstream_conditionals.append(target_node)
                            
                            # Recursively process downstream conditionals
                            for downstream_cond in downstream_conditionals:
                                self._process_downstream_conditional(
                                    downstream_cond, analyzer, node_map, edges, 
                                    processed_nodes, stages, [cond_node.id]
                                )
        
        return stages
    
    def _process_downstream_conditional(
        self,
        cond_node: WorkflowNode,
        source_analyzer: str,
        node_map: Dict[str, WorkflowNode],
        edges: List[WorkflowEdge],
        processed_nodes: set,
        stages: List[Dict[str, Any]],
        current_path: List[str]
    ):
        """Process a conditional that depends on an analyzer from a previous conditional branch"""
        if cond_node.id in current_path:
            logger.warning(f"Circular conditional dependency detected: {current_path}")
            return
        
        # Get condition configuration
        condition_config = self._extract_condition_config(cond_node, source_analyzer)
        
        # Process branches for this downstream conditional
        output_edges = [e for e in edges if e.source == cond_node.id]
        
        for is_true_branch in [True, False]:
            branch_analyzers = []
            branch_result_nodes = []
            
            branch_condition = dict(condition_config)
            if not is_true_branch:
                branch_condition["negate"] = True
            
            # Collect analyzers and result nodes for this branch
            for edge in output_edges:
                target_node = node_map.get(edge.target)
                if not target_node:
                    continue
                
                branch_type = edge.sourceHandle == "true-output" if is_true_branch else edge.sourceHandle == "false-output"
                
                if target_node.type == NodeType.ANALYZER:
                    analyzer_name = target_node.data.get("analyzer")
                    if analyzer_name and branch_type:
                        branch_analyzers.append(analyzer_name)
                elif target_node.type == NodeType.RESULT and branch_type:
                    branch_result_nodes.append(edge.target)
            
            # Find result nodes connected to the analyzers in this branch
            analyzer_result_nodes = self._find_result_nodes_for_analyzers(
                branch_analyzers, node_map, edges
            )
            branch_result_nodes.extend(analyzer_result_nodes)
            branch_result_nodes = list(set(branch_result_nodes))  # Remove duplicates
            
            # Fallback: if stage has analyzers but no target_nodes, target all result nodes
            if branch_analyzers and not branch_result_nodes:
                all_result_nodes = [node.id for node in node_map.values() if node.type == NodeType.RESULT]
                branch_result_nodes = all_result_nodes
                logger.warning(f"Downstream conditional branch with analyzers {branch_analyzers} has no target nodes, falling back to all result nodes")
            
            # Create stage for this downstream branch
            if branch_analyzers or branch_result_nodes:
                branch_type_str = "TRUE" if is_true_branch else "FALSE"
                logger.info(
                    f"📍 Building chained {branch_type_str} branch stage: "
                    f"analyzers={branch_analyzers}, target_nodes={branch_result_nodes}, "
                    f"condition={branch_condition.get('type', 'unknown')}"
                )
                
                stage = {
                    "stage_id": -1,  # Will be reassigned
                    "analyzers": branch_analyzers,
                    "depends_on": source_analyzer,
                    "condition": branch_condition,
                    "target_nodes": branch_result_nodes,
                    "description": f"Chained conditional branch: {branch_condition.get('type', 'unknown')}"
                }
                stages.append(stage)
                
                # Mark analyzers as processed
                for analyzer in branch_analyzers:
                    processed_nodes.add(analyzer)
    
    def _extract_condition_config(self, cond_node: WorkflowNode, default_source: str) -> Dict[str, Any]:
        """Extract condition configuration from conditional node"""
        if cond_node.conditional_data:
            condition_config = {
                "type": cond_node.conditional_data.condition_type,
                "source_analyzer": cond_node.conditional_data.source_analyzer,
            }
            if cond_node.conditional_data.field_path:
                condition_config["field_path"] = cond_node.conditional_data.field_path
            if cond_node.conditional_data.expected_value:
                condition_config["expected_value"] = cond_node.conditional_data.expected_value
        else:
            # Fallback to data dict
            frontend_condition_type = cond_node.data.get("conditionType")
            frontend_source_analyzer = cond_node.data.get("sourceAnalyzer")

            if frontend_condition_type:
                condition_config = {
                    "type": frontend_condition_type,
                    "source_analyzer": frontend_source_analyzer or default_source
                }
            else:
                condition_config = cond_node.data.get("condition")
        
        if not condition_config:
            condition_config = {
                "type": "verdict_malicious",
                "source_analyzer": default_source
            }
        elif isinstance(condition_config, dict) and "source_analyzer" not in condition_config:
            condition_config["source_analyzer"] = default_source
        
        return condition_config
    
    def _order_stages_by_dependencies(self, stages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Order stages by their dependencies to ensure proper execution sequence"""
        if not stages:
            return stages
        
        # Build dependency graph
        stage_deps = {}
        stage_map = {}
        
        for stage in stages:
            stage_id = stage["stage_id"]
            stage_map[stage_id] = stage
            stage_deps[stage_id] = set()
            
            # Find dependencies
            depends_on = stage.get("depends_on")
            if depends_on:
                # Find which stage contains this analyzer
                for other_stage in stages:
                    if other_stage["stage_id"] != stage_id and depends_on in other_stage.get("analyzers", []):
                        stage_deps[stage_id].add(other_stage["stage_id"])
                        break
        
        # Topological sort
        visited = set()
        temp_visited = set()
        ordered = []
        
        def visit(stage_id):
            if stage_id in temp_visited:
                logger.warning(f"Circular dependency detected involving stage {stage_id}")
                return
            if stage_id in visited:
                return
            
            temp_visited.add(stage_id)
            
            for dep_id in stage_deps.get(stage_id, set()):
                visit(dep_id)
            
            temp_visited.remove(stage_id)
            visited.add(stage_id)
            ordered.append(stage_map[stage_id])
        
        # Visit all stages
        for stage_id in stage_map.keys():
            if stage_id not in visited:
                visit(stage_id)
        
        return ordered
    
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
    
    def _get_preconditional_analyzers(
        self,
        file_node_id: str,
        conditional_nodes: List[WorkflowNode],
        node_map: Dict[str, WorkflowNode],
        edge_map: Dict[str, List[str]]
    ) -> List[str]:
        """Get all analyzers that can execute before conditional evaluation"""
        analyzers = []
        visited = set()
        conditional_node_ids = {node.id for node in conditional_nodes}
        
        def traverse_from_node(node_id: str):
            if node_id in visited:
                return
            visited.add(node_id)
            
            node = node_map.get(node_id)
            if not node:
                return
            
            # If this is an analyzer, add it (unless it's after a conditional)
            if node.type == NodeType.ANALYZER:
                analyzer_name = node.data.get("analyzer")
                if analyzer_name and analyzer_name not in analyzers:
                    analyzers.append(analyzer_name)
            
            # Continue to connected nodes, but stop at conditional nodes
            if node.type != NodeType.RESULT and node_id not in conditional_node_ids:
                for target_id in edge_map.get(node_id, []):
                    # Don't traverse through conditional nodes
                    if target_id not in conditional_node_ids:
                        traverse_from_node(target_id)
        
        traverse_from_node(file_node_id)
        return analyzers
    
    def _find_result_nodes_for_analyzers(
        self,
        analyzer_names: List[str],
        node_map: Dict[str, WorkflowNode],
        edges: List[WorkflowEdge]
    ) -> List[str]:
        """Find result nodes that are reachable from the given analyzers (recursively)"""
        result_nodes = []
        
        # Create a map of analyzer names to node IDs
        analyzer_node_map = {}
        for node in node_map.values():
            if node.type == NodeType.ANALYZER:
                analyzer_name = node.data.get("analyzer")
                if analyzer_name:
                    analyzer_node_map[analyzer_name] = node.id
        
        # For each analyzer, find all reachable result nodes
        for analyzer_name in analyzer_names:
            analyzer_node_id = analyzer_node_map.get(analyzer_name)
            if analyzer_node_id:
                reachable = self._find_all_reachable_result_nodes(
                    analyzer_node_id, edges, node_map
                )
                result_nodes.extend(reachable)
        
        return list(set(result_nodes))  # Deduplicate
    
    def _find_all_reachable_result_nodes(
        self,
        start_node_id: str,
        edges: List[WorkflowEdge],
        node_map: Dict[str, WorkflowNode],
        visited: Optional[Set[str]] = None
    ) -> List[str]:
        """
        Recursively find ALL result nodes reachable from start_node_id.
        
        This method properly traverses through conditional nodes to find
        downstream result nodes that are connected via conditional branches.
        
        Args:
            start_node_id: Starting node ID for traversal
            edges: List of workflow edges
            node_map: Map of node IDs to nodes
            visited: Set of already visited nodes (to prevent cycles)
        
        Returns:
            List of result node IDs reachable from start_node_id
        """
        if visited is None:
            visited = set()
        
        if start_node_id in visited:
            return []
        
        visited.add(start_node_id)
        current_node = node_map.get(start_node_id)
        
        if not current_node:
            return []
        
        # Found a result node - return it
        if current_node.type == NodeType.RESULT:
            logger.debug(f"Found result node: {start_node_id}")
            return [start_node_id]
        
        # Recurse through all outgoing edges
        result_nodes = []
        outgoing_edges = [e for e in edges if e.source == start_node_id]
        
        for edge in outgoing_edges:
            # CRITICAL FIX: Continue traversal through ALL node types including conditionals
            # Use a fresh copy of visited set for each branch to allow proper tree traversal
            downstream_results = self._find_all_reachable_result_nodes(
                edge.target, edges, node_map, visited.copy()
            )
            result_nodes.extend(downstream_results)
        
        return list(set(result_nodes))  # Deduplicate


# Create singleton instance
workflow_parser = WorkflowParser()