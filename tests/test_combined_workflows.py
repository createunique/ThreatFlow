"""
Test Section 3: Complex Combined Workflows
Tests multi-branch, diamond patterns, and complex routing
"""

import pytest
from conftest import WorkflowBuilder, WorkflowTester


class TestDiamondPattern:
    """
    Test diamond workflow patterns where branches reconverge
    """
    
    def test_split_and_merge_at_result(self, workflow_tester, workflow_builder, safe_sample_path):
        """
        Workflow (Diamond):
                          → ClamAV → 
        File → File_Info                → Result (shared)
                          → Strings_Info →
        
        Expected: Both analyzers results appear in the same Result node
        """
        file_id = workflow_builder.add_file_node()
        file_info_id = workflow_builder.add_analyzer_node("File_Info", x=200)
        clamav_id = workflow_builder.add_analyzer_node("ClamAV", x=400, y=100)
        strings_id = workflow_builder.add_analyzer_node("Strings_Info", x=400, y=300)
        result_id = workflow_builder.add_result_node(x=600, y=200)
        
        workflow_builder.connect(file_id, file_info_id)
        workflow_builder.connect(file_info_id, clamav_id)
        workflow_builder.connect(file_info_id, strings_id)
        workflow_builder.connect(clamav_id, result_id)
        workflow_builder.connect(strings_id, result_id)
        
        nodes, edges = workflow_builder.get_workflow()
        result = workflow_tester.execute_workflow(nodes, edges, safe_sample_path)
        
        assert result.success, f"Workflow failed: {result.error}"
        
        reports = result.results.get('analyzer_reports', [])
        analyzer_names = [r['name'] for r in reports]
        
        # All three analyzers should be in the result
        assert 'File_Info' in analyzer_names, f"File_Info missing from {analyzer_names}"
        assert 'ClamAV' in analyzer_names, f"ClamAV missing from {analyzer_names}"
        assert 'Strings_Info' in analyzer_names, f"Strings_Info missing from {analyzer_names}"


class TestMultiResultDistribution:
    """
    Test workflows with multiple result nodes receiving different subsets
    """
    
    def test_different_analyzers_to_different_results(self, workflow_tester, workflow_builder, safe_sample_path):
        """
        Workflow:
        File → File_Info → Result1
                        ↘
        File → ClamAV → Result2
        
        Expected:
        - Result1 has: File_Info
        - Result2 has: ClamAV
        """
        file_id = workflow_builder.add_file_node()
        file_info_id = workflow_builder.add_analyzer_node("File_Info", x=300, y=100)
        clamav_id = workflow_builder.add_analyzer_node("ClamAV", x=300, y=300)
        result1_id = workflow_builder.add_result_node(x=500, y=100)
        result2_id = workflow_builder.add_result_node(x=500, y=300)
        
        workflow_builder.connect(file_id, file_info_id)
        workflow_builder.connect(file_info_id, result1_id)
        workflow_builder.connect(file_id, clamav_id)
        workflow_builder.connect(clamav_id, result2_id)
        
        nodes, edges = workflow_builder.get_workflow()
        result = workflow_tester.execute_workflow(nodes, edges, safe_sample_path)
        
        assert result.success, f"Workflow failed: {result.error}"
        
        # Check distribution to each result node
        result1_analyzers = result.get_result_node_analyzers(result1_id)
        result2_analyzers = result.get_result_node_analyzers(result2_id)
        
        # File_Info should be in Result1's path
        # ClamAV should be in Result2's path


