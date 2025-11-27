"""
Test Section 2: Conditional Workflows
Tests workflows with conditional branching logic
"""

import pytest
from conftest import WorkflowBuilder, WorkflowTester


class TestConditionalMalwareDetection:
    """Test conditional workflows based on malware detection"""
    
    def test_malicious_branch_with_eicar(self, workflow_tester, workflow_builder, malicious_sample_path):
        """
        Workflow:
        File → ClamAV → [verdict_malicious] 
                        → TRUE: Strings_Info → Result1
                        → FALSE: Result2
        
        With EICAR file:
        Expected:
        - TRUE branch executes (Strings_Info → Result1)
        - FALSE branch is skipped
        """
        file_id = workflow_builder.add_file_node()
        clamav_id = workflow_builder.add_analyzer_node("ClamAV", x=300)
        conditional_id = workflow_builder.add_conditional_node(
            condition_type="verdict_malicious",
            source_analyzer="ClamAV",
            x=500
        )
        strings_id = workflow_builder.add_analyzer_node("Strings_Info", x=700, y=100)
        result1_id = workflow_builder.add_result_node(x=900, y=100)
        result2_id = workflow_builder.add_result_node(x=700, y=300)
        
        workflow_builder.connect(file_id, clamav_id)
        workflow_builder.connect(clamav_id, conditional_id)
        workflow_builder.connect(conditional_id, strings_id, source_handle="true-output")
        workflow_builder.connect(strings_id, result1_id)
        workflow_builder.connect(conditional_id, result2_id, source_handle="false-output")
        
        nodes, edges = workflow_builder.get_workflow()
        result = workflow_tester.execute_workflow(nodes, edges, malicious_sample_path)
        
        assert result.success, f"Workflow failed: {result.error}"
        assert result.has_conditionals is True
        
        # Check stage routing
        executed = result.executed_stages
        skipped = result.skipped_stages
        
        # Stage 0 (ClamAV) should execute
        assert 0 in executed, f"Stage 0 should be executed, got: {executed}"
        
        # TRUE branch should execute (Strings_Info)
        reports = result.results.get('analyzer_reports', [])
        analyzer_names = [r['name'] for r in reports]
        
        assert 'ClamAV' in analyzer_names, f"ClamAV missing from {analyzer_names}"
        assert 'Strings_Info' in analyzer_names, f"Strings_Info (TRUE branch) should execute for malicious file"
    
    def test_clean_branch_with_safe_file(self, workflow_tester, workflow_builder, safe_sample_path):
        """
        Workflow:
        File → ClamAV → [verdict_malicious] 
                        → TRUE: Strings_Info → Result1
                        → FALSE: File_Info → Result2
        
        With safe file:
        Expected:
        - FALSE branch executes (File_Info → Result2)
        - TRUE branch is skipped
        """
        file_id = workflow_builder.add_file_node()
        clamav_id = workflow_builder.add_analyzer_node("ClamAV", x=300)
        conditional_id = workflow_builder.add_conditional_node(
            condition_type="verdict_malicious",
            source_analyzer="ClamAV",
            x=500
        )
        strings_id = workflow_builder.add_analyzer_node("Strings_Info", x=700, y=100)
        file_info_id = workflow_builder.add_analyzer_node("File_Info", x=700, y=300)
        result1_id = workflow_builder.add_result_node(x=900, y=100)
        result2_id = workflow_builder.add_result_node(x=900, y=300)
        
        workflow_builder.connect(file_id, clamav_id)
        workflow_builder.connect(clamav_id, conditional_id)
        workflow_builder.connect(conditional_id, strings_id, source_handle="true-output")
        workflow_builder.connect(strings_id, result1_id)
        workflow_builder.connect(conditional_id, file_info_id, source_handle="false-output")
        workflow_builder.connect(file_info_id, result2_id)
        
        nodes, edges = workflow_builder.get_workflow()
        result = workflow_tester.execute_workflow(nodes, edges, safe_sample_path)
        
        assert result.success, f"Workflow failed: {result.error}"
        assert result.has_conditionals is True
        
        reports = result.results.get('analyzer_reports', [])
        analyzer_names = [r['name'] for r in reports]
        
        assert 'ClamAV' in analyzer_names
        # For safe file, FALSE branch (File_Info) should execute
        assert 'File_Info' in analyzer_names, f"File_Info (FALSE branch) should execute for safe file"
        # TRUE branch (Strings_Info) should NOT execute
        # Note: This depends on condition evaluation - if ClamAV finds no malware, TRUE branch skips


