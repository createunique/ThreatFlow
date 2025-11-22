/**
 * Main Workflow Canvas
 * React Flow canvas with drag-drop, node connections, and execution
 */

import React, { useCallback, useMemo } from 'react';
import ReactFlow, {
  Background,
  Controls,
  MiniMap,
  Panel,
  useNodesState,
  useEdgesState,
  addEdge,
  Connection,
  NodeTypes,
  BackgroundVariant,
  Node,
  Edge,
  NodeChange,
  EdgeChange,
} from 'reactflow';
import 'reactflow/dist/style.css';

import FileNode from './CustomNodes/FileNode';
import AnalyzerNode from './CustomNodes/AnalyzerNode';
import ResultNode from './CustomNodes/ResultNode';
import ErrorBoundary from '../ErrorBoundary';
import { useWorkflowState } from '../../hooks/useWorkflowState';
import { Box, Typography } from '@mui/material';

const nodeTypes: NodeTypes = {
  file: FileNode,
  analyzer: AnalyzerNode,
  result: ResultNode,
};

const WorkflowCanvas: React.FC = () => {
  const storeNodes = useWorkflowState((state) => state.nodes);
  const storeEdges = useWorkflowState((state) => state.edges);
  const addStoreEdge = useWorkflowState((state) => state.addEdge);
  const updateStoreNode = useWorkflowState((state) => state.updateNode);
  const deleteStoreNode = useWorkflowState((state) => state.deleteNode);
  const deleteStoreEdge = useWorkflowState((state) => state.deleteEdge);
  const setSelectedNode = useWorkflowState((state) => state.setSelectedNode);

  // Local state for React Flow - synced with Zustand store
  const [nodes, setNodes, onNodesChange] = useNodesState<Node<any>[]>(storeNodes as Node<any>[]);
  const [edges, setEdges, onEdgesChange] = useEdgesState(storeEdges);

  // Sync local state with store when store updates
  React.useEffect(() => {
    setNodes(storeNodes as Node<any>[]);
  }, [storeNodes, setNodes]);

  React.useEffect(() => {
    setEdges(storeEdges);
  }, [storeEdges, setEdges]);

  // Custom node change handler to sync position updates to store
  const handleNodesChange = useCallback(
    (changes: NodeChange[]) => {
      // Apply changes to local state first
      onNodesChange(changes);

      // Sync position/selection changes to store
      changes.forEach((change) => {
        if (change.type === 'position' && change.position && !change.dragging) {
          // Update final position in store after drag ends
          updateStoreNode(change.id, { position: change.position } as any);
        } else if (change.type === 'select') {
          // Update selection in store
          const node = nodes.find(n => n.id === change.id);
          if (node && change.selected) {
            setSelectedNode(node as any);
          } else if (!change.selected) {
            setSelectedNode(null);
          }
        } else if (change.type === 'remove') {
          // Delete from store
          deleteStoreNode(change.id);
        }
      });
    },
    [onNodesChange, updateStoreNode, deleteStoreNode, setSelectedNode, nodes]
  );

  // Custom edge change handler to sync to store
  const handleEdgesChange = useCallback(
    (changes: EdgeChange[]) => {
      // Apply changes to local state first
      onEdgesChange(changes);

      // Sync deletions to store
      changes.forEach((change) => {
        if (change.type === 'remove') {
          deleteStoreEdge(change.id);
        }
      });
    },
    [onEdgesChange, deleteStoreEdge]
  );

  // Handle new connections
  const onConnect = useCallback(
    (params: Connection) => {
      // Ensure source and target are not null
      if (!params.source || !params.target) return;

      const newEdge: Edge = {
        id: `e${params.source}-${params.target}`,
        source: params.source,
        target: params.target,
        sourceHandle: params.sourceHandle,
        targetHandle: params.targetHandle,
        type: 'default',
        animated: true,
      };
      
      // Update local state
      setEdges((eds) => addEdge(newEdge, eds));
      
      // Sync to store
      addStoreEdge(newEdge);
    },
    [setEdges, addStoreEdge]
  );

  // Handle node click for selection
  const onNodeClick = useCallback(
    (_event: React.MouseEvent, node: Node) => {
      setSelectedNode(node as any);
    },
    [setSelectedNode]
  );

  // Handle pane click to deselect
  const onPaneClick = useCallback(() => {
    setSelectedNode(null);
  }, [setSelectedNode]);

  // Minimap style
  const minimapStyle = useMemo(
    () => ({
      height: 120,
    }),
    []
  );

  return (
    <Box sx={{ width: '100%', height: '100%', position: 'relative' }}>
      <ErrorBoundary
        name="React Flow Canvas"
        fallback={
          <Box
            sx={{
              width: '100%',
              height: '100%',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              backgroundColor: '#f5f5f5',
              border: '2px dashed #ccc',
              borderRadius: 2,
            }}
          >
            <Box textAlign="center" color="error.main">
              <Typography variant="h6" fontWeight="bold" mb={1}>
                Canvas Error
              </Typography>
              <Typography variant="body2">
                Failed to load workflow canvas. Please refresh the page.
              </Typography>
            </Box>
          </Box>
        }
      >
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={handleNodesChange}
          onEdgesChange={handleEdgesChange}
          onConnect={onConnect}
          onNodeClick={onNodeClick}
          onPaneClick={onPaneClick}
          nodeTypes={nodeTypes}
          fitView
          snapToGrid={true}
          snapGrid={[15, 15]}
          attributionPosition="bottom-left"
          deleteKeyCode="Backspace"
          multiSelectionKeyCode="Shift"
        >
          <Background 
            variant={BackgroundVariant.Dots} 
            gap={16} 
            size={1}
            color="#aaa"
          />
          <Controls showInteractive={false} />
          <MiniMap 
            style={minimapStyle} 
            zoomable 
            pannable
            nodeColor={(node) => {
              switch (node.type) {
                case 'file':
                  return '#2196f3';
                case 'analyzer':
                  return '#4caf50';
                case 'result':
                  return '#9c27b0';
                default:
                  return '#666';
              }
            }}
          />

          <Panel position="top-center">
            <Box
              sx={{
                backgroundColor: 'rgba(255, 255, 255, 0.95)',
                padding: 1.5,
                paddingX: 3,
                borderRadius: 2,
                boxShadow: 2,
              }}
            >
              <Typography variant="h6" fontWeight="bold" color="primary">
                🔐 ThreatFlow Workflow Canvas
              </Typography>
            </Box>
          </Panel>
        </ReactFlow>
      </ErrorBoundary>
    </Box>
  );
};

export default WorkflowCanvas;
