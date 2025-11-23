/**
 * Custom hook for workflow execution
 * Handles file submission and job status polling
 */

import { useState, useCallback, useRef, useEffect } from 'react';
import { api } from '../services/api';
import { useWorkflowState } from './useWorkflowState';
import { JobStatusResponse, CustomNode, Edge, StageRouting } from '../types/workflow';

/**
 * Distribute analysis results to the appropriate result nodes based on workflow connections
 * Enhanced with conditional routing support
 */
const distributeResultsToResultNodes = (
  allResults: any,
  stageRouting: StageRouting[] | undefined,
  hasConditionals: boolean,
  nodes: CustomNode[],
  edges: Edge[],
  updateNode: (id: string, data: any) => void
) => {
  if (!allResults || !allResults.analyzer_reports) {
    console.warn('No results to distribute');
    return;
  }

  // Find all result nodes
  const resultNodes = nodes.filter(node => node.type === 'result');
  
  if (resultNodes.length === 0) {
    console.warn('No result nodes found in workflow');
    return;
  }

  console.log('=== Result Distribution Debug ===');
  console.log('Has conditionals:', hasConditionals);
  console.log('Stage routing:', stageRouting);
  console.log('Result nodes:', resultNodes.map(n => n.id));
  console.log('=================================');

  // Clear all result nodes first to ensure clean state
  resultNodes.forEach(resultNode => {
    updateNode(resultNode.id, {
      jobId: null,
      status: 'idle',
      results: null,
      error: null,
    });
  });

  // If workflow has conditionals and routing metadata, use it
  if (hasConditionals && stageRouting && stageRouting.length > 0) {
    console.log('Using conditional routing metadata for result distribution');

    // Create maps to track which result nodes should receive results and from which analyzers
    const resultNodeUpdates = new Map<string, { shouldUpdate: boolean, analyzers: string[], error?: string }>();

    // Initialize all result nodes
    resultNodes.forEach(resultNode => {
      resultNodeUpdates.set(resultNode.id, { shouldUpdate: false, analyzers: [], error: 'Branch not executed (condition not met)' });
    });

    // Process each stage's routing
    stageRouting.forEach(routing => {
      const stageAnalyzers = routing.analyzers || [];
      const isExecuted = routing.executed;

      routing.target_nodes.forEach(nodeId => {
        if (resultNodeUpdates.has(nodeId)) {
          const currentUpdate = resultNodeUpdates.get(nodeId)!;

          if (isExecuted) {
            // This stage executed - add its analyzers to this result node
            currentUpdate.shouldUpdate = true;
            currentUpdate.analyzers = Array.from(new Set([...currentUpdate.analyzers, ...stageAnalyzers])); // Unique analyzers
            currentUpdate.error = undefined; // Clear any error
          } else {
            // This stage was skipped - keep the error message
            // Don't change shouldUpdate or analyzers for skipped stages
          }
        }
      });
    });

    console.log('Result node updates map:', Array.from(resultNodeUpdates.entries()));

    // Update result nodes based on the computed updates
    resultNodes.forEach(resultNode => {
      const updateInfo = resultNodeUpdates.get(resultNode.id);

      if (updateInfo && updateInfo.shouldUpdate && updateInfo.analyzers.length > 0) {
        // This node should receive results from specific analyzers
        const filteredResults = {
          ...allResults,
          analyzer_reports: allResults.analyzer_reports.filter((report: any) =>
            updateInfo.analyzers.includes(report.name)
          )
        };

        updateNode(resultNode.id, {
          jobId: allResults.job_id || null,
          status: allResults.status || 'reported_without_fails',
          results: filteredResults,
          error: null,
        });

        console.log(`✅ Result node ${resultNode.id} updated (executed branch) with ${filteredResults.analyzer_reports.length} reports from analyzers:`,
          updateInfo.analyzers);
      } else if (updateInfo && !updateInfo.shouldUpdate) {
        // This node is in a skipped branch
        updateNode(resultNode.id, {
          jobId: null,
          status: 'idle',
          results: null,
          error: updateInfo.error || 'Branch not executed (condition not met)',
        });

        console.log(`⏭️ Result node ${resultNode.id} skipped (${updateInfo.error})`);
      } else {
        // Fallback: no routing info or empty analyzers - use legacy logic
        console.log(`⚠️ Result node ${resultNode.id} using fallback logic`);
        const connectedAnalyzers = findConnectedAnalyzers(resultNode.id, nodes, edges);
        const executedAnalyzers = getExecutedAnalyzersFromRouting(stageRouting!, allResults);
        const connectedExecutedAnalyzers = connectedAnalyzers.filter(analyzer => executedAnalyzers.includes(analyzer));

        if (connectedExecutedAnalyzers.length > 0) {
          const filteredResults = {
            ...allResults,
            analyzer_reports: allResults.analyzer_reports.filter((report: any) =>
              connectedExecutedAnalyzers.includes(report.name)
            )
          };

          updateNode(resultNode.id, {
            jobId: allResults.job_id || null,
            status: allResults.status || 'reported_without_fails',
            results: filteredResults,
            error: null,
          });

          console.log(`⚠️ Result node ${resultNode.id} updated (conditional fallback) with ${filteredResults.analyzer_reports.length} reports:`,
            filteredResults.analyzer_reports.map((r: any) => r.name));
        } else {
          // No connected executed analyzers - show as skipped
          updateNode(resultNode.id, {
            jobId: null,
            status: 'idle',
            results: null,
            error: 'No executed analyzers connected to this result node',
          });

          console.log(`⏭️ Result node ${resultNode.id} skipped (no connected executed analyzers)`);
        }
      }
    });
  } else {
    // Non-conditional workflow - distribute to all result nodes (original behavior)
    console.log('Using legacy result distribution (no conditionals)');
    
    resultNodes.forEach(resultNode => {
      const connectedAnalyzers = findConnectedAnalyzers(resultNode.id, nodes, edges);
      const filteredResults = {
        ...allResults,
        analyzer_reports: allResults.analyzer_reports.filter((report: any) => 
          connectedAnalyzers.includes(report.name)
        )
      };

      updateNode(resultNode.id, {
        jobId: allResults.job_id || null,
        status: allResults.status || 'reported_without_fails',
        results: filteredResults,
        error: null,
      });

      console.log(`Result node ${resultNode.id} updated with ${filteredResults.analyzer_reports.length} reports:`, 
        filteredResults.analyzer_reports.map((r: any) => r.name));
    });
  }
};

