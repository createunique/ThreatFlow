# ThreatFlow Middleware API Documentation

## Overview

The ThreatFlow Middleware is a FastAPI-based service that acts as an intermediary between the React frontend and IntelOwl backend for malware analysis workflows. It provides a clean, RESTful API for workflow execution, job monitoring, and analyzer management.

## ThreatFlow Project Phases

### Phase 1: IntelOwl Backend Integration
**Purpose:** Provides the core malware analysis engine and analyzer ecosystem.

**What it does:**
- Hosts 200+ malware analysis tools and services
- Provides REST API for file/observable analysis
- Manages analyzer configurations and health checks
- Stores analysis results and job history
- Offers web-based UI for direct analysis

**Key Components:**
- **File Analyzers:** File_Info, ClamAV, VirusTotal, YARA, PEiD, etc.
- **Observable Analyzers:** DNS, IP reputation, domain analysis
- **Playbooks:** Pre-configured analysis workflows
- **Web Interface:** Direct analysis and result viewing

**Dependencies:**
- Docker containers for analyzer isolation
- External API keys (VirusTotal, AbuseIPDB, etc.)
- PostgreSQL for data storage
- Redis for caching and queuing

### Phase 2: FastAPI Middleware (Current)
**Purpose:** Orchestrates communication between visual frontend and analysis backend.

**What it does:**
- Translates React Flow workflows to IntelOwl analysis requests
- Provides unified REST API for frontend consumption
- Handles file uploads and job status monitoring
- Manages authentication and error handling
- Offers health checks and analyzer discovery

### Phase 3: React Frontend
**Purpose:** Provides visual drag-and-drop interface for building analysis workflows.

**What it does:**
- Visual workflow builder using React Flow
- File upload and analysis initiation
- Real-time job progress monitoring
- Results visualization and reporting
- Workflow template management

**Key Features:**
- Drag-and-drop analyzer nodes
- Visual workflow connections
- Real-time status updates
- Analysis result display
- Workflow save/load functionality

**Dependencies:**
- React 18+ with TypeScript
- React Flow for visual workflows
- Axios for API communication
- Material-UI or similar component library

## Architecture

```
React Frontend (Port 3000) ←→ ThreatFlow Middleware (Port 8030) ←→ IntelOwl Backend (Port 80/8001)
       ↓                           ↓                                    ↓
Visual Workflows            API Orchestration                 Analysis Engines
File Upload                 Job Management                    200+ Analyzers
Real-time Updates           Status Polling                   Result Storage
```

## Quick Start

### Prerequisites
- Python 3.12+
- IntelOwl instance running
- Virtual environment

### Installation

```bash
cd threatflow-middleware
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Configuration

Create a `.env` file in the middleware directory:

```env
INTELOWL_URL=http://localhost:80
INTELOWL_API_KEY=your_api_key_here
```

### Running the Server

```bash
# Development mode with auto-reload
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8030

# Production mode
python -m uvicorn app.main:app --host 0.0.0.0 --port 8030
```

The API will be available at: `http://localhost:8030`

## API Endpoints

### Health Check Endpoints

#### GET `/health/`
Basic health check for the middleware service.

**Response:**
```json
{
  "status": "healthy",
  "service": "ThreatFlow Middleware"
}
```

#### GET `/health/intelowl`
Checks connectivity to IntelOwl backend and reports available analyzers.

**Response:**
```json
{
  "status": "connected",
  "analyzers_available": 3
}
```
**Note:** This endpoint tests actual connectivity and returns the count of working analyzers.

### Analyzer Management

#### GET `/api/analyzers`
Retrieves list of available and unavailable IntelOwl analyzers with container detection.

**Query Parameters:**
- `type` (optional): Filter by analyzer type (`file`, `observable`)

