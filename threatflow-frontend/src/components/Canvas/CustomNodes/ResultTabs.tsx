import React, { useState } from 'react';
import {
  Box,
  Typography,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Chip,
  Button,
} from '@mui/material';
import {
  CheckCircle2,
  XCircle,
  FileText,
  Shield,
  Bug,
  Code,
} from 'lucide-react';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import { RawJsonModal } from '../../../components/Canvas/CustomNodes/RawJsonModal';

interface AnalyzerReport {
  name: string;
  status: string;
  report: any;
  errors?: string[];
  start_time?: string;
  end_time?: string;
}

interface AnalysisResults {
  analyzer_reports: AnalyzerReport[];
  [key: string]: any;
}

interface ResultTabsProps {
  results: AnalysisResults | null;
}

export const ResultTabs: React.FC<ResultTabsProps> = ({ results }) => {
  const [expandedPanel, setExpandedPanel] = useState<string | false>(false);
  const [jsonModalOpen, setJsonModalOpen] = useState(false);
  const [selectedReport, setSelectedReport] = useState<AnalyzerReport | null>(null);

  const handleAccordionChange = (panel: string) => (event: React.SyntheticEvent, isExpanded: boolean) => {
    setExpandedPanel(isExpanded ? panel : false);
  };

  const handleViewRawJson = (report: AnalyzerReport) => {
    setSelectedReport(report);
    setJsonModalOpen(true);
  };

  const handleCloseJsonModal = () => {
    setJsonModalOpen(false);
    setSelectedReport(null);
  };

  const renderAnalyzerIcon = (analyzerName: string) => {
    switch (analyzerName) {
      case 'File_Info':
        return <FileText size={16} />;
      case 'ClamAV':
        return <Shield size={16} />;
      case 'VirusTotal_v3_Get_File':
        return <Bug size={16} />;
      default:
        return <Code size={16} />;
    }
  };

  const renderAnalyzerSummary = (report: AnalyzerReport) => {
    try {
      switch (report.name) {
        case 'File_Info':
          const fileInfo = report.report;
          return (
            <Box>
              <Typography variant="caption">
                {fileInfo?.magic || 'Unknown type'} • {fileInfo?.size || 'Unknown'} bytes
              </Typography>
            </Box>
          );

        case 'ClamAV':
          const detections = report.report?.detections || [];
          return (
            <Box>
              {detections.length > 0 ? (
                <Typography variant="caption" color="error.main">
                  🚨 {detections.length} threat(s) detected
                </Typography>
              ) : (
                <Typography variant="caption" color="success.main">
                   No malware detected
                </Typography>
              )}
            </Box>
          );

        case 'VirusTotal_v3_Get_File':
          const vtData = report.report?.data;
          if (vtData) {
            const positives = vtData.positives || 0;
            const total = vtData.total || 0;
            return (
              <Box>
                <Typography variant="caption">
                  Detection ratio: {positives}/{total}
                  {positives > 0 && <span style={{ color: '#f44336', fontWeight: 'bold' }}> 🚨</span>}
                </Typography>
              </Box>
            );
          }
          return (
            <Typography variant="caption" color="text.secondary">
              No data available
            </Typography>
          );

        default:
          return (
            <Typography variant="caption" color="text.secondary">
              Analysis completed
            </Typography>
          );
      }
    } catch (error) {
      return (
        <Typography variant="caption" color="error.main">
          Error displaying summary
        </Typography>
      );
    }
  };

  const renderAnalyzerDetails = (report: AnalyzerReport) => {
    try {
      switch (report.name) {
        case 'File_Info':
          const fileInfo = report.report;
          return (
            <Box component="dl" sx={{ m: 0 }}>
              <Box display="flex" justifyContent="space-between" mb={0.5}>
                <Typography variant="caption" component="dt" sx={{ fontWeight: 'bold', minWidth: 60 }}>Type:</Typography>
                <Typography variant="caption" component="dd">{fileInfo?.magic || 'Unknown'}</Typography>
              </Box>
              <Box display="flex" justifyContent="space-between" mb={0.5}>
                <Typography variant="caption" component="dt" sx={{ fontWeight: 'bold', minWidth: 60 }}>Size:</Typography>
                <Typography variant="caption" component="dd">{fileInfo?.size || 'Unknown'} bytes</Typography>
              </Box>
              <Box display="flex" justifyContent="space-between" mb={0.5}>
                <Typography variant="caption" component="dt" sx={{ fontWeight: 'bold', minWidth: 60 }}>MD5:</Typography>
                <Typography variant="caption" component="dd" sx={{ fontFamily: 'monospace' }}>{fileInfo?.md5 || 'Unknown'}</Typography>
              </Box>
              <Box display="flex" justifyContent="space-between" mb={0.5}>
                <Typography variant="caption" component="dt" sx={{ fontWeight: 'bold', minWidth: 60 }}>SHA1:</Typography>
                <Typography variant="caption" component="dd" sx={{ fontFamily: 'monospace' }}>{fileInfo?.sha1 || 'Unknown'}</Typography>
              </Box>
              <Box display="flex" justifyContent="space-between" mb={0.5}>
                <Typography variant="caption" component="dt" sx={{ fontWeight: 'bold', minWidth: 60 }}>SHA256:</Typography>
                <Typography variant="caption" component="dd" sx={{ fontFamily: 'monospace' }}>{fileInfo?.sha256 || 'Unknown'}</Typography>
              </Box>
            </Box>
          );

        case 'ClamAV':
          const detections = report.report?.detections || [];
          return (
            <Box>
              {detections.length > 0 ? (
                <Box>
                  <Typography variant="caption" color="error.main" sx={{ fontWeight: 'bold', mb: 1 }}>
                    🚨 {detections.length} threat(s) detected:
                  </Typography>
                  {detections.map((detection: string, idx: number) => (
                    <Typography key={idx} variant="caption" color="error.main" display="block" sx={{ ml: 1 }}>
                      • {detection}
                    </Typography>
                  ))}
                </Box>
              ) : (
                <Typography variant="caption" color="success.main">
                   No malware detected
                </Typography>
              )}
            </Box>
          );

        case 'VirusTotal_v3_Get_File':
          const vtData = report.report?.data;
          if (vtData) {
            const positives = vtData.positives || 0;
            const total = vtData.total || 0;
            return (
              <Box>
                <Box display="flex" justifyContent="space-between" mb={0.5}>
                  <Typography variant="caption" sx={{ fontWeight: 'bold' }}>Detection Ratio:</Typography>
                  <Typography variant="caption">{positives}/{total}</Typography>
                </Box>
                <Box display="flex" justifyContent="space-between" mb={0.5}>
                  <Typography variant="caption" sx={{ fontWeight: 'bold' }}>Scan Date:</Typography>
                  <Typography variant="caption">{vtData.scan_date || 'Unknown'}</Typography>
                </Box>
                {positives === 0 ? (
                  <Typography variant="caption" color="success.main">
                     File appears clean
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
              {JSON.stringify(report.report, null, 2)}
            </Typography>
          );
      }
    } catch (error) {
      console.error('Error rendering analyzer details:', error);
      return (
        <Typography variant="caption" color="error.main">
          Error displaying details for {report.name}
        </Typography>
      );
    }
  };

  if (!results || !results.analyzer_reports) {
    return (
      <Typography variant="caption" color="text.secondary">
        No analysis results available
      </Typography>
    );
  }

  return (
    <Box>
      {results.analyzer_reports.map((report: AnalyzerReport, index: number) => (
        <Accordion
          key={index}
          expanded={expandedPanel === `panel-${index}`}
          onChange={handleAccordionChange(`panel-${index}`)}
          sx={{
            mb: index < results.analyzer_reports.length - 1 ? 1 : 0,
            '&:before': { display: 'none' },
            boxShadow: 'none',
            border: '1px solid #e0e0e0',
            borderRadius: '4px !important',
            '&:first-of-type': { borderTopLeftRadius: '4px !important', borderTopRightRadius: '4px !important' },
            '&:last-of-type': { borderBottomLeftRadius: '4px !important', borderBottomRightRadius: '4px !important' },
          }}
        >
          <AccordionSummary
            expandIcon={<ExpandMoreIcon />}
            sx={{
              minHeight: 48,
              '& .MuiAccordionSummary-content': { alignItems: 'center', gap: 1 },
              '& .MuiAccordionSummary-expandIconWrapper': { order: 1 },
            }}
          >
            <Box display="flex" alignItems="center" gap={1} flex={1}>
              {report.status === 'SUCCESS' ? (
                <CheckCircle2 size={16} color="#4caf50" />
              ) : (
                <XCircle size={16} color="#f44336" />
              )}
              <Box display="flex" alignItems="center" gap={1}>
                {renderAnalyzerIcon(report.name)}
                <Typography variant="subtitle2" fontWeight="bold">
                  {report.name}
                </Typography>
              </Box>
              <Chip
                label={report.status}
                size="small"
                color={report.status === 'SUCCESS' ? 'success' : 'error'}
                variant="outlined"
              />
            </Box>
            <Box sx={{ mr: 2 }}>
              {report.status === 'SUCCESS' && renderAnalyzerSummary(report)}
            </Box>
          </AccordionSummary>
          <AccordionDetails sx={{ pt: 0 }}>
            <Box>
              {report.status === 'SUCCESS' && report.report && (
                <Box mb={2}>
                  {renderAnalyzerDetails(report)}
                </Box>
              )}

              {report.errors && report.errors.length > 0 && (
                <Box mb={2}>
                  <Typography variant="caption" color="error.main" sx={{ fontWeight: 'bold' }}>
                    Errors:
                  </Typography>
                  {report.errors.map((error: string, idx: number) => (
                    <Typography key={idx} variant="caption" color="error.main" display="block" sx={{ ml: 1 }}>
                      • {error}
                    </Typography>
                  ))}
                </Box>
              )}

              <Box display="flex" gap={1} justifyContent="flex-end">
                <Button
                  size="small"
                  variant="outlined"
                  startIcon={<Code size={14} />}
                  onClick={() => handleViewRawJson(report)}
                  sx={{ fontSize: '0.7rem' }}
                >
                  View Raw JSON
                </Button>
              </Box>
            </Box>
          </AccordionDetails>
        </Accordion>
      ))}

      <RawJsonModal
        open={jsonModalOpen}
        onClose={handleCloseJsonModal}
        report={selectedReport}
      />
    </Box>
  );
};