/**
 * Node Palette - Drag-and-drop sidebar
 * Users drag nodes from here onto the canvas
 */

import React from 'react';
import { Box, Paper, Typography, Divider } from '@mui/material';
import { Upload, Shield, FileText } from 'lucide-react';

interface NodePaletteItem {
  type: string;
  label: string;
  icon: React.ReactNode;
  color: string;
  description: string;
}

const nodeItems: NodePaletteItem[] = [
  {
    type: 'file',
    label: 'File Upload',
    icon: <Upload size={24} />,
    color: '#2196f3',
    description: 'Upload file for analysis',
  },
  {
    type: 'analyzer',
    label: 'Analyzer',
    icon: <Shield size={24} />,
    color: '#4caf50',
    description: 'Select IntelOwl analyzer',
  },
  {
    type: 'result',
    label: 'Results',
    icon: <FileText size={24} />,
    color: '#9c27b0',
    description: 'Display analysis results',
  },
];

const NodePalette: React.FC = () => {
  const onDragStart = (event: React.DragEvent, nodeType: string) => {
    event.dataTransfer.setData('application/reactflow', nodeType);
    event.dataTransfer.effectAllowed = 'move';
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
      <Typography variant="h6" gutterBottom>
        Node Palette
      </Typography>
      <Typography variant="caption" color="text.secondary" paragraph>
        Drag nodes onto the canvas to build your workflow
      </Typography>

      <Divider sx={{ mb: 2 }} />

      {/* Node Items */}
      {nodeItems.map((item) => (
        <Paper
          key={item.type}
          draggable
          onDragStart={(e) => onDragStart(e, item.type)}
          elevation={1}
          sx={{
            padding: 2,
            marginBottom: 2,
            cursor: 'grab',
            border: `2px solid ${item.color}`,
            borderRadius: 2,
            '&:hover': {
              boxShadow: 3,
              backgroundColor: '#fff',
            },
            '&:active': {
              cursor: 'grabbing',
            },
          }}
        >
          <Box display="flex" alignItems="center" gap={1.5} mb={1}>
            <Box sx={{ color: item.color }}>{item.icon}</Box>
            <Typography variant="subtitle2" fontWeight="bold">
              {item.label}
            </Typography>
          </Box>
          <Typography variant="caption" color="text.secondary">
            {item.description}
          </Typography>
        </Paper>
      ))}

      {/* Instructions */}
      <Box mt={4} p={2} sx={{ backgroundColor: '#e3f2fd', borderRadius: 1 }}>
        <Typography variant="caption" fontWeight="bold" display="block" mb={1}>
          How to use:
        </Typography>
        <Typography variant="caption" component="div">
          1. Drag <strong>File Upload</strong> node first
          <br />
          2. Drag <strong>Analyzer</strong> nodes
          <br />
          3. Connect nodes by dragging handles
          <br />
          4. Click <strong>Execute</strong> to run
        </Typography>
      </Box>
    </Paper>
  );
};

export default NodePalette;
