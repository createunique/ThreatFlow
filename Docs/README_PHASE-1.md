# ThreatFlow Phase 1 - IntelOwl Backend Integration Documentation

## Overview

This document provides complete information about the IntelOwl backend integration in ThreatFlow Phase 1, including setup, configuration, working endpoints, middleware usage, and troubleshooting.

## Project Structure

```
ThreatFlow/
├── Docs/                          # Documentation files
│   ├── README_PHASE-1.md         # This file (Phase 1 docs)
│   ├── README_PHASE-2.md         # Phase 2 middleware docs
│   └── README_PHASE-3.md         # Phase 3 frontend docs
├── IntelOwl/                     # IntelOwl backend (Docker-based)
├── threatflow-middleware/        # FastAPI middleware service
├── threatflow-frontend/          # React frontend (optional)
└── [Other project files...]
```

## ThreatFlow Project Phases

### Phase 1: IntelOwl Backend Integration (Current)
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

### Phase 2: FastAPI Middleware
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

### Prerequisites
- Docker and Docker Compose
- Python 3.12+ (for middleware)
- Git

### Installation & Startup

1. **Clone IntelOwl Repository:**
   ```bash
   cd /home/anonymous/COLLEGE/ThreatFlow
   git clone https://github.com/intelowlproject/IntelOwl.git
   cd IntelOwl
   ```

2. **Start IntelOwl with Docker:**
   ```bash
   # From IntelOwl directory
   docker-compose up -d
   ```

3. **Access IntelOwl:**
   - **Web Interface:** http://localhost
   - **API Base URL:** http://localhost/api
   - **Default Admin:** admin / admin

### IntelOwl Configuration

#### API Key Generation
1. Log into IntelOwl web interface
2. Go to **Admin Panel** → **Tokens** → **Add Token**
3. Create a token with appropriate permissions
4. **Example Token:** `9e16ffdf58e18e11f0f4d0dd98277b1a73861ad8`

#### Analyzer Configuration

##### VirusTotal Setup
1. **Get VirusTotal API Key:**
   - Sign up at https://www.virustotal.com/
   - Generate API key from your account settings

2. **Configure in IntelOwl:**
   - Go to **Admin Panel** → **Analyzer Configs**
   - Find **VirusTotal_v3_Get_File**
   - Add your API key in the configuration
   - Save changes

3. **Verify Configuration:**
   ```bash
   # Test health check
   curl -s "http://localhost/api/analyzer/VirusTotal_v3_Get_File/health_check" \
     -H "Authorization: Token YOUR_API_KEY"
   # Expected: {"status": true}
   ```

## Working IntelOwl Endpoints

### Authentication
All API requests require authentication:
```bash
# Header format
Authorization: Token YOUR_API_KEY
```

### Core Endpoints

#### 1. Health Check
```bash
GET /api/analyzer/{analyzer_name}/health_check
```
**Example:**
```bash
curl -s "http://localhost/api/analyzer/VirusTotal_v3_Get_File/health_check" \
  -H "Authorization: Token YOUR_API_KEY"
```
**Response:** `{"status": true}` or `{"status": false}` (depending on analyzer configuration)
**Note:** Not all analyzers implement health checks. Some return `{"errors":{"detail":"No healthcheck implemented"}}`

#### 2. List Analyzers
```bash
GET /api/analyzer
```
**Query Parameters:**
- `type`: `file` or `observable`
- `page`: pagination
- `page_size`: results per page

**Example:**
```bash
# Get all analyzers
curl -s "http://localhost/api/analyzer" -H "Authorization: Token YOUR_API_KEY" | jq '.count'
# Returns: 205 (total analyzers)

# Get file analyzers
curl -s "http://localhost/api/analyzer?type=file" -H "Authorization: Token YOUR_API_KEY" | jq '.count'
# Returns: ~150 file analyzers
```

#### 3. Get Playbooks
```bash
GET /api/playbook
```
**Example:**
```bash
curl -s "http://localhost/api/playbook" -H "Authorization: Token YOUR_API_KEY" | jq '.count'
# Returns: 15 (total playbooks)
```

#### 4. Submit File Analysis
```bash
POST /api/analyze_file
Content-Type: multipart/form-data
```
**Form Data:**
- `file`: binary file data
- `file_name`: filename
- `analyzers_requested`: comma-separated analyzer names
- `tlp`: Traffic Light Protocol (CLEAR, GREEN, AMBER, RED)

**Example:**
```bash
curl -X POST http://localhost/api/analyze_file \
  -H "Authorization: Token YOUR_API_KEY" \
  -F "file=@sample.exe" \
  -F "analyzers_requested=File_Info,ClamAV,VirusTotal_v3_Get_File" \
  -F "tlp=CLEAR"
```

#### 5. Submit Observable Analysis
```bash
POST /api/analyze_observable
Content-Type: application/json
```
**Body:**
```json
{
  "observable_name": "example.com",
  "analyzers_requested": ["DNS", "VirusTotal_v3_Get_Observable"],
  "tlp": "CLEAR"
}
```

