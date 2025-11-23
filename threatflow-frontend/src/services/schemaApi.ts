/**
 * Schema API Service
 * Wraps all 8 Phase 1 API endpoints for frontend integration
 * Provides type-safe access to analyzer schemas, validation, and field suggestions
 */

const API_BASE_URL = 'http://localhost:8030/api/schema';

// ============= Types =============

export interface FieldDefinition {
  name: string;
  type: 'string' | 'number' | 'boolean' | 'array' | 'object' | 'any';
  description: string;
  example?: any;
  required?: boolean;
}

export interface ConditionTemplate {
  name: string;
  description: string;
  use_case: string;
  condition_type: string;
  field_path?: string;
  expected_value?: any;
  operator?: string;
  example?: string;
}

export interface AnalyzerSchema {
  name: string;
  type: 'file' | 'observable';
  description: string;
  output_structure: {
    verdict: FieldDefinition;
    report: Record<string, FieldDefinition>;
    errors?: FieldDefinition;
  };
  condition_templates: ConditionTemplate[];
  common_indicators: {
    malware_verdicts: string[];
    suspicious_indicators: string[];
    error_indicators: string[];
  };
}

export interface FieldValidationRequest {
  analyzer_name: string;
  field_path: string;
}

export interface FieldValidationResponse {
  is_valid: boolean;
  field_exists: boolean;
  field_type: string | null;
  suggestions: string[];
  errors: string[];
}

export interface ConditionValidationRequest {
  analyzer_name: string;
  condition_type: string;
  field_path?: string;
  expected_value?: any;
  operator?: string;
}

export interface ConditionValidationResponse {
  is_valid: boolean;
  errors: string[];
  warnings: string[];
  suggestions: string[];
  confidence: number;
}

export interface WorkflowValidationNode {
  id: string;
  type: string;
  data: any;
}

export interface WorkflowValidationEdge {
  id: string;
  source: string;
  target: string;
}

export interface ValidationIssue {
  severity: 'error' | 'warning' | 'info';
  category: string;
  message: string;
  node_id?: string;
  suggestions: string[];
}

export interface WorkflowValidationResponse {
  is_valid: boolean;
  errors_count: number;
  warnings_count: number;
  info_count: number;
  issues: ValidationIssue[];
  summary: string;
}

export interface FieldSuggestion {
  field_path: string;
  type: string;
  description: string;
  confidence: number;
}

// ============= API Functions =============

/**
 * Get list of all analyzers with schema availability
 */
export async function getAllAnalyzers(): Promise<{ analyzers: string[]; total_count: number }> {
  try {
    const response = await fetch(`${API_BASE_URL}/analyzers`);
    if (!response.ok) {
      throw new Error(`Failed to fetch analyzers: ${response.statusText}`);
    }
    const data = await response.json();
    
    // Extract just the analyzer names from the objects
    const analyzerNames = data.analyzers.map((analyzer: any) => analyzer.name);
    
    return {
      analyzers: analyzerNames,
      total_count: data.total_count
    };
  } catch (error) {
    console.error('Error fetching analyzers:', error);
    throw error;
  }
}

/**
 * Get detailed schema for a specific analyzer
 */
export async function getAnalyzerSchema(analyzerName: string): Promise<AnalyzerSchema> {
  try {
    const response = await fetch(`${API_BASE_URL}/analyzers/${analyzerName}`);
    if (!response.ok) {
      throw new Error(`Failed to fetch schema for ${analyzerName}: ${response.statusText}`);
    }
    return await response.json();
  } catch (error) {
    console.error(`Error fetching schema for ${analyzerName}:`, error);
    throw error;
  }
}

/**
 * Get list of available fields for an analyzer
 */
export async function getAnalyzerFields(analyzerName: string): Promise<{ fields: FieldDefinition[] }> {
  try {
    const response = await fetch(`${API_BASE_URL}/analyzers/${analyzerName}/fields`);
    if (!response.ok) {
      throw new Error(`Failed to fetch fields for ${analyzerName}: ${response.statusText}`);
    }
    return await response.json();
  } catch (error) {
    console.error(`Error fetching fields for ${analyzerName}:`, error);
    throw error;
  }
}

/**
 * Get pre-built condition templates for an analyzer
 */
