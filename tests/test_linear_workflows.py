"""
Test Section 1: Linear Workflows (File → Analyzer(s) → Result)
Tests basic workflows without conditional logic
"""

import pytest
from conftest import WorkflowBuilder, WorkflowTester


class TestLinearSingleAnalyzer:
    """Test workflows with a single analyzer"""
    
    def test_file_info_analyzer(self, workflow_tester, workflow_builder, safe_sample_path):
        """
        Workflow: File → File_Info → Result
        Expected: Result shows File_Info report
        """
        # Build workflow
        file_id = workflow_builder.add_file_node()
        analyzer_id = workflow_builder.add_analyzer_node("File_Info", x=300)
        result_id = workflow_builder.add_result_node(x=500)
        
        workflow_builder.connect(file_id, analyzer_id)
        workflow_builder.connect(analyzer_id, result_id)
        
        nodes, edges = workflow_builder.get_workflow()
        
        # Execute
        result = workflow_tester.execute_workflow(nodes, edges, safe_sample_path)
        
        # Assertions
        assert result.success, f"Workflow failed: {result.error}"
        assert result.job_id is not None
        assert result.has_conditionals is False
        assert result.results is not None
        
        # Check analyzer_reports
        reports = result.results.get('analyzer_reports', [])
        assert len(reports) >= 1, "Expected at least 1 analyzer report"
        
        analyzer_names = [r['name'] for r in reports]
        assert 'File_Info' in analyzer_names, f"Expected File_Info in {analyzer_names}"
    
    def test_clamav_safe_file(self, workflow_tester, workflow_builder, safe_sample_path):
        """
        Workflow: File → ClamAV → Result
        Expected: Result shows ClamAV report with no detections
        """
        file_id = workflow_builder.add_file_node()
        analyzer_id = workflow_builder.add_analyzer_node("ClamAV", x=300)
        result_id = workflow_builder.add_result_node(x=500)
        
        workflow_builder.connect(file_id, analyzer_id)
        workflow_builder.connect(analyzer_id, result_id)
        
        nodes, edges = workflow_builder.get_workflow()
        result = workflow_tester.execute_workflow(nodes, edges, safe_sample_path)
        
        assert result.success, f"Workflow failed: {result.error}"
        
        reports = result.results.get('analyzer_reports', [])
        clamav_report = next((r for r in reports if r['name'] == 'ClamAV'), None)
        assert clamav_report is not None, "ClamAV report not found"
        
        # For safe file, detections should be empty
        detections = clamav_report.get('report', {}).get('detections', [])
        assert len(detections) == 0, f"Expected no detections for safe file, got: {detections}"
    
    def test_clamav_malicious_file(self, workflow_tester, workflow_builder, malicious_sample_path):
        """
        Workflow: File → ClamAV → Result
        Expected: Result shows ClamAV report with EICAR detection
        """
        file_id = workflow_builder.add_file_node()
        analyzer_id = workflow_builder.add_analyzer_node("ClamAV", x=300)
        result_id = workflow_builder.add_result_node(x=500)
        
        workflow_builder.connect(file_id, analyzer_id)
        workflow_builder.connect(analyzer_id, result_id)
        
        nodes, edges = workflow_builder.get_workflow()
        result = workflow_tester.execute_workflow(nodes, edges, malicious_sample_path)
        
        assert result.success, f"Workflow failed: {result.error}"
        
        reports = result.results.get('analyzer_reports', [])
        clamav_report = next((r for r in reports if r['name'] == 'ClamAV'), None)
        assert clamav_report is not None, "ClamAV report not found"
        
        # For EICAR, should have detection
        detections = clamav_report.get('report', {}).get('detections', [])
        assert len(detections) > 0, f"Expected EICAR detection, got: {detections}"


class TestLinearMultipleAnalyzers:
    """Test workflows with multiple analyzers in sequence"""
    
    def test_two_analyzers_sequential(self, workflow_tester, workflow_builder, safe_sample_path):
        """
        Workflow: File → File_Info → ClamAV → Result
        Expected: Result shows BOTH File_Info AND ClamAV reports
        """
        file_id = workflow_builder.add_file_node()
        analyzer1_id = workflow_builder.add_analyzer_node("File_Info", x=300)
        analyzer2_id = workflow_builder.add_analyzer_node("ClamAV", x=500)
        result_id = workflow_builder.add_result_node(x=700)
        
        workflow_builder.connect(file_id, analyzer1_id)
        workflow_builder.connect(analyzer1_id, analyzer2_id)
        workflow_builder.connect(analyzer2_id, result_id)
        
        nodes, edges = workflow_builder.get_workflow()
        result = workflow_tester.execute_workflow(nodes, edges, safe_sample_path)
        
        assert result.success, f"Workflow failed: {result.error}"
        
        reports = result.results.get('analyzer_reports', [])
        analyzer_names = [r['name'] for r in reports]
        
        # CRITICAL: Both analyzers should be in results
        assert 'File_Info' in analyzer_names, f"File_Info missing from {analyzer_names}"
        assert 'ClamAV' in analyzer_names, f"ClamAV missing from {analyzer_names}"
        assert len(reports) >= 2, f"Expected at least 2 reports, got {len(reports)}"
    
    def test_three_analyzers_sequential(self, workflow_tester, workflow_builder, safe_sample_path):
        """
        Workflow: File → File_Info → ClamAV → Strings_Info → Result
        Expected: Result shows all 3 analyzer reports
        """
        file_id = workflow_builder.add_file_node()
        analyzer1_id = workflow_builder.add_analyzer_node("File_Info", x=300)
        analyzer2_id = workflow_builder.add_analyzer_node("ClamAV", x=500)
        analyzer3_id = workflow_builder.add_analyzer_node("Strings_Info", x=700)
        result_id = workflow_builder.add_result_node(x=900)
        
        workflow_builder.connect(file_id, analyzer1_id)
        workflow_builder.connect(analyzer1_id, analyzer2_id)
        workflow_builder.connect(analyzer2_id, analyzer3_id)
        workflow_builder.connect(analyzer3_id, result_id)
        
        nodes, edges = workflow_builder.get_workflow()
        result = workflow_tester.execute_workflow(nodes, edges, safe_sample_path)
        
        assert result.success, f"Workflow failed: {result.error}"
        
        reports = result.results.get('analyzer_reports', [])
        analyzer_names = [r['name'] for r in reports]
        
        assert 'File_Info' in analyzer_names
        assert 'ClamAV' in analyzer_names
        assert 'Strings_Info' in analyzer_names
        assert len(reports) >= 3