**Response Structure:**
```json
{
  "available": [
    {
      "id": 190,
      "name": "APK_Artifacts",
      "type": "file",
      "description": "APK strings analysis",
      "supported_filetypes": ["application/zip", "application/vnd.android.package-archive"],
      "available": true
    }
  ],
  "unavailable": [
    {
      "id": 167,
      "name": "AILTypoSquatting",
      "type": "observable",
      "description": "Typo squatting detection",
      "available": false,
      "unavailable_reason": "Requires observable analyzers container (--observable_analyzers)"
    }
  ],
  "summary": {
    "available_count": 18,
    "unavailable_count": 186,
    "total_count": 204,
    "containers_detected": {
      "core": true,
      "malware_tools": true,
      "apk_analyzers": false,
      "advanced_analyzers": false,
      "observable_analyzers": false
    }
  }
}
```

**Key Improvements (Solution 1):**
- **Analyzer Availability Detection**: Checks running Docker containers to determine which analyzers are available
- **Container Mapping**: Identifies which analyzers require which containers
- **Unavailable Reasons**: Provides specific reasons why analyzers are unavailable (missing containers or API configuration)
- **Frontend Integration**: Separates available/unavailable to display visual indicators (✅ green vs 🔒 red)

### Workflow Execution

#### POST `/api/execute`
Executes a malware analysis workflow defined in React Flow format.

**Content-Type:** `multipart/form-data`

**Form Fields:**
- `workflow_json`: JSON string containing React Flow workflow definition
- `file`: The file to analyze

**Workflow JSON Format:**
```json
{
  "nodes": [
    {
      "id": "file-1",
      "type": "file",
      "data": {
        "filename": "sample.exe"
      }
    },
    {
      "id": "analyzer-1",
      "type": "analyzer",
      "data": {
        "analyzer": "File_Info"
      }
    }
  ],
  "edges": [
    {
      "id": "edge-1",
      "source": "file-1",
      "target": "analyzer-1"
    }
  ]
}
```

**Response:**
```json
{
  "success": true,
  "job_id": 3947,
  "analyzers": ["File_Info", "ClamAV", "VirusTotal_v3_Get_File"],
  "message": "Analysis started with 3 analyzers"
}
```

**Example Usage:**
```bash
curl -X POST http://localhost:8030/api/execute \
  -F "workflow_json=$(cat workflow.json)" \
  -F "file=@sample.exe"
```

### Job Status Monitoring

#### GET `/api/status/{job_id}`
Retrieves the current status and results of an analysis job.

**Path Parameters:**
- `job_id`: The job ID returned from `/api/execute`

**Response:**
```json
{
  "job_id": 3947,
  "status": "reported_without_fails",
  "progress": null,
  "analyzers_completed": 3,
  "analyzers_total": 3,
  "results": {
    "job_id": 3947,
    "status": "reported_without_fails",
    "analyzers_completed": 3,
    "analyzers_total": 3,
    "file_info": {
      "File_Info": {
        "success": true,
        "report": {
          "file": {
            "name": "sample.exe",
            "size": 1024,
            "md5": "d41d8cd98f00b204e9800998ecf8427e",
            "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            "magic": "PE32 executable (GUI) Intel 80386, for MS Windows",
            "mime": "application/x-dosexec"
          }
        }
      }
    },
    "malware_info": {
      "ClamAV": {
        "success": true,
        "report": {
          "clamav": {
            "signatures": [],
            "infected": false,
            "result": "OK"
          }
        }
      },
      "VirusTotal_v3_Get_File": {
        "success": true,
        "report": {
          "virustotal": {
            "detection_ratio": "0/60",
            "positives": 0,
            "total": 60,
            "scan_date": "2024-01-15 10:30:00",
            "permalink": "https://www.virustotal.com/gui/file/...",
            "scans": {
              "Bkav": {"detected": false, "result": null},
              "ClamAV": {"detected": false, "result": null},
              // ... 58 more scanners
            }
          }
        }
      }
    }
  }
}
```

## Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `INTELOWL_URL` | IntelOwl API base URL | `http://localhost:80` | Yes |
| `INTELOWL_API_KEY` | IntelOwl API authentication token | - | Yes |

### CORS Configuration

The middleware is configured to accept requests from:
- `http://localhost:3000` (React development server)
- `http://127.0.0.1:3000` (React development server)

## Data Models

### WorkflowNode
```python
class WorkflowNode(BaseModel):
    id: str
    type: NodeType  # "file", "analyzer", "conditional", "result"
    data: Dict[str, Any]
    position: Optional[Dict[str, float]] = None
```

