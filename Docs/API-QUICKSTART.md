# ThreatFlow Enhanced API - Quick Reference Guide

## 🚀 Quick Start

### Base URL
```
http://localhost:8030
```

### API Documentation
```
http://localhost:8030/docs      # Swagger UI
http://localhost:8030/redoc     # ReDoc
```

---

## 📋 Schema Management APIs

### 1. List All Analyzers
Get overview of all 18 analyzers with schema information.

```http
GET /api/schema/analyzers
```

**Response:**
```json
{
  "analyzers": [
    {
      "name": "ClamAV",
      "description": "Open-source antivirus scanner",
      "field_count": 3,
      "template_count": 2,
      "malware_indicators": ["detections"]
    }
  ],
  "total_count": 18
}
```

**Use Case:** Populate analyzer dropdown in UI

---

### 2. Get Analyzer Schema
Get detailed schema for a specific analyzer.

```http
GET /api/schema/analyzers/{analyzer_name}
```

**Example:**
```bash
curl http://localhost:8030/api/schema/analyzers/ClamAV
```

**Response:**
```json
{
  "name": "ClamAV",
  "description": "Open-source antivirus scanner",
  "output_fields": [
    {
      "path": "report.detections",
      "type": "array",
      "description": "Malware detections",
      "examples": [["Win.Trojan.Generic-123"]],
      "required": false
    }
  ],
  "condition_templates": [
    {
      "name": "Malware detected",
      "description": "Check if ClamAV found threats",
      "condition_type": "verdict_malicious",
      "use_case": "Trigger advanced analysis on infected files"
    }
  ],
  "malware_indicators": ["detections"],
  "success_patterns": ["detections", "raw_report"]
}
```

**Use Case:** Show available fields and templates when user selects analyzer

---

### 3. Get Analyzer Fields
Get just the output fields with optional search filter.

```http
GET /api/schema/analyzers/{analyzer_name}/fields?search={term}
```

**Examples:**
```bash
# All fields
curl http://localhost:8030/api/schema/analyzers/PE_Info/fields

# Search for signature fields
curl http://localhost:8030/api/schema/analyzers/PE_Info/fields?search=signature
```

**Response:**
```json
{
  "analyzer": "PE_Info",
  "fields": [
    {
      "path": "report.pe_info.signature.valid",
      "type": "boolean",
      "description": "Digital signature valid",
      "examples": [true, false]
    }
  ],
  "total_count": 1
}
```

**Use Case:** Field path autocomplete in UI

---

### 4. Get Condition Templates
Get pre-built condition templates for common use cases.

```http
GET /api/schema/analyzers/{analyzer_name}/templates
```

**Example:**
```bash
curl http://localhost:8030/api/schema/analyzers/Yara/templates
```

**Response:**
```json
{
  "analyzer": "Yara",
  "templates": [
    {
      "name": "YARA rule match",
      "description": "Check if any rules matched",
      "condition_type": "yara_rule_match",
      "field_path": null,
      "expected_value": null,
      "use_case": "High-priority alert for rule matches"
    },
    {
      "name": "Specific rule match",
      "description": "Check for specific rule",
      "condition_type": "field_contains",
      "field_path": "report.rules",
      "expected_value": "Ransomware",
      "use_case": "Activate ransomware response protocol"
    }
  ],
  "total_count": 2
}
```

**Use Case:** Quick setup for common conditions

---

### 5. Field Path Suggestions
Get autocomplete suggestions for field paths.

```http
GET /api/schema/field-suggestions/{analyzer_name}?partial={path}
```

**Example:**
```bash
curl "http://localhost:8030/api/schema/field-suggestions/PE_Info?partial=report.pe"
```

**Response:**
```json
{
  "analyzer": "PE_Info",
  "partial": "report.pe",
  "suggestions": [
    "report.pe_info",
    "report.pe_info.signature",
    "report.pe_info.signature.valid",
    "report.pe_info.imphash",
    "report.pe_info.sections",
    "report.pe_info.imports"
  ],
  "count": 6
}
```

**Use Case:** Real-time autocomplete as user types

---

## ✅ Validation APIs

### 6. Validate Field Path
Check if a field path exists in analyzer schema.

```http
POST /api/schema/validate/field-path
Content-Type: application/json

{
  "analyzer_name": "PE_Info",
  "field_path": "report.pe_info.signature.valid"
}
```

**Response:**
```json
{
  "is_valid": true,
  "message": "Valid field path",
  "suggestions": []
}
```

**Invalid Path Response:**
```json
{
  "is_valid": false,
  "message": "Field path not found in PE_Info schema. Available fields: report.md5, report.sha256, ...",
  "suggestions": [
    "report.pe_info.signature.valid",
    "report.pe_info.signature.signer",
    "report.pe_info.signature.timestamp"
  ]
}
```

**Use Case:** Real-time validation in condition builder

