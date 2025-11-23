/**
 * TemplateSelector Component
 * Displays pre-built condition templates with one-click apply
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Button,
  Menu,
  MenuItem,
  ListItemText,
  Chip,
  Typography,
  Divider,
  CircularProgress,
} from '@mui/material';
import { ContentCopy, PlayArrow } from '@mui/icons-material';
import { getConditionTemplates, ConditionTemplate } from '../../services/schemaApi';

interface TemplateSelectorProps {
  analyzerName: string;
  onApplyTemplate: (template: {
    conditionType: string;
    fieldPath?: string;
    expectedValue?: any;
    operator?: string;
  }) => void;
  disabled?: boolean;
}

export const TemplateSelector: React.FC<TemplateSelectorProps> = ({
  analyzerName,
  onApplyTemplate,
  disabled = false,
}) => {
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [templates, setTemplates] = useState<ConditionTemplate[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const open = Boolean(anchorEl);

  const fetchTemplates = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await getConditionTemplates(analyzerName);
      setTemplates(response.templates);
    } catch (err) {
      console.error('Failed to fetch templates:', err);
      setError('Failed to load templates');
      setTemplates([]);
    } finally {
      setLoading(false);
    }
  }, [analyzerName]);

  useEffect(() => {
    if (analyzerName && open) {
      fetchTemplates();
    }
  }, [analyzerName, open, fetchTemplates]);

  const handleClick = (event: React.MouseEvent<HTMLButtonElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleClose = () => {
    setAnchorEl(null);
  };

  const handleApplyTemplate = (template: ConditionTemplate) => {
    onApplyTemplate({
      conditionType: template.condition_type,
      fieldPath: template.field_path,
      expectedValue: template.expected_value,
      operator: template.operator,
    });
    handleClose();
  };

  // Group templates by use case
  const groupedTemplates = templates.reduce((acc, template) => {
    const useCase = template.use_case || 'General';
    if (!acc[useCase]) {
      acc[useCase] = [];
    }
    acc[useCase].push(template);
    return acc;
  }, {} as Record<string, ConditionTemplate[]>);

  return (
    <>
      <Button
        variant="outlined"
        size="small"
        startIcon={<ContentCopy />}
        onClick={handleClick}
        disabled={disabled || !analyzerName}
        fullWidth
      >
        Use Template
      </Button>

      <Menu
        anchorEl={anchorEl}
        open={open}
        onClose={handleClose}
        PaperProps={{
          sx: {
            maxHeight: 400,
            minWidth: 350,
          },
        }}
      >
        {loading && (
          <Box sx={{ display: 'flex', justifyContent: 'center', p: 2 }}>
            <CircularProgress size={24} />
          </Box>
        )}

        {error && (
          <MenuItem disabled>
            <ListItemText
              primary={error}
              primaryTypographyProps={{ color: 'error' }}
            />
          </MenuItem>
        )}

        {!loading && !error && templates.length === 0 && (
          <MenuItem disabled>
            <ListItemText primary="No templates available" />
          </MenuItem>
        )}

        {!loading && !error && Object.entries(groupedTemplates).map(([useCase, useCaseTemplates], idx) => (
          <Box key={useCase}>
            {idx > 0 && <Divider />}
            
            {/* Use Case Header */}
            <Box sx={{ px: 2, py: 1, backgroundColor: '#f5f5f5' }}>
              <Typography variant="caption" fontWeight="bold" color="primary">
                {useCase}
              </Typography>
            </Box>

            {/* Templates in this use case */}
            {useCaseTemplates.map((template, templateIdx) => (
              <MenuItem
                key={`${useCase}-${templateIdx}`}
                onClick={() => handleApplyTemplate(template)}
                sx={{ flexDirection: 'column', alignItems: 'flex-start', py: 1.5 }}
              >
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5, width: '100%' }}>
                  <PlayArrow fontSize="small" color="primary" />
                  <Typography variant="body2" fontWeight="medium">
                    {template.name}
                  </Typography>
                </Box>

                <Typography
                  variant="caption"
                  color="text.secondary"
                  sx={{ ml: 3, mb: 0.5 }}
                >
                  {template.description}
                </Typography>

                <Box sx={{ display: 'flex', gap: 0.5, ml: 3, flexWrap: 'wrap' }}>
                  <Chip
                    label={template.condition_type}
                    size="small"
                    variant="outlined"
                    sx={{ height: 18, fontSize: '0.65rem' }}
                  />
                  {template.field_path && (
                    <Chip
                      label={template.field_path}
                      size="small"
                      color="primary"
                      variant="outlined"
                      sx={{ height: 18, fontSize: '0.65rem', fontFamily: 'monospace' }}
                    />
                  )}
                </Box>

                {template.example && (
                  <Typography
                    variant="caption"
                    sx={{
                      ml: 3,
                      mt: 0.5,
                      fontFamily: 'monospace',
                      fontSize: '0.65rem',
                      color: 'text.secondary',
                      fontStyle: 'italic',
                    }}
                  >
                    {template.example}
                  </Typography>
                )}
              </MenuItem>
            ))}
          </Box>
        ))}
      </Menu>
    </>
  );
};
