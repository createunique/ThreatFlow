# ThreatFlow Frontend

A professional React-based visual workflow builder for IntelOwl threat analysis platform.

## Phase 3: React Frontend Implementation

Built with React, TypeScript, React Flow, Zustand, Material-UI, and Axios.

## Features

- 🎨 **Drag-and-Drop Canvas**: Visual workflow builder using React Flow
- 📤 **File Upload Node**: Upload files for malware analysis
- 🔍 **Analyzer Nodes**: Select from File_Info, ClamAV, VirusTotal analyzers
- 📊 **Real-time Status**: Live job execution monitoring
- 🎯 **Type-Safe**: Full TypeScript support
- 🎭 **Professional UI**: Material-UI components

## Prerequisites

- Node.js 16+ 
- npm or yarn
- ThreatFlow Middleware running on port 8030
- IntelOwl instance running

## Installation

```bash
cd /home/anonymous/COLLEGE/ThreatFlow/threatflow-frontend

# Install dependencies (already done)
npm install

# Start development server
npm start
```

## Project Structure

```
src/
├── components/
│   ├── Canvas/
│   │   ├── WorkflowCanvas.tsx          # Main React Flow canvas
│   │   └── CustomNodes/
│   │       ├── FileNode.tsx            # File upload node
│   │       ├── AnalyzerNode.tsx        # Analyzer selection
│   │       └── ResultNode.tsx          # Display results
│   ├── Sidebar/
│   │   ├── NodePalette.tsx             # Drag-drop palette
│   │   └── PropertiesPanel.tsx         # Node properties
│   └── ExecutionPanel/
│       ├── ExecuteButton.tsx           # Run workflow
│       └── StatusMonitor.tsx           # Job status display
├── hooks/
│   ├── useWorkflowState.ts             # Zustand store
│   └── useWorkflowExecution.ts         # API integration
├── services/
│   └── api.ts                          # Axios client
├── types/
│   └── workflow.ts                     # TypeScript types
├── utils/
│   └── nodeFactory.ts                  # Node creation helpers
├── App.tsx                             # Main app component
└── index.tsx                           # Entry point
```

## Usage

1. **Start the Application**
   ```bash
   npm start
   ```
   App will open at http://localhost:3000

2. **Build a Workflow**
   - Drag "File Upload" node from left sidebar onto canvas
   - Upload a test file by clicking or dragging into the node
   - Drag "Analyzer" node(s) onto canvas
   - Select analyzer (File_Info, ClamAV, or VirusTotal)
   - Connect nodes by dragging from output handle to input handle
   - Click "Execute" button

3. **Monitor Execution**
   - Status monitor appears at bottom showing progress
   - Job ID and completion percentage displayed
   - Results shown when complete

## Configuration

Edit `.env` file to customize:

```bash
REACT_APP_API_URL=http://localhost:8030
REACT_APP_POLL_INTERVAL=5000
REACT_APP_MAX_FILE_SIZE=104857600
```

## Testing

```bash
# Run tests
npm test

# Build for production
npm run build
```

## Troubleshooting

### "Failed to load analyzers"
- Ensure middleware is running on port 8030
- Check `curl http://localhost:8030/api/analyzers`

### "Network Error" on Execute
- Verify `.env` has correct `REACT_APP_API_URL`
- Restart app: `npm start`

### Nodes not draggable
- Reinstall React Flow: `npm install reactflow@11.10.4`

## Architecture

- **React Flow v11**: Canvas and node rendering
- **Zustand**: Lightweight state management
- **Material-UI v5**: Professional UI components
- **Axios**: HTTP client for middleware API
- **TypeScript**: Type safety across all components

## Next Steps

- Phase 4: Add conditional logic nodes
- Multi-step workflow execution
- Enhanced result visualization
- Workflow save/load functionality

## License

Part of the ThreatFlow project for IntelOwl integration.
