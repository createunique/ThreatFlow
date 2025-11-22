/**
 * Main ThreatFlow Application
 * Integrates all components into a cohesive UI
 */

import React, { useCallback, useState } from 'react';
import { Box, AppBar, Toolbar, Typography, IconButton, Tooltip, Fade } from '@mui/material';
import { ChevronLeft, ChevronRight, Menu, Settings } from '@mui/icons-material';
import { ReactFlowProvider } from 'reactflow';
import WorkflowCanvas from './components/Canvas/WorkflowCanvas';
import NodePalette from './components/Sidebar/NodePalette';
import PropertiesPanel from './components/Sidebar/PropertiesPanel';
import ExecuteButton from './components/ExecutionPanel/ExecuteButton';
import StatusMonitor from './components/ExecutionPanel/StatusMonitor';
import ErrorBoundary from './components/ErrorBoundary';
import 'reactflow/dist/style.css';

function AppContent() {
  const [leftSidebarOpen, setLeftSidebarOpen] = useState(true);
  const [rightSidebarOpen, setRightSidebarOpen] = useState(true);

  const toggleLeftSidebar = useCallback(() => {
    setLeftSidebarOpen(prev => !prev);
  }, []);

  const toggleRightSidebar = useCallback(() => {
    setRightSidebarOpen(prev => !prev);
  }, []);

  const onDragOver = useCallback((event: React.DragEvent) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = 'move';
  }, []);

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', height: '100vh' }}>
      {/* Top App Bar */}
      <AppBar position="static" elevation={1}>
        <Toolbar>
          <Tooltip title={leftSidebarOpen ? "Hide Node Palette" : "Show Node Palette"}>
            <IconButton
              color="inherit"
              onClick={toggleLeftSidebar}
              sx={{ mr: 1 }}
              aria-label={leftSidebarOpen ? "Hide node palette" : "Show node palette"}
            >
              <Menu />
            </IconButton>
          </Tooltip>
          
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            ThreatFlow - IntelOwl Workflow Builder
          </Typography>
          
          <ErrorBoundary name="Execute Button">
            <ExecuteButton />
          </ErrorBoundary>
          
          <Tooltip title={rightSidebarOpen ? "Hide Properties" : "Show Properties"}>
            <IconButton
              color="inherit"
              onClick={toggleRightSidebar}
              sx={{ ml: 1 }}
              aria-label={rightSidebarOpen ? "Hide properties panel" : "Show properties panel"}
            >
              <Settings />
            </IconButton>
          </Tooltip>
        </Toolbar>
      </AppBar>

      {/* Main Content */}
      <Box sx={{ display: 'flex', flexGrow: 1, overflow: 'hidden' }}>
        {/* Left Sidebar - Node Palette */}
        <Fade in={leftSidebarOpen} timeout={300}>
          <Box
            sx={{
              width: leftSidebarOpen ? 280 : 0,
              transition: 'width 0.3s ease-in-out',
              overflow: 'hidden',
            }}
          >
            {leftSidebarOpen && (
              <ErrorBoundary name="Node Palette">
                <NodePalette />
              </ErrorBoundary>
            )}
          </Box>
        </Fade>

        {/* Left Sidebar Toggle Button (when collapsed) */}
        {!leftSidebarOpen && (
          <Box
            sx={{
              position: 'relative',
              width: 40,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              backgroundColor: '#f5f5f5',
              borderRight: '1px solid #e0e0e0',
            }}
          >
            <Tooltip title="Show Node Palette" placement="right">
              <IconButton
                onClick={toggleLeftSidebar}
                sx={{
                  color: '#666',
                  '&:hover': {
                    backgroundColor: '#e0e0e0',
                    color: '#333',
                  },
                }}
                aria-label="Show node palette"
              >
                <ChevronRight />
              </IconButton>
            </Tooltip>
          </Box>
        )}

        {/* Center - Workflow Canvas */}
        <Box
          sx={{ flexGrow: 1, position: 'relative' }}
          onDragOver={onDragOver}
        >
          <ErrorBoundary name="Workflow Canvas">
            <ReactFlowProvider>
              <WorkflowCanvas />
            </ReactFlowProvider>
          </ErrorBoundary>
        </Box>

        {/* Right Sidebar Toggle Button (when collapsed) */}
        {!rightSidebarOpen && (
          <Box
            sx={{
              position: 'relative',
              width: 40,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              backgroundColor: '#f5f5f5',
              borderLeft: '1px solid #e0e0e0',
            }}
          >
            <Tooltip title="Show Properties" placement="left">
              <IconButton
                onClick={toggleRightSidebar}
                sx={{
                  color: '#666',
                  '&:hover': {
                    backgroundColor: '#e0e0e0',
                    color: '#333',
                  },
                }}
                aria-label="Show properties panel"
              >
                <ChevronLeft />
              </IconButton>
            </Tooltip>
          </Box>
        )}

        {/* Right Sidebar - Properties */}
        <Fade in={rightSidebarOpen} timeout={300}>
          <Box
            sx={{
              width: rightSidebarOpen ? 320 : 0,
              transition: 'width 0.3s ease-in-out',
              overflow: 'hidden',
            }}
          >
            {rightSidebarOpen && (
              <ErrorBoundary name="Properties Panel">
                <PropertiesPanel />
              </ErrorBoundary>
            )}
          </Box>
        </Fade>
      </Box>

      {/* Bottom Panel - Status Monitor */}
      <Box
        sx={{
          padding: 2,
          backgroundColor: '#fafafa',
          borderTop: '1px solid #e0e0e0',
        }}
      >
        <ErrorBoundary name="Status Monitor">
          <StatusMonitor />
        </ErrorBoundary>
      </Box>
    </Box>
  );
}

function App() {
  return (
    <ErrorBoundary
      name="ThreatFlow Application"
      onError={(error, errorInfo) => {
        // Log to console and potentially to external service
        console.error('Application Error:', error);
        console.error('Error Info:', errorInfo);

        // In production, send to error reporting service
        // Example: Sentry.captureException(error, { contexts: { react: errorInfo } });
      }}
    >
      <AppContent />
    </ErrorBoundary>
  );
}

export default App;
