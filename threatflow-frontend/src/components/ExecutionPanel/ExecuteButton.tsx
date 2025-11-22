/**
 * Execute Button
 * Triggers workflow execution
 */

import React from 'react';
import { Button, CircularProgress, Box, Tooltip, Typography } from '@mui/material';
import { Play, RotateCcw } from 'lucide-react';
import { useWorkflowExecution } from '../../hooks/useWorkflowExecution';
import { useWorkflowState } from '../../hooks/useWorkflowState';

const ExecuteButton: React.FC = () => {
  const { executeWorkflow, resetExecution, loading, error } = useWorkflowExecution();
  const executionStatus = useWorkflowState((state) => state.executionStatus);
  const uploadedFile = useWorkflowState((state) => state.uploadedFile);
  const nodes = useWorkflowState((state) => state.nodes);

  const handleExecute = async () => {
    const result = await executeWorkflow();
    if (result) {
      console.log('Execution completed:', result);
    }
  };

  const handleReset = () => {
    resetExecution();
  };

  const canExecute = uploadedFile && nodes.length > 0 && executionStatus === 'idle';

  const getButtonLabel = () => {
    if (loading) return 'Executing workflow...';
    if (executionStatus === 'completed') return 'Workflow completed';
    if (executionStatus === 'error') return 'Execution failed - try again';
    return 'Execute workflow';
  };

  const getButtonAriaLabel = () => {
    if (!uploadedFile) return 'Cannot execute: No file uploaded. Please upload a file first.';
    if (nodes.length === 0) return 'Cannot execute: No workflow nodes added. Please add analyzer nodes to the workflow.';
    if (loading) return `Executing workflow. ${executionStatus === 'running' ? 'Analysis in progress.' : 'Please wait.'}`;
    if (executionStatus === 'completed') return 'Workflow execution completed successfully. Results are available.';
    if (executionStatus === 'error') return 'Workflow execution failed. Click to try again.';
    return 'Execute workflow analysis. This will upload the file and run all configured analyzers.';
  };

  return (
    <Box display="flex" gap={2} alignItems="center">
      {/* Execute Button */}
      <Tooltip
        title={
          !uploadedFile
            ? 'Please upload a file first'
            : nodes.length === 0
            ? 'Add nodes to the workflow'
            : 'Execute workflow'
        }
      >
        <span>
          <Button
            variant="contained"
            color="primary"
            size="large"
            startIcon={loading ? <CircularProgress size={20} color="inherit" /> : <Play size={20} />}
            onClick={handleExecute}
            disabled={!canExecute || loading}
            sx={{ minWidth: 150 }}
            aria-label={getButtonAriaLabel()}
            aria-describedby={error ? "execution-error" : undefined}
            role="button"
          >
            {getButtonLabel()}
          </Button>
        </span>
      </Tooltip>

      {/* Reset Button */}
      {executionStatus !== 'idle' && (
        <Tooltip title="Reset workflow execution">
          <Button
            variant="outlined"
            color="secondary"
            size="large"
            startIcon={<RotateCcw size={20} />}
            onClick={handleReset}
            disabled={loading}
            aria-label="Reset workflow execution. This will clear all results and allow you to run the analysis again."
            role="button"
          >
            Reset
          </Button>
        </Tooltip>
      )}

      {/* Error Display */}
      {error && (
        <Box 
          color="error.main" 
          ml={2}
          role="alert"
          aria-live="assertive"
          id="execution-error"
        >
          <Typography variant="caption">{error}</Typography>
        </Box>
      )}
    </Box>
  );
};

export default ExecuteButton;
