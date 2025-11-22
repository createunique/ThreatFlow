/**
 * Custom hook for workflow execution
 * Handles file submission and job status polling
 */

import { useState, useCallback } from 'react';
import { api } from '../services/api';
import { useWorkflowState } from './useWorkflowState';
import { JobStatusResponse } from '../types/workflow';

export const useWorkflowExecution = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [statusUpdates, setStatusUpdates] = useState<JobStatusResponse | null>(null);

  const nodes = useWorkflowState((state) => state.nodes);
  const edges = useWorkflowState((state) => state.edges);
  const uploadedFile = useWorkflowState((state) => state.uploadedFile);
  const setJobId = useWorkflowState((state) => state.setJobId);
  const setExecutionStatus = useWorkflowState((state) => state.setExecutionStatus);
  const updateNode = useWorkflowState((state) => state.updateNode);

  /**
   * Execute workflow
   */
  const executeWorkflow = useCallback(async () => {
    // Validation
    if (!uploadedFile) {
      setError('No file uploaded');
      return null;
    }

    if (nodes.length === 0) {
      setError('Workflow is empty');
      return null;
    }

    // Check if file node exists
    const hasFileNode = nodes.some((n) => n.type === 'file');
    if (!hasFileNode) {
      setError('Workflow must contain a file node');
      return null;
    }

    // Check if analyzer nodes exist
    const hasAnalyzer = nodes.some((n) => n.type === 'analyzer');
    if (!hasAnalyzer) {
      setError('Workflow must contain at least one analyzer');
      return null;
    }

    setLoading(true);
    setError(null);
    setExecutionStatus('running');

    try {
      // Submit workflow
      const response = await api.executeWorkflow(nodes, edges, uploadedFile);

      console.log('Workflow submitted:', response);
      setJobId(response.job_id);

      // Start polling
      const finalStatus = await api.pollJobStatus(
        response.job_id,
        (status) => {
          console.log('Status update:', status);
          setStatusUpdates(status);
        }
      );

      console.log('Workflow completed:', finalStatus);
      setExecutionStatus('completed');
      
      // Update ResultNode with results
      const resultNode = nodes.find(n => n.type === 'result');
      if (resultNode) {
        updateNode(resultNode.id, {
          jobId: finalStatus.job_id,
          status: finalStatus.status,
          results: finalStatus.results || null,
          error: null,
        });
      }
      
      return finalStatus;
    } catch (err: any) {
      console.error('Workflow execution failed:', err);
      setError(err.message || 'Execution failed');
      setExecutionStatus('error');
      
      // Update ResultNode with error
      const resultNode = nodes.find(n => n.type === 'result');
      if (resultNode) {
        updateNode(resultNode.id, {
          jobId: null,
          status: 'failed',
          results: null,
          error: err.message || 'Execution failed',
        });
      }
      
      return null;
    } finally {
      setLoading(false);
    }
  }, [nodes, edges, uploadedFile, setJobId, setExecutionStatus, updateNode]);

  /**
   * Reset execution state
   */
  const resetExecution = useCallback(() => {
    setLoading(false);
    setError(null);
    setStatusUpdates(null);
    setJobId(null);
    setExecutionStatus('idle');
  }, [setJobId, setExecutionStatus]);

  return {
    executeWorkflow,
    resetExecution,
    loading,
    error,
    statusUpdates,
  };
};
