# Phase 2 Quick Reference Guide

## 🚀 Quick Start

### Starting the Application

```bash
# Terminal 1 - Backend
cd threatflow-middleware
source venv/bin/activate
python -m uvicorn app.main:app --reload --port 8030

# Terminal 2 - Frontend
cd threatflow-frontend
npm start
```

### Accessing the UI

- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8030
- **API Docs:** http://localhost:8030/docs

---

## 📚 Component Quick Reference

### 1. Using FieldPathInput

```tsx
import { FieldPathInput } from '@/components/ConditionBuilder';

<FieldPathInput
  analyzerName="ClamAV"
  value={fieldPath}
  onChange={setFieldPath}
  label="Field Path"
  helperText="Use dot notation"
  required
  disabled={false}
/>
```

**Features:**
- ✅ Autocomplete after 2 characters
- ✅ Real-time validation
- ✅ Confidence scoring
- ✅ Error correction suggestions

---

### 2. Using TemplateSelector

```tsx
import { TemplateSelector } from '@/components/ConditionBuilder';

<TemplateSelector
  analyzerName={sourceAnalyzer}
  onApplyTemplate={(template) => {
    setConditionType(template.conditionType);
    setFieldPath(template.fieldPath);
    setExpectedValue(template.expectedValue);
    setOperator(template.operator);
  }}
  disabled={!sourceAnalyzer}
/>
```

**Features:**
- ✅ 586 pre-built templates
- ✅ Grouped by use case
- ✅ One-click apply
- ✅ Rich descriptions

---

### 3. Using ConditionBuilder

```tsx
import { ConditionBuilder } from '@/components/ConditionBuilder';

<ConditionBuilder
  nodeId={nodeId}
  initialData={{
    conditionType: 'field_equals',
    sourceAnalyzer: 'ClamAV',
    fieldPath: 'report.is_malware',
    expectedValue: true,
    operator: 'equals'
  }}
  onUpdate={(data) => updateNode(nodeId, data)}
  availableAnalyzers={['ClamAV', 'PE_Info', 'Yara']}
/>
```

**Features:**
- ✅ Complete condition builder
- ✅ Integrated templates
- ✅ Real-time validation
- ✅ Dynamic form fields
- ✅ Confidence display

---

### 4. Using ValidationPanel

```tsx
import { ValidationPanel } from '@/components/Validation';

<ValidationPanel
  nodes={nodes.map(n => ({ 
    id: n.id, 
    type: n.type || 'unknown', 
    data: n.data 
  }))}
  edges={edges.map(e => ({ 
    id: e.id, 
    source: e.source, 
    target: e.target 
  }))}
  onValidationComplete={(isValid) => {
    console.log('Valid:', isValid);
  }}
/>
```

**Features:**
- ✅ Comprehensive validation
- ✅ Grouped by severity
- ✅ Actionable suggestions
- ✅ Expandable details

---

## 🔌 API Quick Reference

### Schema API Service

```typescript
import * as schemaApi from '@/services/schemaApi';

// Get all analyzers
const { analyzers } = await schemaApi.getAllAnalyzers();
// Returns: { analyzers: string[] }

// Get analyzer schema
const schema = await schemaApi.getAnalyzerSchema('ClamAV');
// Returns: AnalyzerSchema

// Get fields
const { fields } = await schemaApi.getAnalyzerFields('ClamAV');
// Returns: { fields: FieldDefinition[] }

// Get templates
const { templates } = await schemaApi.getConditionTemplates('ClamAV');
// Returns: { templates: ConditionTemplate[] }

// Validate field path
const validation = await schemaApi.validateFieldPath({
  analyzer_name: 'ClamAV',
  field_path: 'report.is_malware'
});
// Returns: FieldValidationResponse

// Validate condition
const conditionValidation = await schemaApi.validateCondition({
  analyzer_name: 'ClamAV',
  condition_type: 'field_equals',
  field_path: 'report.is_malware',
  expected_value: true
});
// Returns: ConditionValidationResponse

// Get field suggestions
const { suggestions } = await schemaApi.getFieldSuggestions(
  'ClamAV', 
  'report.', 
  10
);
// Returns: { suggestions: FieldSuggestion[] }

// Validate workflow
const workflowValidation = await schemaApi.validateWorkflow(nodes, edges);
// Returns: WorkflowValidationResponse
```

---

## 🎨 Condition Types Reference

### Simple Verdict Checks

