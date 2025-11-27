"""
Test Section 4: Frontend Result Distribution Logic
Unit tests for the tree-based distribution functions in useWorkflowExecution.ts
"""

import pytest
import json
from typing import Dict, List, Any


class MockNode:
    """Mock representation of a React Flow node"""
    def __init__(self, id: str, node_type: str, data: Dict = None, position: Dict = None):
        self.id = id
        self.type = node_type
        self.data = data or {}
        self.position = position or {"x": 0, "y": 0}
    
    def to_dict(self):
        return {
            "id": self.id,
            "type": self.type,
            "data": self.data,
            "position": self.position
        }


class MockEdge:
    """Mock representation of a React Flow edge"""
    def __init__(self, source: str, target: str, source_handle: str = None, target_handle: str = None):
        self.id = f"{source}-{target}"
        self.source = source
        self.target = target
        self.sourceHandle = source_handle
        self.targetHandle = target_handle
    
    def to_dict(self):
        return {
            "id": self.id,
            "source": self.source,
            "target": self.target,
            "sourceHandle": self.sourceHandle,
            "targetHandle": self.targetHandle
        }


class TreeBasedDistributionSimulator:
    """
    Python simulation of the tree-based frontend distribution logic.
    Mirrors the logic in useWorkflowExecution.ts for testing.
    
    Architecture:
    - Each Result node (leaf) displays results from ALL analyzers in path from File (root)
    - Primary: Use backend stage routing (pre-computed tree analysis)
    - Fallback: DFS from File root to each Result leaf
    """
    
    def __init__(self, nodes: List[MockNode], edges: List[MockEdge]):
        self.nodes = {n.id: n for n in nodes}
        self.edges = edges
    
    def find_root_node(self) -> str:
        """Find the File node (root of tree)"""
        for nid, n in self.nodes.items():
            if n.type == 'file':
                return nid
        return None
    
    def find_leaf_nodes(self) -> List[str]:
        """Find all Result nodes (leaves in tree)"""
        return [nid for nid, n in self.nodes.items() if n.type == 'result']
    
    def find_analyzer_nodes(self) -> List[str]:
        """Find all analyzer nodes"""
        return [nid for nid, n in self.nodes.items() if n.type == 'analyzer']
    
    def get_children(self, node_id: str) -> List[str]:
        """Get all child nodes (outgoing edges)"""
        children = []
        for edge in self.edges:
            if edge.source == node_id:
                children.append(edge.target)
        return children
    
    def has_path_between_nodes(self, start_id: str, target_id: str) -> bool:
        """Check if there's any path between two nodes using BFS"""
        visited = set()
        queue = [start_id]
        
        while queue:
            current = queue.pop(0)
            if current == target_id:
                return True
            if current in visited:
                continue
            visited.add(current)
            
            children = self.get_children(current)
            queue.extend(children)
        
        return False
    
    def find_analyzers_in_tree_path(self, root_id: str, target_leaf_id: str) -> List[str]:
        """
        DFS to find all analyzers in paths from root to target leaf.
        Mirrors findAnalyzersInTreePath from useWorkflowExecution.ts
        
        Algorithm:
        1. Start at File node (root)
        2. Recursively explore child nodes (outgoing edges)
        3. Collect Analyzer nodes encountered
        4. Stop when reaching target Result node (leaf)
        5. Backtrack to explore other branches
        6. Return unique analyzers from all paths found
        """
        all_paths = []
        visited = set()
        
        def dfs_traversal(current_id: str, current_path: List[str]):
            if current_id in visited:
                return
            
            node = self.nodes.get(current_id)
            if not node:
                return
            
            # Collect analyzer if current node is Analyzer type
            path_with_current = list(current_path)
            if node.type == 'analyzer':
                analyzer_name = node.data.get('analyzer', node.data.get('name', 'Unknown'))
                path_with_current.append(analyzer_name)
            
            # BASE CASE: Reached target leaf node
            if current_id == target_leaf_id:
                all_paths.append(path_with_current)
                return
            
            # Mark as visited for this path
            visited.add(current_id)
            
            # RECURSIVE CASE: Explore all child nodes
            children = self.get_children(current_id)
            for child in children:
                dfs_traversal(child, path_with_current)
            
            # Backtrack
            visited.discard(current_id)
        
        dfs_traversal(root_id, [])
        
        # Aggregate unique analyzers from all paths
        unique_analyzers = set()
        for path in all_paths:
            for analyzer in path:
                unique_analyzers.add(analyzer)
        
        return list(unique_analyzers)
    
    def distribute_using_tree_traversal(self, all_results: Dict) -> Dict[str, Dict]:
        """
        Simulate distributeUsingTreeTraversal from useWorkflowExecution.ts
        Fallback strategy using DFS from root to each leaf
        """
        root_id = self.find_root_node()
        leaf_ids = self.find_leaf_nodes()
        
        if not root_id:
            return {}
        
        all_analyzer_reports = all_results.get('analyzer_reports', [])
        leaf_results = {}
        
        for leaf_id in leaf_ids:
            path_analyzers = self.find_analyzers_in_tree_path(root_id, leaf_id)
            
            if len(path_analyzers) == 0:
                # Check if there's any path at all
                has_path = self.has_path_between_nodes(root_id, leaf_id)
                
                if has_path:
                    # Path exists but no analyzers
                    leaf_results[leaf_id] = {
                        'job_id': all_results.get('job_id'),
                        'status': all_results.get('status'),
                        'analyzer_reports': []
                    }
                else:
                    # No path at all
                    leaf_results[leaf_id] = {
                        'job_id': None,
                        'status': 'idle',
                        'analyzer_reports': [],
                        'error': 'No path from File node (root) to this Result node (leaf)'
                    }
            else:
                # Filter reports for analyzers in this path
                filtered_reports = [
                    report for report in all_analyzer_reports
                    if report.get('name') in path_analyzers
                ]
                
                leaf_results[leaf_id] = {
                    'job_id': all_results.get('job_id'),
                    'status': all_results.get('status'),
                    'analyzer_reports': filtered_reports
                }
        
        return leaf_results
    
    def distribute_using_backend_routing(self, all_results: Dict, stage_routing: List[Dict]) -> Dict[str, Dict]:
        """
        Simulate distributeUsingBackendRouting from useWorkflowExecution.ts
        Primary strategy using backend's pre-computed tree analysis
        """
        leaf_ids = self.find_leaf_nodes()
        
        # Aggregate all analyzer reports
        all_analyzer_reports = []
        if all_results.get('analyzer_reports'):
            all_analyzer_reports = all_results['analyzer_reports']
        else:
            for key in all_results:
                if isinstance(all_results[key], dict) and 'analyzer_reports' in all_results[key]:
                    all_analyzer_reports.extend(all_results[key]['analyzer_reports'])
        
        # Build leaf node map
        leaf_node_map = {
            leaf_id: {
                'analyzers': [],
                'executed': False,
                'error': 'Path not executed (condition not met or branch not taken)'
            }
            for leaf_id in leaf_ids
        }
        
        # Process stage routing
        for routing in stage_routing:
            executed = routing.get('executed', False)
            analyzers = routing.get('analyzers', [])
            target_nodes = routing.get('target_nodes', [])
            
            for leaf_id in target_nodes:
                if leaf_id not in leaf_node_map:
                    continue
                
                leaf_info = leaf_node_map[leaf_id]
                
                if executed:
                    leaf_info['executed'] = True
                    leaf_info['analyzers'] = list(set(leaf_info['analyzers'] + analyzers))
                    leaf_info['error'] = None
        
        # Build results
        leaf_results = {}
        for leaf_id, info in leaf_node_map.items():
            if info['executed']:
                filtered_reports = [
                    r for r in all_analyzer_reports
                    if r.get('name') in info['analyzers']
                ]
                leaf_results[leaf_id] = {
                    'job_id': all_results.get('job_id'),
                    'status': all_results.get('status'),
                    'analyzer_reports': filtered_reports
                }
            else:
                leaf_results[leaf_id] = {
                    'job_id': None,
                    'status': 'idle',
                    'analyzer_reports': [],
                    'error': info['error']
                }
        
        return leaf_results


