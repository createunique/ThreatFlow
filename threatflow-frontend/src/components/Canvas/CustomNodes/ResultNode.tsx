/**
 * Result Display Node
 * Shows analysis results and job status
 */

import React, { FC } from 'react';
import { Handle, Position, NodeProps } from 'reactflow';
import { CheckCircle2, XCircle, Loader2, AlertTriangle, FileText, Shield, Bug } from 'lucide-react';
import { Box, Typography, Paper, Chip, Divider } from '@mui/material';
import { ResultNodeData } from '../../../types/workflow';

const ResultNode: FC<NodeProps<ResultNodeData>> = ({ data, selected }) => {
  const renderAnalysisResults = (results: any) => {
    if (!results || !results.analyzer_reports) {
      return (
        <Typography variant="caption" color="text.secondary">
          No analysis results available
        </Typography>
      );
    }

    return (
      <Box>
        {results.analyzer_reports.map((report: any, index: number) => (
          <Box key={index} mb={index < results.analyzer_reports.length - 1 ? 2 : 0}>
            <Box display="flex" alignItems="center" gap={1} mb={1}>
              {report.status === 'SUCCESS' ? (
                <CheckCircle2 size={16} color="#4caf50" />
              ) : (
                <XCircle size={16} color="#f44336" />
              )}
              <Typography variant="subtitle2" fontWeight="bold">
                {report.name}
              </Typography>
              <Chip
                label={report.status}
                size="small"
                color={report.status === 'SUCCESS' ? 'success' : 'error'}
                variant="outlined"
              />
            </Box>

            {report.status === 'SUCCESS' && report.report && (
              <Box ml={2}>
                {renderAnalyzerSpecificResults(report.name, report.report)}
              </Box>
            )}

            {index < results.analyzer_reports.length - 1 && <Divider sx={{ my: 1 }} />}
          </Box>
        ))}
      </Box>
    );
  };

  const renderAnalyzerSpecificResults = (analyzerName: string, report: any) => {
    switch (analyzerName) {
      case 'File_Info':
        return (
          <Box>
            <Box display="flex" alignItems="center" gap={1} mb={1}>
              <FileText size={14} />
              <Typography variant="caption" fontWeight="bold">File Information</Typography>
            </Box>
            <Box component="dl" sx={{ m: 0 }}>
              <Box display="flex" justifyContent="space-between" mb={0.5}>
                <Typography variant="caption" component="dt" sx={{ fontWeight: 'bold', minWidth: 60 }}>Type:</Typography>
                <Typography variant="caption" component="dd">{report.magic || 'Unknown'}</Typography>
              </Box>
              <Box display="flex" justifyContent="space-between" mb={0.5}>
                <Typography variant="caption" component="dt" sx={{ fontWeight: 'bold', minWidth: 60 }}>Size:</Typography>
                <Typography variant="caption" component="dd">{report.size || 'Unknown'} bytes</Typography>
              </Box>
              <Box display="flex" justifyContent="space-between" mb={0.5}>
                <Typography variant="caption" component="dt" sx={{ fontWeight: 'bold', minWidth: 60 }}>MD5:</Typography>
                <Typography variant="caption" component="dd" sx={{ fontFamily: 'monospace' }}>{report.md5 || 'Unknown'}</Typography>
              </Box>
            </Box>
          </Box>
        );

      case 'ClamAV':
        const detections = report.detections || [];
        return (
          <Box>
            <Box display="flex" alignItems="center" gap={1} mb={1}>
              <Shield size={14} />
              <Typography variant="caption" fontWeight="bold">Antivirus Scan</Typography>
            </Box>
            {detections.length > 0 ? (
              <Box>
                <Typography variant="caption" color="error.main" sx={{ fontWeight: 'bold' }}>
                  🚨 {detections.length} threat(s) detected:
                </Typography>
                {detections.slice(0, 3).map((detection: string, idx: number) => (
                  <Typography key={idx} variant="caption" color="error.main" display="block" sx={{ ml: 1 }}>
                    • {detection}
                  </Typography>
                ))}
              </Box>
            ) : (
              <Typography variant="caption" color="success.main">
                ✅ No malware detected
              </Typography>
            )}
          </Box>
        );

      case 'VirusTotal_v3_Get_File':
        const vtData = report.data;
        if (vtData) {
          const positives = vtData.positives || 0;
          const total = vtData.total || 0;
          return (
            <Box>
              <Box display="flex" alignItems="center" gap={1} mb={1}>
                <Bug size={14} />
                <Typography variant="caption" fontWeight="bold">VirusTotal Analysis</Typography>
              </Box>
              <Box display="flex" justifyContent="space-between" mb={0.5}>
                <Typography variant="caption" sx={{ fontWeight: 'bold' }}>Detection Ratio:</Typography>
                <Typography variant="caption">
                  {positives}/{total} 
                  {positives > 0 && <span style={{ color: '#f44336', fontWeight: 'bold' }}> 🚨</span>}
                </Typography>
              </Box>
              {positives === 0 ? (
                <Typography variant="caption" color="success.main">
                  ✅ File appears clean
                </Typography>
              ) : (
                <Typography variant="caption" color="error.main">
                  🚨 Potentially malicious file
                </Typography>
              )}
            </Box>
          );
        }
        return (
          <Typography variant="caption" color="text.secondary">
            No VirusTotal data available
          </Typography>
        );

      default:
        return (
          <Typography variant="caption" component="pre" sx={{ whiteSpace: 'pre-wrap', fontSize: '0.7rem' }}>
            {JSON.stringify(report, null, 2)}
          </Typography>
        );
    }
  };
  const getStatusIcon = () => {
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
  };

  const getStatusColor = () => {
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
      />

      {/* Results */}
      {data.results && (
        <Box
          sx={{
            backgroundColor: '#f5f5f5',
            padding: 1.5,
            borderRadius: 1,
            maxHeight: 300,
            overflow: 'auto',
          }}
        >
          {renderAnalysisResults(data.results)}
        </Box>
      )}

      {/* Error */}
      {data.error && (
        <Box display="flex" alignItems="center" gap={1} color="error.main" mt={1}>
          <XCircle size={16} />
          <Typography variant="caption">{data.error}</Typography>
        </Box>
      )}
    </Paper>
  );
};

export default ResultNode;