#### 6. Get Job Status
```bash
GET /api/jobs/{job_id}
```
**Example:**
```bash
curl -s "http://localhost/api/jobs/123" -H "Authorization: Token YOUR_API_KEY"
```

### Available Analyzers (Working)

#### File Analyzers
- **File_Info**: Basic file information extraction ✅
- **ClamAV**: Antivirus scanning ✅
- **VirusTotal_v3_Get_File**: VirusTotal file hash lookup ✅
- **APKiD**: Android APK analysis
- **Androguard**: Android malware analysis
- **YARA**: YARA rule matching

#### Observable Analyzers
- **DNS**: DNS resolution and analysis
- **VirusTotal_v3_Get_Observable**: VirusTotal observable lookup ✅
- **AbuseIPDB**: IP reputation
- **AILTypoSquatting**: Typo squatting detection
- **Anomali_Threatstream**: Threat intelligence

## ThreatFlow Middleware Setup

### Installation

1. **Navigate to middleware directory:**
   ```bash
   cd /home/anonymous/COLLEGE/ThreatFlow/threatflow-middleware
   ```

2. **Create virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # Linux/Mac
   # OR
   venv\Scripts\activate     # Windows
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Create environment file:**
   ```bash
   # Create .env file
   cat > .env << EOF
   INTELOWL_URL=http://localhost:80
   INTELOWL_API_KEY=9e16ffdf58e18e11f0f4d0dd98277b1a73861ad8
   EOF
   ```

### Running the Middleware

```bash
# Development mode (with auto-reload)
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8030

# Production mode
python -m uvicorn app.main:app --host 0.0.0.0 --port 8030
```

**Access Points:**
- **API:** http://localhost:8030
- **Swagger Docs:** http://localhost:8030/docs
- **ReDoc:** http://localhost:8030/redoc

## Middleware API Endpoints

### Health Endpoints

#### GET `/health/`
Basic middleware health check.

#### GET `/health/intelowl`
Tests IntelOwl connectivity and reports analyzer count.

### Core Endpoints

#### GET `/api/analyzers`
Returns available IntelOwl analyzers.
```json
[
  {
    "name": "File_Info",
    "type": "file",
    "description": "Basic file information extractor",
    "supported_filetypes": ["*"],
    "disabled": false
  }
]
```

#### POST `/api/execute`
Executes workflow-based analysis.
**Content-Type:** `multipart/form-data`
**Form Fields:**
- `workflow_json`: React Flow workflow definition
- `file`: File to analyze

**Workflow Format:**
```json
{
  "nodes": [
    {
      "id": "file-1",
      "type": "file",
      "data": {"filename": "sample.exe"}
    },
    {
      "id": "analyzer-1",
      "type": "analyzer",
      "data": {"analyzer": "File_Info"}
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

#### GET `/api/status/{job_id}`
Returns job status and results.

## Testing Procedures

### IntelOwl Connectivity Tests

1. **Basic Connection Test:**
   ```bash
   cd threatflow-middleware
   source venv/bin/activate
   python tests/test_connection.py
   ```

2. **File Analysis Test:**
   ```bash
   python tests/test_file_analysis.py
   ```

### Expected Test Results

#### Connection Test Output:
```
============================================================
TEST 1: Fetching Analyzer Configurations
============================================================
✓ IntelOwl API accessible
✓ Found 205 total analyzers
✓ Found 15 playbooks

============================================================
TEST 2: Health Check Tests
============================================================
✓ Some analyzers have health checks implemented
⚠ Some analyzers return: {"errors":{"detail":"No healthcheck implemented"}}
```


#### File Analysis Test Output:
```
============================================================
Submitting test file to IntelOwl via Middleware
============================================================
✓ Analysis submitted! Job ID: [varies]
✓ Analysis completed successfully
✓ Status: reported_without_fails
✓ File information extracted
✓ Multiple analyzers can be configured
```

## How Middleware Uses IntelOwl

### Architecture Flow

```
React Frontend → ThreatFlow Middleware → IntelOwl Backend
      ↓               ↓                        ↓
   Workflow JSON → Workflow Parser → IntelOwl API Calls
      ↓               ↓                        ↓
   File Upload → File Processing → Analysis Results
