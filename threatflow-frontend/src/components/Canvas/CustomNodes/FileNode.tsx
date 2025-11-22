/**
 * File Upload Node
 * Allows drag-drop or click to upload files for analysis
 */

import React, { FC, useCallback } from 'react';
import { Handle, Position, NodeProps } from 'reactflow';
import { useDropzone } from 'react-dropzone';
import { Upload, File as FileIcon, X } from 'lucide-react';
import { Box, Typography, Paper, IconButton } from '@mui/material';
import ErrorBoundary from '../../ErrorBoundary';
import { useWorkflowState } from '../../../hooks/useWorkflowState';
import { FileNodeData } from '../../../types/workflow';

const FileNodeContent: FC<NodeProps<FileNodeData>> = ({ id, data, selected }) => {
  const updateNode = useWorkflowState((state) => state.updateNode);
  const setUploadedFile = useWorkflowState((state) => state.setUploadedFile);

  const onDrop = useCallback(
    (acceptedFiles: File[]) => {
      try {
        const file = acceptedFiles[0];
        if (file) {
          console.log('File dropped:', file.name, file.size);

          // Update node data
          updateNode(id, {
            file,
            fileName: file.name,
            fileSize: file.size,
          } as any);

          // Store file in global state
          setUploadedFile(file);
        }
      } catch (error) {
        console.error('Error handling file drop:', error);
        throw error; // Let error boundary catch it
      }
    },
    [id, updateNode, setUploadedFile]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    multiple: false,
    maxSize: parseInt(process.env.REACT_APP_MAX_FILE_SIZE || '104857600'), // 100MB
    accept: {
      'application/*': [],
      'text/*': [],
      'image/*': [],
    },
  });

  const handleRemoveFile = useCallback(() => {
    try {
      updateNode(id, {
        file: null,
        fileName: '',
        fileSize: 0,
      } as any);
      setUploadedFile(null);
    } catch (error) {
      console.error('Error removing file:', error);
      throw error; // Let error boundary catch it
    }
  }, [id, updateNode, setUploadedFile]);

  return (
    <Paper
      elevation={selected ? 8 : 2}
      sx={{
        padding: 2,
        minWidth: 280,
        border: selected ? '2px solid #2196f3' : '1px solid #ccc',
        borderRadius: 2,
        backgroundColor: '#fff',
      }}
    >
      {/* Handle (output) */}
      <Handle
        type="source"
        position={Position.Right}
        style={{
          background: '#2196f3',
          width: 12,
          height: 12,
          border: '2px solid #fff',
        }}
      />

      {/* Header */}
      <Box display="flex" alignItems="center" gap={1} mb={2}>
        <Upload size={20} color="#2196f3" />
        <Typography variant="subtitle1" fontWeight="bold">
          File Upload
        </Typography>
      </Box>

      {/* Dropzone */}
      <Box
        {...getRootProps()}
        sx={{
          border: '2px dashed',
          borderColor: isDragActive ? '#2196f3' : '#ccc',
          borderRadius: 1,
          padding: 2,
          textAlign: 'center',
          cursor: 'pointer',
          backgroundColor: isDragActive ? '#e3f2fd' : '#fafafa',
          '&:hover': {
            backgroundColor: '#f5f5f5',
          },
        }}
      >
        <input {...getInputProps()} />
        {data.file ? (
          <Box>
            <FileIcon size={32} color="#4caf50" />
            <Typography variant="body2" color="success.main" mt={1}>
              ✓ {data.fileName}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              {(data.fileSize / 1024).toFixed(2)} KB
            </Typography>
            <IconButton size="small" onClick={handleRemoveFile} sx={{ mt: 1 }}>
              <X size={16} />
            </IconButton>
          </Box>
        ) : (
          <Box>
            <Upload size={32} color="#9e9e9e" />
            <Typography variant="body2" color="text.secondary" mt={1}>
              {isDragActive ? 'Drop file here...' : 'Click or drag file here'}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              Max 100MB
            </Typography>
          </Box>
        )}
      </Box>
    </Paper>
  );
};

const FileNode: FC<NodeProps<FileNodeData>> = (props) => {
  return (
    <ErrorBoundary
      name={`File Node (${props.id})`}
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
              File Node Error
            </Typography>
            <Typography variant="caption">
              Failed to load file upload component
            </Typography>
          </Box>
        </Paper>
      }
    >
      <FileNodeContent {...props} />
    </ErrorBoundary>
  );
};

export default FileNode;
