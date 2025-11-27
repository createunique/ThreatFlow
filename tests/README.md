# ThreatFlow Test Suite

This directory contains comprehensive tests for the ThreatFlow workflow execution system.

## Test Structure

```
tests/
├── conftest.py                    # Pytest fixtures and utilities
├── pytest.ini                     # Pytest configuration
├── run_tests.sh                   # Test runner script
├── test_linear_workflows.py       # Linear workflow tests
├── test_conditional_workflows.py  # Conditional branching tests
├── test_combined_workflows.py     # Complex combined workflow tests
├── test_distribution_logic.py     # Unit tests for distribution logic
└── test_api_integration.py        # API integration tests
```

## Quick Start

### 1. Run All Tests
```bash
cd tests
chmod +x run_tests.sh
./run_tests.sh all
```

### 2. Run Unit Tests Only (No External Services)
```bash
./run_tests.sh unit
```

### 3. Run Specific Test Categories
```bash
./run_tests.sh linear        # Linear workflow tests
./run_tests.sh conditional   # Conditional workflow tests
./run_tests.sh combined      # Complex workflow tests
./run_tests.sh api           # API integration tests
```

## Prerequisites

### Install Dependencies
```bash
pip install pytest pytest-timeout requests
```

### Start Services
For integration tests, ensure the middleware is running:
```bash
cd threatflow-middleware
uvicorn app.main:app --port 8030
```

## Test Categories

### 1. Linear Workflows (`test_linear_workflows.py`)
Tests basic sequential workflows:
- Single analyzer to result
- Multiple analyzers in chain
- Parallel branches to single result
- Multiple file sources

### 2. Conditional Workflows (`test_conditional_workflows.py`)
Tests conditional branching:
- `verdict_malicious` condition with EICAR files
- `verdict_clean` condition with safe files
- `analyzer_success` condition
- `field_equals` condition
- Chained conditionals

### 3. Combined Workflows (`test_combined_workflows.py`)
Tests complex patterns:
- Diamond patterns (split and merge)
- Multi-result distribution
- Conditionals with parallel paths
- Shared analyzers in multiple branches
- Three-stage conditional chains

### 4. Distribution Logic (`test_distribution_logic.py`)
Unit tests for frontend distribution:
- Graph traversal distribution
- Stage routing distribution
- Edge cases (empty results, duplicates)

### 5. API Integration (`test_api_integration.py`)
Tests actual API behavior:
- Health checks
- Workflow execution
- Stage routing metadata

## Test Samples

Tests use files from `/testing_responses/Malware safe Malware samples/`:
- **Safe samples**: `safe/test.txt`, `safe/safe.pdf`
- **Malicious samples**: `malicious/eicar.com`

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MIDDLEWARE_URL` | `http://localhost:8030` | Middleware API URL |
| `FRONTEND_URL` | `http://localhost:3000` | Frontend URL (for reference) |
| `THREATFLOW_API_URL` | `http://localhost:8001` | Alternative API URL |

## Writing New Tests

### Use WorkflowBuilder
```python
def test_my_workflow(workflow_tester, workflow_builder, safe_sample_path):
    # Build workflow
    file_id = workflow_builder.add_file_node()
    analyzer_id = workflow_builder.add_analyzer_node("ClamAV", x=300)
    result_id = workflow_builder.add_result_node(x=500)
    
    workflow_builder.connect(file_id, analyzer_id)
    workflow_builder.connect(analyzer_id, result_id)
    
    # Execute
    nodes, edges = workflow_builder.get_workflow()
    result = workflow_tester.execute_workflow(nodes, edges, safe_sample_path)
    
    # Assert
    assert result.success
    assert 'ClamAV' in [r['name'] for r in result.results.get('analyzer_reports', [])]
```

### Conditional Workflows
```python
conditional_id = workflow_builder.add_conditional_node(
    condition_type="verdict_malicious",
    source_analyzer="ClamAV",
    x=500
)
workflow_builder.connect(conditional_id, result_true, source_handle="true-output")
workflow_builder.connect(conditional_id, result_false, source_handle="false-output")
```

## Debugging

### Verbose Output
```bash
pytest -v -s test_file.py
```

### Run Single Test
```bash
pytest test_file.py::TestClass::test_method -v -s
```

### Show Stage Routing
Tests print `stage_routing` metadata for debugging conditional paths.

## Expected Results

### Linear Workflows
- All analyzers in path should appear in result's `analyzer_reports`
- Multiple analyzers should all be present

### Conditional Workflows
- Executed branch analyzers should appear in corresponding result node
- Skipped branch analyzers should NOT appear
- `stage_routing` should show `executed: true/false` for each stage

## Troubleshooting

### "Middleware not available"
Ensure middleware is running:
```bash
curl http://localhost:8030/health/
```

### "Analyzer not found"
Check available analyzers:
```bash
curl http://localhost:8030/api/analyzers
```

### Tests timeout
Increase timeout in pytest.ini or use `-o timeout=600`
