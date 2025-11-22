/**
 * Error Boundary Component
 * Catches JavaScript errors in the component tree and displays fallback UI
 * Professional implementation with error reporting and recovery options
 */

import React, { Component, ErrorInfo, ReactNode } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  Alert,
  AlertTitle,
  Collapse,
  Divider,
} from '@mui/material';
import {
  Error as ErrorIcon,
  Refresh as RefreshIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
  BugReport as BugReportIcon,
} from '@mui/icons-material';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
  showDetails?: boolean;
  name?: string;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
  showDetails: boolean;
}

class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
      showDetails: props.showDetails || false,
    };
  }

  static getDerivedStateFromError(error: Error): Partial<State> {
    // Update state so the next render will show the fallback UI
    return {
      hasError: true,
      error,
    };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    // Log the error to console for debugging
    console.error('[ErrorBoundary]', error);
    console.error('[ErrorBoundary] Component Stack:', errorInfo.componentStack);

    // Update state with error details
    this.setState({
      error,
      errorInfo,
    });

    // Call optional error handler
    if (this.props.onError) {
      this.props.onError(error, errorInfo);
    }

    // In production, you might want to send this to an error reporting service
    // Example: Sentry, LogRocket, etc.
    if (process.env.NODE_ENV === 'production') {
      // this.reportError(error, errorInfo);
    }
  }

  handleRetry = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
      showDetails: false,
    });
  };

  toggleDetails = () => {
    this.setState(prevState => ({
      showDetails: !prevState.showDetails,
    }));
  };

  render() {
    if (this.state.hasError) {
      // Custom fallback UI
      if (this.props.fallback) {
        return this.props.fallback;
      }

      // Default error UI
      return (
        <Paper
          elevation={4}
          sx={{
            p: 3,
            m: 2,
            maxWidth: 600,
            mx: 'auto',
            border: '1px solid #f44336',
            borderRadius: 2,
          }}
        >
          <Box display="flex" alignItems="center" gap={2} mb={2}>
            <ErrorIcon color="error" fontSize="large" />
            <Box>
              <Typography variant="h6" color="error" fontWeight="bold">
                Something went wrong
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {this.props.name ? `Error in ${this.props.name}` : 'An unexpected error occurred'}
              </Typography>
            </Box>
          </Box>

          <Alert severity="error" sx={{ mb: 2 }}>
            <AlertTitle>Error Details</AlertTitle>
            <Typography variant="body2">
              {this.state.error?.message || 'Unknown error occurred'}
            </Typography>
          </Alert>

          <Box display="flex" gap={1} mb={2}>
            <Button
              variant="contained"
              color="primary"
              startIcon={<RefreshIcon />}
              onClick={this.handleRetry}
              size="small"
            >
              Try Again
            </Button>
            <Button
              variant="outlined"
              startIcon={<BugReportIcon />}
              onClick={this.toggleDetails}
              endIcon={
                this.state.showDetails ?
                  <ExpandLessIcon /> :
                  <ExpandMoreIcon />
              }
              size="small"
            >
              {this.state.showDetails ? 'Hide' : 'Show'} Details
            </Button>
          </Box>

          <Collapse in={this.state.showDetails}>
            <Paper
              variant="outlined"
              sx={{
                p: 2,
                backgroundColor: '#f5f5f5',
                fontFamily: 'monospace',
                fontSize: '0.75rem',
                maxHeight: 300,
                overflow: 'auto',
              }}
            >
              <Typography variant="caption" fontWeight="bold" display="block" mb={1}>
                Error Stack:
              </Typography>
              <pre style={{ margin: 0, whiteSpace: 'pre-wrap' }}>
                {this.state.error?.stack}
              </pre>

              {this.state.errorInfo && (
                <>
                  <Divider sx={{ my: 2 }} />
                  <Typography variant="caption" fontWeight="bold" display="block" mb={1}>
                    Component Stack:
                  </Typography>
                  <pre style={{ margin: 0, whiteSpace: 'pre-wrap' }}>
                    {this.state.errorInfo.componentStack}
                  </pre>
                </>
              )}
            </Paper>
          </Collapse>

          <Typography variant="caption" color="text.secondary" sx={{ mt: 2, display: 'block' }}>
            If this problem persists, please refresh the page or contact support.
          </Typography>
        </Paper>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;