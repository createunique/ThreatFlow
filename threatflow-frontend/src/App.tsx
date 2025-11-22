/**
 * Main ThreatFlow Application
 * Integrates all components into a cohesive UI
 */

import React, { useCallback } from 'react';
import { Box, AppBar, Toolbar, Typography } from '@mui/material';
import { ReactFlowProvider } from 'reactflow';
import WorkflowCanvas from './components/Canvas/WorkflowCanvas';
import NodePalette from './components/Sidebar/NodePalette';
import PropertiesPanel from './components/Sidebar/PropertiesPanel';
import ExecuteButton from './components/ExecutionPanel/ExecuteButton';
import StatusMonitor from './components/ExecutionPanel/StatusMonitor';
import { useWorkflowState } from './hooks/useWorkflowState';
import { nodeFactory } from './utils/nodeFactory';
import 'reactflow/dist/style.css';

function App() {
  const addNode = useWorkflowState((state) => state.addNode);

  // Handle drop on canvas
  const onDrop = useCallback(
    (event: React.DragEvent) => {
      event.preventDefault();

      const type = event.dataTransfer.getData('application/reactflow');
      if (!type) return;

      // Calculate drop position (adjust for canvas offset)
      const reactFlowBounds = (event.target as HTMLElement)
        .closest('.react-flow')
        ?.getBoundingClientRect();

      if (!reactFlowBounds) return;

      const position = {
        x: event.clientX - reactFlowBounds.left - 140,
        y: event.clientY - reactFlowBounds.top - 50,
      };

      // Create new node using factory
      const createNode = nodeFactory[type as keyof typeof nodeFactory];
      if (createNode) {
        const newNode = createNode(position);
        addNode(newNode as any);
      }
    },
    [addNode]
  );

  const onDragOver = useCallback((event: React.DragEvent) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = 'move';
  }, []);

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', height: '100vh' }}>
      {/* Top App Bar */}
      <AppBar position="static" elevation={1}>
        <Toolbar>
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            ThreatFlow - IntelOwl Workflow Builder
          </Typography>
          <ExecuteButton />
        </Toolbar>
      </AppBar>

      {/* Main Content */}
      <Box sx={{ display: 'flex', flexGrow: 1, overflow: 'hidden' }}>
        {/* Left Sidebar - Node Palette */}
        <NodePalette />

        {/* Center - Workflow Canvas */}
        <Box
          sx={{ flexGrow: 1, position: 'relative' }}
          onDrop={onDrop}
          onDragOver={onDragOver}
        >
          <ReactFlowProvider>
            <WorkflowCanvas />
          </ReactFlowProvider>
        </Box>

        {/* Right Sidebar - Properties */}
        <PropertiesPanel />
      </Box>

      {/* Bottom Panel - Status Monitor */}
      <Box
        sx={{
          padding: 2,
          backgroundColor: '#fafafa',
          borderTop: '1px solid #e0e0e0',
        }}
      >
        <StatusMonitor />
      </Box>
    </Box>
  );
}

export default App;
