/**
 * ConditionBuilder Component
 * Intelligent UI for building conditions with analyzer-aware validation
 * Integrates autocomplete, templates, and real-time validation
 */

import React, { useState, useEffect, useCallback, useRef } from 'react';
import {
  Box,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  TextField,
  Typography,
  Alert,
  AlertTitle,
  Chip,
  LinearProgress,
  Divider,
  SelectChangeEvent,
} from '@mui/material';
import { CheckCircle, Error as ErrorIcon, Warning, Info } from '@mui/icons-material';
import { FieldPathInput } from './FieldPathInput';
import { TemplateSelector } from './TemplateSelector';
import {
  validateCondition,
  getConditionTypeLabel,
  requiresFieldPath,
  requiresExpectedValue,
  ConditionValidationResponse,
} from '../../services/schemaApi';

interface ConditionBuilderProps {
  nodeId: string;
  initialData?: {
    conditionType: string;
    sourceAnalyzer: string;
    fieldPath?: string;
    expectedValue?: any;
    operator?: string;
  };
  onUpdate: (data: {
    conditionType: string;
    sourceAnalyzer: string;
    fieldPath?: string;
    expectedValue?: any;
    operator?: string;
  }) => void;
  availableAnalyzers?: string[];
}

const CONDITION_TYPES = [
  'verdict_malicious',
  'verdict_suspicious',
  'verdict_clean',
  'analyzer_success',
  'analyzer_failed',
  'field_equals',
  'field_contains',
  'field_greater_than',
  'field_less_than',
  'yara_rule_match',
  'capability_detected',
];

const OPERATORS = [
  { value: 'equals', label: 'Equals' },
  { value: 'contains', label: 'Contains' },
  { value: 'greater_than', label: 'Greater Than' },
  { value: 'less_than', label: 'Less Than' },
  { value: 'regex', label: 'Regex Match' },
];

