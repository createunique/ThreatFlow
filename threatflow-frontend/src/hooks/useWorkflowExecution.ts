/**
 * Custom hook for workflow execution
 * Handles file submission and job status polling
 * 
 * ARCHITECTURE: Tree-Based Result Distribution
 * - Each Result node (leaf) displays results from ALL analyzers in the path from File node (root)
 * - Primary Strategy: Backend stage routing (pre-computed tree analysis)
 * - Fallback Strategy: DFS traversal from File (root) to Result (leaf)
 */

import { useState, useCallback, useRef, useEffect } from 'react';
import { api } from '../services/api';
import { useWorkflowState } from './useWorkflowState';
import { JobStatusResponse, CustomNode, Edge, StageRouting } from '../types/workflow';

/**
 * 🎯 TREE-BASED RESULT DISTRIBUTION (Works for ALL workflows)
 * Strategy 1: Backend `stageRouting.executed` → Which Result leaves to activate
 * Strategy 2: DFS File(root)→Result(leaf) → Which analyzers for each leaf
 */
const distributeResultsToResultNodes = (
  allResults: any,
  stageRouting: StageRouting[] | undefined,
  hasConditionals: boolean,  // Unused - tree logic works for all
  nodes: CustomNode[],
  edges: Edge[],
  updateNode: (id: string, data: any) => void
) => {
  if (!allResults) {
    console.warn('🌳 No results to distribute');
    return;
  }

  const resultNodes = nodes.filter(node => node.type === 'result'); // All TREE LEAVES
  if (resultNodes.length === 0) {
    console.warn('🌳 No Result leaves found');
    return;
  }

  // Clear all leaves
  resultNodes.forEach(node => {
    updateNode(node.id, { 
      jobId: null, 
      status: 'idle', 
      results: null, 
      error: null 
    });
  });

  console.log('🌳 TREE DISTRIBUTION START:', {
    leaves: resultNodes.length,
    stageRouting: !!stageRouting?.length,
    allResults: !!allResults,
    hasConditionals
  });

  if (stageRouting) {
    console.log('📋 Stage routing received:', stageRouting);
  }

  // STRATEGY 1: Backend tells us which leaves executed
  const executedLeaves = getExecutedLeaves(stageRouting, resultNodes.map(n => n.id));
  
  console.log('🎯 STRATEGY 1 - Executed leaves:', executedLeaves);

  // STRATEGY 2: For each executed leaf, compute File→Leaf analyzers via DFS
  resultNodes.forEach(leafNode => {
    if (!executedLeaves.includes(leafNode.id)) {
      // Non-executed leaf: Show error
      updateNode(leafNode.id, {
        jobId: null,
        status: 'idle',
        results: null,
        error: 'Branch not executed (conditional path not taken)'
      });
      console.log(`⏭️ Leaf ${leafNode.id}: Branch not executed`);
      return;
    }

    // 🎯 EXECUTED LEAF: Compute exact path analyzers (File→this leaf)
    const pathAnalyzers = computeTreePathAnalyzers(
      nodes.find(n => n.type === 'file')?.id || '',
      leafNode.id,
      nodes,
      edges
    );

    if (pathAnalyzers.length === 0) {
      updateNode(leafNode.id, {
        jobId: null, status: 'idle', results: null,
        error: 'No analyzer path from File to Result'
      });
      return;
    }

    // Filter results to ONLY analyzers on this leaf's path
    const leafResults = {
      ...allResults,
      analyzer_reports: getAllAnalyzerReports(allResults).filter(
        (report: any) => pathAnalyzers.includes(report.name)
      )
    };

    console.log(`🔍 Filtering: pathAnalyzers=${JSON.stringify(pathAnalyzers)}, found ${leafResults.analyzer_reports.length} matching reports`);

    updateNode(leafNode.id, {
      jobId: allResults.job_id ?? null,
      status: 'reported_without_fails',
      results: leafResults,
      error: null
    });

    console.log(`✅ Leaf ${leafNode.id}: ${leafResults.analyzer_reports.length} reports`, 
      `[${pathAnalyzers.join(', ')}]`,
      'Reports:', leafResults.analyzer_reports.map((r: any) => r.name));
  });
};

// STRATEGY 1: Backend → Which Result leaves executed?
const getExecutedLeaves = (stageRouting: StageRouting[] | undefined, allLeaves: string[]): string[] => {
  if (!stageRouting?.length) return allLeaves; // Fallback: assume all executed
  
  const executed = new Set<string>();
  stageRouting.forEach(routing => {
    if (routing.executed) {
      (routing.target_nodes || []).forEach(nodeId => executed.add(nodeId));
    }
  });
  return Array.from(executed);
};

// STRATEGY 2: DFS computes File(root)→Result(leaf) analyzer path
const computeTreePathAnalyzers = (
  rootId: string, leafId: string, nodes: CustomNode[], edges: Edge[]
): string[] => {
  const allPaths: string[][] = [];
  const visited = new Set<string>();

  const dfs = (currentId: string, path: string[]) => {
    if (visited.has(currentId)) return;
    
    const node = nodes.find(n => n.id === currentId);
    if (!node) return;

    const newPath = [...path];
    // Collect analyzer from this node
    if (node.type === 'analyzer') {
      const analyzer = (node.data as any).analyzer;
      if (analyzer) newPath.push(analyzer);
    }

    // Found target leaf - save path
    if (currentId === leafId) {
      allPaths.push(newPath);
      return;
    }

    visited.add(currentId);
    
    // Explore children (tree edges)
    edges
      .filter(e => e.source === currentId)
      .forEach(edge => dfs(edge.target, newPath));
    
    visited.delete(currentId); // Backtrack
  };

  dfs(rootId, []);
  
  // Merge ALL paths: unique analyzers from root→leaf
  const analyzers = new Set<string>();
  allPaths.flat().forEach(a => analyzers.add(a));
  
  return Array.from(analyzers);
};

// Helper: Collect ALL analyzer reports from results
const getAllAnalyzerReports = (allResults: any): any[] => {
  const reports: any[] = [];

  // Check if analyzer_reports is at root level (IntelOwl job structure)
  if (allResults.analyzer_reports && Array.isArray(allResults.analyzer_reports)) {
    reports.push(...allResults.analyzer_reports);
  }

  // Also check nested structure (stage-based results)
  Object.keys(allResults).forEach(key => {
    const data = allResults[key];
    if (data && typeof data === 'object' && data.analyzer_reports && Array.isArray(data.analyzer_reports)) {
      reports.push(...data.analyzer_reports);
    }
  });

  console.log('📊 All analyzer reports found:', reports.map(r => ({ name: r.name, status: r.status })));
  return reports;
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
      // Handle both single job_id and multiple job_ids (for conditional workflows)
      const jobId = response.job_id ?? (response.job_ids?.[0] ?? null);
      setJobId(jobId);

      // Start polling with abort signal
      const finalStatus = await api.pollJobStatus(
        jobId ?? 0,
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
      
      // Check if workflow has conditionals
      const hasConditionals = nodes.some(node => node.type === 'conditional');
      
      // Distribute results to appropriate result nodes based on workflow connections
      distributeResultsToResultNodes(
        finalStatus.results,
        finalStatus.stagerouting,
        hasConditionals,
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
