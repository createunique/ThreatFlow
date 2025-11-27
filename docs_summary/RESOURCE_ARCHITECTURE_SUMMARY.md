# ThreatFlow Architecture Resource Summary

## Overview
ThreatFlow is a visual workflow builder for IntelOwl malware analysis. This document maps all resources responsible for:
1. **Result Display** - How analysis results are shown in the UI
2. **Conditional Logic** - How conditional branching works
3. **Workflow Execution** - How workflows are executed

---

## 🎨 FRONTEND (`threatflow-frontend/src/`)

### Core Workflow Hooks

| File | Purpose | Key Functions |
|------|---------|---------------|
| `hooks/useWorkflowExecution.ts` | **MAIN EXECUTION LOGIC** - Submits workflows, polls status, distributes results | `executeWorkflow()`, `distributeResultsToResultNodes()`, `distributeUsingStageRouting()`, `distributeUsingGraphTraversal()`, `findAnalyzersInPath()` |
| `hooks/useWorkflowState.ts` | Zustand store for workflow state management | `addNode()`, `updateNode()`, `deleteNode()`, `setExecutionStatus()` |

### Custom Nodes (UI Components)

| File | Purpose | Key Data |
|------|---------|----------|
| `components/Canvas/CustomNodes/FileNode.tsx` | File upload dropzone | Stores `file`, `fileName`, `fileSize` |
| `components/Canvas/CustomNodes/AnalyzerNode.tsx` | Analyzer selection | Stores `analyzer`, `analyzerType`, `description` |
| `components/Canvas/CustomNodes/ConditionalNode.tsx` | Conditional branching node | Stores `conditionType`, `sourceAnalyzer`, `fieldPath`, `expectedValue` |
| `components/Canvas/CustomNodes/ResultNode.tsx` | **RESULT DISPLAY** - Shows analysis results | Stores `jobId`, `status`, `results`, `error` |
| `components/Canvas/CustomNodes/ResultTabs.tsx` | **RESULT RENDERING** - Formats analyzer reports | Renders `analyzer_reports[]` with accordion UI |

### Services

| File | Purpose | Key Methods |
|------|---------|-------------|
| `services/api.ts` | HTTP client for middleware | `executeWorkflow()`, `getJobStatus()`, `pollJobStatus()`, `getAnalyzers()` |

### Types

| File | Key Types |
|------|-----------|
| `types/workflow.ts` | `CustomNode`, `ResultNodeData`, `ConditionalNodeData`, `StageRouting`, `JobStatusResponse`, `ExecuteWorkflowResponse` |

---

## 🔧 BACKEND (`threatflow-middleware/app/`)

### Routers (API Endpoints)

| File | Endpoints | Purpose |
|------|-----------|---------|
| `routers/execute.py` | `POST /api/execute`, `GET /api/status/{job_id}`, `GET /api/analyzers` | **MAIN EXECUTION ENDPOINT** - Parses workflow, submits to IntelOwl, returns `stage_routing` metadata |

### Services

| File | Purpose | Key Methods |
|------|---------|-------------|
| `services/intelowl_service.py` | **INTELOWL CLIENT** - Submits files, polls results, evaluates conditions | `submit_file_analysis()`, `execute_workflow_with_conditionals()`, `_evaluate_condition()`, `_check_malicious()`, `_check_clean()` |
| `services/workflow_parser.py` | **WORKFLOW PARSING** - Converts React Flow JSON to execution stages | `parse()`, `_parse_conditional_workflow()`, `_build_conditional_stages()` |
| `services/condition_evaluator.py` | Mixin for condition evaluation strategies | `_evaluate_with_schema_fallback()`, `_evaluate_generic_fallback()`, `_get_safe_default()` |
| `services/analyzer_schema.py` | Schema definitions for all 18 analyzers | Field mappings, validation, malware indicator detection |

### Models

| File | Key Classes |
|------|-------------|
| `models/workflow.py` | `WorkflowNode`, `WorkflowEdge`, `WorkflowRequest`, `JobStatusResponse`, `NodeType`, `ConditionType` |

---

## 📊 DATA FLOW: Result Distribution

### 1. Backend Generates Stage Routing
```python
# execute.py - Line ~55
stage_routing = []
for stage in stages:
    stage_routing.append({
        "stage_id": stage["stage_id"],
        "target_nodes": stage.get("target_nodes", []),  # Result node IDs
        "executed": stage["stage_id"] in result["executed_stages"],
        "analyzers": stage.get("analyzers", [])
    })
```

