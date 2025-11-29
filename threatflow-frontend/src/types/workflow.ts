/**
 * TypeScript type definitions for ThreatFlow
 * Based on React Flow v11 and IntelOwl API
 */

import { Node, Edge } from 'reactflow';

// Re-export Edge for use in other modules
export type { Edge } from 'reactflow';

// ============= Node Types =============

export enum NodeType {
  FILE = 'file',
  ANALYZER = 'analyzer',
  RESULT = 'result',
  CONDITIONAL = 'conditional',
}

export interface FileNodeData {
  label: string;
  file: File | null;
  fileName: string;
  fileSize: number;
  onFileSelect?: (nodeId: string, file: File) => void;
}

export interface AnalyzerNodeData {
  label: string;
  analyzer: string;
  analyzerType: 'file' | 'observable';
  description: string;
  onAnalyzerSelect?: (nodeId: string, analyzer: string) => void;
}

export interface ResultNodeData {
  label: string;
  jobId: number | null;
  status: string;
  results: any | null;
  error: string | null;
}

export interface ConditionalNodeData {
  label: string;
  conditionType: 
    | 'verdict_malicious'           // Check if malware detected
    | 'verdict_suspicious'          // Check if suspicious
    | 'verdict_clean'               // Check if clean
    | 'analyzer_success'            // Check if analyzer succeeded
    | 'analyzer_failed'             // Check if analyzer failed
    | 'field_equals'                // Check if field equals value
    | 'field_contains'              // Check if field contains value
    | 'field_greater_than'          // Check if field > value
    | 'field_less_than'             // Check if field < value
    | 'yara_rule_match'             // Check if YARA rule matched
    | 'capability_detected';        // Check if Capa capability detected
  
  sourceAnalyzer: string;
  fieldPath?: string;               // e.g., "report.pe_info.signature.valid"
  expectedValue?: any;              // Value to compare against
  operator?: 'equals' | 'contains' | 'greater_than' | 'less_than' | 'regex';
  executionResult?: boolean | null; // null = not executed, true = condition met, false = condition not met
}

// Union type for all node data
export type CustomNodeData = FileNodeData | AnalyzerNodeData | ResultNodeData | ConditionalNodeData;

// Extended Node types with custom data
export type FileNode = Node<FileNodeData>;
export type AnalyzerNode = Node<AnalyzerNodeData>;
export type ResultNode = Node<ResultNodeData>;
export type ConditionalNode = Node<ConditionalNodeData>;
export type CustomNode = FileNode | AnalyzerNode | ResultNode | ConditionalNode;

// Use Node<any> for workflow state to handle union types properly
export type WorkflowNode = Node<any>;

// ============= API Types =============

export interface AnalyzerInfo {
  id: number;
  name: string;
  type: 'file' | 'observable';
  description: string;
  supported_filetypes: string[];
  not_supported_filetypes: string[];
  observable_supported: string[];
  available: boolean;
  unavailable_reason?: string;
}

export interface AnalyzersSummary {
  available_count: number;
  unavailable_count: number;
  total_count: number;
  containers_detected: {
    core: boolean;
    malware_tools: boolean;
    apk_analyzers: boolean;
    advanced_analyzers: boolean;
    observable_analyzers: boolean;
  };
}

export interface AnalyzersResponse {
  available: AnalyzerInfo[];
  unavailable: AnalyzerInfo[];
  summary: AnalyzersSummary;
}

export interface JobStatusResponse {
  job_id: number;
  status: string;
  progress?: number;
  analyzers_completed: number;
  analyzers_total: number;
  results: any | null;
  has_conditionals?: boolean;
  stagerouting?: StageRouting[];
}

export interface StageRouting {
  stage_id: number;
  target_nodes: string[];
  executed: boolean;
  analyzers?: string[];
}

export interface ExecuteWorkflowResponse {
  success: boolean;
  job_id?: number; // For backwards compatibility
  job_ids?: number[]; // For conditional workflows
  analyzers?: string[];
  total_stages?: number;
  executed_stages?: number[];
  skipped_stages?: number[];
  has_conditionals?: boolean;
  stagerouting?: StageRouting[]; // NEW: Routing metadata for conditional workflows
  message: string;
}

// ============= Workflow Types =============

export interface WorkflowState {
  nodes: CustomNode[];
  edges: Edge[];
  selectedNode: CustomNode | null;
  executionStatus: 'idle' | 'running' | 'completed' | 'error';
  jobId: number | null;
  uploadedFile: File | null;
}

export interface WorkflowActions {
  addNode: (node: CustomNode) => void;
  updateNode: (id: string, data: Partial<CustomNodeData>) => void;
  deleteNode: (id: string) => void;
  addEdge: (edge: Edge) => void;
  deleteEdge: (id: string) => void;
  setSelectedNode: (node: CustomNode | null) => void;
  setExecutionStatus: (status: WorkflowState['executionStatus']) => void;
  setJobId: (jobId: number | null) => void;
  setUploadedFile: (file: File | null) => void;
  reset: () => void;
}

export type WorkflowStore = WorkflowState & WorkflowActions;
