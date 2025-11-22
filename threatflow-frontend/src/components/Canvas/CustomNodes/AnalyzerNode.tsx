import React, { FC, useState, useEffect, memo } from 'react';
import { Handle, Position, NodeProps, useReactFlow } from 'reactflow';
import { Shield, AlertCircle, X, Edit2 } from 'lucide-react';
import {
  Box,
  Typography,
  Paper,
  CircularProgress,
  IconButton,
  Tooltip,
  Button,
  Chip,
} from '@mui/material';
import ErrorBoundary from '../../ErrorBoundary';
import AnalyzerSelectionModal from '../../Sidebar/AnalyzerSelectionModal';
import { useWorkflowState } from '../../../hooks/useWorkflowState';
import { AnalyzerNodeData, AnalyzerInfo, AnalyzersResponse } from '../../../types/workflow';
import { api } from '../../../services/api';

// Singleton to prevent duplicate API calls
let cachedAnalyzers: AnalyzerInfo[] | null = null;
let analyzersFetchPromise: Promise<AnalyzerInfo[]> | null = null;

const fetchAnalyzersOnce = async (): Promise<AnalyzerInfo[]> => {
  if (cachedAnalyzers) {
    return cachedAnalyzers;
  }
  
  if (!analyzersFetchPromise) {
    analyzersFetchPromise = api.getAnalyzers('file').then((response: AnalyzersResponse) => {
      // Combine available and unavailable analyzers
      cachedAnalyzers = [...response.available, ...response.unavailable];
      analyzersFetchPromise = null;
      return cachedAnalyzers;
    });
  }
  
  return analyzersFetchPromise;
};