export const ConditionBuilder: React.FC<ConditionBuilderProps> = ({
  nodeId,
  initialData,
  onUpdate,
  availableAnalyzers = [],
}) => {
  const [conditionType, setConditionType] = useState(initialData?.conditionType || '');
  const [sourceAnalyzer, setSourceAnalyzer] = useState(initialData?.sourceAnalyzer || '');
  const [fieldPath, setFieldPath] = useState(initialData?.fieldPath || '');
  const [expectedValue, setExpectedValue] = useState(initialData?.expectedValue || '');
  const [operator, setOperator] = useState(initialData?.operator || 'equals');
  
  const [validation, setValidation] = useState<ConditionValidationResponse | null>(null);
  const [validating, setValidating] = useState(false);

  const validateCurrentCondition = useCallback(async () => {
    setValidating(true);
    try {
      const response = await validateCondition({
        analyzer_name: sourceAnalyzer,
        condition_type: conditionType,
        field_path: fieldPath || undefined,
        expected_value: expectedValue || undefined,
        operator: operator || undefined,
      });
      setValidation(response);
    } catch (error) {
      console.error('Failed to validate condition:', error);
      setValidation(null);
    } finally {
      setValidating(false);
    }
  }, [sourceAnalyzer, conditionType, fieldPath, expectedValue, operator]);

  // Refs to store latest callback functions
  const validateRef = useRef(validateCurrentCondition);
  const onUpdateRef = useRef(onUpdate);

  // Update refs when callbacks change
  useEffect(() => {
    validateRef.current = validateCurrentCondition;
  }, [validateCurrentCondition]);

  useEffect(() => {
    onUpdateRef.current = onUpdate;
  }, [onUpdate]);

  // Validate condition whenever inputs change
  useEffect(() => {
    if (!conditionType || !sourceAnalyzer) {
      setValidation(null);
      return;
    }

    const timeoutId = setTimeout(() => {
      validateRef.current();
    }, 500);

    return () => clearTimeout(timeoutId);
  }, [conditionType, sourceAnalyzer, fieldPath, expectedValue, operator, validateCurrentCondition]);

  // Update parent whenever state changes
  useEffect(() => {
    onUpdateRef.current({
      conditionType,
      sourceAnalyzer,
      fieldPath: fieldPath || undefined,
      expectedValue: expectedValue || undefined,
      operator: operator || undefined,
    });
  }, [conditionType, sourceAnalyzer, fieldPath, expectedValue, operator, onUpdate]);

  const handleConditionTypeChange = (event: SelectChangeEvent<string>) => {
    setConditionType(event.target.value);
  };

  const handleSourceAnalyzerChange = (event: SelectChangeEvent<string>) => {
    setSourceAnalyzer(event.target.value);
  };

  const handleOperatorChange = (event: SelectChangeEvent<string>) => {
    setOperator(event.target.value);
  };

  const handleTemplateApply = (template: {
    conditionType: string;
    fieldPath?: string;
    expectedValue?: any;
    operator?: string;
  }) => {
    setConditionType(template.conditionType);
    if (template.fieldPath) setFieldPath(template.fieldPath);
    if (template.expectedValue !== undefined) setExpectedValue(template.expectedValue);
    if (template.operator) setOperator(template.operator);
  };

  const showFieldPath = requiresFieldPath(conditionType);
  const showExpectedValue = requiresExpectedValue(conditionType);

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
      <Typography variant="subtitle2" fontWeight="bold">
        Condition Configuration
      </Typography>

      {/* Template Selector */}
      {sourceAnalyzer && (
        <TemplateSelector
          analyzerName={sourceAnalyzer}
          onApplyTemplate={handleTemplateApply}
          disabled={!sourceAnalyzer}
        />
      )}

      <Divider />

      {/* Source Analyzer */}
      <FormControl fullWidth size="small" required>
        <InputLabel>Source Analyzer</InputLabel>
        <Select
          value={sourceAnalyzer}
          onChange={handleSourceAnalyzerChange}
          label="Source Analyzer"
        >
          {availableAnalyzers.length === 0 && (
            <MenuItem disabled value="">
              <em>No analyzers available</em>
            </MenuItem>
          )}
          {availableAnalyzers.map((analyzer) => (
            <MenuItem key={analyzer} value={analyzer}>
              {analyzer}
            </MenuItem>
          ))}
        </Select>
      </FormControl>

      {/* Condition Type */}
      <FormControl fullWidth size="small" required disabled={!sourceAnalyzer}>
        <InputLabel>Condition Type</InputLabel>
        <Select
          value={conditionType}
          onChange={handleConditionTypeChange}
          label="Condition Type"
        >
          {CONDITION_TYPES.map((type) => (
            <MenuItem key={type} value={type}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                {getConditionTypeLabel(type)}
              </Box>
            </MenuItem>
          ))}
        </Select>
      </FormControl>

      {/* Field Path (conditional) */}
      {showFieldPath && sourceAnalyzer && (
        <FieldPathInput
          analyzerName={sourceAnalyzer}
          value={fieldPath}
          onChange={setFieldPath}
          label="Field Path"
          helperText="Use dot notation (e.g., report.pe_info.signature.valid)"
          required
          disabled={!sourceAnalyzer}
        />
      )}

      {/* Operator (conditional) */}
      {showFieldPath && (
        <FormControl fullWidth size="small">
          <InputLabel>Operator</InputLabel>
          <Select
            value={operator}
            onChange={handleOperatorChange}
            label="Operator"
          >
            {OPERATORS.map((op) => (
              <MenuItem key={op.value} value={op.value}>
                {op.label}
              </MenuItem>
            ))}
          </Select>
        </FormControl>
      )}

      {/* Expected Value (conditional) */}
      {showExpectedValue && (
        <TextField
          fullWidth
          size="small"
          label="Expected Value"
          value={expectedValue}
          onChange={(e) => setExpectedValue(e.target.value)}
          helperText="Value to compare against"
          required
        />
      )}

      {/* Validation Progress */}
      {validating && <LinearProgress />}

      {/* Validation Results */}
      {validation && !validating && (
        <Box>
          {/* Success */}
          {validation.is_valid && (
            <Alert
              severity="success"
              icon={<CheckCircle />}
              sx={{ mb: 1 }}
            >
              <AlertTitle>Valid Condition</AlertTitle>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Typography variant="body2">
                  Confidence: {Math.round(validation.confidence * 100)}%
                </Typography>
                <Chip
                  label="Ready to Execute"
                  size="small"
                  color="success"
                  sx={{ height: 20 }}
                />
              </Box>
            </Alert>
          )}

          {/* Errors */}
          {validation.errors.length > 0 && (
            <Alert severity="error" icon={<ErrorIcon />} sx={{ mb: 1 }}>
              <AlertTitle>Configuration Errors</AlertTitle>
              <ul style={{ margin: 0, paddingLeft: 20 }}>
                {validation.errors.map((error, idx) => (
                  <li key={idx}>
                    <Typography variant="body2">{error}</Typography>
                  </li>
                ))}
              </ul>
            </Alert>
          )}

          {/* Warnings */}
          {validation.warnings.length > 0 && (
            <Alert severity="warning" icon={<Warning />} sx={{ mb: 1 }}>
              <AlertTitle>Warnings</AlertTitle>
              <ul style={{ margin: 0, paddingLeft: 20 }}>
                {validation.warnings.map((warning, idx) => (
                  <li key={idx}>
                    <Typography variant="body2">{warning}</Typography>
                  </li>
                ))}
              </ul>
            </Alert>
          )}

          {/* Suggestions */}
          {validation.suggestions.length > 0 && (
            <Alert severity="info" icon={<Info />}>
              <AlertTitle>Suggestions</AlertTitle>
              <ul style={{ margin: 0, paddingLeft: 20 }}>
                {validation.suggestions.map((suggestion, idx) => (
                  <li key={idx}>
                    <Typography variant="body2">{suggestion}</Typography>
                  </li>
                ))}
              </ul>
            </Alert>
          )}
        </Box>
      )}
    </Box>
  );
};
