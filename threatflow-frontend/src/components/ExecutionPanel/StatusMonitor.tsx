/**
 * Status Monitor
 * Real-time display of job execution status
 */

import React from 'react';
import { Box, Paper, Typography, LinearProgress, Chip } from '@mui/material';
import { Clock, CheckCircle2, XCircle, Loader2 } from 'lucide-react';
import { useWorkflowExecution } from '../../hooks/useWorkflowExecution';
import { useWorkflowState } from '../../hooks/useWorkflowState';

const StatusMonitor: React.FC = () => {
  const { statusUpdates, loading } = useWorkflowExecution();
  const executionStatus = useWorkflowState((state) => state.executionStatus);
  const jobId = useWorkflowState((state) => state.jobId);

  if (executionStatus === 'idle' && !jobId) {
    return null;
  }

  const getStatusIcon = () => {
    switch (executionStatus) {
      case 'running':
        return <Loader2 size={20} className="animate-spin" />;
      case 'completed':
        return <CheckCircle2 size={20} color="#4caf50" />;
      case 'error':
        return <XCircle size={20} color="#f44336" />;
      default:
        return <Clock size={20} />;
    }
  };

  const getStatusColor = () => {
    switch (executionStatus) {
      case 'running':
        return 'info';
      case 'completed':
        return 'success';
      case 'error':
        return 'error';
      default:
        return 'default';
    }
  };

  const progress = statusUpdates
    ? (statusUpdates.analyzers_completed / statusUpdates.analyzers_total) * 100
    : 0;

  return (
    <Paper
      elevation={2}
      sx={{
        padding: 2,
        minWidth: 400,
        border: '1px solid #e0e0e0',
        borderRadius: 2,
      }}
    >
      {/* Header */}
      <Box display="flex" alignItems="center" justifyContent="space-between" mb={2}>
        <Box display="flex" alignItems="center" gap={1}>
          {getStatusIcon()}
          <Typography variant="subtitle1" fontWeight="bold">
            Execution Status
          </Typography>
        </Box>
        <Chip label={executionStatus} color={getStatusColor() as any} size="small" />
      </Box>

      {/* Job ID */}
      {jobId && (
        <Typography variant="caption" color="text.secondary" display="block" mb={1}>
          Job ID: {jobId}
        </Typography>
      )}

      {/* Progress Bar */}
      {loading && statusUpdates && (
        <Box mb={2}>
          <Box display="flex" justifyContent="space-between" mb={0.5}>
            <Typography variant="caption">
              Analyzers: {statusUpdates.analyzers_completed} / {statusUpdates.analyzers_total}
            </Typography>
            <Typography variant="caption">{Math.round(progress)}%</Typography>
          </Box>
          <LinearProgress variant="determinate" value={progress} />
        </Box>
      )}

      {/* Status Details */}
      {statusUpdates && (
        <Box
          sx={{
            backgroundColor: '#f5f5f5',
            padding: 1.5,
            borderRadius: 1,
            maxHeight: 150,
            overflow: 'auto',
          }}
        >
          <Typography variant="caption" fontWeight="bold" display="block" mb={0.5}>
            Status: {statusUpdates.status}
          </Typography>
          {statusUpdates.results && (
            <Typography variant="caption" color="success.main">
              ✓ Analysis complete
            </Typography>
          )}
        </Box>
      )}
    </Paper>
  );
};

export default StatusMonitor;