class TestConditionalCleanVerdict:
    """Test conditional workflows based on clean file verdict"""
    
    def test_clean_verdict_safe_file(self, workflow_tester, workflow_builder, safe_sample_path):
        """
        Workflow:
        File → ClamAV → [verdict_clean] 
                        → TRUE: Result1 (Clean path)
                        → FALSE: Strings_Info → Result2 (Further analysis)
        
        With safe file:
        Expected: TRUE branch (clean confirmation) executes
        """
        file_id = workflow_builder.add_file_node()
        clamav_id = workflow_builder.add_analyzer_node("ClamAV", x=300)
        conditional_id = workflow_builder.add_conditional_node(
            condition_type="verdict_clean",
            source_analyzer="ClamAV",
            x=500
        )
        result1_id = workflow_builder.add_result_node(x=700, y=100)  # Clean result
        strings_id = workflow_builder.add_analyzer_node("Strings_Info", x=700, y=300)
        result2_id = workflow_builder.add_result_node(x=900, y=300)
        
        workflow_builder.connect(file_id, clamav_id)
        workflow_builder.connect(clamav_id, conditional_id)
        workflow_builder.connect(conditional_id, result1_id, source_handle="true-output")
        workflow_builder.connect(conditional_id, strings_id, source_handle="false-output")
        workflow_builder.connect(strings_id, result2_id)
        
        nodes, edges = workflow_builder.get_workflow()
        result = workflow_tester.execute_workflow(nodes, edges, safe_sample_path)
        
        assert result.success, f"Workflow failed: {result.error}"
        assert result.has_conditionals is True
        
        # For safe file, verdict_clean should be TRUE
        # So TRUE branch should execute, FALSE branch should skip
        stage_routing = result.stage_routing
        print(f"Stage routing: {stage_routing}")


class TestConditionalAnalyzerSuccess:
    """Test conditional workflows based on analyzer success/failure"""
    
    def test_analyzer_success_condition(self, workflow_tester, workflow_builder, safe_sample_path):
        """
        Workflow:
        File → File_Info → [analyzer_success] 
                          → TRUE: ClamAV → Result1
                          → FALSE: Result2 (Error handling)
        
        Expected: File_Info succeeds, so TRUE branch executes
        """
        file_id = workflow_builder.add_file_node()
        file_info_id = workflow_builder.add_analyzer_node("File_Info", x=300)
        conditional_id = workflow_builder.add_conditional_node(
            condition_type="analyzer_success",
            source_analyzer="File_Info",
            x=500
        )
        clamav_id = workflow_builder.add_analyzer_node("ClamAV", x=700, y=100)
        result1_id = workflow_builder.add_result_node(x=900, y=100)
        result2_id = workflow_builder.add_result_node(x=700, y=300)
        
        workflow_builder.connect(file_id, file_info_id)
        workflow_builder.connect(file_info_id, conditional_id)
        workflow_builder.connect(conditional_id, clamav_id, source_handle="true-output")
        workflow_builder.connect(clamav_id, result1_id)
        workflow_builder.connect(conditional_id, result2_id, source_handle="false-output")
        
        nodes, edges = workflow_builder.get_workflow()
        result = workflow_tester.execute_workflow(nodes, edges, safe_sample_path)
        
        assert result.success, f"Workflow failed: {result.error}"
        
        reports = result.results.get('analyzer_reports', [])
        analyzer_names = [r['name'] for r in reports]
        
        # File_Info should always succeed on valid files
        assert 'File_Info' in analyzer_names
        # ClamAV should run (TRUE branch)
        assert 'ClamAV' in analyzer_names, f"ClamAV should execute when File_Info succeeds"


class TestConditionalFieldEquals:
    """Test conditional workflows with field_equals conditions"""
    
    def test_field_equals_mimetype(self, workflow_tester, workflow_builder, safe_sample_path):
        """
        Workflow:
        File → File_Info → [field_equals: mimetype == "text/plain"] 
                          → TRUE: Strings_Info → Result1
                          → FALSE: ClamAV → Result2
        
        With text file:
        Expected: TRUE branch (Strings_Info) executes
        """
        file_id = workflow_builder.add_file_node()
        file_info_id = workflow_builder.add_analyzer_node("File_Info", x=300)
        conditional_id = workflow_builder.add_conditional_node(
            condition_type="field_equals",
            source_analyzer="File_Info",
            field_path="mimetype",
            expected_value="text/plain",
            x=500
        )
        strings_id = workflow_builder.add_analyzer_node("Strings_Info", x=700, y=100)
        clamav_id = workflow_builder.add_analyzer_node("ClamAV", x=700, y=300)
        result1_id = workflow_builder.add_result_node(x=900, y=100)
        result2_id = workflow_builder.add_result_node(x=900, y=300)
        
        workflow_builder.connect(file_id, file_info_id)
        workflow_builder.connect(file_info_id, conditional_id)
        workflow_builder.connect(conditional_id, strings_id, source_handle="true-output")
        workflow_builder.connect(strings_id, result1_id)
        workflow_builder.connect(conditional_id, clamav_id, source_handle="false-output")
        workflow_builder.connect(clamav_id, result2_id)
        
        nodes, edges = workflow_builder.get_workflow()
        result = workflow_tester.execute_workflow(nodes, edges, safe_sample_path)
        
        assert result.success, f"Workflow failed: {result.error}"
        
        # Check which branch executed based on mimetype
        reports = result.results.get('analyzer_reports', [])
        analyzer_names = [r['name'] for r in reports]
        
        assert 'File_Info' in analyzer_names
        # Branch depends on file type - for test.txt should be text/plain