class TestLinearBranchingToMultipleResults:
    """Test workflows where analyzers branch to multiple result nodes"""
    
    def test_two_analyzers_two_results(self, workflow_tester, workflow_builder, safe_sample_path):
        """
        Workflow:
        File → File_Info → Result1
             → ClamAV → Result2
        
        Expected:
        - Result1: Only File_Info
        - Result2: Only ClamAV
        """
        file_id = workflow_builder.add_file_node()
        analyzer1_id = workflow_builder.add_analyzer_node("File_Info", x=300, y=100)
        analyzer2_id = workflow_builder.add_analyzer_node("ClamAV", x=300, y=300)
        result1_id = workflow_builder.add_result_node(x=500, y=100)
        result2_id = workflow_builder.add_result_node(x=500, y=300)
        
        workflow_builder.connect(file_id, analyzer1_id)
        workflow_builder.connect(file_id, analyzer2_id)
        workflow_builder.connect(analyzer1_id, result1_id)
        workflow_builder.connect(analyzer2_id, result2_id)
        
        nodes, edges = workflow_builder.get_workflow()
        result = workflow_tester.execute_workflow(nodes, edges, safe_sample_path)
        
        assert result.success, f"Workflow failed: {result.error}"
        
        # Note: The backend returns combined results
        # The frontend is responsible for distributing to correct result nodes
        # This test validates the backend correctly runs both analyzers
        reports = result.results.get('analyzer_reports', [])
        analyzer_names = [r['name'] for r in reports]
        
        assert 'File_Info' in analyzer_names
        assert 'ClamAV' in analyzer_names
    
    def test_shared_first_analyzer_different_seconds(self, workflow_tester, workflow_builder, safe_sample_path):
        """
        Workflow:
        File → File_Info → ClamAV → Result1
                        → Strings_Info → Result2
        
        Expected:
        - Result1: File_Info + ClamAV
        - Result2: File_Info + Strings_Info
        """
        file_id = workflow_builder.add_file_node()
        analyzer1_id = workflow_builder.add_analyzer_node("File_Info", x=300, y=200)
        analyzer2_id = workflow_builder.add_analyzer_node("ClamAV", x=500, y=100)
        analyzer3_id = workflow_builder.add_analyzer_node("Strings_Info", x=500, y=300)
        result1_id = workflow_builder.add_result_node(x=700, y=100)
        result2_id = workflow_builder.add_result_node(x=700, y=300)
        
        workflow_builder.connect(file_id, analyzer1_id)
        workflow_builder.connect(analyzer1_id, analyzer2_id)
        workflow_builder.connect(analyzer1_id, analyzer3_id)
        workflow_builder.connect(analyzer2_id, result1_id)
        workflow_builder.connect(analyzer3_id, result2_id)
        
        nodes, edges = workflow_builder.get_workflow()
        result = workflow_tester.execute_workflow(nodes, edges, safe_sample_path)
        
        assert result.success, f"Workflow failed: {result.error}"
        
        reports = result.results.get('analyzer_reports', [])
        analyzer_names = [r['name'] for r in reports]
        
        # All three analyzers should have run
        assert 'File_Info' in analyzer_names
        assert 'ClamAV' in analyzer_names
        assert 'Strings_Info' in analyzer_names


class TestLinearEdgeCases:
    """Test edge cases for linear workflows"""
    
    def test_single_result_multiple_paths(self, workflow_tester, workflow_builder, safe_sample_path):
        """
        Workflow:
        File → File_Info ─┐
             → ClamAV ───→ Result
        
        Expected: Result shows both analyzers
        """
        file_id = workflow_builder.add_file_node()
        analyzer1_id = workflow_builder.add_analyzer_node("File_Info", x=300, y=100)
        analyzer2_id = workflow_builder.add_analyzer_node("ClamAV", x=300, y=300)
        result_id = workflow_builder.add_result_node(x=500, y=200)
        
        workflow_builder.connect(file_id, analyzer1_id)
        workflow_builder.connect(file_id, analyzer2_id)
        workflow_builder.connect(analyzer1_id, result_id)
        workflow_builder.connect(analyzer2_id, result_id)
        
        nodes, edges = workflow_builder.get_workflow()
        result = workflow_tester.execute_workflow(nodes, edges, safe_sample_path)
        
        assert result.success, f"Workflow failed: {result.error}"
        
        reports = result.results.get('analyzer_reports', [])
        analyzer_names = [r['name'] for r in reports]
        
        assert 'File_Info' in analyzer_names
        assert 'ClamAV' in analyzer_names


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
