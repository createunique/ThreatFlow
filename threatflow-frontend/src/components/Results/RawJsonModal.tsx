import React from 'react';
import { Dialog, DialogTitle, DialogContent, DialogActions, Button, IconButton, Box, Typography } from '@mui/material';
import { Copy, Download } from 'lucide-react';

type Props = {
  open: boolean;
  onClose: () => void;
  json: any;
  title?: string;
};

export default function RawJsonModal({ open, onClose, json, title = 'Raw JSON' }: Props) {
  const pretty = React.useMemo(() => JSON.stringify(json, null, 2), [json]);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(pretty);
    } catch (e) {
      // ignore
    }
  };

  const handleDownload = () => {
    const blob = new Blob([pretty], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${title.replace(/\s+/g, '_')}.json`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  };

  return (
    <Dialog open={open} onClose={onClose} fullWidth maxWidth="lg" aria-label="Full JSON view">
      <DialogTitle>{title}</DialogTitle>
      <DialogContent dividers>
        <Box component="pre" sx={{ whiteSpace: 'pre-wrap', fontSize: 12, lineHeight: 1.4 }}>
          {pretty}
        </Box>
      </DialogContent>
      <DialogActions>
        <IconButton onClick={handleCopy} aria-label="Copy JSON">
          <Copy size={16} />
        </IconButton>
        <IconButton onClick={handleDownload} aria-label="Download JSON">
          <Download size={16} />
        </IconButton>
        <Button onClick={onClose}>Close</Button>
      </DialogActions>
    </Dialog>
  );
}