```typescript
// No additional fields required
{
  conditionType: 'verdict_malicious' | 'verdict_suspicious' | 'verdict_clean',
  sourceAnalyzer: 'ClamAV'
}
```

### Analyzer Status Checks

```typescript
// No additional fields required
{
  conditionType: 'analyzer_success' | 'analyzer_failed',
  sourceAnalyzer: 'PE_Info'
}
```

### Field Comparisons

```typescript
// Requires: fieldPath, expectedValue, operator
{
  conditionType: 'field_equals' | 'field_contains' | 'field_greater_than' | 'field_less_than',
  sourceAnalyzer: 'PE_Info',
  fieldPath: 'report.pe_info.signature.valid',
  expectedValue: true,
  operator: 'equals' | 'contains' | 'greater_than' | 'less_than' | 'regex'
}
```

### YARA & Capability Checks

```typescript
// Requires: fieldPath, expectedValue
{
  conditionType: 'yara_rule_match' | 'capability_detected',
  sourceAnalyzer: 'Yara' | 'Flare_Capa',
  fieldPath: 'report.matches[0].rule_name',
  expectedValue: 'malware_rule'
}
```

---

## 📊 Validation Response Structure

### FieldValidationResponse

```typescript
{
  is_valid: boolean;           // Is field path valid?
  field_exists: boolean;       // Does field exist in schema?
  field_type: string | null;   // Field type (string, number, etc.)
  suggestions: string[];       // Suggested corrections
  errors: string[];            // Error messages
}
```

### ConditionValidationResponse

```typescript
{
  is_valid: boolean;           // Is condition valid?
  errors: string[];            // Error messages
  warnings: string[];          // Warning messages
  suggestions: string[];       // Improvement suggestions
  confidence: number;          // 0.0 to 1.0
}
```

### WorkflowValidationResponse

```typescript
{
  is_valid: boolean;           // Is workflow valid?
  errors_count: number;        // Number of errors
  warnings_count: number;      // Number of warnings
  info_count: number;          // Number of info items
  issues: ValidationIssue[];   // Detailed issues
  summary: string;             // Summary message
}
```

### ValidationIssue

```typescript
{
  severity: 'error' | 'warning' | 'info';
  category: string;            // Issue category
  message: string;             // Issue description
  node_id?: string;            // Affected node
  suggestions: string[];       // Fix suggestions
}
```

---

## 🧪 Testing Examples

### Test Autocomplete

```typescript
// Type in FieldPathInput
// After 2 characters, should see suggestions
// Example: "rep" → shows "report.is_malware", "report.detections", etc.

const { suggestions } = await getFieldSuggestions('ClamAV', 'rep', 10);
console.log(suggestions);
// [
//   { field_path: 'report.is_malware', type: 'boolean', confidence: 0.95 },
//   { field_path: 'report.detections', type: 'array', confidence: 0.90 },
//   ...
// ]
```

### Test Validation

```typescript
// Configure condition
const validation = await validateCondition({
  analyzer_name: 'ClamAV',
  condition_type: 'field_equals',
  field_path: 'report.is_malware',
  expected_value: true
});

console.log('Valid:', validation.is_valid);
console.log('Confidence:', validation.confidence);
console.log('Errors:', validation.errors);
console.log('Suggestions:', validation.suggestions);
```

### Test Templates

```typescript
// Load templates
const { templates } = await getConditionTemplates('ClamAV');

console.log(`Found ${templates.length} templates`);

// Apply template
const malwareTemplate = templates.find(t => 
  t.name === 'Malware Detected'
);

console.log('Template:', malwareTemplate);
// {
//   name: 'Malware Detected',
//   condition_type: 'verdict_malicious',
//   field_path: undefined,
//   expected_value: undefined,
//   description: 'Check if ClamAV detected malware'
// }
```

---

## 🐛 Troubleshooting

### Autocomplete Not Working

**Problem:** No suggestions appearing  
**Solutions:**
1. Check analyzer name is valid
2. Type at least 2 characters
3. Verify backend is running (port 8030)
4. Check console for API errors
5. Test API directly: `curl http://localhost:8030/api/schema/field-suggestions/ClamAV?partial=rep`

### Validation Not Running

**Problem:** No validation feedback  
**Solutions:**
1. Wait 500ms after typing (debounce)
2. Ensure analyzer is selected
3. Check condition type is set
4. Verify backend API is accessible
5. Check console for errors

