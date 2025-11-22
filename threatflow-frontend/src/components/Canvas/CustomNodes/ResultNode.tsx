/**
 * Result Display Node
 * Shows analysis results and job status
 */

import React, { FC } from 'react';
import { Handle, Position, NodeProps } from 'reactflow';
import { CheckCircle2, XCircle, Loader2, AlertTriangle } from 'lucide-react';
import { Box, Typography, Paper, Chip } from '@mui/material';
import { ResultNodeData } from '../../../types/workflow';

const ResultNode: FC<NodeProps<ResultNodeData>> = ({ data, selected }) => {
  const getStatusIcon = () => {
    switch (data.status) {
      case 'reported_without_fails':
        return <CheckCircle2 size={20} color="#4caf50" />;
      case 'reported_with_fails':
        return <AlertTriangle size={20} color="#ff9800" />;
      case 'running':
        return <Loader2 size={20} color="#2196f3" className="animate-spin" />;
      case 'failed':
        return <XCircle size={20} color="#f44336" />;
      default:
        return <Loader2 size={20} color="#9e9e9e" />;
    }
  };

  const getStatusColor = () => {
    switch (data.status) {
      case 'reported_without_fails':
        return 'success';
      case 'reported_with_fails':
        return 'warning';
      case 'running':
        return 'info';
      case 'failed':
        return 'error';
      default:
        return 'default';
    }
  };

  return (
    <Paper
      elevation={selected ? 8 : 2}
      sx={{
        padding: 2,
        minWidth: 280,
        border: selected ? '2px solid #9c27b0' : '1px solid #ccc',
        borderRadius: 2,
        backgroundColor: '#fff',
      }}
    >
      {/* Handle (input) */}
      <Handle
        type="target"
        position={Position.Left}
        style={{
          background: '#9c27b0',
          width: 12,
          height: 12,
          border: '2px solid #fff',
        }}
      />

      {/* Header */}
      <Box display="flex" alignItems="center" gap={1} mb={2}>
        {getStatusIcon()}
        <Typography variant="subtitle1" fontWeight="bold">
          Results
        </Typography>
      </Box>

      {/* Job ID */}
      {data.jobId && (
        <Typography variant="caption" color="text.secondary" mb={1} display="block">
          Job ID: {data.jobId}
        </Typography>
      )}

      {/* Status */}
      <Chip
        label={data.status || 'Idle'}
        color={getStatusColor() as any}
        size="small"
        sx={{ mb: 2 }}
      />

      {/* Results */}
      {data.results && (
        <Box
          sx={{
            backgroundColor: '#f5f5f5',
            padding: 1.5,
            borderRadius: 1,
            maxHeight: 200,
            overflow: 'auto',
          }}
        >
          <Typography variant="caption" component="pre" sx={{ whiteSpace: 'pre-wrap' }}>
            {JSON.stringify(data.results, null, 2)}
          </Typography>
        </Box>
      )}

      {/* Error */}
      {data.error && (
        <Box display="flex" alignItems="center" gap={1} color="error.main" mt={1}>
          <XCircle size={16} />
          <Typography variant="caption">{data.error}</Typography>
        </Box>
      )}
    </Paper>
  );
};

export default ResultNode;