### WorkflowEdge
```python
class WorkflowEdge(BaseModel):
    id: str
    source: str
    target: str
    sourceHandle: Optional[str] = None
    targetHandle: Optional[str] = None
```

### JobStatusResponse
```python
class JobStatusResponse(BaseModel):
    job_id: int
    status: str  # "pending", "running", "reported_without_fails", "failed"
    progress: Optional[int] = None
    analyzers_completed: int = 0
    analyzers_total: int = 0
    results: Optional[Dict[str, Any]] = None
```

## Testing

### Running Tests

```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test file
python -m pytest tests/test_api.py -v

# Run with coverage
python -m pytest --cov=app tests/
```

### Test Files

- `tests/test_api.py`: API endpoint tests
- `tests/test_connection.py`: IntelOwl connectivity tests
- `tests/test_file_analysis.py`: File analysis workflow tests

### Verified Endpoints (Tested Working)

#### Health Endpoints
- `GET /health/` ✅ Returns: `{"status":"healthy","service":"ThreatFlow Middleware"}`
- `GET /health/intelowl` ✅ Returns: `{"status":"connected","analyzers_available":3}`

#### Analyzer Management
- `GET /api/analyzers?type=file` ✅ Returns array of available file analyzers
- `GET /api/analyzers?type=observable` ✅ Returns array of available observable analyzers

#### Workflow Execution
- `POST /api/execute` ✅ Successfully submits analysis jobs with workflow JSON + file
- `GET /api/status/{job_id}` ✅ Returns real-time job status and results

## Error Handling

The API uses standard HTTP status codes:

- `200`: Success
- `400`: Bad Request (validation errors)
- `404`: Not Found (invalid job ID)
- `500`: Internal Server Error

Error responses include detailed error messages:

```json
{
  "detail": "Validation error: Invalid workflow format"
}
```

## Development

### Project Structure

```
threatflow-middleware/
├── app/
│   ├── main.py              # FastAPI application entry point
│   ├── config.py            # Configuration management
│   ├── models/
│   │   └── workflow.py      # Pydantic data models
│   ├── services/
│   │   ├── intelowl_service.py  # IntelOwl API integration
│   │   └── workflow_parser.py   # React Flow to execution plan
│   └── routers/
│       ├── health.py        # Health check endpoints
│       └── execute.py       # Workflow execution endpoints
├── tests/                   # Test suite
├── .env                     # Environment configuration
├── requirements.txt         # Python dependencies
└── README.md               # This documentation
```

### Key Components

#### IntelOwlService
Handles all communication with IntelOwl backend:
- File analysis submission
- Job status polling
- Analyzer configuration retrieval

#### WorkflowParser
Converts React Flow JSON workflows into execution plans:
- Validates workflow structure
- Extracts analyzer sequence
- Handles conditional logic

#### Configuration
Uses Pydantic settings for type-safe configuration management with environment variable support.

## API Documentation

Interactive API documentation is available at:
- **Swagger UI:** `http://localhost:8030/docs`
- **ReDoc:** `http://localhost:8030/redoc`
- **OpenAPI JSON:** `http://localhost:8030/openapi.json`

## Troubleshooting

### Common Issues

1. **Connection to IntelOwl fails**
   - Verify IntelOwl is running on the configured URL
   - Check API key is valid
   - Ensure network connectivity

2. **Empty analyzer list**
   - IntelOwl may not be responding to analyzer config requests
   - Check IntelOwl logs for API errors

3. **File upload fails**
   - Ensure file size is within limits
   - Check file permissions
   - Verify multipart form data format

Application logs are written to stdout/stderr. Enable debug logging by setting:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Dependencies & Data Sources

### What This Middleware Depends On (IntelOwl)

The middleware relies on IntelOwl backend for all analysis capabilities:

- **Analyzer Configurations:** Fetches available analyzers via `/api/analyzer` endpoint
- **File Analysis:** Submits files to `/api/analyze_file` for processing by selected analyzers
- **Job Status:** Polls `/api/jobs/{job_id}` for analysis progress and completion
- **Health Checks:** Verifies analyzer health via individual `/api/analyzer/{name}/health_check` endpoints
- **Authentication:** Uses IntelOwl API tokens for all backend communication

