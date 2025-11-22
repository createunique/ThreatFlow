# ThreatFlow Frontend & Middleware Documentation

## Overview

ThreatFlow is a visual malware analysis platform that integrates IntelOwl's analysis capabilities through a React-based drag-and-drop workflow builder. This documentation covers the complete Phase 2 & Phase 3 implementation.

## Architecture

```
React Frontend (Port 3000) ←→ ThreatFlow Middleware (Port 8030) ←→ IntelOwl Backend (Port 80)
       ↓                           ↓                                    ↓
Visual Workflows            API Orchestration                 Analysis Engines
File Upload                 Job Management                    200+ Analyzers
Real-time Updates           Status Polling                   Result Storage
```

## Phase 2: FastAPI Middleware (Backend API)

### Purpose
The middleware acts as an orchestration layer between the visual frontend and IntelOwl analysis backend, providing a clean REST API for workflow execution and job monitoring.

### Dependencies
- **IntelOwl Backend**: Primary dependency for all analysis capabilities
  - Analyzer configurations via `/api/analyzer` endpoint
  - File analysis submission via `/api/analyze_file`
  - Job status polling via `/api/jobs/{job_id}`
  - Health checks for analyzer connectivity
- **Python Environment**: Python 3.12+, FastAPI, Uvicorn
- **External Services**: PostgreSQL (IntelOwl), Redis (IntelOwl)

### Key Components
- **IntelOwlService**: Handles all IntelOwl API communication
- **WorkflowParser**: Converts React Flow JSON to execution plans
- **Health Endpoints**: System and IntelOwl connectivity checks

## Phase 3: React Frontend (Visual Interface)

### Technology Stack
- **React 18.2.0** with TypeScript 4.9.5
- **React Flow v11.10.4** for drag-and-drop canvas
- **Zustand v4.5.0** for state management
- **Material-UI v5.15.10** for professional UI
- **Axios v1.6.7** for API communication

### Core Components

#### Canvas System
- **WorkflowCanvas**: Main React Flow canvas with drag-drop support
- **Custom Nodes**:
  - `FileNode`: File upload with drag-drop support
  - `AnalyzerNode`: IntelOwl analyzer selection dropdown
  - `ResultNode`: Analysis results display

#### UI Components
- **NodePalette**: Drag-and-drop sidebar for adding nodes
- **PropertiesPanel**: Live node property editing
- **ExecutionPanel**: Workflow execution and status monitoring

#### State Management
- **Zustand Store**: Centralized workflow state (nodes, edges, execution status)
- **React Flow Hooks**: Local canvas state with middleware sync

## API Endpoints & Integration

### Middleware Endpoints (Port 8030)

#### Health Checks
```bash
GET /health/                    # Basic middleware health
GET /health/intelowl           # IntelOwl connectivity check
```

#### Analyzer Management
```bash
GET /api/analyzers?type=file    # List available analyzers
# Returns: [{name, type, description, supported_filetypes, disabled}]
```

#### Workflow Execution
```bash
POST /api/execute               # Execute workflow
# FormData: workflow_json + file
# Returns: {success, job_id, analyzers, message}
```

#### Job Monitoring
```bash
GET /api/status/{job_id}        # Get job status and results
# Returns: {job_id, status, progress, analyzers_completed, results}
```

### Frontend API Integration

#### Axios Client Configuration
```typescript
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8030';
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
});
```

#### Key API Methods
- `api.getAnalyzers(type)`: Fetch analyzers for dropdowns
- `api.executeWorkflow(nodes, edges, file)`: Submit workflow for execution
- `api.pollJobStatus(jobId, onUpdate)`: Monitor execution progress

## How to Use

### Quick Start

1. **Start Services**:
   ```bash
   # Terminal 1: Start IntelOwl backend
   cd IntelOwl && docker-compose up

   # Terminal 2: Start ThreatFlow middleware
   cd threatflow-middleware
   source venv/bin/activate
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8030

   # Terminal 3: Start React frontend
   cd threatflow-frontend
   npm start
   ```

2. **Build a Workflow**:
   - Open http://localhost:3000
   - Drag "File Upload" node from left sidebar
   - Upload a file by clicking or dragging into the node
   - Drag "Analyzer" node(s) and select analyzers from dropdown
   - Connect nodes by dragging from output to input handles
   - Click "Execute" button to run analysis

3. **Monitor Results**:
   - Status panel shows real-time progress
   - Results display when analysis completes
   - View detailed analyzer reports

