/**
 * Professional Analyzer Selection Modal
 * Displays 200+ analyzers with search, categorization, and filtering
 * Separates available from unavailable analyzers with container detection
 * Follows Material-UI best practices and accessibility standards
 */

import React, { FC, useState, useMemo, useCallback, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  Tabs,
  Tab,
  Box,
  Typography,
  List,
  ListItem,
  ListItemButton,
  ListItemText,
  Chip,
  CircularProgress,
  Alert,
  InputAdornment,
  Badge,
  Paper,
  Grid,
  Divider,
  Tooltip,
} from '@mui/material';
import { Search, Filter, CheckCircle, AlertCircle, Zap, Lock } from 'lucide-react';
import { AnalyzerInfo } from '../../types/workflow';

interface AnalyzerSelectionModalProps {
  open: boolean;
  analyzers: AnalyzerInfo[];
  loading: boolean;
  error: string | null;
  selectedAnalyzer: string | null;
  onSelect: (analyzer: AnalyzerInfo) => void;
  onClose: () => void;
}

// Helper: Group analyzers by type
const groupAnalyzersByType = (analyzers: AnalyzerInfo[]): Record<string, AnalyzerInfo[]> => {
  return analyzers.reduce((acc, analyzer) => {
    const type = analyzer.type || 'unknown';
    if (!acc[type]) {
      acc[type] = [];
    }
    acc[type].push(analyzer);
    return acc;
  }, {} as Record<string, AnalyzerInfo[]>);
};

// Helper: Group analyzers by category (inferred from description/name patterns)
const categorizeAnalyzers = (analyzers: AnalyzerInfo[]): Record<string, AnalyzerInfo[]> => {
  const categories: Record<string, AnalyzerInfo[]> = {
    'IP & Network': [],
    'Domain & URL': [],
    'Hash Analysis': [],
    'File Analysis': [],
    'Threat Intelligence': [],
    'Code Analysis': [],
    'Mobile Analysis': [],
    'Other': [],
  };

  analyzers.forEach((analyzer) => {
    const name = analyzer.name.toLowerCase();
    const desc = analyzer.description.toLowerCase();

    if (name.includes('ip') || desc.includes('ip address') || desc.includes('ipv4')) {
      categories['IP & Network'].push(analyzer);
    } else if (
      name.includes('domain') ||
      name.includes('url') ||
      desc.includes('domain') ||
      desc.includes('url')
    ) {
      categories['Domain & URL'].push(analyzer);
    } else if (
      name.includes('hash') ||
      name.includes('md5') ||
      name.includes('sha') ||
      desc.includes('hash')
    ) {
      categories['Hash Analysis'].push(analyzer);
    } else if (
      analyzer.type === 'file' ||
      name.includes('file') ||
      name.includes('artifact') ||
      desc.includes('file analysis')
    ) {
      categories['File Analysis'].push(analyzer);
    } else if (
      name.includes('threat') ||
      name.includes('virustotal') ||
      name.includes('abuseipdb') ||
      desc.includes('threat')
    ) {
      categories['Threat Intelligence'].push(analyzer);
    } else if (
      name.includes('decompil') ||
      name.includes('androguard') ||
      name.includes('apk') ||
      desc.includes('decompil')
    ) {
      categories['Mobile Analysis'].push(analyzer);
    } else if (
      name.includes('yara') ||
      name.includes('ssdeep') ||
      desc.includes('code analysis')
    ) {
      categories['Code Analysis'].push(analyzer);
    } else {
      categories['Other'].push(analyzer);
    }
  });

  // Remove empty categories
  return Object.fromEntries(
    Object.entries(categories).filter(([, items]) => items.length > 0)
  );
};