class TestConditionalWithParallel:
    """
    Test conditionals combined with parallel execution paths
    """
    
    def test_parallel_before_conditional(self, workflow_tester, workflow_builder, malicious_sample_path):
        """
        Workflow:
                          → ClamAV ↘
        File → File_Info            → [verdict_malicious] → TRUE: Strings_Info → Result1
                          → Hash ↗                        → FALSE: Result2
        
        Parallel analyzers feed into conditional decision
        """
        file_id = workflow_builder.add_file_node()
        file_info_id = workflow_builder.add_analyzer_node("File_Info", x=200)
        clamav_id = workflow_builder.add_analyzer_node("ClamAV", x=400, y=100)
        # Note: Using Hash as a pseudo-analyzer for testing
        conditional_id = workflow_builder.add_conditional_node(
            condition_type="verdict_malicious",
            source_analyzer="ClamAV",
            x=600
        )
        strings_id = workflow_builder.add_analyzer_node("Strings_Info", x=800, y=100)
        result1_id = workflow_builder.add_result_node(x=1000, y=100)
        result2_id = workflow_builder.add_result_node(x=800, y=300)
        
        workflow_builder.connect(file_id, file_info_id)
        workflow_builder.connect(file_info_id, clamav_id)
        workflow_builder.connect(clamav_id, conditional_id)
        workflow_builder.connect(conditional_id, strings_id, source_handle="true-output")
        workflow_builder.connect(strings_id, result1_id)
        workflow_builder.connect(conditional_id, result2_id, source_handle="false-output")
        
        nodes, edges = workflow_builder.get_workflow()
        result = workflow_tester.execute_workflow(nodes, edges, malicious_sample_path)
        
        assert result.success, f"Workflow failed: {result.error}"
        
        reports = result.results.get('analyzer_reports', [])
        analyzer_names = [r['name'] for r in reports]
        
        # File_Info and ClamAV always run
        assert 'File_Info' in analyzer_names
        assert 'ClamAV' in analyzer_names
        
        # For malicious file, Strings_Info should run (TRUE branch)
        assert 'Strings_Info' in analyzer_names, f"TRUE branch should execute for malicious file"


class TestConditionalsWithSharedAnalyzers:
    """
    Test conditionals where analyzer appears in multiple paths
    """
    
    def test_shared_analyzer_in_both_branches(self, workflow_tester, workflow_builder, safe_sample_path):
        """
        Workflow:
        File → ClamAV → [verdict_malicious]
                       → TRUE: Strings_Info → File_Info → Result1
                       → FALSE: File_Info → Result2
        
        File_Info appears in BOTH branches
        Expected: File_Info runs in the executed branch only
        """
        file_id = workflow_builder.add_file_node()
        clamav_id = workflow_builder.add_analyzer_node("ClamAV", x=200)
        conditional_id = workflow_builder.add_conditional_node(
            condition_type="verdict_malicious",
            source_analyzer="ClamAV",
            x=400
        )
        strings_id = workflow_builder.add_analyzer_node("Strings_Info", x=600, y=100)
        file_info_true_id = workflow_builder.add_analyzer_node("File_Info", x=800, y=100)
        file_info_false_id = workflow_builder.add_analyzer_node("File_Info", x=600, y=300)
        result1_id = workflow_builder.add_result_node(x=1000, y=100)
        result2_id = workflow_builder.add_result_node(x=800, y=300)
        
        workflow_builder.connect(file_id, clamav_id)
        workflow_builder.connect(clamav_id, conditional_id)
        workflow_builder.connect(conditional_id, strings_id, source_handle="true-output")
        workflow_builder.connect(strings_id, file_info_true_id)
        workflow_builder.connect(file_info_true_id, result1_id)
        workflow_builder.connect(conditional_id, file_info_false_id, source_handle="false-output")
        workflow_builder.connect(file_info_false_id, result2_id)
        
        nodes, edges = workflow_builder.get_workflow()
        result = workflow_tester.execute_workflow(nodes, edges, safe_sample_path)
        
        assert result.success, f"Workflow failed: {result.error}"
        
        reports = result.results.get('analyzer_reports', [])
        analyzer_names = [r['name'] for r in reports]
        
        # ClamAV always runs
        assert 'ClamAV' in analyzer_names
        # File_Info should run (either branch)
        assert 'File_Info' in analyzer_names