**Data Flow:**
```
Middleware → IntelOwl API → Analysis Results → Middleware → Frontend
```

## Consumers & Usage Patterns

### Who Depends On This Middleware (Frontend)

The React frontend consumes the middleware API for all user interactions:

**Primary Consumer:** ThreatFlow React Frontend (Port 3000)

**How Frontend Uses Middleware:**

1. **Analyzer Discovery (Solution 1):**
   ```javascript
   // Fetch available AND unavailable analyzers for workflow builder
   GET /api/analyzers?type=file
   // Returns: {available, unavailable, summary} with container detection
   ```
   - Frontend displays available analyzers with green checkmarks (✅)
   - Unavailable analyzers shown with lock icons (🔒) and reasons
   - Users cannot select unavailable analyzers

2. **Workflow Execution:**
   ```javascript
   // Submit visual workflow + file for analysis
   POST /api/execute
   FormData: { workflow_json, file }
   ```

3. **Status Monitoring:**
   ```javascript
   // Poll for real-time analysis progress
   GET /api/status/{job_id}
   ```

4. **Health Monitoring:**
   ```javascript
   // Check system connectivity and container status
   GET /health/intelowl
   ```

**Integration Pattern:**
- Frontend builds visual workflows using React Flow
- Displays analyzer availability based on container detection
- Converts canvas to JSON and sends to middleware
- Displays real-time progress via status polling
- Shows detailed results when analysis completes

**Solution 1 Enhancement:**
- Analyzer selection modal now shows 204 total analyzers (18 available + 186 unavailable)
- Visual separation prevents users from selecting unavailable analyzers
- Container status visible in summary (which containers running/not running)
- Unavailable reasons help users understand why analyzers aren't available

## Contributing

1. Follow the existing code structure
2. Add tests for new functionality
3. Update this documentation for API changes
4. Use type hints and Pydantic models
5. Handle errors gracefully

---

**Last Updated:** November 23, 2025
**Version:** Phase 2 - FastAPI Middleware with Solution 1 (Container Detection)
**Status:** ✅ Fully Functional with Analyzer Availability Detection

## Solution 1: Analyzer Availability Detection (Backend Enhancement)

### Problem Solved
IntelOwl backend doesn't directly expose which analyzers are available. All analyzers are registered in the database, but many require specific Docker containers that may not be installed.

### Solution Implementation
Detect running Docker containers and determine analyzer availability based on container presence.

### Backend Changes
**File:** `app/services/intelowl_service.py`

1. **Container Detection Method:**
   ```python
   def _detect_installed_containers(self) -> Dict[str, bool]:
       # Runs: docker ps --format {{.Names}}
       # Returns: {'core': true, 'malware_tools': true, 'apk_analyzers': false, ...}
   ```

2. **Analyzer Categorization Constants:**
   - `MALWARE_TOOLS_ANALYZERS`: 18 analyzers (ClamAV, APKiD, etc.)
   - `APK_ANALYZERS`: Android analysis tools (Androguard, MobSF, etc.)
   - `ADVANCED_ANALYZERS`: Binary tools (SpeakEasy, ELF_Info, Suricata, etc.)
   - `OBSERVABLE_ANALYZERS`: Network tools (DNS, IP reputation, domain tools, etc.)

3. **Availability Check Method:**
   ```python
   def _is_analyzer_available(analyzer_name, containers) -> bool:
       # Maps analyzer to required container
       # Returns True if container is installed
   ```

4. **Response Structure:**
   ```python
   def get_available_analyzers() -> Dict[str, Any]:
       # Returns:
       # {
       #   "available": [18 analyzers],
       #   "unavailable": [186 analyzers],
       #   "summary": {counts, container_status}
       # }
   ```

### Current Environment Results
- **18 Available Analyzers** (malware_tools container running)
- **186 Unavailable Analyzers** (containers not installed)
- **204 Total** (enabled analyzers)
- **1 Disabled** (Securitytrails)</content>
<parameter name="filePath">/home/anonymous/COLLEGE/ThreatFlow/threatflow-middleware/README.md