/**
 * Get all analyzers that were actually executed based on stage routing
 */
const getExecutedAnalyzersFromRouting = (stageRouting: StageRouting[], allResults: any): string[] => {
  const executedAnalyzers: string[] = [];

  stageRouting.forEach(routing => {
    if (routing.executed && routing.analyzers) {
      routing.analyzers.forEach((analyzer: string) => {
        if (!executedAnalyzers.includes(analyzer)) {
          executedAnalyzers.push(analyzer);
        }
      });
    }
  });

  console.log('Executed analyzers from routing:', executedAnalyzers);
  return executedAnalyzers;
};

/**
 * Find all analyzers that are connected to a result node by tracing back through edges
 */
const findConnectedAnalyzers = (resultNodeId: string, nodes: CustomNode[], edges: Edge[]): string[] => {
  const connectedAnalyzers: string[] = [];
  const visited = new Set<string>();
  
  const traceBackwards = (currentNodeId: string) => {
    if (visited.has(currentNodeId)) return;
    visited.add(currentNodeId);
    
    // Find all edges that point TO this node (incoming edges)
    const incomingEdges = edges.filter(edge => edge.target === currentNodeId);
    
    incomingEdges.forEach(edge => {
      const sourceNode = nodes.find(node => node.id === edge.source);
      
      if (sourceNode) {
        if (sourceNode.type === 'analyzer') {
          // Found an analyzer connected to this result node
          const analyzerData = sourceNode.data as { analyzer: string };
          connectedAnalyzers.push(analyzerData.analyzer);
        } else if (sourceNode.type !== 'result') {
          // Continue tracing back through other node types (like file nodes)
          traceBackwards(sourceNode.id);
        }
      }
    });
  };
  
  // Start tracing from the result node
  traceBackwards(resultNodeId);
  
  return connectedAnalyzers;
};

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
      // Handle both single job_id (linear) and job_ids (conditional) responses
      const jobId = response.job_id || (response.job_ids && response.job_ids.length > 0 ? response.job_ids[0] : null);
      if (!jobId) {
        throw new Error('No job ID returned from server');
      }
      setJobId(jobId);

      // Store routing metadata from initial response
      const workflowMetadata = {
        has_conditionals: response.has_conditionals || false,
        stage_routing: response.stage_routing || []
      };

      // Start polling with abort signal
      const finalStatus = await api.pollJobStatus(
        jobId,
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
      
      // Distribute results to appropriate result nodes based on workflow connections and routing
      distributeResultsToResultNodes(
        finalStatus.results,
        workflowMetadata.stage_routing,
        workflowMetadata.has_conditionals,
        nodes,
        edges,
        updateNode
      );
      
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
      
      // Update all result nodes with error status
      const resultNodes = nodes.filter(n => n.type === 'result');
      resultNodes.forEach(resultNode => {
        updateNode(resultNode.id, {
          jobId: null,
          status: 'failed',
          results: null,
          error: err.message || 'Execution failed',
        });
      });
      
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
