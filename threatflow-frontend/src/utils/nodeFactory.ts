/**
 * Node Factory
 * Helper functions to create new nodes
 */

import { Node } from 'reactflow';
import {
  FileNodeData,
  AnalyzerNodeData,
  ResultNodeData,
  NodeType,
} from '../types/workflow';

let nodeIdCounter = 0;

export const generateNodeId = (type: string): string => {
  nodeIdCounter++;
  return `${type}-${nodeIdCounter}`;
};

export const createFileNode = (position: { x: number; y: number }): Node<FileNodeData> => {
  return {
    id: generateNodeId('file'),
    type: NodeType.FILE,
    position,
    data: {
      label: 'File Upload',
      file: null,
      fileName: '',
      fileSize: 0,
    },
  };
};

export const createAnalyzerNode = (position: { x: number; y: number }): Node<AnalyzerNodeData> => {
  return {
    id: generateNodeId('analyzer'),
    type: NodeType.ANALYZER,
    position,
    data: {
      label: 'Analyzer',
      analyzer: '',
      analyzerType: 'file',
      description: '',
    },
  };
};

export const createConditionalNode = (position: { x: number; y: number }): Node => {
  return {
    id: generateNodeId('conditional'),
    type: 'conditional',
    position,
    data: {
      label: 'Is Malicious?',
      conditionType: 'verdict_malicious',
      sourceAnalyzer: '',
    },
  };
};

export const createResultNode = (position: { x: number; y: number }): Node<ResultNodeData> => {
  return {
    id: generateNodeId('result'),
    type: NodeType.RESULT,
    position,
    data: {
      label: 'Results',
      jobId: null,
      status: 'idle',
      results: null,
      error: null,
    },
  };
};

export const nodeFactory = {
  file: createFileNode,
  analyzer: createAnalyzerNode,
  conditional: createConditionalNode,
  result: createResultNode,
};
