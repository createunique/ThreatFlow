/**
 * File Upload Node
 * Allows drag-drop or click to upload files for analysis
 */

import React, { FC, useCallback, useState } from 'react';
import { Handle, Position, NodeProps } from 'reactflow';
import { useDropzone } from 'react-dropzone';
import { Upload, File as FileIcon, X, Loader2 } from 'lucide-react';
import { Box, Typography, Paper, IconButton, LinearProgress, Fade } from '@mui/material';
import ErrorBoundary from '../../ErrorBoundary';
import { useWorkflowState } from '../../../hooks/useWorkflowState';
import { useWorkflowExecution } from '../../../hooks/useWorkflowExecution';
import { FileNodeData } from '../../../types/workflow';

const FileNodeContent: FC<NodeProps<FileNodeData>> = ({ id, data, selected }) => {
  const [isProcessing, setIsProcessing] = useState(false);
  const updateNode = useWorkflowState((state) => state.updateNode);
  const setUploadedFile = useWorkflowState((state) => state.setUploadedFile);
  const { uploadProgress, loading: isExecuting } = useWorkflowExecution();

  const onDrop = useCallback(
    async (acceptedFiles: File[]) => {
      try {
        const file = acceptedFiles[0];
        if (file) {
          setIsProcessing(true);
          console.log('File dropped:', file.name, file.size);

          // Simulate file processing time (in real app, this might be validation, preview generation, etc.)
          await new Promise(resolve => setTimeout(resolve, 500));

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
      } finally {
        setIsProcessing(false);
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

  const handleRemoveFile = useCallback(async () => {
    try {
      setIsProcessing(true);

      // Simulate cleanup time
      await new Promise(resolve => setTimeout(resolve, 200));

      updateNode(id, {
        file: null,
        fileName: '',
        fileSize: 0,
      } as any);
      setUploadedFile(null);
    } catch (error) {
      console.error('Error removing file:', error);
      throw error; // Let error boundary catch it
    } finally {
      setIsProcessing(false);
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
        position: 'relative',
        overflow: 'hidden',
      }}
    >
      {/* Processing Overlay */}
      <Fade in={isProcessing || isExecuting}>
        <Box
          sx={{
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: 'rgba(255, 255, 255, 0.9)',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 10,
          }}
        >
          <Loader2 size={32} className="animate-spin" color="#2196f3" />
          <Typography variant="caption" color="primary" sx={{ mt: 1 }}>
            {isExecuting
              ? `Uploading file... ${uploadProgress}%`
              : data.file
              ? 'Removing file...'
              : 'Processing file...'
            }
          </Typography>
          {isExecuting ? (
            <LinearProgress
              variant="determinate"
              value={uploadProgress}
              sx={{ width: '80%', mt: 1 }}
            />
          ) : (
            <LinearProgress sx={{ width: '80%', mt: 1 }} />
          )}
        </Box>
      </Fade>

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
          borderColor: isDragActive ? '#2196f3' : isProcessing ? '#ff9800' : isExecuting ? '#4caf50' : '#ccc',
          borderRadius: 1,
          padding: 2,
          textAlign: 'center',
          cursor: isProcessing || isExecuting ? 'not-allowed' : 'pointer',
          backgroundColor: isDragActive ? '#e3f2fd' : isProcessing ? '#fff3e0' : isExecuting ? '#e8f5e8' : '#fafafa',
          '&:hover': {
            backgroundColor: isProcessing || isExecuting ? (isProcessing ? '#fff3e0' : '#e8f5e8') : '#f5f5f5',
          },
          transition: 'all 0.2s ease-in-out',
          opacity: isProcessing || isExecuting ? 0.7 : 1,
        }}
      >
        <input {...getInputProps()} disabled={isProcessing || isExecuting} />
        {data.file ? (
          <Box>
            <FileIcon size={32} color="#4caf50" />
            <Typography variant="body2" color="success.main" mt={1}>
              ✓ {data.fileName}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              {(data.fileSize / 1024).toFixed(2)} KB
            </Typography>
            <IconButton
              size="small"
              onClick={(e) => {
                e.stopPropagation();
                handleRemoveFile();
              }}
              sx={{ mt: 1 }}
              disabled={isProcessing || isExecuting}
            >
              <X size={16} />
            </IconButton>
          </Box>
        ) : (
          <Box>
            {isProcessing ? (
              <Loader2 size={32} className="animate-spin" color="#ff9800" />
            ) : (
              <Upload size={32} color="#9e9e9e" />
            )}
            <Typography variant="body2" color="text.secondary" mt={1}>
              {isExecuting
                ? `Uploading... ${uploadProgress}%`
                : isProcessing
                ? 'Processing...'
                : isDragActive
                ? 'Drop file here...'
                : 'Click or drag file here'
              }
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