class TestTreeTraversal:
    """Test the tree-based DFS traversal distribution logic"""
    
    def test_linear_workflow_single_result(self):
        """
        File → ClamAV → File_Info → Result
        """
        nodes = [
            MockNode("file-1", "file"),
            MockNode("analyzer-1", "analyzer", {"analyzer": "ClamAV"}),
            MockNode("analyzer-2", "analyzer", {"analyzer": "File_Info"}),
            MockNode("result-1", "result")
        ]
        edges = [
            MockEdge("file-1", "analyzer-1"),
            MockEdge("analyzer-1", "analyzer-2"),
            MockEdge("analyzer-2", "result-1")
        ]
        
        simulator = TreeBasedDistributionSimulator(nodes, edges)
        
        mock_results = {
            "job_id": "123",
            "status": "completed",
            "analyzer_reports": [
                {"name": "ClamAV", "status": "success", "report": {"malicious": False}},
                {"name": "File_Info", "status": "success", "report": {"size": 1024}}
            ]
        }
        
        distribution = simulator.distribute_using_tree_traversal(mock_results)
        
        assert "result-1" in distribution
        reports = distribution["result-1"]["analyzer_reports"]
        names = [r["name"] for r in reports]
        
        assert "ClamAV" in names
        assert "File_Info" in names
    
    def test_parallel_branches_single_result(self):
        """
                   → ClamAV →
        File → FileInfo          → Result
                   → Strings →
        """
        nodes = [
            MockNode("file-1", "file"),
            MockNode("analyzer-1", "analyzer", {"analyzer": "File_Info"}),
            MockNode("analyzer-2", "analyzer", {"analyzer": "ClamAV"}),
            MockNode("analyzer-3", "analyzer", {"analyzer": "Strings_Info"}),
            MockNode("result-1", "result")
        ]
        edges = [
            MockEdge("file-1", "analyzer-1"),
            MockEdge("analyzer-1", "analyzer-2"),
            MockEdge("analyzer-1", "analyzer-3"),
            MockEdge("analyzer-2", "result-1"),
            MockEdge("analyzer-3", "result-1")
        ]
        
        simulator = TreeBasedDistributionSimulator(nodes, edges)
        
        mock_results = {
            "job_id": "123",
            "status": "completed",
            "analyzer_reports": [
                {"name": "File_Info", "status": "success", "report": {}},
                {"name": "ClamAV", "status": "success", "report": {}},
                {"name": "Strings_Info", "status": "success", "report": {}}
            ]
        }
        
        distribution = simulator.distribute_using_tree_traversal(mock_results)
        
        reports = distribution["result-1"]["analyzer_reports"]
        names = [r["name"] for r in reports]
        
        assert len(names) == 3
        assert "File_Info" in names
        assert "ClamAV" in names
        assert "Strings_Info" in names
    
    def test_separate_paths_two_results(self):
        """
        File → ClamAV → Result1
        File → File_Info → Result2
        """
        nodes = [
            MockNode("file-1", "file"),
            MockNode("analyzer-1", "analyzer", {"analyzer": "ClamAV"}),
            MockNode("analyzer-2", "analyzer", {"analyzer": "File_Info"}),
            MockNode("result-1", "result"),
            MockNode("result-2", "result")
        ]
        edges = [
            MockEdge("file-1", "analyzer-1"),
            MockEdge("analyzer-1", "result-1"),
            MockEdge("file-1", "analyzer-2"),
            MockEdge("analyzer-2", "result-2")
        ]
        
        simulator = TreeBasedDistributionSimulator(nodes, edges)
        
        mock_results = {
            "job_id": "123",
            "status": "completed",
            "analyzer_reports": [
                {"name": "ClamAV", "status": "success", "report": {}},
                {"name": "File_Info", "status": "success", "report": {}}
            ]
        }
        
        distribution = simulator.distribute_using_tree_traversal(mock_results)
        
        # Result1 should have ClamAV
        result1_names = [r["name"] for r in distribution["result-1"]["analyzer_reports"]]
        assert "ClamAV" in result1_names
        
        # Result2 should have File_Info
        result2_names = [r["name"] for r in distribution["result-2"]["analyzer_reports"]]
        assert "File_Info" in result2_names


