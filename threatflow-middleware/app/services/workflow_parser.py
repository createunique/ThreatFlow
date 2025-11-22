"""
Parser to convert React Flow JSON to IntelOwl execution plan
"""

from typing import Dict, List, Any
from app.models.workflow import WorkflowNode, WorkflowEdge, NodeType
import logging

logger = logging.getLogger(__name__)

class WorkflowParser:
    """Translates visual workflow (nodes + edges) into executable plan"""
    
    def parse(self, nodes: List[WorkflowNode], edges: List[WorkflowEdge]) -> Dict[str, Any]:
        """
        Parse workflow and generate execution plan
        
        Args:
            nodes: List of workflow nodes
            edges: List of connections between nodes
        
        Returns:
            Execution plan with file info and analyzers to run
        """
        node_map = {node.id: node for node in nodes}
        
        # Find file source node
        file_node = next(
            (n for n in nodes if n.type == NodeType.FILE),
            None
        )
        
        if not file_node:
            raise ValueError("Workflow must contain a file node")
        
        # Find analyzer nodes connected to file
        file_edges = [e for e in edges if e.source == file_node.id]
        
        analyzers = []
        for edge in file_edges:
            target_node = node_map.get(edge.target)
            if target_node and target_node.type == NodeType.ANALYZER:
                analyzer_name = target_node.data.get("analyzer")
                if analyzer_name:
                    analyzers.append(analyzer_name)
        
        if not analyzers:
            raise ValueError("No analyzers connected to file node")
        
        logger.info(f"Parsed workflow: {len(analyzers)} analyzers")
        
        return {
            "file_node_id": file_node.id,
            "file_data": file_node.data,
            "analyzers": analyzers
        }

workflow_parser = WorkflowParser()