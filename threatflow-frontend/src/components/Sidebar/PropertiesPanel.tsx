/**
 * Inspector Panel
 * Unified panel showing properties for non-result nodes and detailed results for result nodes
 * Enhanced with intelligent condition builder and real-time validation
 */

import React, { useState, useEffect, useCallback } from 'react';
import { Box, Paper, Typography, Divider, Chip, Button } from '@mui/material';
import { Info, Upload, Shield, FileText } from 'lucide-react';
import { useWorkflowState } from '../../hooks/useWorkflowState';
import { ConditionalNodeData } from '../../types/workflow';
import { ConditionBuilder } from '../ConditionBuilder/ConditionBuilder';
import { ValidationPanel } from '../Validation/ValidationPanel';
import { getAllAnalyzers } from '../../services/schemaApi';

const InspectorPanel: React.FC = () => {
  const selectedNode = useWorkflowState((state) => state.selectedNode);
  const nodes = useWorkflowState((state) => state.nodes);
  const edges = useWorkflowState((state) => state.edges);
  const [availableAnalyzers, setAvailableAnalyzers] = useState<string[]>([]);
  const [showValidation, setShowValidation] = useState(false);

  // Fetch available analyzers on mount
  useEffect(() => {
    const fetchAnalyzers = async () => {
      try {
        const response = await getAllAnalyzers();
        setAvailableAnalyzers(response.analyzers);
      } catch (error) {
        console.error('Failed to fetch analyzers:', error);
      }
    };
    fetchAnalyzers();
  }, []);

  const getNodeIcon = (type?: string) => {
    switch (type) {
      case 'file':
        return <Upload size={20} color="#2196f3" />;
      case 'analyzer':
        return <Shield size={20} color="#4caf50" />;
      case 'result':
        return <FileText size={20} color="#9c27b0" />;
      default:
        return <Info size={20} />;
    }
  };

  const getNodeTypeColor = (type?: string) => {
    switch (type) {
      case 'file':
        return 'primary';
      case 'analyzer':
        return 'success';
      case 'result':
        return 'secondary';
      default:
        return 'default';
    }
  };

  const renderNodeProperties = () => {
    if (!selectedNode) {
      return (
        <Box
          display="flex"
          flexDirection="column"
          alignItems="center"
          justifyContent="center"
          height="80%"
          color="text.secondary"
        >
          <Info size={48} strokeWidth={1.5} />
          <Typography variant="body2" mt={2} textAlign="center">
            Select a node to inspect its properties
          </Typography>
        </Box>
      );
    }

    const { type, data, id } = selectedNode;
    // Default properties view for other node types
    return (
      <Box>
        {/* Node Header */}
        <Box display="flex" alignItems="center" gap={1.5} mb={2}>
          {getNodeIcon(type)}
          <Box flex={1}>
            <Typography variant="h6" fontWeight="bold">
              {data.label || type}
            </Typography>
            <Chip
              label={type?.toUpperCase()}
              size="small"
              color={getNodeTypeColor(type) as any}
              sx={{ mt: 0.5 }}
            />
          </Box>
        </Box>

        <Divider sx={{ mb: 2 }} />

        {/* Node ID */}
        <Box mb={2}>
          <Typography variant="caption" color="text.secondary" fontWeight="bold">
            Node ID
          </Typography>
          <Typography
            variant="body2"
            sx={{
              fontFamily: 'monospace',
              fontSize: '0.85rem',
              backgroundColor: '#f5f5f5',
              padding: 0.5,
              borderRadius: 0.5,
              mt: 0.5,
            }}
          >
            {id}
          </Typography>
        </Box>

        {/* Type-specific properties */}
        {type === 'file' && (
          <>
            <Box mb={2}>
              <Typography variant="caption" color="text.secondary" fontWeight="bold">
                File Name
              </Typography>
              <Typography variant="body2" mt={0.5}>
                {(data as any).fileName || 'No file selected'}
              </Typography>
            </Box>
            {(data as any).fileSize > 0 && (
              <Box mb={2}>
                <Typography variant="caption" color="text.secondary" fontWeight="bold">
                  File Size
                </Typography>
                <Typography variant="body2" mt={0.5}>
                  {((data as any).fileSize / 1024).toFixed(2)} KB
                </Typography>
              </Box>
            )}
          </>
        )}

        {type === 'analyzer' && (
          <>
            <Box mb={2}>
              <Typography variant="caption" color="text.secondary" fontWeight="bold">
                Selected Analyzer
              </Typography>
              <Typography variant="body2" mt={0.5} fontWeight="medium">
                {(data as any).analyzer || 'Not selected'}
              </Typography>
            </Box>
            {(data as any).analyzer && (
              <>
                <Box mb={2}>
                  <Typography variant="caption" color="text.secondary" fontWeight="bold">
                    Analyzer Type
                  </Typography>
                  <Chip
                    label={(data as any).analyzerType?.toUpperCase()}
                    size="small"
                    variant="outlined"
                    sx={{ mt: 0.5 }}
                  />
                </Box>
                <Box mb={2}>
                  <Typography variant="caption" color="text.secondary" fontWeight="bold">
                    Description
                  </Typography>
                  <Typography variant="body2" mt={0.5}>
                    {(data as any).description || 'No description available'}
                  </Typography>
                </Box>
              </>
            )}
          </>
        )}

        {type === 'conditional' && (
          <ConditionalNodeConfig 
            nodeId={id} 
            data={data as ConditionalNodeData}
            availableAnalyzers={availableAnalyzers}
          />
        )}

        <Divider sx={{ my: 2 }} />

        {/* Raw Data (collapsible) */}
        <Box>
          <Typography variant="caption" color="text.secondary" fontWeight="bold" mb={1} display="block">
            Raw Data (JSON)
          </Typography>
          <Box
            sx={{
              backgroundColor: '#f5f5f5',
              padding: 1.5,
              borderRadius: 1,
              border: '1px solid #e0e0e0',
              maxHeight: 250,
              overflow: 'auto',
            }}
          >
            <Typography
              variant="caption"
              component="pre"
              sx={{
                whiteSpace: 'pre-wrap',
                fontFamily: 'monospace',
                fontSize: '0.75rem',
                margin: 0,
              }}
            >
              {JSON.stringify(data, null, 2)}
            </Typography>
          </Box>
        </Box>
      </Box>
    );
  };

  return (
    <Paper
      elevation={2}
      sx={{
        width: 280,
        height: '100%',
        padding: 2,
        overflowY: 'auto',
        backgroundColor: '#fafafa',
      }}
    >
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="h6" fontWeight="bold">
          Properties
        </Typography>
        <Button
          size="small"
          variant={showValidation ? 'contained' : 'outlined'}
          onClick={() => setShowValidation(!showValidation)}
          sx={{ fontSize: '0.7rem' }}
        >
          {showValidation ? 'Hide' : 'Validate'}
        </Button>
      </Box>

      <Divider sx={{ mb: 2 }} />

      {/* Show ValidationPanel or Node Properties */}
      {showValidation ? (
        <ValidationPanel
          nodes={nodes.map(n => ({ id: n.id, type: n.type || 'unknown', data: n.data }))}
          edges={edges.map(e => ({ id: e.id, source: e.source, target: e.target }))}
          onValidationComplete={(isValid) => console.log('Validation complete:', isValid)}
        />
      ) : (
        renderNodeProperties()
      )}
    </Paper>
  );
};

