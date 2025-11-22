/**
 * File Upload Node
 * Allows drag-drop or click to upload files for analysis
 */

import React, { FC, useCallback, useState, useRef } from 'react';
import { Handle, Position, NodeProps } from 'reactflow';
import { useDropzone } from 'react-dropzone';
import { Upload, X, Loader2, AlertCircle, CheckCircle2 } from 'lucide-react';
import { Box, Typography, Paper, IconButton, LinearProgress, Fade, Alert, Tooltip } from '@mui/material';
import ErrorBoundary from '../../ErrorBoundary';
import { useWorkflowState } from '../../../hooks/useWorkflowState';
import { useWorkflowExecution } from '../../../hooks/useWorkflowExecution';
import { FileNodeData } from '../../../types/workflow';

const FileNodeContent: FC<NodeProps<FileNodeData>> = ({ id, data, selected }) => {
  const [isProcessing, setIsProcessing] = useState(false);
  const [validationError, setValidationError] = useState<string | null>(null);
  const [announcement, setAnnouncement] = useState<string>('');
  
  const dropzoneRef = useRef<HTMLDivElement>(null);
  
  const updateNode = useWorkflowState((state) => state.updateNode);
  const setUploadedFile = useWorkflowState((state) => state.setUploadedFile);
  const deleteNode = useWorkflowState((state) => state.deleteNode);
  const { uploadProgress, loading: isExecuting } = useWorkflowExecution();

  // Screen reader announcements
  const announceToScreenReader = useCallback((message: string) => {
    setAnnouncement(message);
    // Clear announcement after screen reader has time to read it
    setTimeout(() => setAnnouncement(''), 1000);
  }, []);

  // File validation function - COMMENTED OUT to allow any file
  /*
  const validateFile = useCallback((file: File): string | null => {
    // Size validation
    const maxSize = parseInt(process.env.REACT_APP_MAX_FILE_SIZE || '104857600'); // 100MB
    if (file.size > maxSize) {
      return `File size ${(file.size / 1024 / 1024).toFixed(2)}MB exceeds maximum allowed size of ${maxSize / 1024 / 1024}MB`;
    }

    if (file.size === 0) {
      return 'File appears to be empty';
    }

    // More permissive validation - allow common file types
    const fileName = file.name.toLowerCase();
    const allowedExtensions = [
      // Documents
      '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.txt', '.csv', '.rtf',
      // Archives
      '.zip', '.rar', '.7z', '.tar', '.gz', '.bz2',
      // Executables
      '.exe', '.dll', '.msi', '.bat', '.cmd', '.com', '.scr',
      // Images
      '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.svg',
      // Other common types
      '.json', '.xml', '.html', '.htm', '.log', '.cfg', '.ini',
      // Office and productivity
      '.ppt', '.pptx', '.odt', '.ods', '.odp'
    ];

    const hasAllowedExtension = allowedExtensions.some(ext => fileName.endsWith(ext));
    if (!hasAllowedExtension) {
      return `File type not supported. Supported formats include: PDF, Office documents, archives, executables, images, and text files`;
    }

    return null; // File is valid
  }, []);
  */

  // Enhanced file drop handler with validation
  const onDrop = useCallback(
    (acceptedFiles: File[], rejectedFiles: any[]) => {
      console.log('onDrop called:', { acceptedFiles: acceptedFiles.length, rejectedFiles: rejectedFiles.length });
      
      // Handle rejected files
      if (rejectedFiles.length > 0) {
        console.log('Rejected files:', rejectedFiles);
        const rejection = rejectedFiles[0];
        let errorMessage = 'File upload failed';
        
        if (rejection.errors) {
          errorMessage = rejection.errors.map((error: any) => {
            switch (error.code) {
              case 'file-too-large':
                return `File is too large. Maximum size is ${parseInt(process.env.REACT_APP_MAX_FILE_SIZE || '104857600') / 1024 / 1024}MB`;
              case 'file-invalid-type':
                return 'File type not supported for analysis';
              default:
                return error.message;
            }
          }).join(', ');
        }
        
        setValidationError(errorMessage);
        announceToScreenReader(`File upload failed: ${errorMessage}`);
        return;
      }

      const file = acceptedFiles[0];
      if (!file) {
        console.log('No file selected');
        return;
      }

      console.log('Processing file:', file.name, file.size);

      // COMMENTED OUT: File validation - allow any file
      /*
      const validationError = validateFile(file);
      if (validationError) {
        console.log('Validation failed:', validationError);
        setValidationError(validationError);
        announceToScreenReader(`File validation failed: ${validationError}`);
        return;
      }
      */

      // Clear any previous errors
      setValidationError(null);
      
      // Update node data immediately
      updateNode(id, {
        file,
        fileName: file.name,
        fileSize: file.size,
      } as any);

      // Store file in global state
      setUploadedFile(file);
      
      announceToScreenReader(`File ${file.name} successfully uploaded and ready for analysis`);
    },
    [id, updateNode, setUploadedFile, announceToScreenReader]
  );  const { getRootProps, getInputProps, isDragActive, open } = useDropzone({
    onDrop,
    multiple: false,
    maxSize: parseInt(process.env.REACT_APP_MAX_FILE_SIZE || '104857600'), // 100MB
    accept: {
      'application/*': [],
      'text/*': [],
      'image/*': [],
    }, // Use broad accept like the old working implementation
    noClick: false, // Enable automatic click handling
    noKeyboard: false, // Enable automatic keyboard handling
    disabled: false, // Temporarily disable to test
  });

  const handleRemoveFile = useCallback(async () => {
    try {
      setIsProcessing(true);
      setValidationError(null);
      announceToScreenReader('Removing file...');

      // Simulate cleanup time
      await new Promise(resolve => setTimeout(resolve, 200));

      updateNode(id, {
        file: null,
        fileName: '',
        fileSize: 0,
      } as any);
      setUploadedFile(null);
      
      announceToScreenReader('File removed successfully');
    } catch (error) {
      console.error('Error removing file:', error);
      setValidationError('Failed to remove file');
      announceToScreenReader('Failed to remove file');
      throw error; // Let error boundary catch it
    } finally {
      setIsProcessing(false);
    }
  }, [id, updateNode, setUploadedFile, announceToScreenReader]);

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
      role="region"
      aria-label={`File upload node ${selected ? '(selected)' : ''}`}
    >
      {/* Screen reader announcements */}
      <div
        aria-live="polite"
        aria-atomic="true"
        style={{ position: 'absolute', left: '-10000px', width: '1px', height: '1px', overflow: 'hidden' }}
      >
        {announcement}
      </div>

      {/* Validation Error Alert */}
      {validationError && (
        <Alert 
          severity="error" 
          sx={{ mb: 2 }}
          icon={<AlertCircle />}
          role="alert"
          aria-live="assertive"
        >
          <Typography variant="body2">{validationError}</Typography>
        </Alert>
      )}

      {/* Processing Overlay */}
      <Fade in={isExecuting}>
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
          role="status"
          aria-label={isExecuting ? `Uploading file, ${uploadProgress}% complete` : 'Processing file'}
        >
          <Loader2 size={32} className="animate-spin" color="#2196f3" aria-hidden="true" />
          <Typography variant="caption" color="primary" sx={{ mt: 1 }}>
            {isExecuting
              ? `Uploading file... ${uploadProgress}%`
              : 'Processing file...'
            }
          </Typography>
          {isExecuting ? (
            <LinearProgress
              variant="determinate"
              value={uploadProgress}
              sx={{ width: '80%', mt: 1 }}
              aria-label={`Upload progress: ${uploadProgress}%`}
            />
          ) : (
            <LinearProgress sx={{ width: '80%', mt: 1 }} aria-label="Processing progress" />
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
            aria-label="Delete file node"
          >
            <X size={14} />
          </IconButton>
        </Tooltip>
      </Box>

      {/* Dropzone */}
      <Box
        {...getRootProps()}
        ref={dropzoneRef}
        sx={{
          border: '2px dashed',
          borderColor: isDragActive ? '#2196f3' : isExecuting ? '#4caf50' : '#ccc',
          borderRadius: 1,
          padding: 2,
          textAlign: 'center',
          cursor: isExecuting ? 'not-allowed' : 'pointer',
          backgroundColor: isDragActive ? '#e3f2fd' : isExecuting ? '#e8f5e8' : '#fafafa',
          '&:hover': {
            backgroundColor: isExecuting ? '#e8f5e8' : '#f5f5f5',
          },
          transition: 'all 0.2s ease-in-out',
          opacity: isExecuting ? 0.7 : 1,
        }}
        role="button"
        tabIndex={isExecuting ? -1 : 0}
        aria-label={data.file 
          ? `File uploaded: ${data.fileName}, size: ${(data.fileSize / 1024).toFixed(2)} KB. Press Enter or Space to replace file.`
          : 'File upload area. Click to select file, or drag and drop file here.'
        }
        aria-describedby={validationError ? "file-validation-error" : undefined}
        onKeyDown={(e) => {
          if ((e.key === 'Enter' || e.key === ' ') && !isExecuting) {
            e.preventDefault();
            open();
          }
        }}
      >
        <input {...getInputProps()} />
        {data.file ? (
          <Box>
            <CheckCircle2 size={32} color="#4caf50" aria-hidden="true" />
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
              disabled={isExecuting}
              aria-label={`Remove file ${data.fileName}`}
            >
              <X size={16} aria-hidden="true" />
            </IconButton>
          </Box>
        ) : (
          <Box>
            {isProcessing ? (
              <Loader2 size={32} className="animate-spin" color="#ff9800" aria-hidden="true" />
            ) : (
              <Upload size={32} color="#9e9e9e" aria-hidden="true" />
            )}
            <Typography variant="body2" color="text.secondary" mt={1}>
              {isExecuting
                ? `Uploading... ${uploadProgress}%`
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
