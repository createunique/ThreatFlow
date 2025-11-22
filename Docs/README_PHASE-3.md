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
GET /api/analyzers?type=file    # List all analyzers (available + unavailable)
# Returns: {available, unavailable, summary} with container detection
```

**Solution 1 Enhancement:**
- Returns both available (18) and unavailable (186) analyzers
- Each analyzer includes `available: true/false` and `unavailable_reason` (if not available)
- Summary shows which Docker containers are installed/missing
- Frontend uses this to show visual indicators (✅ green vs 🔒 red)

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
- `api.getAnalyzers(type)`: Fetch analyzers for dropdowns ✅
- `api.executeWorkflow(nodes, edges, file)`: Submit workflow for execution ✅
- `api.pollJobStatus(jobId, onUpdate)`: Monitor execution progress ✅

#### Verified API Integration
- **Analyzer Discovery:** Successfully fetches analyzers from middleware
- **Workflow Execution:** Converts React Flow canvas to JSON and submits
- **Status Monitoring:** Real-time polling of analysis progress
- **Result Display:** Shows completed analysis results

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
   - **Solution 1**: Dropdown now shows:
     - **Green checkmark** (✅): Available analyzers you can select
     - **Red lock icon** (🔒): Unavailable analyzers (containers not installed)
   - Connect nodes by dragging from output to input handles
   - Click "Execute" button to run analysis (only available analyzers will run)

3. **Monitor Results**:
   - Status panel shows real-time progress
   - Results display when analysis completes
   - View detailed analyzer reports

### Analyzer Selection (Solution 1 Enhancement)

**AnalyzerSelectionModal Component Updates:**
- **Visual Indicators**: Each analyzer shows availability status
  - ✅ Green checkmark for available analyzers
  - 🔒 Red lock for unavailable analyzers (disabled, cannot click)
  - Strike-through text for unavailable analyzers
  - Red "Unavailable" badge

- **Information Display**: 
  - Shows unavailable reason on hover (e.g., "Requires observable analyzers container")
  - Displays container requirements clearly
  - Shows total: "18/204 analyzers available"

- **Selection Control**:
  - Available analyzers can be selected normally
  - Unavailable analyzers cannot be clicked or selected
  - Gray/disabled state prevents user confusion

### Node Types & Usage

#### File Upload Node
- **Purpose**: Upload files for analysis
- **Features**: Drag-drop upload, file validation, size display
- **Data**: `{file, fileName, fileSize}`

#### Analyzer Node (Solution 1 Enhanced)
- **Purpose**: Select IntelOwl analyzers
- **Features**: 
  - Dropdown shows 204 total analyzers (18 available + 186 unavailable)
  - Visual indicators show availability status
  - Badge displays "18/204 analyzers available"
  - Cannot select unavailable analyzers (disabled UI elements)
- **Data**: `{analyzer, analyzerType, description}`
- **Endpoints Used**: `GET /api/analyzers`

**Example Badge:**
```
[18/204 analyzers available] 🔒

Available (18):     ✅ File_Info, ClamAV, PE_Info, APKiD, ...
Unavailable (186):  🔒 AILTypoSquatting, AbuseIPDB, VirusTotal_v3_Get_Observable, ...
```

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
# Expected: {"status":"healthy","service":"ThreatFlow Middleware"}

# Test analyzer API
curl "http://localhost:8030/api/analyzers?type=file"
# Expected: Array of file analyzers

# Check IntelOwl connectivity
curl http://localhost/health
# Expected: IntelOwl nginx response

# View middleware logs (when running with --reload)
# Logs appear in terminal where uvicorn is running

# Check React frontend
curl -I http://localhost:3000
# Expected: HTTP/1.1 200 OK
```

## Development Notes

## Development Notes

### Solution 1: Analyzer Availability Detection (Frontend Integration)

#### Type Definitions (workflow.ts)
New types for handling availability information:

