import React, { useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Box,
  Typography,
  IconButton,
  Tooltip,
} from '@mui/material';
import {
  Download,
  Copy,
  X,
} from 'lucide-react';

interface AnalyzerReport {
  name: string;
  status: string;
  report: any;
  errors?: string[];
  start_time?: string;
  end_time?: string;
}

interface RawJsonModalProps {
  open: boolean;
  onClose: () => void;
  report: AnalyzerReport | null;
}

export const RawJsonModal: React.FC<RawJsonModalProps> = ({ open, onClose, report }) => {
  const [copySuccess, setCopySuccess] = useState(false);

  const handleCopyToClipboard = async () => {
    if (!report) return;

    try {
      await navigator.clipboard.writeText(JSON.stringify(report, null, 2));
      setCopySuccess(true);
      setTimeout(() => setCopySuccess(false), 2000);
    } catch (error) {
      console.error('Failed to copy to clipboard:', error);
    }
  };

  const handleDownloadJson = () => {
    if (!report) return;

    const dataStr = JSON.stringify(report, null, 2);
    const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr);

    const exportFileDefaultName = `${report.name}_report.json`;

    const linkElement = document.createElement('a');
    linkElement.setAttribute('href', dataUri);
    linkElement.setAttribute('download', exportFileDefaultName);
    linkElement.click();
  };

  if (!report) return null;

  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="md"
      fullWidth
      aria-labelledby="raw-json-dialog-title"
      aria-describedby="raw-json-dialog-description"
    >
      <DialogTitle id="raw-json-dialog-title">
        <Box display="flex" alignItems="center" justifyContent="space-between">
          <Typography variant="h6" component="div">
            Raw JSON Report: {report.name}
          </Typography>
          <Box display="flex" gap={1}>
            <Tooltip title={copySuccess ? "Copied!" : "Copy to clipboard"}>
              <IconButton
                onClick={handleCopyToClipboard}
                size="small"
                aria-label="Copy JSON to clipboard"
              >
                <Copy size={18} />
              </IconButton>
            </Tooltip>
            <Tooltip title="Download JSON">
              <IconButton
                onClick={handleDownloadJson}
                size="small"
                aria-label="Download JSON file"
              >
                <Download size={18} />
              </IconButton>
            </Tooltip>
            <IconButton
              onClick={onClose}
              size="small"
              aria-label="Close modal"
            >
              <X size={18} />
            </IconButton>
          </Box>
        </Box>
      </DialogTitle>
      <DialogContent id="raw-json-dialog-description">
        <Box
          component="pre"
          sx={{
            backgroundColor: '#f5f5f5',
            padding: 2,
            borderRadius: 1,
            fontSize: '0.8rem',
            fontFamily: 'monospace',
            whiteSpace: 'pre-wrap',
            wordBreak: 'break-word',
            maxHeight: '60vh',
            overflow: 'auto',
            margin: 0,
          }}
        >
          {JSON.stringify(report, null, 2)}
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose} variant="outlined">
          Close
        </Button>
      </DialogActions>
    </Dialog>
  );
};