export default InspectorPanel;

// Conditional Node Configuration Component with Intelligent Builder
const ConditionalNodeConfig: React.FC<{ 
  nodeId: string; 
  data: ConditionalNodeData;
  availableAnalyzers: string[];
}> = ({ nodeId, data, availableAnalyzers }) => {
  const updateNode = useWorkflowState((state) => state.updateNode);

  const handleUpdate = useCallback((updatedData: {
    conditionType: string;
    sourceAnalyzer: string;
    fieldPath?: string;
    expectedValue?: any;
    operator?: string;
  }) => {
    updateNode(nodeId, {
      ...data,
      ...updatedData,
    });
  }, [nodeId, data, updateNode]);

  return (
    <Box>
      <ConditionBuilder
        nodeId={nodeId}
        initialData={{
          conditionType: data.conditionType || '',
          sourceAnalyzer: data.sourceAnalyzer || '',
          fieldPath: data.fieldPath,
          expectedValue: data.expectedValue,
          operator: data.operator,
        }}
        onUpdate={handleUpdate}
        availableAnalyzers={availableAnalyzers}
      />

      <Divider sx={{ my: 2 }} />

      <Box>
        <Typography variant="caption" color="text.secondary" fontWeight="bold" mb={1} display="block">
          How it works:
        </Typography>
        <Typography variant="caption" color="text.secondary" display="block">
          • TRUE output: When condition is met
        </Typography>
        <Typography variant="caption" color="text.secondary" display="block">
          • FALSE output: When condition is NOT met
        </Typography>
        <Typography variant="caption" color="text.secondary" display="block" sx={{ mt: 1 }}>
          Connect analyzers to the TRUE/FALSE outputs to create conditional workflows.
        </Typography>
      </Box>
    </Box>
  );
};
