/**
 * Zustand store for workflow state management
 * Integrates with React Flow for node/edge operations
 */

import { create } from 'zustand';
import { devtools } from 'zustand/middleware';
import { Edge } from 'reactflow';
import {
  WorkflowStore,
  WorkflowState,
  CustomNode,
  CustomNodeData,
  ResultNode,
} from '../types/workflow';

// Initial state
const initialState: WorkflowState = {
  nodes: [],
  edges: [],
  selectedNode: null,
  executionStatus: 'idle',
  jobId: null,
  uploadedFile: null,
};

// Create Zustand store with devtools
export const useWorkflowState = create<WorkflowStore>()(
  devtools(
    (set) => ({
      ...initialState,

      // ============= Node Operations =============

      addNode: (node: CustomNode) =>
        set((state) => ({
          nodes: [...state.nodes, node],
        })),

      updateNode: (id: string, data: Partial<CustomNodeData>) =>
        set((state) => ({
          nodes: state.nodes.map((node) =>
            node.id === id
              ? { ...node, data: { ...node.data, ...data } } as CustomNode
              : node
          ),
        })),

      deleteNode: (id: string) =>
        set((state) => ({
          nodes: state.nodes.filter((n) => n.id !== id),
          edges: state.edges.filter(
            (e) => e.source !== id && e.target !== id
          ),
        })),

      // ============= Edge Operations =============

      addEdge: (edge: Edge) =>
        set((state) => ({
          edges: [...state.edges, edge],
        })),

      deleteEdge: (id: string) =>
        set((state) => ({
          edges: state.edges.filter((e) => e.id !== id),
        })),

      // ============= Selection =============

      setSelectedNode: (node: CustomNode | null) =>
        set({ selectedNode: node }),

      // ============= Execution State =============

      setExecutionStatus: (status: WorkflowState['executionStatus']) =>
        set({ executionStatus: status }),

      setJobId: (jobId: number | null) => set({ jobId }),

      setUploadedFile: (file: File | null) => set({ uploadedFile: file }),

      // ============= Reset =============

      reset: () => set((state) => ({
        ...initialState,
        // Clear node data but keep the nodes structure
        nodes: state.nodes.map(node => {
          if (node.type === 'result') {
            return {
              ...node,
              data: { label: 'Results', jobId: null, status: 'idle', results: null, error: null }
            } as ResultNode;
          }
          return node;
        })
      })),
    }),
    { name: 'ThreatFlow-Workflow' }
  )
);


// Selectors (for optimized component re-renders)
export const useNodes = () => useWorkflowState((state) => state.nodes);
export const useEdges = () => useWorkflowState((state) => state.edges);
export const useExecutionStatus = () => useWorkflowState((state) => state.executionStatus);
export const useJobId = () => useWorkflowState((state) => state.jobId);
export const useUploadedFile = () => useWorkflowState((state) => state.uploadedFile);