class TestBackendRoutingDistribution:
    """Test the backend routing distribution logic"""
    
    def test_conditional_true_branch(self):
        """
        File → ClamAV → [cond] → TRUE: Strings → Result1
                              → FALSE: Result2
        
        When condition is TRUE, Result1 gets ClamAV + Strings
        """
        nodes = [
            MockNode("file-1", "file"),
            MockNode("analyzer-1", "analyzer", {"analyzer": "ClamAV"}),
            MockNode("cond-1", "conditional"),
            MockNode("analyzer-2", "analyzer", {"analyzer": "Strings_Info"}),
            MockNode("result-1", "result"),
            MockNode("result-2", "result")
        ]
        edges = [
            MockEdge("file-1", "analyzer-1"),
            MockEdge("analyzer-1", "cond-1"),
            MockEdge("cond-1", "analyzer-2", source_handle="true-output"),
            MockEdge("analyzer-2", "result-1"),
            MockEdge("cond-1", "result-2", source_handle="false-output")
        ]
        
        simulator = TreeBasedDistributionSimulator(nodes, edges)
        
        mock_results = {
            "job_id": "123",
            "status": "completed",
            "analyzer_reports": [
                {"name": "ClamAV", "status": "success", "report": {"malicious": True}},
                {"name": "Strings_Info", "status": "success", "report": {}}
            ]
        }
        
        # Stage routing indicating TRUE branch executed
        stage_routing = [
            {"stage_id": 0, "executed": True, "analyzers": ["ClamAV"], "target_nodes": ["result-1", "result-2"]},
            {"stage_id": 1, "executed": True, "analyzers": ["Strings_Info"], "target_nodes": ["result-1"]}
        ]
        
        distribution = simulator.distribute_using_backend_routing(mock_results, stage_routing)
        
        # Result1 should have both analyzers
        result1_names = [r["name"] for r in distribution["result-1"]["analyzer_reports"]]
        assert "ClamAV" in result1_names
        assert "Strings_Info" in result1_names
        
        # Result2 should only have ClamAV (from stage 0)
        result2_names = [r["name"] for r in distribution["result-2"]["analyzer_reports"]]
        assert "ClamAV" in result2_names
        assert "Strings_Info" not in result2_names
    
    def test_conditional_false_branch(self):
        """
        Same workflow but FALSE branch executes
        """
        nodes = [
            MockNode("file-1", "file"),
            MockNode("analyzer-1", "analyzer", {"analyzer": "ClamAV"}),
            MockNode("cond-1", "conditional"),
            MockNode("analyzer-2", "analyzer", {"analyzer": "Strings_Info"}),
            MockNode("result-1", "result"),
            MockNode("result-2", "result")
        ]
        edges = [
            MockEdge("file-1", "analyzer-1"),
            MockEdge("analyzer-1", "cond-1"),
            MockEdge("cond-1", "analyzer-2", source_handle="true-output"),
            MockEdge("analyzer-2", "result-1"),
            MockEdge("cond-1", "result-2", source_handle="false-output")
        ]
        
        simulator = TreeBasedDistributionSimulator(nodes, edges)
        
        mock_results = {
            "job_id": "123",
            "status": "completed",
            "analyzer_reports": [
                {"name": "ClamAV", "status": "success", "report": {"malicious": False}}
            ]
        }
        
        # Stage routing indicating FALSE branch executed
        stage_routing = [
            {"stage_id": 0, "executed": True, "analyzers": ["ClamAV"], "target_nodes": ["result-2"]},
            {"stage_id": 1, "executed": False, "analyzers": ["Strings_Info"], "target_nodes": ["result-1"]}
        ]
        
        distribution = simulator.distribute_using_backend_routing(mock_results, stage_routing)
        
        # Result1 should be empty (TRUE branch didn't execute)
        result1_reports = distribution["result-1"]["analyzer_reports"]
        assert len(result1_reports) == 0
        
        # Result2 should have ClamAV
        result2_names = [r["name"] for r in distribution["result-2"]["analyzer_reports"]]
        assert "ClamAV" in result2_names