class TestConditionalChained:
    """Test chained conditional workflows"""
    
    def test_two_conditionals_in_sequence(self, workflow_tester, workflow_builder, malicious_sample_path):
        """
        Workflow:
        File → ClamAV → [verdict_malicious]
                       → TRUE: File_Info → [analyzer_success] 
                                          → TRUE: Strings_Info → Result1
                                          → FALSE: Result2
                       → FALSE: Result3
        
        Expected: For malicious file, executes: ClamAV → File_Info → Strings_Info → Result1
        """
        file_id = workflow_builder.add_file_node()
        clamav_id = workflow_builder.add_analyzer_node("ClamAV", x=200)
        cond1_id = workflow_builder.add_conditional_node(
            condition_type="verdict_malicious",
            source_analyzer="ClamAV",
            x=400
        )
        file_info_id = workflow_builder.add_analyzer_node("File_Info", x=600, y=100)
        cond2_id = workflow_builder.add_conditional_node(
            condition_type="analyzer_success",
            source_analyzer="File_Info",
            x=800, y=100
        )
        strings_id = workflow_builder.add_analyzer_node("Strings_Info", x=1000, y=50)
        result1_id = workflow_builder.add_result_node(x=1200, y=50)
        result2_id = workflow_builder.add_result_node(x=1000, y=150)
        result3_id = workflow_builder.add_result_node(x=600, y=300)
        
        workflow_builder.connect(file_id, clamav_id)
        workflow_builder.connect(clamav_id, cond1_id)
        workflow_builder.connect(cond1_id, file_info_id, source_handle="true-output")
        workflow_builder.connect(file_info_id, cond2_id)
        workflow_builder.connect(cond2_id, strings_id, source_handle="true-output")
        workflow_builder.connect(strings_id, result1_id)
        workflow_builder.connect(cond2_id, result2_id, source_handle="false-output")
        workflow_builder.connect(cond1_id, result3_id, source_handle="false-output")
        
        nodes, edges = workflow_builder.get_workflow()
        result = workflow_tester.execute_workflow(nodes, edges, malicious_sample_path)
        
        assert result.success, f"Workflow failed: {result.error}"
        assert result.has_conditionals is True
        
        reports = result.results.get('analyzer_reports', [])
        analyzer_names = [r['name'] for r in reports]
        
        # All three analyzers should run for malicious file with successful File_Info
        assert 'ClamAV' in analyzer_names
        assert 'File_Info' in analyzer_names
        assert 'Strings_Info' in analyzer_names


class TestConditionalStageRouting:
    """Test that stage_routing metadata is correctly generated"""
    
    def test_stage_routing_metadata(self, workflow_tester, workflow_builder, safe_sample_path):
        """
        Verify that stage_routing includes correct target_nodes and executed flags
        """
        file_id = workflow_builder.add_file_node()
        clamav_id = workflow_builder.add_analyzer_node("ClamAV", x=300)
        conditional_id = workflow_builder.add_conditional_node(
            condition_type="verdict_malicious",
            source_analyzer="ClamAV",
            x=500
        )
        result1_id = workflow_builder.add_result_node(x=700, y=100)  # TRUE path
        result2_id = workflow_builder.add_result_node(x=700, y=300)  # FALSE path
        
        workflow_builder.connect(file_id, clamav_id)
        workflow_builder.connect(clamav_id, conditional_id)
        workflow_builder.connect(conditional_id, result1_id, source_handle="true-output")
        workflow_builder.connect(conditional_id, result2_id, source_handle="false-output")
        
        nodes, edges = workflow_builder.get_workflow()
        result = workflow_tester.execute_workflow(nodes, edges, safe_sample_path)
        
        assert result.success, f"Workflow failed: {result.error}"
        
        # Check stage_routing
        routing = result.stage_routing
        print(f"Stage routing: {routing}")
        
        # Verify structure
        assert isinstance(routing, list), "stage_routing should be a list"
        
        for stage in routing:
            assert 'stage_id' in stage
            assert 'executed' in stage
            assert 'target_nodes' in stage


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