export async function getConditionTemplates(
  analyzerName: string,
  useCase?: string
): Promise<{ templates: ConditionTemplate[] }> {
  try {
    const url = useCase 
      ? `${API_BASE_URL}/analyzers/${analyzerName}/templates?use_case=${encodeURIComponent(useCase)}`
      : `${API_BASE_URL}/analyzers/${analyzerName}/templates`;
    
    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(`Failed to fetch templates for ${analyzerName}: ${response.statusText}`);
    }
    return await response.json();
  } catch (error) {
    console.error(`Error fetching templates for ${analyzerName}:`, error);
    throw error;
  }
}

/**
 * Validate a field path against an analyzer schema
 */
export async function validateFieldPath(
  request: FieldValidationRequest
): Promise<FieldValidationResponse> {
  try {
    const response = await fetch(`${API_BASE_URL}/validate/field-path`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });
    
    if (!response.ok) {
      throw new Error(`Failed to validate field path: ${response.statusText}`);
    }
    return await response.json();
  } catch (error) {
    console.error('Error validating field path:', error);
    throw error;
  }
}

/**
 * Validate a condition configuration
 */
export async function validateCondition(
  request: ConditionValidationRequest
): Promise<ConditionValidationResponse> {
  try {
    const response = await fetch(`${API_BASE_URL}/validate/condition`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });
    
    if (!response.ok) {
      throw new Error(`Failed to validate condition: ${response.statusText}`);
    }
    return await response.json();
  } catch (error) {
    console.error('Error validating condition:', error);
    throw error;
  }
}

/**
 * Validate entire workflow structure and conditions
 */
export async function validateWorkflow(
  nodes: WorkflowValidationNode[],
  edges: WorkflowValidationEdge[]
): Promise<WorkflowValidationResponse> {
  try {
    const response = await fetch(`${API_BASE_URL}/validate/workflow`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ nodes, edges }),
    });
    
    if (!response.ok) {
      throw new Error(`Failed to validate workflow: ${response.statusText}`);
    }
    return await response.json();
  } catch (error) {
    console.error('Error validating workflow:', error);
    throw error;
  }
}

/**
 * Get field path suggestions with autocomplete
 */
export async function getFieldSuggestions(
  analyzerName: string,
  partial?: string,
  limit: number = 10
): Promise<{ suggestions: FieldSuggestion[] }> {
  try {
    let url = `${API_BASE_URL}/field-suggestions/${analyzerName}?limit=${limit}`;
    if (partial) {
      url += `&partial=${encodeURIComponent(partial)}`;
    }
    
    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(`Failed to fetch field suggestions: ${response.statusText}`);
    }
    return await response.json();
  } catch (error) {
    console.error('Error fetching field suggestions:', error);
    throw error;
  }
}

// ============= Helper Functions =============

/**
 * Get human-readable condition type label
 */
export function getConditionTypeLabel(type: string): string {
  const labels: Record<string, string> = {
    verdict_malicious: 'Verdict: Malicious',
    verdict_suspicious: 'Verdict: Suspicious',
    verdict_clean: 'Verdict: Clean',
    analyzer_success: 'Analyzer: Success',
    analyzer_failed: 'Analyzer: Failed',
    field_equals: 'Field Equals',
    field_contains: 'Field Contains',
    field_greater_than: 'Field Greater Than',
    field_less_than: 'Field Less Than',
    yara_rule_match: 'YARA Rule Match',
    capability_detected: 'Capability Detected',
  };
  return labels[type] || type;
}

/**
 * Get condition types that require field path
 */
export function requiresFieldPath(conditionType: string): boolean {
  return [
    'field_equals',
    'field_contains',
    'field_greater_than',
    'field_less_than',
    'yara_rule_match',
    'capability_detected',
  ].includes(conditionType);
}

/**
 * Get condition types that require expected value
 */
export function requiresExpectedValue(conditionType: string): boolean {
  return [
    'field_equals',
    'field_contains',
    'field_greater_than',
    'field_less_than',
    'yara_rule_match',
    'capability_detected',
  ].includes(conditionType);
}

/**
 * Format validation error for display
 */
export function formatValidationError(error: string): string {
  return error.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
}

/**
 * Get severity color for Material-UI
 */
export function getSeverityColor(severity: 'error' | 'warning' | 'info'): 'error' | 'warning' | 'info' {
  return severity;
}