class TestEdgeCases:
    """Test edge cases in distribution logic"""
    
    def test_no_analyzer_reports(self):
        """Handle empty analyzer_reports - Direct File → Result path"""
        nodes = [
            MockNode("file-1", "file"),
            MockNode("result-1", "result")
        ]
        edges = [
            MockEdge("file-1", "result-1")
        ]
        
        simulator = TreeBasedDistributionSimulator(nodes, edges)
        
        mock_results = {
            "job_id": "123",
            "status": "completed",
            "analyzer_reports": []
        }
        
        distribution = simulator.distribute_using_tree_traversal(mock_results)
        
        assert "result-1" in distribution
        assert distribution["result-1"]["analyzer_reports"] == []
        # Path exists but no analyzers
        assert distribution["result-1"].get("error") is None
    
    def test_duplicate_analyzer_in_results(self):
        """Handle if same analyzer appears multiple times"""
        nodes = [
            MockNode("file-1", "file"),
            MockNode("analyzer-1", "analyzer", {"analyzer": "ClamAV"}),
            MockNode("result-1", "result")
        ]
        edges = [
            MockEdge("file-1", "analyzer-1"),
            MockEdge("analyzer-1", "result-1")
        ]
        
        simulator = TreeBasedDistributionSimulator(nodes, edges)
        
        # Results with duplicate (shouldn't happen but test resilience)
        mock_results = {
            "job_id": "123",
            "status": "completed",
            "analyzer_reports": [
                {"name": "ClamAV", "status": "success", "report": {"pass": 1}},
                {"name": "ClamAV", "status": "success", "report": {"pass": 2}}
            ]
        }
        
        distribution = simulator.distribute_using_tree_traversal(mock_results)
        
        # Both should be included (matching by name)
        reports = distribution["result-1"]["analyzer_reports"]
        assert len(reports) == 2
    
    def test_deep_tree_five_analyzers(self):
        """
        Test 4: Deep Nested Tree
        File → A1 → A2 → A3 → A4 → A5 → Result
        Expected: Result displays [A1, A2, A3, A4, A5]
        """
        nodes = [
            MockNode("file-1", "file"),
            MockNode("a1", "analyzer", {"analyzer": "A1"}),
            MockNode("a2", "analyzer", {"analyzer": "A2"}),
            MockNode("a3", "analyzer", {"analyzer": "A3"}),
            MockNode("a4", "analyzer", {"analyzer": "A4"}),
            MockNode("a5", "analyzer", {"analyzer": "A5"}),
            MockNode("result-1", "result")
        ]
        edges = [
            MockEdge("file-1", "a1"),
            MockEdge("a1", "a2"),
            MockEdge("a2", "a3"),
            MockEdge("a3", "a4"),
            MockEdge("a4", "a5"),
            MockEdge("a5", "result-1")
        ]
        
        simulator = TreeBasedDistributionSimulator(nodes, edges)
        
        mock_results = {
            "job_id": "123",
            "status": "completed",
            "analyzer_reports": [
                {"name": "A1", "status": "success", "report": {}},
                {"name": "A2", "status": "success", "report": {}},
                {"name": "A3", "status": "success", "report": {}},
                {"name": "A4", "status": "success", "report": {}},
                {"name": "A5", "status": "success", "report": {}}
            ]
        }
        
        distribution = simulator.distribute_using_tree_traversal(mock_results)
        
        reports = distribution["result-1"]["analyzer_reports"]
        names = [r["name"] for r in reports]
        
        assert len(names) == 5
        assert "A1" in names
        assert "A2" in names
        assert "A3" in names
        assert "A4" in names
        assert "A5" in names
    
    def test_wide_tree_multiple_branches(self):
        """
        Test 5: Wide Tree (Multiple Branches)
        File → Analyzer1 → Analyzer2 → Result1
             → Analyzer3 → Result2
             → Analyzer4 → Result3
             → Analyzer5 → Result4
        """
        nodes = [
            MockNode("file-1", "file"),
            MockNode("a1", "analyzer", {"analyzer": "Analyzer1"}),
            MockNode("a2", "analyzer", {"analyzer": "Analyzer2"}),
            MockNode("a3", "analyzer", {"analyzer": "Analyzer3"}),
            MockNode("a4", "analyzer", {"analyzer": "Analyzer4"}),
            MockNode("a5", "analyzer", {"analyzer": "Analyzer5"}),
            MockNode("result-1", "result"),
            MockNode("result-2", "result"),
            MockNode("result-3", "result"),
            MockNode("result-4", "result")
        ]
        edges = [
            # Branch 1
            MockEdge("file-1", "a1"),
            MockEdge("a1", "a2"),
            MockEdge("a2", "result-1"),
            # Branch 2
            MockEdge("file-1", "a3"),
            MockEdge("a3", "result-2"),
            # Branch 3
            MockEdge("file-1", "a4"),
            MockEdge("a4", "result-3"),
            # Branch 4
            MockEdge("file-1", "a5"),
            MockEdge("a5", "result-4")
        ]
        
        simulator = TreeBasedDistributionSimulator(nodes, edges)
        
        mock_results = {
            "job_id": "123",
            "status": "completed",
            "analyzer_reports": [
                {"name": "Analyzer1", "status": "success", "report": {}},
                {"name": "Analyzer2", "status": "success", "report": {}},
                {"name": "Analyzer3", "status": "success", "report": {}},
                {"name": "Analyzer4", "status": "success", "report": {}},
                {"name": "Analyzer5", "status": "success", "report": {}}
            ]
        }
        
        distribution = simulator.distribute_using_tree_traversal(mock_results)
        
        # Result1: [Analyzer1, Analyzer2]
        result1_names = [r["name"] for r in distribution["result-1"]["analyzer_reports"]]
        assert "Analyzer1" in result1_names
        assert "Analyzer2" in result1_names
        assert len(result1_names) == 2
        
        # Result2: [Analyzer3]
        result2_names = [r["name"] for r in distribution["result-2"]["analyzer_reports"]]
        assert "Analyzer3" in result2_names
        assert len(result2_names) == 1
        
        # Result3: [Analyzer4]
        result3_names = [r["name"] for r in distribution["result-3"]["analyzer_reports"]]
        assert "Analyzer4" in result3_names
        assert len(result3_names) == 1
        
        # Result4: [Analyzer5]
        result4_names = [r["name"] for r in distribution["result-4"]["analyzer_reports"]]
        assert "Analyzer5" in result4_names
        assert len(result4_names) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
