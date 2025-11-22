import React, { FC, useState, useEffect, memo } from 'react';
import { Handle, Position, NodeProps, useReactFlow } from 'reactflow';
import { Shield, AlertCircle } from 'lucide-react';
import {
  Box,
  Typography,
  Paper,
  Select,
  MenuItem,
  FormControl,
  CircularProgress,
  SelectChangeEvent,
} from '@mui/material';
import { useWorkflowState } from '../../../hooks/useWorkflowState';
import { AnalyzerNodeData, AnalyzerInfo } from '../../../types/workflow';
import { api } from '../../../services/api';

// Singleton to prevent duplicate API calls
let cachedAnalyzers: AnalyzerInfo[] | null = null;
let analyzersFetchPromise: Promise<AnalyzerInfo[]> | null = null;

const fetchAnalyzersOnce = async (): Promise<AnalyzerInfo[]> => {
  if (cachedAnalyzers) {
    return cachedAnalyzers;
  }
  
  if (!analyzersFetchPromise) {
    analyzersFetchPromise = api.getAnalyzers('file').then(data => {
      cachedAnalyzers = data;
      analyzersFetchPromise = null;
      return data;
    });
  }
  
  return analyzersFetchPromise;
};

const AnalyzerNode: FC<NodeProps<AnalyzerNodeData>> = ({ id, data, selected }) => {
  const [analyzers, setAnalyzers] = useState<AnalyzerInfo[]>(cachedAnalyzers || []);
  const [loading, setLoading] = useState(!cachedAnalyzers);
  const [error, setError] = useState<string | null>(null);

  const { setNodes } = useReactFlow();
  const updateNode = useWorkflowState((state) => state.updateNode);

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

  const handleAnalyzerChange = (event: SelectChangeEvent<string>) => {
    const analyzerName = event.target.value;
    const analyzer = analyzers.find((a) => a.name === analyzerName);

    if (analyzer) {
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
    }
  };

  return (
    <Paper
      elevation={selected ? 8 : 2}
      sx={{
        padding: 2,
        minWidth: 280,
        maxWidth: 300,
        border: selected ? '2px solid #4caf50' : '1px solid #ccc',
        borderRadius: 2,
        backgroundColor: '#fff',
        position: 'relative',
      }}
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
      </Box>

      {/* Analyzer Selection */}
      {loading ? (
        <Box display="flex" justifyContent="center" py={2}>
          <CircularProgress size={24} />
        </Box>
      ) : error ? (
        <Box display="flex" alignItems="center" gap={1} color="error.main">
          <AlertCircle size={16} />
          <Typography variant="caption">{error}</Typography>
        </Box>
      ) : (
        <FormControl fullWidth size="small">
          <Select
            value={data.analyzer || ''}
            onChange={handleAnalyzerChange}
            displayEmpty
            className="nodrag"
            sx={{ 
              backgroundColor: '#fafafa',
              '& .MuiSelect-select': {
                py: 1,
              }
            }}
            MenuProps={{
              PaperProps: {
                style: {
                  maxHeight: 300,
                },
              },
            }}
          >
            <MenuItem value="" disabled>
              <em>Select Analyzer...</em>
            </MenuItem>
            {analyzers.map((analyzer) => (
              <MenuItem key={analyzer.name} value={analyzer.name}>
                <Box>
                  <Typography variant="body2">{analyzer.name}</Typography>
                  <Typography variant="caption" color="text.secondary" noWrap>
                    {analyzer.description.substring(0, 50)}
                    {analyzer.description.length > 50 ? '...' : ''}
                  </Typography>
                </Box>
              </MenuItem>
            ))}
          </Select>
        </FormControl>
      )}

      {/* Selected Analyzer Info */}
      {data.analyzer && (
        <Box mt={2} p={1.5} sx={{ backgroundColor: '#f5f5f5', borderRadius: 1 }}>
          <Typography variant="caption" fontWeight="bold" display="block" mb={0.5}>
            {data.analyzer}
          </Typography>
          <Typography variant="caption" color="text.secondary" display="block">
            {data.description || 'No description available'}
          </Typography>
        </Box>
      )}
    </Paper>
  );
};

// Memoize to prevent unnecessary re-renders
export default memo(AnalyzerNode);