const AnalyzerNodeContent: FC<NodeProps<AnalyzerNodeData>> = ({ id, data, selected }) => {
  const [analyzers, setAnalyzers] = useState<AnalyzerInfo[]>(cachedAnalyzers || []);
  const [loading, setLoading] = useState(!cachedAnalyzers);
  const [error, setError] = useState<string | null>(null);
  const [modalOpen, setModalOpen] = useState(false);

  const { setNodes } = useReactFlow();
  const updateNode = useWorkflowState((state) => state.updateNode);
  const deleteNode = useWorkflowState((state) => state.deleteNode);

  // Fetch analyzers on mount (singleton pattern)
  useEffect(() => {
    if (cachedAnalyzers) {
      setAnalyzers(cachedAnalyzers);
      setLoading(false);
      return;
    }

    let mounted = true;

    fetchAnalyzersOnce()
      .then((data) => {
        if (mounted) {
          setAnalyzers(data);
          setError(null);
        }
      })
      .catch((err: any) => {
        console.error('[AnalyzerNode] Failed to fetch analyzers:', err);
        if (mounted) {
          setError('Failed to load analyzers');
        }
      })
      .finally(() => {
        if (mounted) {
          setLoading(false);
        }
      });

    return () => {
      mounted = false;
    };
  }, []);

  const handleAnalyzerSelect = (analyzer: AnalyzerInfo) => {
    try {
      // Update React Flow state directly for immediate UI update
      setNodes((nds) =>
        nds.map((node) => {
          if (node.id === id) {
            return {
              ...node,
              data: {
                ...node.data,
                analyzer: analyzer.name,
                description: analyzer.description,
                analyzerType: analyzer.type,
              },
            };
          }
          return node;
        })
      );

      // Also update Zustand store for persistence
      updateNode(id, {
        analyzer: analyzer.name,
        description: analyzer.description,
        analyzerType: analyzer.type,
      });

      setModalOpen(false);
    } catch (error) {
      console.error('Error selecting analyzer:', error);
      throw error; // Let error boundary catch it
    }
  };

  const handleOpenModal = () => {
    if (!loading) {
      setModalOpen(true);
    }
  };

  return (
    <>
      <Paper
        elevation={selected ? 8 : 2}
        sx={{
          padding: 2,
          minWidth: 280,
          maxWidth: 320,
          border: selected ? '2px solid #4caf50' : '1px solid #ccc',
          borderRadius: 2,
          backgroundColor: '#fff',
          position: 'relative',
          transition: 'all 0.2s ease-in-out',
          '&:hover': {
            boxShadow: selected ? 8 : 4,
          },
        }}
        role="region"
        aria-label={`Analyzer node ${selected ? '(selected)' : ''}${data.analyzer ? ` - ${data.analyzer} selected` : ' - no analyzer selected'}`}
      >
        {/* Handles */}
        <Handle
          type="target"
          position={Position.Left}
          id="input"
          style={{
            background: '#4caf50',
            width: 12,
            height: 12,
            border: '2px solid #fff',
          }}
        />
        <Handle
          type="source"
          position={Position.Right}
          id="output"
          style={{
            background: '#4caf50',
            width: 12,
            height: 12,
            border: '2px solid #fff',
          }}
        />

        {/* Header */}
        <Box display="flex" alignItems="center" gap={1} mb={2}>
          <Shield size={20} color="#4caf50" />
          <Typography variant="subtitle1" fontWeight="bold">
            Analyzer
          </Typography>
          <Box sx={{ flexGrow: 1 }} />
          <Tooltip title="Delete node (Del)" placement="top">
            <IconButton
              size="small"
              onClick={(e) => {
                e.stopPropagation();
                deleteNode(id);
              }}
              sx={{
                color: '#666',
                '&:hover': {
                  color: '#f44336',
                  backgroundColor: '#ffebee',
                },
                width: 24,
                height: 24,
              }}
              aria-label="Delete analyzer node"
            >
              <X size={14} />
            </IconButton>
          </Tooltip>
        </Box>

        {/* Analyzer Selection */}
        {loading ? (
          <Box display="flex" justifyContent="center" py={2} role="status" aria-label="Loading analyzers">
            <CircularProgress size={24} aria-hidden="true" />
          </Box>
        ) : error ? (
          <Box display="flex" alignItems="center" gap={1} color="error.main" role="alert" aria-live="assertive">
            <AlertCircle size={16} aria-hidden="true" />
            <Typography variant="caption">{error}</Typography>
          </Box>
        ) : (
          <Box
            sx={{
              display: 'flex',
              flexDirection: 'column',
              gap: 1.5,
            }}
          >
            {/* Selection Button */}
            <Button
              fullWidth
              variant="outlined"
              onClick={handleOpenModal}
              startIcon={<Edit2 size={18} />}
              sx={{
                textTransform: 'none',
                color: data.analyzer ? '#4caf50' : '#666',
                borderColor: data.analyzer ? '#4caf50' : '#ccc',
                backgroundColor: data.analyzer ? '#f1f8f4' : '#fafafa',
                '&:hover': {
                  borderColor: '#4caf50',
                  backgroundColor: '#e8f5e9',
                },
                py: 1,
              }}
              aria-label={`Select analyzer (currently ${data.analyzer || 'none'} selected)`}
            >
              {data.analyzer ? 'Change Analyzer' : 'Select Analyzer'}
            </Button>

            {/* Analyzer Count Badge */}
            <Chip
              label={`${analyzers.filter(a => a.available).length}/${analyzers.length} analyzers available`}
              size="small"
              variant="outlined"
              sx={{
                width: 'fit-content',
                mx: 'auto',
                fontSize: '0.75rem',
              }}
            />
          </Box>
        )}

        {/* Selected Analyzer Info */}
        {data.analyzer && (
          <Box 
            mt={2} 
            p={1.5} 
            sx={{
              backgroundColor: '#f0f8f4',
              borderRadius: 1,
              border: '1px solid #c8e6c9',
            }}
            id="selected-analyzer-info"
            role="region"
            aria-label={`Selected analyzer information: ${data.analyzer}`}
          >
            <Box display="flex" alignItems="center" gap={1} mb={0.5}>
              <Box
                sx={{
                  width: 8,
                  height: 8,
                  borderRadius: '50%',
                  backgroundColor: '#4caf50',
                }}
              />
              <Typography variant="caption" fontWeight="bold" sx={{ color: '#2e7d32' }}>
                {data.analyzer}
              </Typography>
            </Box>
            <Typography variant="caption" color="text.secondary" display="block" sx={{ mt: 0.5 }}>
              {data.description || 'No description available'}
            </Typography>
          </Box>
        )}
      </Paper>

      {/* Analyzer Selection Modal */}
      <AnalyzerSelectionModal
        open={modalOpen}
        analyzers={analyzers}
        loading={loading}
        error={error}
        selectedAnalyzer={data.analyzer || null}
        onSelect={handleAnalyzerSelect}
        onClose={() => setModalOpen(false)}
      />
    </>
  );
};

const AnalyzerNode: FC<NodeProps<AnalyzerNodeData>> = (props) => {
  return (
    <ErrorBoundary
      name={`Analyzer Node (${props.id})`}
      fallback={
        <Paper
          elevation={props.selected ? 8 : 2}
          sx={{
            padding: 2,
            minWidth: 280,
            maxWidth: 300,
            border: props.selected ? '2px solid #f44336' : '1px solid #f44336',
            borderRadius: 2,
            backgroundColor: '#ffebee',
          }}
        >
          <Box textAlign="center" color="error.main">
            <Typography variant="subtitle1" fontWeight="bold">
              Analyzer Node Error
            </Typography>
            <Typography variant="caption">
              Failed to load analyzer selection component
            </Typography>
          </Box>
        </Paper>
      }
    >
      <AnalyzerNodeContent {...props} />
    </ErrorBoundary>
  );
};

// Memoize to prevent unnecessary re-renders
export default memo(AnalyzerNode);
