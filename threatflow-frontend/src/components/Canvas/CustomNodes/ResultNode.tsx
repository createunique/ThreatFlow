/**
 * Result Display Node
 * Shows analysis results and job status
 */

import React, { FC } from 'react';
import { Handle, Position, NodeProps } from 'reactflow';
import { CheckCircle2, XCircle, Loader2, AlertTriangle } from 'lucide-react';
import { Box, Typography, Paper, Chip } from '@mui/material';
import ErrorBoundary from '../../ErrorBoundary';
import { ResultTabs } from './ResultTabs';
import { ResultNodeData } from '../../../types/workflow';

const ResultNodeContent: FC<NodeProps<ResultNodeData>> = ({ data, selected }) => {

  const getStatusIcon = () => {
    try {
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
    } catch (error) {
      console.error('Error getting status icon:', error);
      return <XCircle size={20} color="#f44336" />;
    }
  };

  const getStatusColor = () => {
    try {
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
    } catch (error) {
      console.error('Error getting status color:', error);
      return 'error';
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
      role="region"
      aria-label={`Results node ${selected ? '(selected)' : ''} - Status: ${data.status || 'Idle'}${data.jobId ? ` - Job ID: ${data.jobId}` : ''}`}
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
        role="status"
        aria-label={`Analysis status: ${data.status || 'Idle'}`}
      />

      {/* Results */}
      {data.results && (
        <Box
          sx={{
            backgroundColor: '#f5f5f5',
            padding: 1.5,
            borderRadius: 1,
            maxHeight: 300,
            overflow: 'auto',
          }}
          role="region"
          aria-label="Analysis results"
          tabIndex={0}
        >
          <ResultTabs results={data.results} />
        </Box>
      )}

      {/* Error */}
      {data.error && (
        <Box 
          display="flex" 
          alignItems="center" 
          gap={1} 
          color="error.main" 
          mt={1}
          role="alert"
          aria-live="assertive"
        >
          <XCircle size={16} aria-hidden="true" />
          <Typography variant="caption">{data.error}</Typography>
        </Box>
      )}
    </Paper>
  );
};

const ResultNode: FC<NodeProps<ResultNodeData>> = (props) => {
  return (
    <ErrorBoundary
      name={`Result Node (${props.id})`}
      fallback={
        <Paper
          elevation={props.selected ? 8 : 2}
          sx={{
            padding: 2,
            minWidth: 280,
            border: props.selected ? '2px solid #f44336' : '1px solid #f44336',
            borderRadius: 2,
            backgroundColor: '#ffebee',
          }}
        >
          <Box textAlign="center" color="error.main">
            <Typography variant="subtitle1" fontWeight="bold">
              Result Node Error
            </Typography>
            <Typography variant="caption">
              Failed to load results display component
            </Typography>
          </Box>
        </Paper>
      }
    >
      <ResultNodeContent {...props} />
    </ErrorBoundary>
  );
};

export default ResultNode;