```

### Key Integration Points

1. **Authentication:**
   - Middleware reads `INTELOWL_API_KEY` from environment
   - Forwards token in all IntelOwl API requests

2. **Analyzer Discovery:**
   - Fetches available analyzers from `/api/analyzer`
   - Filters by type (file/observable)
   - Caches analyzer configurations

3. **Workflow Execution:**
   - Parses React Flow JSON workflows
   - Extracts analyzer sequence from nodes/edges
   - Submits files to IntelOwl with selected analyzers

4. **Job Monitoring:**
   - Polls IntelOwl job status endpoints
   - Aggregates results from multiple analyzers
   - Provides unified status API to frontend

5. **Error Handling:**
   - Translates IntelOwl errors to user-friendly messages
   - Handles network timeouts and API failures
   - Provides fallback responses

### Data Flow Example

1. **Frontend sends:**
   - Workflow JSON defining analysis pipeline
   - File to analyze

2. **Middleware processes:**
   - Validates workflow structure
   - Extracts analyzer list: `["File_Info", "ClamAV", "VirusTotal_v3_Get_File"]`
   - Submits to IntelOwl: `POST /api/analyze_file`

3. **IntelOwl processes:**
   - Runs each analyzer on the file
   - Returns job ID for status tracking

4. **Middleware monitors:**
   - Polls `GET /api/jobs/{job_id}` until completion
   - Formats results for frontend consumption

## Configuration Files

### .env (Middleware)
```env
INTELOWL_URL=http://localhost:80
INTELOWL_API_KEY=your_api_key_here
```

### requirements.txt (Middleware)
```
fastapi==0.109.0
uvicorn[standard]==0.27.0
python-multipart==0.0.9
pydantic==2.6.0
python-dotenv==1.0.1
httpx==0.26.0
pytest==8.0.0
pytest-asyncio==0.23.0
pyintelowl==5.1.0
requests==2.32.5
```

## Troubleshooting

### Common Issues

#### 1. IntelOwl Connection Failed
**Symptoms:** `Connection refused` or `500 Internal Server Error`
**Solutions:**
- Verify IntelOwl is running: `docker ps | grep intelowl`
- Check IntelOwl logs: `docker logs intelowl_nginx`
- Ensure correct URL in `.env`: `INTELOWL_URL=http://localhost:80`

#### 2. API Key Invalid
**Symptoms:** `401 Unauthorized` or `403 Forbidden`
**Solutions:**
- Verify API key in IntelOwl admin panel
- Check token format: `Authorization: Token YOUR_KEY`
- Regenerate token if expired

#### 3. Analyzer Not Working
**Symptoms:** Analyzer shows as failed in job results
**Solutions:**
- Check analyzer health: `/api/analyzer/{name}/health_check`
- Verify analyzer is enabled in IntelOwl admin
- Check analyzer-specific configuration (API keys, etc.)

#### 4. File Upload Issues
**Symptoms:** `413 Request Entity Too Large` or upload failures
**Solutions:**
- Check file size limits in IntelOwl configuration
- Verify multipart form data format
- Ensure file permissions allow reading

#### 5. Middleware Won't Start
**Symptoms:** `ModuleNotFoundError` or import errors
**Solutions:**
- Activate virtual environment: `source venv/bin/activate`
- Install dependencies: `pip install -r requirements.txt`
- Check Python version compatibility

### Debug Commands

```bash
# Check IntelOwl containers
docker ps | grep intelowl

# View IntelOwl logs
docker logs intelowl_nginx
docker logs intelowl_api

# Test IntelOwl API directly
curl -s "http://localhost/api/playbook" -H "Authorization: Token YOUR_KEY"

# Check middleware logs
python -m uvicorn app.main:app --log-level debug
```

## Security Considerations

### API Key Management
- Never commit API keys to version control
- Use environment variables for sensitive data
- Rotate keys regularly
- Use read-only tokens when possible

### Network Security
- IntelOwl should run on internal network only
- Use HTTPS in production
- Implement rate limiting
- Monitor API usage

### File Handling
- Validate file types and sizes
- Scan uploads with multiple analyzers
- Implement file retention policies
- Use secure temporary directories

## Performance Optimization

### IntelOwl Tuning
- Configure appropriate analyzer timeouts
- Enable analyzer caching where possible
- Use job queuing for high-volume analysis
- Monitor resource usage

### Middleware Optimization
- Implement connection pooling
- Cache analyzer configurations
- Use async processing for multiple jobs
- Implement request rate limiting

## Next Steps (Future Phases)

### Phase 2 Enhancements
- Advanced workflow engine with conditionals
- Real-time job progress streaming
- Batch analysis capabilities
- Custom analyzer integration

### Phase 3 Features
- Machine learning model integration
- Advanced threat intelligence correlation
- Automated response workflows
- Multi-tenant architecture

## Support and Resources

### Documentation Links
- **IntelOwl Docs:** https://intelowlproject.github.io/docs/
- **PyIntelOwl SDK:** https://intelowlproject.github.io/docs/pyintelowl/
- **FastAPI Docs:** https://fastapi.tiangolo.com/

### Community Resources
- **IntelOwl GitHub:** https://github.com/intelowlproject/IntelOwl
- **IntelOwl Slack:** https://honeynetpublic.slack.com/
- **ThreatFlow Repository:** [Your repo URL]

### Contact
For issues specific to this ThreatFlow integration, check the middleware logs and IntelOwl documentation first. Create issues in the appropriate repositories with detailed error logs and configuration information.

---

**Last Updated:** November 22, 2025
**Version:** Phase 1 - IntelOwl Backend Integration
**Status:** ✅ Fully Functional and Tested</content>
<parameter name="filePath">/home/anonymous/COLLEGE/ThreatFlow/phase1/README.md