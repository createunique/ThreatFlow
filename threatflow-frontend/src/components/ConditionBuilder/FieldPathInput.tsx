/**
 * FieldPathInput Component
 * Intelligent field path input with autocomplete and real-time validation
 * Uses schema API for suggestions and validation
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  TextField,
  Autocomplete,
  Box,
  Typography,
  Chip,
  CircularProgress,
  Alert,
} from '@mui/material';
import { CheckCircle, Error as ErrorIcon, Warning } from '@mui/icons-material';
import {
  getFieldSuggestions,
  validateFieldPath,
  FieldSuggestion,
  FieldValidationResponse,
} from '../../services/schemaApi';

interface FieldPathInputProps {
  analyzerName: string;
  value: string;
  onChange: (value: string) => void;
  label?: string;
  helperText?: string;
  required?: boolean;
  disabled?: boolean;
}

export const FieldPathInput: React.FC<FieldPathInputProps> = ({
  analyzerName,
  value,
  onChange,
  label = 'Field Path',
  helperText,
  required = false,
  disabled = false,
}) => {
  const [suggestions, setSuggestions] = useState<FieldSuggestion[]>([]);
  const [loading, setLoading] = useState(false);
  const [validation, setValidation] = useState<FieldValidationResponse | null>(null);
  const [validating, setValidating] = useState(false);
  const [inputValue, setInputValue] = useState(value);

  const fetchSuggestions = useCallback(async (partial: string) => {
    setLoading(true);
    try {
      const response = await getFieldSuggestions(analyzerName, partial, 10);
      setSuggestions(response.suggestions);
    } catch (error) {
      console.error('Failed to fetch suggestions:', error);
      setSuggestions([]);
    } finally {
      setLoading(false);
    }
  }, [analyzerName]);

  const validateField = useCallback(async (fieldPath: string) => {
    setValidating(true);
    try {
      const response = await validateFieldPath({
        analyzer_name: analyzerName,
        field_path: fieldPath,
      });
      setValidation(response);
    } catch (error) {
      console.error('Failed to validate field:', error);
      setValidation(null);
    } finally {
      setValidating(false);
    }
  }, [analyzerName]);

  // Debounced autocomplete fetching
  useEffect(() => {
    if (!analyzerName || inputValue.length < 2) {
      setSuggestions([]);
      return;
    }

    const timeoutId = setTimeout(() => {
      fetchSuggestions(inputValue);
    }, 300);

    return () => clearTimeout(timeoutId);
  }, [inputValue, analyzerName, fetchSuggestions]);

  // Validate field path when value changes
  useEffect(() => {
    if (!analyzerName || !value) {
      setValidation(null);
      return;
    }

    const timeoutId = setTimeout(() => {
      validateField(value);
    }, 500);

    return () => clearTimeout(timeoutId);
  }, [value, analyzerName, validateField]);

  const handleInputChange = (event: React.SyntheticEvent, newInputValue: string) => {
    setInputValue(newInputValue);
  };

  const handleChange = (event: React.SyntheticEvent, newValue: string | null) => {
    const selectedValue = newValue || '';
    onChange(selectedValue);
    setInputValue(selectedValue);
  };

  const getValidationIcon = () => {
    if (validating) {
      return <CircularProgress size={20} />;
    }
    if (!validation) return null;

    if (validation.is_valid) {
      return <CheckCircle color="success" fontSize="small" />;
    }
    if (validation.suggestions.length > 0) {
      return <Warning color="warning" fontSize="small" />;
    }
    return <ErrorIcon color="error" fontSize="small" />;
  };

  const getValidationHelperText = () => {
    if (helperText && !validation) return helperText;
    if (!validation) return undefined;

    if (validation.is_valid) {
      return `✓ Valid field (type: ${validation.field_type})`;
    }

    if (validation.errors.length > 0) {
      return validation.errors[0];
    }

    return undefined;
  };

  return (
    <Box>
      <Autocomplete
        freeSolo
        value={value}
        inputValue={inputValue}
        onInputChange={handleInputChange}
        onChange={handleChange}
        options={suggestions.map(s => s.field_path)}
        loading={loading}
        disabled={disabled}
        renderInput={(params) => (
          <TextField
            {...params}
            label={label}
            required={required}
            error={validation?.is_valid === false}
            helperText={getValidationHelperText()}
            InputProps={{
              ...params.InputProps,
              endAdornment: (
                <>
                  {loading && <CircularProgress color="inherit" size={20} />}
                  {!loading && getValidationIcon()}
                  {params.InputProps.endAdornment}
                </>
              ),
            }}
          />
        )}
        renderOption={(props, option) => {
          const suggestion = suggestions.find(s => s.field_path === option);
          if (!suggestion) return null;

          return (
            <Box component="li" {...props}>
              <Box sx={{ width: '100%' }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <Typography variant="body2" sx={{ fontFamily: 'monospace' }}>
                    {suggestion.field_path}
                  </Typography>
                  <Chip
                    label={suggestion.type}
                    size="small"
                    color="primary"
                    variant="outlined"
                    sx={{ height: 20, fontSize: '0.7rem' }}
                  />
                  <Typography
                    variant="caption"
                    color="text.secondary"
                    sx={{ ml: 'auto' }}
                  >
                    {Math.round(suggestion.confidence * 100)}%
                  </Typography>
                </Box>
                {suggestion.description && (
                  <Typography variant="caption" color="text.secondary">
                    {suggestion.description}
                  </Typography>
                )}
              </Box>
            </Box>
          );
        }}
        noOptionsText={
          inputValue.length < 2
            ? 'Type at least 2 characters for suggestions'
            : 'No matching fields found'
        }
      />

      {/* Show suggestions if field is invalid */}
      {validation && !validation.is_valid && validation.suggestions.length > 0 && (
        <Alert severity="info" sx={{ mt: 1 }}>
          <Typography variant="caption" sx={{ fontWeight: 'bold' }}>
            Did you mean:
          </Typography>
          <Box sx={{ mt: 0.5, display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
            {validation.suggestions.slice(0, 3).map((suggestion, idx) => (
              <Chip
                key={idx}
                label={suggestion}
                size="small"
                onClick={() => onChange(suggestion)}
                sx={{ cursor: 'pointer' }}
              />
            ))}
          </Box>
        </Alert>
      )}
    </Box>
  );
};