---

### 7. Validate Condition
Validate complete condition configuration.

```http
POST /api/schema/validate/condition
Content-Type: application/json

{
  "condition_type": "field_equals",
  "source_analyzer": "PE_Info",
  "field_path": "report.pe_info.signature.valid",
  "expected_value": true
}
```

**Valid Response:**
```json
{
  "is_valid": true,
  "errors": []
}
```

**Invalid Response:**
```json
{
  "is_valid": false,
  "errors": [
    "Field path 'report.pe_info.signature' not found in PE_Info schema",
    "Expected value missing for field_equals condition"
  ]
}
```

**Use Case:** Validate before saving condition

---

### 8. Validate Entire Workflow
**🎯 MOST IMPORTANT ENDPOINT**

Comprehensive pre-execution validation of workflow structure, conditions, and dependencies.

```http
POST /api/schema/validate/workflow
Content-Type: application/json

{
  "nodes": [
    {
      "id": "file-1",
      "type": "file",
      "data": { "label": "Input File" }
    },
    {
      "id": "analyzer-1",
      "type": "analyzer",
      "data": { "analyzer": "ClamAV", "label": "Virus Scan" }
    },
    {
      "id": "cond-1",
      "type": "conditional",
      "data": {
        "conditionType": "verdict_malicious",
        "sourceAnalyzer": "ClamAV",
        "label": "Is Malicious?"
      }
    }
  ],
  "edges": [
    { "id": "e1", "source": "file-1", "target": "analyzer-1" },
    { "id": "e2", "source": "analyzer-1", "target": "cond-1" }
  ]
}
```

**Response:**
```json
{
  "is_valid": true,
  "issues": [],
  "errors_count": 0,
  "warnings_count": 0,
  "info_count": 0
}
```

**Response with Issues:**
```json
{
  "is_valid": false,
  "issues": [
    {
      "severity": "error",
      "message": "Conditional node references analyzer 'VirusTotal' which is not in the workflow",
      "node_id": "cond-1",
      "field": "sourceAnalyzer",
      "suggestions": [
        "Add VirusTotal analyzer to the workflow",
        "Change sourceAnalyzer to an existing analyzer"
      ],
      "auto_fix": null
    },
    {
      "severity": "warning",
      "message": "Node 'PE Analysis' is not connected to workflow",
      "node_id": "analyzer-2",
      "field": null,
      "suggestions": [
        "Connect this node to the workflow or remove it"
      ],
      "auto_fix": null
    },
    {
      "severity": "info",
      "message": "Consider adding a result node to view final output",
      "node_id": null,
      "field": null,
      "suggestions": [
        "Add a Result node from the Node Palette"
      ],
      "auto_fix": null
    }
  ],
  "errors_count": 1,
  "warnings_count": 1,
  "info_count": 1
}
```

**Use Case:** Validate before workflow execution, show errors in UI

---

## 🔧 Integration Examples

### Frontend React Integration

#### 1. Load Analyzer Schema on Mount
```typescript
const [analyzerSchema, setAnalyzerSchema] = useState(null);

useEffect(() => {
  if (selectedAnalyzer) {
    fetch(`http://localhost:8030/api/schema/analyzers/${selectedAnalyzer}`)
      .then(res => res.json())
      .then(data => setAnalyzerSchema(data));
  }
}, [selectedAnalyzer]);
```

#### 2. Field Path Autocomplete
```typescript
const [suggestions, setSuggestions] = useState([]);

const handleFieldPathChange = async (value: string) => {
  if (value.length > 3) {
    const response = await fetch(
      `http://localhost:8030/api/schema/field-suggestions/${selectedAnalyzer}?partial=${value}`
    );
    const data = await response.json();
    setSuggestions(data.suggestions);
  }
};
```

#### 3. Real-Time Validation
```typescript
const [validationErrors, setValidationErrors] = useState([]);

const validateCondition = async (condition) => {
  const response = await fetch('http://localhost:8030/api/schema/validate/condition', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(condition)
  });
  const result = await response.json();
  
  if (!result.is_valid) {
    setValidationErrors(result.errors);
  } else {
    setValidationErrors([]);
  }
};
```

#### 4. Pre-Execution Workflow Validation
```typescript
const validateBeforeExecution = async () => {
  const response = await fetch('http://localhost:8030/api/schema/validate/workflow', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      nodes: workflowNodes,
      edges: workflowEdges
    })
  });
  
  const validation = await response.json();
  
  if (!validation.is_valid) {
    // Show errors in UI
    const errorMessages = validation.issues
      .filter(i => i.severity === 'error')
      .map(i => i.message);
    
    alert(`Workflow has errors:\n${errorMessages.join('\n')}`);
    return false;
  }
  
  return true;
};

