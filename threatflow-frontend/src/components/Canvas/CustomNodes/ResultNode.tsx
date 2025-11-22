/**
 * Result Display Node
 * Shows analysis results and job status
 */

import React, { FC, useState } from 'react';
import { Handle, Position, NodeProps } from 'reactflow';
import { CheckCircle2, XCircle, Loader2, AlertTriangle, Eye } from 'lucide-react';
import { Box, Typography, Paper, Chip, Button, Dialog, DialogTitle, DialogContent, DialogActions, IconButton } from '@mui/material';
import { Close as CloseIcon } from '@mui/icons-material';
import ErrorBoundary from '../../ErrorBoundary';
import { ResultTabs } from './ResultTabs';
import { ResultNodeData } from '../../../types/workflow';

const ResultNodeContent: FC<NodeProps<ResultNodeData>> = ({ data, selected }) => {
  const [modalOpen, setModalOpen] = useState(false);

  const handleOpenModal = () => setModalOpen(true);
  const handleCloseModal = () => setModalOpen(false);

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

      {/* Results Summary */}
      {data.results ? (
        <Box
          sx={{
            backgroundColor: '#f5f5f5',
            padding: 1.5,
            borderRadius: 1,
          }}
          role="region"
          aria-label="Analysis results summary"
        >
          <Box display="flex" alignItems="center" gap={1} mb={1}>
            <CheckCircle2 size={16} color="#4caf50" />
            <Typography variant="body2" fontWeight="medium">
              Analysis Complete
            </Typography>
          </Box>
          <Typography variant="caption" color="text.secondary">
            {data.results.analyzer_reports?.length || 0} analyzers ran
          </Typography>
          <Box mt={1}>
            <Button
              size="small"
              variant="outlined"
              startIcon={<Eye size={14} />}
              onClick={handleOpenModal}
              sx={{
                fontSize: '0.75rem',
                padding: '4px 8px',
                minHeight: '28px',
              }}
            >
              View Details
            </Button>
          </Box>
        </Box>
      ) : data.status === 'running' ? (
        <Box
          sx={{
            backgroundColor: '#fff3e0',
            padding: 1.5,
            borderRadius: 1,
          }}
          role="region"
          aria-label="Analysis in progress"
        >
          <Box display="flex" alignItems="center" gap={1} mb={1}>
            <Loader2 size={16} color="#ff9800" className="animate-spin" />
            <Typography variant="body2" fontWeight="medium">
              Analysis Running...
            </Typography>
          </Box>
          <Typography variant="caption" color="text.secondary">
            Processing your file
          </Typography>
        </Box>
      ) : (
        <Box
          sx={{
            backgroundColor: '#f5f5f5',
            padding: 1.5,
            borderRadius: 1,
          }}
          role="region"
          aria-label="No results available"
        >
          <Typography variant="body2" color="text.secondary">
            No results yet
          </Typography>
          <Typography variant="caption" color="text.secondary" display="block">
            Run workflow to generate analysis
          </Typography>
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

      {/* Results Modal */}
      <Dialog
        open={modalOpen}
        onClose={handleCloseModal}
        maxWidth="lg"
        fullWidth
        sx={{
          '& .MuiDialog-paper': {
            width: '70vw',
            height: '70vh',
            maxWidth: 'none',
          },
        }}
        aria-labelledby="results-modal-title"
        aria-describedby="results-modal-description"
      >
        <DialogTitle id="results-modal-title" sx={{ pb: 1 }}>
          <Box display="flex" alignItems="center" justifyContent="space-between">
            <Typography variant="h6" component="div" fontWeight="bold">
              Analysis Results Details
            </Typography>
            <IconButton
              onClick={handleCloseModal}
              size="small"
              aria-label="Close results modal"
            >
              <CloseIcon />
            </IconButton>
          </Box>
          {data.jobId && (
            <Typography variant="caption" color="text.secondary">
              Job ID: {data.jobId}
            </Typography>
          )}
        </DialogTitle>
        <DialogContent id="results-modal-description" sx={{ pt: 1 }}>
          {data.results ? (
            <ResultTabs results={data.results} />
          ) : (
            <Box
              display="flex"
              flexDirection="column"
              alignItems="center"
              justifyContent="center"
              py={4}
              color="text.secondary"
            >
              <Typography variant="body1">
                No results available
              </Typography>
            </Box>
          )}
        </DialogContent>
        <DialogActions sx={{ pt: 1, pb: 2, px: 3 }}>
          <Button onClick={handleCloseModal} variant="outlined">
            Close
          </Button>
        </DialogActions>
      </Dialog>
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