### Node Types & Usage

#### File Upload Node
- **Purpose**: Upload files for analysis
- **Features**: Drag-drop upload, file validation, size display
- **Data**: `{file, fileName, fileSize}`

#### Analyzer Node
- **Purpose**: Select IntelOwl analyzers
- **Features**: Dropdown with available analyzers, live selection
- **Data**: `{analyzer, analyzerType, description}`
- **Endpoints Used**: `GET /api/analyzers`

#### Result Node
- **Purpose**: Display analysis results
- **Features**: Job status, progress tracking, result visualization
- **Data**: `{jobId, status, results, error}`

### Workflow Execution Flow

1. **Frontend**: Converts canvas to JSON workflow
2. **Middleware**: Parses workflow, extracts analyzers, submits to IntelOwl
3. **IntelOwl**: Runs analysis with selected tools
4. **Middleware**: Polls for completion, formats results
5. **Frontend**: Displays real-time status and final results

## Configuration

### Frontend Environment (.env)
```bash
REACT_APP_API_URL=http://localhost:8030
REACT_APP_POLL_INTERVAL=5000
REACT_APP_MAX_FILE_SIZE=104857600
```

### Middleware Environment (.env)
```bash
INTELOWL_URL=http://localhost:80
INTELOWL_API_KEY=your_api_key_here
DEBUG=true
```

## Troubleshooting

### Common Issues

#### "Failed to load analyzers"
- **Cause**: Middleware not running or IntelOwl unreachable
- **Fix**: Check middleware logs, verify IntelOwl connectivity
- **Test**: `curl http://localhost:8030/api/analyzers`

#### "Network Error" on Execute
- **Cause**: Wrong API URL or CORS issues
- **Fix**: Check `.env` file, restart frontend
- **Test**: `curl http://localhost:8030/health`

#### Dropdown Not Working
- **Cause**: Missing `nodrag` class or React Flow event interception
- **Fix**: Ensure `className="nodrag"` on interactive elements

#### Workflow Execution Fails
- **Cause**: No analyzers selected or invalid workflow structure
- **Fix**: Select analyzers in nodes, ensure proper connections
- **Check**: Middleware logs for "No analyzers connected to file node"

### Debug Commands

```bash
# Test middleware health
curl http://localhost:8030/health

# Test analyzer API
curl "http://localhost:8030/api/analyzers?type=file"

# Check IntelOwl connectivity
curl http://localhost/health

# View middleware logs (when running with --reload)
# Logs appear in terminal where uvicorn is running
```

## Development Notes

### Key Implementation Details

#### React Flow Integration
- Uses `useNodesState` and `useEdgesState` for local state
- Syncs with Zustand store for persistence
- Custom nodes use `useReactFlow().setNodes()` for immediate updates

#### State Management
- **Zustand**: Global workflow state (nodes, edges, execution)
- **React Flow**: Local canvas state with automatic change handling
- **Synchronization**: Effects sync Zustand ↔ React Flow states

#### API Error Handling
- Axios interceptors for request/response logging
- Automatic retry logic for transient failures
- User-friendly error messages in UI

#### Performance Optimizations
- Memoized components to prevent unnecessary re-renders
- Singleton analyzer fetching to avoid duplicate API calls
- Efficient polling with configurable intervals

### File Structure
```
threatflow-frontend/
├── src/
│   ├── components/Canvas/          # React Flow canvas & nodes
│   ├── components/Sidebar/         # Palette & properties panels
│   ├── hooks/                      # Zustand store & execution logic
│   ├── services/                   # Axios API client
│   ├── types/                      # TypeScript definitions
│   └── utils/                      # Node factory helpers
├── public/                         # Static assets
├── .env                            # Environment configuration
└── package.json                    # Dependencies & scripts
```

## Next Steps

### Phase 4 Features
- Conditional logic nodes (if/then branches)
- Multi-step workflow execution
- Enhanced result visualization
- Workflow save/load functionality
- Template management system

### Enhancement Opportunities
- Add more analyzer types (observable analysis)
- Implement workflow validation
- Add keyboard shortcuts
- Support for bulk file processing
- Integration with threat intelligence feeds

---

**Last Updated**: November 22, 2025
**Version**: Phase 3 Complete
**Status**: Ready for production use</content>
<parameter name="filePath">/home/anonymous/COLLEGE/ThreatFlow/threatflow-frontend/THREATFLOW_DOCS.md