### 2. Frontend Receives and Distributes
```typescript
// useWorkflowExecution.ts - executeWorkflow()
distributeResultsToResultNodes(
    finalStatus.results,      // IntelOwl job results
    finalStatus.stage_routing, // Backend routing metadata
    hasConditionals,
    nodes,
    edges,
    updateNode
);
```

### 3. Result Node Updates
```typescript
// ResultNode displays:
// - data.status: "reported_without_fails" | "running" | "failed" | "idle"
// - data.results: { analyzer_name: {...}, ... } or { analyzer_reports: [...] }
// - data.error: "Branch not executed" (for skipped conditional branches)
```

---

## 🔀 CONDITIONAL LOGIC FLOW

### 1. Parser Extracts Condition
```python
# workflow_parser.py
condition_config = {
    "type": "verdict_malicious",  # or field_equals, yara_rule_match, etc.
    "source_analyzer": "ClamAV",
    "field_path": "detections",    # for field-based conditions
    "expected_value": [],          # for comparison
    "negate": True/False           # for FALSE branches
}
```

### 2. Evaluator Checks Condition
```python
# intelowl_service.py - _evaluate_condition()
# Multi-level fallback:
# 1. PRIMARY: Direct field access
# 2. SCHEMA_FALLBACK: Schema-defined patterns
# 3. GENERIC_FALLBACK: Pattern matching
# 4. SAFE_DEFAULT: Conservative assumption
```

### 3. Stage Execution Decision
```python
# intelowl_service.py - execute_workflow_with_conditionals()
if should_execute:
    # Submit analyzers, wait for results
    executed_stages.append(stage_id)
else:
    # Skip stage, add to skipped_stages
    skipped_stages.append(stage_id)
```

---

## 📁 TEST RESOURCES

### Test Samples (`testing_responses/Malware safe Malware samples/`)

**Safe Files:**
- `clean.exe`, `safe_pe.exe` - Clean PE files
- `safe.pdf`, `safe.rtf`, `safe_document.doc` - Clean documents
- `safe.js` - Clean JavaScript
- `termux.apk` - Clean APK
- `test.txt`, `strings_test.txt` - Text files

**Malicious Files:**
- `eicar.com`, `eicar_test.exe`, `test_malware.exe` - EICAR test files
- `malicious.pdf`, `malicious.rtf`, `macro_doc.doc` - Malicious documents
- `malicious.js` - Malicious JavaScript
- `malware.apk` - Malicious APK
- `calc_shellcode.bin` - Shellcode

### Response Reference (`testing_responses/responses/`)
- `comprehensive_test_results.json` - 15K+ lines of actual IntelOwl responses
- Contains responses for all 18 analyzers with both safe and malicious files

---

## 🔑 KEY INSIGHT: Data Structure Issue

### Backend Returns:
```json
{
    "job_id": 123,
    "status": "reported_without_fails",
    "analyzer_reports": [
        {"name": "ClamAV", "status": "SUCCESS", "report": {...}},
        {"name": "File_Info", "status": "SUCCESS", "report": {...}}
    ],
    "ClamAV": {"detections": [], ...},  // Top-level key
    "File_Info": {"md5": "...", ...}    // Top-level key
}
```

### Current Frontend Issue:
The `distributeUsingGraphTraversal()` function looks for `allResults[analyzer]` which works for top-level keys, but `ResultTabs.tsx` expects `results.analyzer_reports[]` array format.

### Solution:
Ensure both formats are available in the filtered results passed to result nodes.

---

## 📋 Analyzer Condition Types

| Condition Type | Description | Verified Analyzers |
|----------------|-------------|-------------------|
| `verdict_malicious` | Detected malware | ClamAV, Yara, Doc_Info, Quark_Engine |
| `verdict_clean` | Verified clean | All analyzers |
| `analyzer_success` | Completed without error | All analyzers |
| `yara_rule_match` | YARA rule matched | Yara |
| `has_detections` | Has any detections | ClamAV, Yara, APK_Artifacts |
| `field_equals` | Custom field check | Any analyzer |
| `field_contains` | Field contains value | Any analyzer |
| `field_greater_than` | Numeric comparison | Any analyzer |