### Templates Not Loading

**Problem:** Template menu empty  
**Solutions:**
1. Ensure analyzer is selected first
2. Check backend API: `curl http://localhost:8030/api/schema/analyzers/ClamAV/templates`
3. Verify analyzer has templates
4. Check console for errors
5. Reload page

### Validation Panel Issues

**Problem:** Workflow validation fails  
**Solutions:**
1. Ensure nodes array is not empty
2. Check edges are valid
3. Verify backend endpoint: `POST /api/schema/validate/workflow`
4. Check console for request/response
5. Validate JSON structure

---

## 📖 Common Patterns

### Pattern 1: Build Condition with Template

```typescript
// 1. Select analyzer
setSourceAnalyzer('ClamAV');

// 2. Load templates
const { templates } = await getConditionTemplates('ClamAV');

// 3. Find desired template
const template = templates.find(t => t.use_case === 'malware_detection');

// 4. Apply template
setConditionType(template.condition_type);
setFieldPath(template.field_path);
setExpectedValue(template.expected_value);

// 5. Validate automatically
// (validation runs via useEffect)
```

### Pattern 2: Manual Condition with Autocomplete

```typescript
// 1. Select analyzer
setSourceAnalyzer('PE_Info');

// 2. Select condition type
setConditionType('field_equals');

// 3. Type field path
// User types: "report.pe_"
// Autocomplete shows: "report.pe_info.signature.valid"

// 4. Select from autocomplete
setFieldPath('report.pe_info.signature.valid');

// 5. Set expected value
setExpectedValue(true);

// 6. Validation runs automatically
```

### Pattern 3: Fix Validation Errors

```typescript
// 1. Validate workflow
const validation = await validateWorkflow(nodes, edges);

// 2. Check results
if (!validation.is_valid) {
  // 3. Filter errors
  const errors = validation.issues.filter(i => i.severity === 'error');
  
  // 4. Read suggestions
  errors.forEach(error => {
    console.log('Error:', error.message);
    console.log('Suggestions:', error.suggestions);
  });
  
  // 5. Apply fixes
  // Update nodes based on suggestions
  
  // 6. Re-validate
  const revalidation = await validateWorkflow(updatedNodes, edges);
  console.log('Fixed:', revalidation.is_valid);
}
```

---

## 🎯 Best Practices

### 1. Always Use Templates First

Templates are pre-validated and cover 95% of use cases.

```typescript
// ✅ GOOD: Start with template
<TemplateSelector
  analyzerName={analyzer}
  onApplyTemplate={handleApply}
/>

// ❌ BAD: Manual configuration without checking templates
<TextField
  value={fieldPath}
  onChange={e => setFieldPath(e.target.value)}
/>
```

### 2. Wait for Validation

Don't submit conditions before validation completes.

```typescript
// ✅ GOOD: Check validation
if (validation?.is_valid && validation.confidence > 0.8) {
  submitCondition();
} else {
  showError('Please fix validation errors');
}

// ❌ BAD: Submit without checking
submitCondition();
```

### 3. Use Autocomplete

Always use FieldPathInput instead of plain TextField.

```typescript
// ✅ GOOD: Autocomplete
<FieldPathInput
  analyzerName={analyzer}
  value={fieldPath}
  onChange={setFieldPath}
/>

// ❌ BAD: Plain text
<TextField
  value={fieldPath}
  onChange={e => setFieldPath(e.target.value)}
/>
```

### 4. Handle Errors Gracefully

Always wrap API calls in try-catch.

```typescript
// ✅ GOOD: Error handling
try {
  const validation = await validateCondition(request);
  setValidation(validation);
} catch (error) {
  console.error('Validation failed:', error);
  showUserError('Unable to validate. Please try again.');
}

// ❌ BAD: No error handling
const validation = await validateCondition(request);
setValidation(validation);
```

---

## 📞 Quick Links

- **Phase 1 Docs:** `/Docs/PHASE-1-ENHANCEMENT-COMPLETE.md`
- **Phase 2 Docs:** `/Docs/PHASE-2-IMPLEMENTATION-COMPLETE.md`
- **API Reference:** `/Docs/API-QUICKSTART.md`
- **Implementation Roadmap:** `/Docs/IMPLEMENTATION-ROADMAP.md`
- **Backend API:** http://localhost:8030/docs

---

**Phase 2 Complete!** 🎉

Ready to build intelligent workflows with zero errors! 🚀