```typescript
export interface AnalyzerInfo {
  id: number;
  name: string;
  type: 'file' | 'observable';
  description: string;
  available: boolean;           // NEW: Availability status
  unavailable_reason?: string;  // NEW: Why it's unavailable
  supported_filetypes: string[];
  not_supported_filetypes: string[];
  observable_supported: string[];
}

export interface AnalyzersSummary {
  available_count: number;
  unavailable_count: number;
  total_count: number;
  containers_detected: {
    core: boolean;
    malware_tools: boolean;
    apk_analyzers: boolean;
    advanced_analyzers: boolean;
    observable_analyzers: boolean;
  };
}

export interface AnalyzersResponse {
  available: AnalyzerInfo[];
  unavailable: AnalyzerInfo[];
  summary: AnalyzersSummary;
}
```

#### API Service (api.ts)
Updated to handle new response structure:

```typescript
getAnalyzers: async (type?: 'file' | 'observable'): Promise<AnalyzersResponse> => {
  const response = await apiClient.get<AnalyzersResponse>('/api/analyzers', { params });
  return response.data;  // Returns {available, unavailable, summary}
}
```

#### AnalyzerSelectionModal Component
Enhanced with visual availability indicators:

```typescript
// Shows unavailable analyzers with lock icons and disabled state
{!analyzer.available && (
  <>
    <Lock size={18} color="#f44336" />  // Red lock icon
    <Typography variant="caption" sx={{ color: '#f44336' }}>
      ℹ️ {analyzer.unavailable_reason}  // Show reason on hover
    </Typography>
  </>
)}

// Disable unavailable analyzers from selection
<ListItemButton
  disabled={!analyzer.available}
  opacity: analyzer.available ? 1 : 0.65
/>
```

#### AnalyzerNode Component
Updated to combine available + unavailable and display ratio:

```typescript
// Fetch both available and unavailable analyzers
const response: AnalyzersResponse = await api.getAnalyzers('file');
cachedAnalyzers = [...response.available, ...response.unavailable];

// Display ratio in badge
label={`${analyzers.filter(a => a.available).length}/${analyzers.length} analyzers available`}
```

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
- **Solution 1**: Singleton analyzer fetching to avoid duplicate API calls
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

**Last Updated**: November 23, 2025
**Version**: Phase 3 Complete - React Frontend with Solution 1 (Container Detection)
**Status**: ✅ Fully Functional with Analyzer Availability Detection

## Solution 1: Frontend Implementation Summary

### Problem Solved
Users need to see which analyzers they can actually use based on installed Docker containers, to avoid selecting unavailable analyzers.

### Frontend Components Updated

#### 1. **Type Definitions** (workflow.ts)
- Added `AnalyzerInfo` with `available` and `unavailable_reason` fields
- Added `AnalyzersSummary` with container detection results
- Added `AnalyzersResponse` with separate `available` and `unavailable` arrays

#### 2. **API Service** (api.ts)
- Updated `getAnalyzers()` to return `AnalyzersResponse` (not just array)
- Frontend now receives both available and unavailable analyzers

#### 3. **AnalyzerSelectionModal** (AnalyzerSelectionModal.tsx)
- Displays 204 total analyzers (18 available + 186 unavailable)
- Visual indicators:
  - ✅ Green checkmarks for available
  - 🔒 Red lock icons for unavailable
- Unavailable analyzers are disabled (cannot be clicked)
- Shows hover tooltips with unavailable reasons
- Updated badge to show "18/204 analyzers available"

#### 4. **AnalyzerNode** (AnalyzerNode.tsx)
- Combines available + unavailable analyzers
- Displays ratio: "18/204 analyzers available"
- Uses singleton fetching pattern to prevent duplicate API calls

### Current Status
- ✅ 18 analyzers available (malware_tools container running)
- ✅ 186 analyzers unavailable (containers not installed or require API keys)
- ✅ 204 total enabled analyzers
- ✅ Visual indicators prevent user confusion
- ✅ Unavailable reasons help users understand container requirements</content>
<parameter name="filePath">/home/anonymous/COLLEGE/ThreatFlow/threatflow-frontend/THREATFLOW_DOCS.md