// Before executing
if (await validateBeforeExecution()) {
  executeWorkflow();
}
```

---

## 🎯 Common Use Cases

### Use Case 1: Building Intelligent Condition Selector

```typescript
// 1. User selects analyzer
const analyzer = "ClamAV";

// 2. Load templates
const templates = await fetch(
  `http://localhost:8030/api/schema/analyzers/${analyzer}/templates`
).then(r => r.json());

// 3. Show templates in dropdown
<Select>
  {templates.templates.map(t => (
    <MenuItem value={t}>{t.name} - {t.description}</MenuItem>
  ))}
</Select>

// 4. When template selected, auto-fill fields
const applyTemplate = (template) => {
  setConditionType(template.condition_type);
  setFieldPath(template.field_path);
  setExpectedValue(template.expected_value);
};
```

### Use Case 2: Field Path Builder with Autocomplete

```typescript
const [fieldPath, setFieldPath] = useState('');
const [suggestions, setSuggestions] = useState([]);

const handleFieldPathChange = async (value: string) => {
  setFieldPath(value);
  
  // Get suggestions
  const response = await fetch(
    `http://localhost:8030/api/schema/field-suggestions/${selectedAnalyzer}?partial=${value}`
  );
  const data = await response.json();
  setSuggestions(data.suggestions);
  
  // Validate
  const validation = await fetch(
    'http://localhost:8030/api/schema/validate/field-path',
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        analyzer_name: selectedAnalyzer,
        field_path: value
      })
    }
  ).then(r => r.json());
  
  setIsValid(validation.is_valid);
};

return (
  <Autocomplete
    options={suggestions}
    value={fieldPath}
    onChange={handleFieldPathChange}
    renderInput={(params) => (
      <TextField
        {...params}
        error={!isValid}
        helperText={isValid ? '' : 'Invalid field path'}
      />
    )}
  />
);
```

### Use Case 3: Workflow Validation Panel

```typescript
const ValidationPanel = ({ workflow }) => {
  const [validation, setValidation] = useState(null);
  
  useEffect(() => {
    validateWorkflow();
  }, [workflow.nodes, workflow.edges]);
  
  const validateWorkflow = async () => {
    const response = await fetch(
      'http://localhost:8030/api/schema/validate/workflow',
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          nodes: workflow.nodes.map(n => ({ id: n.id, type: n.type, data: n.data })),
          edges: workflow.edges.map(e => ({ id: e.id, source: e.source, target: e.target }))
        })
      }
    );
    const result = await response.json();
    setValidation(result);
  };
  
  return (
    <Box>
      <Typography variant="h6">
        Workflow Validation
        {validation?.is_valid ? ' ✅' : ' ❌'}
      </Typography>
      
      {validation?.errors_count > 0 && (
        <Alert severity="error">
          {validation.errors_count} error(s) found
        </Alert>
      )}
      
      {validation?.issues.map((issue, idx) => (
        <Alert key={idx} severity={issue.severity}>
          <AlertTitle>{issue.message}</AlertTitle>
          {issue.suggestions.length > 0 && (
            <List dense>
              {issue.suggestions.map((s, i) => (
                <ListItem key={i}>• {s}</ListItem>
              ))}
            </List>
          )}
        </Alert>
      ))}
    </Box>
  );
};
```

---

## 📊 API Performance

| Endpoint | Response Time | Caching |
|----------|--------------|---------|
| `/api/schema/analyzers` | < 10ms | Memory cached |
| `/api/schema/analyzers/{name}` | < 5ms | Memory cached |
| `/api/schema/validate/field-path` | < 20ms | No |
| `/api/schema/validate/condition` | < 30ms | No |
| `/api/schema/validate/workflow` | < 100ms | No |

---

## 🔒 Error Handling

All endpoints return standard error responses:

```json
{
  "detail": "Error message here",
  "status_code": 404
}
```

Common status codes:
- `200`: Success
- `400`: Bad request (invalid input)
- `404`: Resource not found
- `422`: Validation error (Pydantic)
- `500`: Internal server error

---

## 🎓 Best Practices

1. **Always validate before execution**
   ```typescript
   const isValid = await validateWorkflow();
   if (isValid) executeWorkflow();
   ```

2. **Use templates for common patterns**
   ```typescript
   const templates = await getTemplates(analyzer);
   // Apply template instead of manual config
   ```

3. **Implement autocomplete for field paths**
   ```typescript
   // Better UX with real-time suggestions
   ```

4. **Show validation errors immediately**
   ```typescript
   // Don't wait for execution to fail
   ```

5. **Cache analyzer schemas**
   ```typescript
   // Load once, use many times
   ```

---

## 🚀 Next Steps

After implementing Phase 1 APIs:
1. Build intelligent condition builder UI
2. Add template selection dropdown
3. Implement field path autocomplete
4. Show validation errors in real-time
5. Add workflow validation panel

**The backend is ready - time to build an amazing UI! 🎨**