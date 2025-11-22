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
          >
            {loading ? 'Running...' : executionStatus === 'completed' ? 'Completed' : 'Execute'}
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
          >
            Reset
          </Button>
        </Tooltip>
      )}

      {/* Error Display */}
      {error && (
        <Box color="error.main" ml={2}>
          <Typography variant="caption">{error}</Typography>
        </Box>
      )}
    </Box>
  );
};

export default ExecuteButton;