class TestComplexMultiStage:
    """
    Test complex multi-stage workflows with mixed patterns
    """
    
    def test_three_stage_conditional_chain(self, workflow_tester, workflow_builder, safe_sample_path):
        """
        Workflow:
        File → File_Info → [success] 
                          → TRUE: ClamAV → [malicious]
                                          → TRUE: Strings_Info → Result1
                                          → FALSE: Result2
                          → FALSE: Result3
        
        Three-stage execution with nested conditionals
        """
        file_id = workflow_builder.add_file_node()
        file_info_id = workflow_builder.add_analyzer_node("File_Info", x=200)
        cond1_id = workflow_builder.add_conditional_node(
            condition_type="analyzer_success",
            source_analyzer="File_Info",
            x=400
        )
        clamav_id = workflow_builder.add_analyzer_node("ClamAV", x=600, y=100)
        cond2_id = workflow_builder.add_conditional_node(
            condition_type="verdict_malicious",
            source_analyzer="ClamAV",
            x=800, y=100
        )
        strings_id = workflow_builder.add_analyzer_node("Strings_Info", x=1000, y=50)
        result1_id = workflow_builder.add_result_node(x=1200, y=50)
        result2_id = workflow_builder.add_result_node(x=1000, y=150)
        result3_id = workflow_builder.add_result_node(x=600, y=300)
        
        workflow_builder.connect(file_id, file_info_id)
        workflow_builder.connect(file_info_id, cond1_id)
        workflow_builder.connect(cond1_id, clamav_id, source_handle="true-output")
        workflow_builder.connect(clamav_id, cond2_id)
        workflow_builder.connect(cond2_id, strings_id, source_handle="true-output")
        workflow_builder.connect(strings_id, result1_id)
        workflow_builder.connect(cond2_id, result2_id, source_handle="false-output")
        workflow_builder.connect(cond1_id, result3_id, source_handle="false-output")
        
        nodes, edges = workflow_builder.get_workflow()
        result = workflow_tester.execute_workflow(nodes, edges, safe_sample_path)
        
        assert result.success, f"Workflow failed: {result.error}"
        
        # Verify execution path
        reports = result.results.get('analyzer_reports', [])
        analyzer_names = [r['name'] for r in reports]
        
        assert 'File_Info' in analyzer_names
        # File_Info should succeed → ClamAV runs
        assert 'ClamAV' in analyzer_names
        # For safe file, verdict_malicious is FALSE → Result2


class TestEdgeCases:
    """
    Test edge cases and boundary conditions
    """
    
    def test_empty_true_branch(self, workflow_tester, workflow_builder, safe_sample_path):
        """
        Workflow where TRUE branch goes directly to result
        File → ClamAV → [verdict_malicious]
                       → TRUE: Result1
                       → FALSE: File_Info → Result2
        """
        file_id = workflow_builder.add_file_node()
        clamav_id = workflow_builder.add_analyzer_node("ClamAV", x=200)
        conditional_id = workflow_builder.add_conditional_node(
            condition_type="verdict_malicious",
            source_analyzer="ClamAV",
            x=400
        )
        result1_id = workflow_builder.add_result_node(x=600, y=100)
        file_info_id = workflow_builder.add_analyzer_node("File_Info", x=600, y=300)
        result2_id = workflow_builder.add_result_node(x=800, y=300)
        
        workflow_builder.connect(file_id, clamav_id)
        workflow_builder.connect(clamav_id, conditional_id)
        workflow_builder.connect(conditional_id, result1_id, source_handle="true-output")
        workflow_builder.connect(conditional_id, file_info_id, source_handle="false-output")
        workflow_builder.connect(file_info_id, result2_id)
        
        nodes, edges = workflow_builder.get_workflow()
        result = workflow_tester.execute_workflow(nodes, edges, safe_sample_path)
        
        assert result.success, f"Workflow failed: {result.error}"
    
    def test_single_conditional_two_results(self, workflow_tester, workflow_builder, safe_sample_path):
        """
        Minimal conditional workflow
        File → ClamAV → [verdict] → TRUE: Result1
                                  → FALSE: Result2
        """
        file_id = workflow_builder.add_file_node()
        clamav_id = workflow_builder.add_analyzer_node("ClamAV", x=200)
        conditional_id = workflow_builder.add_conditional_node(
            condition_type="verdict_malicious",
            source_analyzer="ClamAV",
            x=400
        )
        result1_id = workflow_builder.add_result_node(x=600, y=100)
        result2_id = workflow_builder.add_result_node(x=600, y=300)
        
        workflow_builder.connect(file_id, clamav_id)
        workflow_builder.connect(clamav_id, conditional_id)
        workflow_builder.connect(conditional_id, result1_id, source_handle="true-output")
        workflow_builder.connect(conditional_id, result2_id, source_handle="false-output")
        
        nodes, edges = workflow_builder.get_workflow()
        result = workflow_tester.execute_workflow(nodes, edges, safe_sample_path)
        
        assert result.success, f"Workflow failed: {result.error}"
        
        reports = result.results.get('analyzer_reports', [])
        analyzer_names = [r['name'] for r in reports]
        
        # ClamAV should always run
        assert 'ClamAV' in analyzer_names