const AnalyzerSelectionModal: FC<AnalyzerSelectionModalProps> = ({
  open,
  analyzers,
  loading,
  error,
  selectedAnalyzer,
  onSelect,
  onClose,
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [tabIndex, setTabIndex] = useState(0);

  // Memoized categorized analyzers
  const categorizedAnalyzers = useMemo(
    () => categorizeAnalyzers(analyzers),
    [analyzers]
  );

  const categories = useMemo(() => Object.keys(categorizedAnalyzers), [categorizedAnalyzers]);

  // Filter analyzers by search term
  const filteredAnalyzers = useMemo(() => {
    if (!searchTerm.trim()) {
      return categorizedAnalyzers;
    }

    const search = searchTerm.toLowerCase();
    const filtered: Record<string, AnalyzerInfo[]> = {};

    Object.entries(categorizedAnalyzers).forEach(([category, items]) => {
      const filtered_items = items.filter(
        (analyzer) =>
          analyzer.name.toLowerCase().includes(search) ||
          analyzer.description.toLowerCase().includes(search)
      );

      if (filtered_items.length > 0) {
        filtered[category] = filtered_items;
      }
    });

    return filtered;
  }, [searchTerm, categorizedAnalyzers]);

  const filteredCategories = useMemo(() => Object.keys(filteredAnalyzers), [filteredAnalyzers]);

  // Handle tab change (category selection)
  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabIndex(Math.min(newValue, filteredCategories.length - 1));
  };

  // Reset tab when categories change
  useEffect(() => {
    setTabIndex(0);
  }, [filteredCategories]);

  const currentCategory = filteredCategories[tabIndex] || categories[0];
  const currentAnalyzers = filteredAnalyzers[currentCategory] || [];

  const handleAnalyzerClick = (analyzer: AnalyzerInfo) => {
    onSelect(analyzer);
    onClose();
  };

  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="lg"
      fullWidth
      PaperProps={{
        sx: {
          maxHeight: '90vh',
          display: 'flex',
          flexDirection: 'column',
        },
      }}
      aria-labelledby="analyzer-selection-title"
      role="presentation"
    >
      {/* Header */}
      <DialogTitle
        id="analyzer-selection-title"
        sx={{
          display: 'flex',
          alignItems: 'center',
          gap: 1,
          paddingBottom: 1,
          borderBottom: '1px solid #e0e0e0',
        }}
      >
        <Filter size={24} color="#1976d2" />
        <Typography variant="h6" sx={{ flexGrow: 1 }}>
          Select Analyzer
        </Typography>
        <Badge badgeContent={analyzers.length} color="primary" sx={{ mr: 1 }}>
          <Typography variant="caption" sx={{ px: 1, py: 0.5, backgroundColor: '#e3f2fd', borderRadius: 1 }}>
            {analyzers.length} available
          </Typography>
        </Badge>
      </DialogTitle>

      {/* Content */}
      <DialogContent
        sx={{
          display: 'flex',
          flexDirection: 'column',
          flex: 1,
          overflow: 'auto',
          padding: 2,
          gap: 2,
        }}
      >
        {/* Search Bar */}
        <TextField
          fullWidth
          variant="outlined"
          placeholder="Search analyzers by name or description..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          size="small"
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <Search size={20} color="#999" />
              </InputAdornment>
            ),
          }}
          aria-label="Search analyzers"
          sx={{
            mb: 1,
            '& .MuiOutlinedInput-root': {
              backgroundColor: '#fafafa',
            },
          }}
        />

        {/* Error State */}
        {error && (
          <Alert severity="error" onClose={() => {}}>
            {error}
          </Alert>
        )}

        {/* Loading State */}
        {loading ? (
          <Box
            display="flex"
            justifyContent="center"
            alignItems="center"
            minHeight={300}
            role="status"
            aria-label="Loading analyzers"
          >
            <CircularProgress />
          </Box>
        ) : filteredCategories.length === 0 ? (
          <Box
            display="flex"
            flexDirection="column"
            justifyContent="center"
            alignItems="center"
            minHeight={300}
            gap={1}
            role="status"
            aria-label="No analyzers found"
          >
            <AlertCircle size={48} color="#ccc" />
            <Typography color="textSecondary">No analyzers found</Typography>
            <Typography variant="caption" color="textSecondary">
              Try adjusting your search terms
            </Typography>
          </Box>
        ) : (
          <>
            {/* Category Tabs */}
            <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
              <Tabs
                value={Math.min(tabIndex, filteredCategories.length - 1)}
                onChange={handleTabChange}
                variant="scrollable"
                scrollButtons="auto"
                aria-label="Analyzer categories"
                sx={{
                  '& .MuiTab-root': {
                    textTransform: 'none',
                    fontSize: '0.95rem',
                    fontWeight: 500,
                  },
                }}
              >
                {filteredCategories.map((category) => (
                  <Tab
                    key={category}
                    label={`${category} (${filteredAnalyzers[category]?.length || 0})`}
                    id={`analyzer-tab-${category}`}
                    aria-controls={`analyzer-tabpanel-${category}`}
                  />
                ))}
              </Tabs>
            </Box>

            {/* Analyzers List */}
            <Paper
              elevation={0}
              sx={{
                flex: 1,
                overflow: 'auto',
                backgroundColor: '#f9f9f9',
                border: '1px solid #e0e0e0',
              }}
              role="region"
              aria-label={`${currentCategory} analyzers`}
            >
              <List sx={{ p: 0 }}>
                {currentAnalyzers.map((analyzer, index) => (
                  <React.Fragment key={analyzer.name}>
                    <ListItemButton
                      selected={selectedAnalyzer === analyzer.name}
                      onClick={() => handleAnalyzerClick(analyzer)}
                      disabled={!analyzer.available}
                      sx={{
                        py: 1.5,
                        px: 2,
                        opacity: analyzer.available ? 1 : 0.65,
                        '&:hover': {
                          backgroundColor: analyzer.available ? '#f0f0f0' : 'inherit',
                        },
                        '&.Mui-selected': {
                          backgroundColor: '#e8f5e9',
                          '&:hover': {
                            backgroundColor: '#e0f2e9',
                          },
                        },
                      }}
                      role="button"
                      aria-pressed={selectedAnalyzer === analyzer.name}
                      aria-label={`${analyzer.name}: ${analyzer.description}${!analyzer.available ? ` - ${analyzer.unavailable_reason}` : ''}`}
                      title={!analyzer.available ? analyzer.unavailable_reason : undefined}
                    >
                      <ListItemText
                        primary={
                          <Box display="flex" alignItems="center" gap={1}>
                            {selectedAnalyzer === analyzer.name && analyzer.available && (
                              <CheckCircle size={18} color="#4caf50" />
                            )}
                            {!analyzer.available && (
                              <Tooltip title={analyzer.unavailable_reason || 'Not available'}>
                                <Lock size={18} color="#f44336" />
                              </Tooltip>
                            )}
                            <Typography
                              variant="body2"
                              fontWeight={600}
                              sx={{
                                color: selectedAnalyzer === analyzer.name ? '#4caf50' : !analyzer.available ? '#ccc' : '#000',
                                textDecoration: !analyzer.available ? 'line-through' : 'none',
                              }}
                            >
                              {analyzer.name}
                            </Typography>
                            {analyzer.type === 'file' && (
                              <Chip
                                label="File"
                                size="small"
                                variant="outlined"
                                sx={{
                                  height: 20,
                                  fontSize: '0.75rem',
                                }}
                              />
                            )}
                            {!analyzer.available && (
                              <Chip
                                label="Unavailable"
                                size="small"
                                sx={{
                                  height: 20,
                                  fontSize: '0.75rem',
                                  backgroundColor: '#ffebee',
                                  color: '#c62828',
                                }}
                              />
                            )}
                          </Box>
                        }
                        secondary={
                          <Typography
                            variant="caption"
                            color="textSecondary"
                            sx={{
                              display: 'block',
                              mt: 0.5,
                              lineHeight: 1.4,
                              color: !analyzer.available ? '#999' : 'inherit',
                            }}
                          >
                            {analyzer.description}
                            {!analyzer.available && analyzer.unavailable_reason && (
                              <Typography variant="caption" sx={{ display: 'block', mt: 0.5, color: '#f44336', fontWeight: 500 }}>
                                ℹ️ {analyzer.unavailable_reason}
                              </Typography>
                            )}
                          </Typography>
                        }
                        secondaryTypographyProps={{
                          component: 'div',
                        }}
                      />
                      {analyzer.available && analyzer.supported_filetypes && analyzer.supported_filetypes.length > 0 && (
                        <Box
                          sx={{
                            ml: 2,
                            display: 'flex',
                            gap: 0.5,
                            flexWrap: 'wrap',
                            justifyContent: 'flex-end',
                            maxWidth: 200,
                          }}
                        >
                          {analyzer.supported_filetypes.slice(0, 2).map((filetype) => (
                            <Chip
                              key={filetype}
                              label={filetype.split('/')[1] || filetype}
                              size="small"
                              variant="outlined"
                              sx={{
                                height: 20,
                                fontSize: '0.7rem',
                              }}
                            />
                          ))}
                          {analyzer.supported_filetypes.length > 2 && (
                            <Chip
                              label={`+${analyzer.supported_filetypes.length - 2}`}
                              size="small"
                              sx={{
                                height: 20,
                                fontSize: '0.7rem',
                              }}
                            />
                          )}
                        </Box>
                      )}
                    </ListItemButton>
                    {index < currentAnalyzers.length - 1 && (
                      <Divider variant="inset" component="li" sx={{ my: 0 }} />
                    )}
                  </React.Fragment>
                ))}
              </List>
            </Paper>

            {/* Stats Footer */}
            <Box
              sx={{
                display: 'flex',
                gap: 2,
                pt: 1,
                px: 1,
                fontSize: '0.875rem',
                color: '#666',
              }}
            >
              <Typography variant="caption">
                Showing {currentAnalyzers.length} analyzers in {currentCategory}
              </Typography>
              <Typography variant="caption">•</Typography>
              <Typography variant="caption">
                {filteredAnalyzers[currentCategory]?.filter((a) => !a.available).length || 0} unavailable
              </Typography>
            </Box>
          </>
        )}
      </DialogContent>

      {/* Actions */}
      <DialogActions sx={{ borderTop: '1px solid #e0e0e0', padding: 2 }}>
        <Button onClick={onClose} aria-label="Cancel analyzer selection">
          Cancel
        </Button>
        <Button
          onClick={onClose}
          variant="contained"
          disabled={!selectedAnalyzer}
          aria-label="Confirm analyzer selection"
        >
          Confirm Selection
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default AnalyzerSelectionModal;
