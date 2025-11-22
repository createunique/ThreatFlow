/**
 * Custom hook for workflow execution
 * Handles file submission and job status polling
 */

import { useState, useCallback, useRef, useEffect } from 'react';
import { api } from '../services/api';
import { useWorkflowState } from './useWorkflowState';
import { JobStatusResponse } from '../types/workflow';

export const useWorkflowExecution = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [statusUpdates, setStatusUpdates] = useState<JobStatusResponse | null>(null);
  const [uploadProgress, setUploadProgress] = useState<number>(0);

  // Refs for cleanup and preventing memory leaks
  const abortControllerRef = useRef<AbortController | null>(null);
  const isMountedRef = useRef(true);

  const nodes = useWorkflowState((state) => state.nodes);
  const edges = useWorkflowState((state) => state.edges);
  const uploadedFile = useWorkflowState((state) => state.uploadedFile);
  const setJobId = useWorkflowState((state) => state.setJobId);
  const setExecutionStatus = useWorkflowState((state) => state.setExecutionStatus);
  const updateNode = useWorkflowState((state) => state.updateNode);

  // Cleanup effect to prevent memory leaks
  useEffect(() => {
    return () => {
      isMountedRef.current = false;
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
        abortControllerRef.current = null;
      }
    };
  }, []);

  // Safe state setters that check if component is mounted
  const safeSetLoading = useCallback((value: boolean) => {
    if (isMountedRef.current) setLoading(value);
  }, []);

  const safeSetError = useCallback((value: string | null) => {
    if (isMountedRef.current) setError(value);
  }, []);

  const safeSetStatusUpdates = useCallback((value: JobStatusResponse | null) => {
    if (isMountedRef.current) setStatusUpdates(value);
  }, []);

  const safeSetUploadProgress = useCallback((value: number) => {
    if (isMountedRef.current) setUploadProgress(value);
  }, []);

  /**
   * Execute workflow
   */
  /* eslint-disable react-hooks/exhaustive-deps */
  const executeWorkflow = useCallback(async () => {
    // Prevent concurrent executions
    if (loading) {
      console.warn('Workflow execution already in progress');
      return null;
    }

    // Cancel any existing operation
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }

    // Create new abort controller
    abortControllerRef.current = new AbortController();

    try {
      // Validation
      if (!uploadedFile) {
        safeSetError('No file uploaded');
        return null;
      }

      if (nodes.length === 0) {
        safeSetError('Workflow is empty');
        return null;
      }

      // Check if file node exists
      const hasFileNode = nodes.some((n) => n.type === 'file');
      if (!hasFileNode) {
        safeSetError('Workflow must contain a file node');
        return null;
      }

      // Check if analyzer nodes exist
      const hasAnalyzer = nodes.some((n) => n.type === 'analyzer');
      if (!hasAnalyzer) {
        safeSetError('Workflow must contain at least one analyzer');
        return null;
      }

      safeSetLoading(true);
      safeSetError(null);
      setExecutionStatus('running');
      safeSetUploadProgress(0);

      // Submit workflow
      const response = await api.executeWorkflow(
        nodes,
        edges,
        uploadedFile,
        (progress) => safeSetUploadProgress(progress)
      );

      console.log('Workflow submitted:', response);
      setJobId(response.job_id);

      // Start polling with abort signal
      const finalStatus = await api.pollJobStatus(
        response.job_id,
        (status) => {
          try {
            console.log('Status update:', status);
            safeSetStatusUpdates(status);
          } catch (updateError) {
            console.error('Error updating status:', updateError);
            // Don't throw here, just log the error
          }
        },
        60, // maxAttempts
        abortControllerRef.current.signal
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
      // Handle abort errors gracefully
      if (err.message === 'Polling aborted') {
        console.log('Workflow execution was cancelled');
        return null;
      }

      console.error('Workflow execution failed:', err);
      safeSetError(err.message || 'Execution failed');
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
      safeSetLoading(false);
      abortControllerRef.current = null;
    }
  }, [nodes, edges, uploadedFile, setJobId, setExecutionStatus, updateNode, loading]);
  /* eslint-enable react-hooks/exhaustive-deps */

  /**
   * Cancel ongoing execution
   */
  /* eslint-disable react-hooks/exhaustive-deps */
  const cancelExecution = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    safeSetLoading(false);
    safeSetError('Execution cancelled');
    setExecutionStatus('idle');
  }, [setExecutionStatus]);
  /* eslint-enable react-hooks/exhaustive-deps */

  /**
   * Check if execution can be cancelled
   */
  const canCancel = useCallback(() => {
    return loading && abortControllerRef.current !== null;
  }, [loading]);

  /**
   * Reset execution state
   */
  /* eslint-disable react-hooks/exhaustive-deps */
  const resetExecution = useCallback(() => {
    // Cancel any ongoing operation
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }

    safeSetLoading(false);
    safeSetError(null);
    safeSetStatusUpdates(null);
    safeSetUploadProgress(0);
    setJobId(null);
    setExecutionStatus('idle');
  }, [setJobId, setExecutionStatus]);
  /* eslint-enable react-hooks/exhaustive-deps */

  return {
    executeWorkflow,
    resetExecution,
    cancelExecution,
    canCancel,
    loading,
    error,
    statusUpdates,
    uploadProgress,
  };
};
