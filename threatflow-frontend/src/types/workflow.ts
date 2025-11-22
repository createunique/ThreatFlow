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

// Union type for all node data
export type CustomNodeData = FileNodeData | AnalyzerNodeData | ResultNodeData;

// Extended Node types with custom data
export type FileNode = Node<FileNodeData>;
export type AnalyzerNode = Node<AnalyzerNodeData>;
export type ResultNode = Node<ResultNodeData>;
export type CustomNode = FileNode | AnalyzerNode | ResultNode;

// Use Node<any> for workflow state to handle union types properly
export type WorkflowNode = Node<any>;

// ============= API Types =============

export interface AnalyzerInfo {
  name: string;
  type: 'file' | 'observable';
  description: string;
  supported_filetypes: string[];
  disabled: boolean;
}

export interface JobStatusResponse {
  job_id: number;
  status: string;
  progress?: number;
  analyzers_completed: number;
  analyzers_total: number;
  results: any | null;
}

export interface ExecuteWorkflowResponse {
  success: boolean;
  job_id: number;
  analyzers: string[];
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