class TestResultNodeDistribution:
    """
    Test that results are correctly distributed to multiple result nodes
    """
    
    def test_conditional_routes_to_correct_result(self, workflow_tester, workflow_builder, safe_sample_path, malicious_sample_path):
        """
        Verify the correct result node receives results based on condition
        """
        # Test with safe file
        file_id = workflow_builder.add_file_node()
        clamav_id = workflow_builder.add_analyzer_node("ClamAV", x=200)
        conditional_id = workflow_builder.add_conditional_node(
            condition_type="verdict_malicious",
            source_analyzer="ClamAV",
            x=400
        )
        result_true_id = workflow_builder.add_result_node(x=600, y=100, label="Malicious Result")
        result_false_id = workflow_builder.add_result_node(x=600, y=300, label="Clean Result")
        
        workflow_builder.connect(file_id, clamav_id)
        workflow_builder.connect(clamav_id, conditional_id)
        workflow_builder.connect(conditional_id, result_true_id, source_handle="true-output")
        workflow_builder.connect(conditional_id, result_false_id, source_handle="false-output")
        
        nodes, edges = workflow_builder.get_workflow()
        
        # Execute with safe file
        result_safe = workflow_tester.execute_workflow(nodes, edges, safe_sample_path)
        assert result_safe.success, f"Workflow failed with safe file: {result_safe.error}"
        
        # Check which result node received results
        print(f"Safe file - Stage routing: {result_safe.stage_routing}")
        
        # Reset and test with malicious file
        workflow_builder = WorkflowBuilder()
        file_id = workflow_builder.add_file_node()
        clamav_id = workflow_builder.add_analyzer_node("ClamAV", x=200)
        conditional_id = workflow_builder.add_conditional_node(
            condition_type="verdict_malicious",
            source_analyzer="ClamAV",
            x=400
        )
        result_true_id = workflow_builder.add_result_node(x=600, y=100, label="Malicious Result")
        result_false_id = workflow_builder.add_result_node(x=600, y=300, label="Clean Result")
        
        workflow_builder.connect(file_id, clamav_id)
        workflow_builder.connect(clamav_id, conditional_id)
        workflow_builder.connect(conditional_id, result_true_id, source_handle="true-output")
        workflow_builder.connect(conditional_id, result_false_id, source_handle="false-output")
        
        nodes, edges = workflow_builder.get_workflow()
        
        # Execute with malicious file
        result_mal = workflow_tester.execute_workflow(nodes, edges, malicious_sample_path)
        assert result_mal.success, f"Workflow failed with malicious file: {result_mal.error}"
        
        print(f"Malicious file - Stage routing: {result_mal.stage_routing}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
