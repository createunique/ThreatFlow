/**
 * ValidationPanel Component
 * Provides comprehensive workflow validation with detailed error reporting
 */

import React, { useState } from 'react';
import {
  Box,
  Button,
  Alert,
  AlertTitle,
  Typography,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Chip,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  CircularProgress,
  Badge,
} from '@mui/material';
import {
  ExpandMore,
  Error as ErrorIcon,
  Warning,
  Info,
  CheckCircle,
  BugReport,
} from '@mui/icons-material';
import {
  validateWorkflow,
  WorkflowValidationResponse,
  WorkflowValidationNode,
  WorkflowValidationEdge,
} from '../../services/schemaApi';

interface ValidationPanelProps {
  nodes: WorkflowValidationNode[];
  edges: WorkflowValidationEdge[];
  onValidationComplete?: (isValid: boolean) => void;
}

export const ValidationPanel: React.FC<ValidationPanelProps> = ({
  nodes,
  edges,
  onValidationComplete,
}) => {
  const [validation, setValidation] = useState<WorkflowValidationResponse | null>(null);
  const [validating, setValidating] = useState(false);

  const handleValidate = async () => {
    setValidating(true);
    
    try {
      const response = await validateWorkflow(nodes, edges);
      setValidation(response);
      onValidationComplete?.(response.is_valid);
    } catch (error) {
      console.error('Failed to validate workflow:', error);
      setValidation(null);
      onValidationComplete?.(false);
    } finally {
      setValidating(false);
    }
  };

  const getSeverityIcon = (severity: 'error' | 'warning' | 'info') => {
    switch (severity) {
      case 'error':
        return <ErrorIcon color="error" fontSize="small" />;
      case 'warning':
        return <Warning color="warning" fontSize="small" />;
      case 'info':
        return <Info color="info" fontSize="small" />;
    }
  };

  // Group issues by severity
  const groupedIssues = validation?.issues.reduce((acc, issue) => {
    if (!acc[issue.severity]) {
      acc[issue.severity] = [];
    }
    acc[issue.severity].push(issue);
    return acc;
  }, {} as Record<string, typeof validation.issues>);

  return (
    <Box sx={{ width: '100%' }}>
      {/* Validation Button */}
      <Box sx={{ mb: 2, display: 'flex', alignItems: 'center', gap: 2 }}>
        <Button
          variant="contained"
          color="primary"
          startIcon={validating ? <CircularProgress size={16} /> : <BugReport />}
          onClick={handleValidate}
          disabled={validating || nodes.length === 0}
          fullWidth
        >
          {validating ? 'Validating Workflow...' : 'Validate Workflow'}
        </Button>
      </Box>

      {/* Validation Results */}
      {validation && !validating && (
        <Box>
          {/* Summary Alert */}
          <Alert
            severity={validation.is_valid ? 'success' : validation.errors_count > 0 ? 'error' : 'warning'}
            icon={validation.is_valid ? <CheckCircle /> : <ErrorIcon />}
            sx={{ mb: 2 }}
          >
            <AlertTitle>
              {validation.is_valid ? 'Workflow is Valid ✓' : 'Workflow Has Issues'}
            </AlertTitle>
            <Typography variant="body2">{validation.summary}</Typography>
            
            <Box sx={{ display: 'flex', gap: 1, mt: 1 }}>
              {validation.errors_count > 0 && (
                <Chip
                  label={`${validation.errors_count} Error${validation.errors_count !== 1 ? 's' : ''}`}
                  color="error"
                  size="small"
                />
              )}
              {validation.warnings_count > 0 && (
                <Chip
                  label={`${validation.warnings_count} Warning${validation.warnings_count !== 1 ? 's' : ''}`}
                  color="warning"
                  size="small"
                />
              )}
              {validation.info_count > 0 && (
                <Chip
                  label={`${validation.info_count} Info`}
                  color="info"
                  size="small"
                />
              )}
            </Box>
          </Alert>

          {/* Issues by Severity */}
          {validation.issues.length > 0 && (
            <Box>
              {/* Errors */}
              {groupedIssues?.error && groupedIssues.error.length > 0 && (
                <Accordion
                  defaultExpanded
                  sx={{
                    mb: 1,
                    border: '1px solid',
                    borderColor: 'error.main',
                    '&:before': { display: 'none' },
                  }}
                >
                  <AccordionSummary expandIcon={<ExpandMore />}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <Badge badgeContent={groupedIssues.error.length} color="error">
                        <ErrorIcon color="error" />
                      </Badge>
                      <Typography variant="subtitle2" fontWeight="bold">
                        Errors (Must Fix)
                      </Typography>
                    </Box>
                  </AccordionSummary>
                  <AccordionDetails>
                    <List dense>
                      {groupedIssues.error.map((issue, idx) => (
                        <ListItem key={idx} sx={{ flexDirection: 'column', alignItems: 'flex-start' }}>
                          <Box sx={{ display: 'flex', alignItems: 'flex-start', width: '100%' }}>
                            <ListItemIcon sx={{ minWidth: 36 }}>
                              {getSeverityIcon(issue.severity)}
                            </ListItemIcon>
                            <ListItemText
                              primary={
                                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                  <Typography variant="body2">{issue.message}</Typography>
                                  {issue.node_id && (
                                    <Chip
                                      label={issue.node_id}
                                      size="small"
                                      variant="outlined"
                                      sx={{ height: 18, fontSize: '0.65rem' }}
                                    />
                                  )}
                                </Box>
                              }
                              secondary={
                                <Typography variant="caption" color="text.secondary">
                                  Category: {issue.category}
                                </Typography>
                              }
                            />
                          </Box>
                          {issue.suggestions.length > 0 && (
                            <Box sx={{ ml: 5, mt: 1, pl: 2, borderLeft: '2px solid #e0e0e0' }}>
                              <Typography variant="caption" fontWeight="bold" color="primary">
                                Suggestions:
                              </Typography>
                              <ul style={{ margin: '4px 0', paddingLeft: 20 }}>
                                {issue.suggestions.map((suggestion, sidx) => (
                                  <li key={sidx}>
                                    <Typography variant="caption">{suggestion}</Typography>
                                  </li>
                                ))}
                              </ul>
                            </Box>
                          )}
                        </ListItem>
                      ))}
                    </List>
                  </AccordionDetails>
                </Accordion>
              )}

              {/* Warnings */}
              {groupedIssues?.warning && groupedIssues.warning.length > 0 && (
                <Accordion
                  sx={{
                    mb: 1,
                    border: '1px solid',
                    borderColor: 'warning.main',
                    '&:before': { display: 'none' },
                  }}
                >
                  <AccordionSummary expandIcon={<ExpandMore />}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <Badge badgeContent={groupedIssues.warning.length} color="warning">
                        <Warning color="warning" />
                      </Badge>
                      <Typography variant="subtitle2" fontWeight="bold">
                        Warnings (Recommended to Fix)
                      </Typography>
                    </Box>
                  </AccordionSummary>
                  <AccordionDetails>
                    <List dense>
                      {groupedIssues.warning.map((issue, idx) => (
                        <ListItem key={idx} sx={{ flexDirection: 'column', alignItems: 'flex-start' }}>
                          <Box sx={{ display: 'flex', alignItems: 'flex-start', width: '100%' }}>
                            <ListItemIcon sx={{ minWidth: 36 }}>
                              {getSeverityIcon(issue.severity)}
                            </ListItemIcon>
                            <ListItemText
                              primary={
                                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                  <Typography variant="body2">{issue.message}</Typography>
                                  {issue.node_id && (
                                    <Chip
                                      label={issue.node_id}
                                      size="small"
                                      variant="outlined"
                                      sx={{ height: 18, fontSize: '0.65rem' }}
                                    />
                                  )}
                                </Box>
                              }
                              secondary={
                                <Typography variant="caption" color="text.secondary">
                                  Category: {issue.category}
                                </Typography>
                              }
                            />
                          </Box>
                          {issue.suggestions.length > 0 && (
                            <Box sx={{ ml: 5, mt: 1, pl: 2, borderLeft: '2px solid #e0e0e0' }}>
                              <Typography variant="caption" fontWeight="bold" color="primary">
                                Suggestions:
                              </Typography>
                              <ul style={{ margin: '4px 0', paddingLeft: 20 }}>
                                {issue.suggestions.map((suggestion, sidx) => (
                                  <li key={sidx}>
                                    <Typography variant="caption">{suggestion}</Typography>
                                  </li>
                                ))}
                              </ul>
                            </Box>
                          )}
                        </ListItem>
                      ))}
                    </List>
                  </AccordionDetails>
                </Accordion>
              )}

              {/* Info */}
              {groupedIssues?.info && groupedIssues.info.length > 0 && (
                <Accordion
                  sx={{
                    border: '1px solid',
                    borderColor: 'info.main',
                    '&:before': { display: 'none' },
                  }}
                >
                  <AccordionSummary expandIcon={<ExpandMore />}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <Badge badgeContent={groupedIssues.info.length} color="info">
                        <Info color="info" />
                      </Badge>
                      <Typography variant="subtitle2" fontWeight="bold">
                        Information
                      </Typography>
                    </Box>
                  </AccordionSummary>
                  <AccordionDetails>
                    <List dense>
                      {groupedIssues.info.map((issue, idx) => (
                        <ListItem key={idx}>
                          <ListItemIcon sx={{ minWidth: 36 }}>
                            {getSeverityIcon(issue.severity)}
                          </ListItemIcon>
                          <ListItemText
                            primary={issue.message}
                            secondary={`Category: ${issue.category}`}
                          />
                        </ListItem>
                      ))}
                    </List>
                  </AccordionDetails>
                </Accordion>
              )}
            </Box>
          )}
        </Box>
      )}

      {/* Empty State */}
      {!validation && !validating && nodes.length === 0 && (
        <Alert severity="info">
          <AlertTitle>No Workflow to Validate</AlertTitle>
          <Typography variant="body2">
            Add nodes and edges to your workflow, then click "Validate Workflow" to check for issues.
          </Typography>
        </Alert>
      )}
    </Box>
  );
};
