# ThreatFlow - Visual Malware Analysis Platform

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/)
[![React](https://img.shields.io/badge/react-18+-blue.svg)](https://reactjs.org/)
[![Docker](https://img.shields.io/badge/docker-required-blue.svg)](https://www.docker.com/)

ThreatFlow is a comprehensive visual malware analysis platform that integrates IntelOwl's powerful analysis capabilities through an intuitive drag-and-drop workflow builder. Built in three phases, it provides SOC analysts and security researchers with a modern interface for automated threat intelligence gathering.

## 🏗️ Architecture Overview

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  React Frontend │    │ FastAPI Middleware│    │ IntelOwl Backend│
│   (Port 3000)   │◄──►│    (Port 8030)    │◄──►│   (Port 80)     │
│                 │    │                   │    │                 │
│ • Visual Canvas │    │ • API Orchestration│    │ • 200+ Analyzers│
│ • Drag & Drop   │    │ • Workflow Parser  │    │ • Docker Engine │
│ • Real-time UI  │    │ • Job Monitoring   │    │ • PostgreSQL    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## 📋 Project Phases

### Phase 1: IntelOwl Backend Integration ✅
**Core malware analysis engine with 200+ integrated analyzers**
- File analyzers: File_Info, ClamAV, VirusTotal, YARA, PEiD, APKiD, Androguard
- Observable analyzers: DNS, IP reputation, domain analysis, AbuseIPDB
- Docker-based analyzer isolation
- REST API for analysis requests
- Web-based management interface

### Phase 2: FastAPI Middleware ✅
**API orchestration layer between frontend and analysis backend**
- Translates React Flow workflows to IntelOwl analysis requests
- Unified REST API for frontend consumption
- File upload handling and job status monitoring
- Authentication and error management
- Health checks and analyzer discovery

### Phase 3: React Frontend ✅
**Visual drag-and-drop interface for building analysis workflows**
- React Flow-based canvas for workflow creation
- Custom nodes: File Upload, Analyzer Selection, Result Display
- Real-time job execution monitoring
- Professional Material-UI interface
- TypeScript for type safety

### Phase 4: Conditional Logic ✅ **NEW!**
**Dynamic workflow branching based on analysis results**
- Conditional nodes with if/then/else logic
- 6 condition types: malicious, suspicious, clean, success, failed, custom field
- Multi-stage workflow execution with automatic stage skipping
- Visual true/false branch outputs (green/red)
- Backwards compatible with linear workflows
- Sequential execution with dependency tracking

## 🚀 Quick Start Guide

### Prerequisites
- **Docker & Docker Compose** (for IntelOwl)
- **Python 3.12+** (for middleware)
- **Node.js 16+** (for frontend)
- **Git** (for cloning repositories)
- **4GB+ RAM** (recommended for Docker containers)

**Note:** IntelOwl uses Docker Compose V2 syntax (`docker compose` without hyphen) via their custom `start` script. If you have Docker Compose V1, the script will handle it automatically.

### IntelOwl Startup Options

IntelOwl provides different startup commands depending on your needs:

- **Basic startup:** `./start prod up` (minimal configuration)
- **With malware analyzers:** `./start prod up --malware_tools_analyzers` (recommended for ThreatFlow)
- **All analyzers:** `./start prod up --all_analyzers` (resource intensive)
- **With Elasticsearch:** `./start prod up --elastic` (for advanced search)

For ThreatFlow, we recommend `--malware_tools_analyzers` as it provides essential malware analysis tools without overwhelming your system.

### Step 1: Clone and Setup IntelOwl Backend

```bash
# Navigate to project root
cd /home/anonymous/COLLEGE/ThreatFlow

# Clone IntelOwl (if not already cloned)
git clone https://github.com/intelowlproject/IntelOwl.git
cd IntelOwl

# Start IntelOwl with malware tools analyzers
./start prod up --malware_tools_analyzers

# Wait for containers to start (may take 2-3 minutes)
# Verify IntelOwl is running
curl -s http://localhost | head -20
```

**Expected Output:** IntelOwl nginx welcome page

### Step 2: Configure IntelOwl API Access

1. **Access IntelOwl Web Interface:**
   - Open: http://localhost
   - Default credentials: `admin` / `admin`

2. **Generate API Token:**
   - Go to **Admin Panel** → **Tokens** → **Add Token**
   - Create token with full permissions
   - **Copy the token** (you'll need it for middleware config)

3. **Configure Analyzers (Optional but Recommended):**
   - Go to **Admin Panel** → **Analyzer Configs**
   - Configure VirusTotal API key if available
   - Enable desired analyzers

### Step 3: Setup ThreatFlow Middleware

```bash
# Navigate to middleware directory
cd /home/anonymous/COLLEGE/ThreatFlow/threatflow-middleware

# Create Python virtual environment
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# OR: venv\Scripts\activate  # Windows

# Install Python dependencies
pip install -r requirements.txt

# Create environment configuration
cat > .env << EOF
INTELOWL_URL=http://localhost:80
INTELOWL_API_KEY=your_api_token_here
EOF

# Replace 'your_api_token_here' with the token from Step 2

# Start middleware server
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8030
```

**Verification:**
```bash
# Test middleware health
curl http://localhost:8030/health
# Expected: {"status":"healthy","service":"ThreatFlow Middleware"}

# Test IntelOwl connectivity
curl http://localhost:8030/health/intelowl
# Expected: {"status":"connected","analyzers_available":205}
```

### Step 4: Setup React Frontend

```bash
# Open new terminal, navigate to frontend
cd /home/anonymous/COLLEGE/ThreatFlow/threatflow-frontend

# Install Node.js dependencies (if not already done)
npm install

# Start React development server
npm start
```

**Access the Application:**
- Frontend: http://localhost:3000
- Middleware API Docs: http://localhost:8030/docs
- IntelOwl Interface: http://localhost

## 🔄 Restarting the Application

After initial setup, use these commands to restart ThreatFlow when you reopen your laptop:

### Quick Restart Sequence

```bash
# Terminal 1: Start IntelOwl Backend
cd /home/anonymous/COLLEGE/ThreatFlow/IntelOwl
./start prod up --malware_tools_analyzers

# Terminal 2: Start ThreatFlow Middleware
cd /home/anonymous/COLLEGE/ThreatFlow/threatflow-middleware
source venv/bin/activate
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8030

# Terminal 3: Start React Frontend
cd /home/anonymous/COLLEGE/ThreatFlow/threatflow-frontend
npm start
```

### Verification Commands

```bash
# Quick check all services are running
curl -s http://localhost:8030/health && echo " ✅ Middleware OK"
curl -s http://localhost/health && echo " ✅ IntelOwl OK"
curl -s -I http://localhost:3000 | head -1 && echo " ✅ Frontend OK"
```

**Note:** IntelOwl may take 1-2 minutes to fully start. The middleware and frontend will be available immediately after running the commands above.

## 🎯 How to Use ThreatFlow

### Building Your First Analysis Workflow

1. **Open ThreatFlow Frontend** (http://localhost:3000)

2. **Add File Upload Node:**
   - Drag "📤 File Upload" from left sidebar onto canvas
   - Click the node to upload a test file (or drag file onto it)
   - Supported: EXE, PDF, DOC, APK, etc.

3. **Add Analyzer Nodes:**
   - Drag "🔍 Analyzer" nodes onto canvas
   - Select analyzers from dropdown:
     - **File_Info**: Basic file metadata
     - **ClamAV**: Antivirus scanning
     - **VirusTotal_v3_Get_File**: VirusTotal hash lookup
     - **YARA**: YARA rule matching
     - **PEiD**: PE file analysis

4. **Add Conditional Nodes (Phase 4 ✨):**
   - Drag "🔀 Conditional" node onto canvas
   - Connect analyzer output to conditional input
   - Connect conditional TRUE output (green) to downstream analyzers
   - Connect conditional FALSE output (red) to alternative path
   - Supports: malicious/clean verdicts, success/failure, custom conditions

5. **Connect the Nodes:**
   - Drag from output handle (right side) of File node
   - Connect to input handle (left side) of Analyzer nodes
   - Use conditional nodes to create branching logic

6. **Execute the Workflow:**
   - Click the "▶️ Execute" button at bottom
   - Monitor real-time progress in status panel
   - View detailed results when complete
   - See which conditional branches executed

### Example Workflow
```
File Upload → File_Info → ClamAV → Conditional: Is Malicious?
     ↓           ↓         ↓              ↓
  sample.exe  metadata  malware     ├─ TRUE → PE_Info → Capa_Info
                scan     detected    └─ FALSE → (skip deep analysis)
```

**Phase 4 Feature:** The conditional node enables dynamic branching based on ClamAV's verdict, automatically running deep analysis only for malicious files!

## 🔧 Configuration

### Environment Variables

#### Middleware (.env)
```bash
INTELOWL_URL=http://localhost:80          # IntelOwl API URL
INTELOWL_API_KEY=your_token_here          # API authentication token
DEBUG=true                                # Enable debug logging
```

#### Frontend (.env)
```bash
REACT_APP_API_URL=http://localhost:8030   # Middleware API URL
REACT_APP_POLL_INTERVAL=5000              # Status poll interval (ms)
REACT_APP_MAX_FILE_SIZE=104857600         # Max file size (100MB)
```

### IntelOwl Configuration
- **Database:** PostgreSQL (auto-configured via Docker)
- **Cache:** Redis (auto-configured via Docker)
- **Analyzers:** Configure API keys in Admin Panel
- **Security:** Change default admin password

## 🧪 Testing & Verification

### Test IntelOwl Backend
```bash
# Check containers
docker ps | grep intelowl

# Test API connectivity
curl -H "Authorization: Token YOUR_TOKEN" http://localhost/api/analyzer | jq '.count'
# Expected: 205+ analyzers

# Test file analysis (replace with real token)
curl -X POST http://localhost/api/analyze_file \
  -H "Authorization: Token YOUR_TOKEN" \
  -F "file=@test.exe" \
  -F "analyzers_requested=File_Info"
```

### Test Middleware API
```bash
# Health checks
curl http://localhost:8030/health
curl http://localhost:8030/health/intelowl

# Get analyzers
curl "http://localhost:8030/api/analyzers?type=file" | jq length
# Expected: 150+ file analyzers
```

### Test Frontend
```bash
# Check React app
curl -I http://localhost:3000
# Expected: HTTP/1.1 200 OK

# Check console for errors
# Open browser dev tools, look for network/API errors
```

## 🐛 Troubleshooting

### Common Issues & Solutions

#### 1. IntelOwl Won't Start
**Symptoms:** `./start prod up --malware_tools_analyzers` fails or containers exit
**Solutions:**
```bash
# Check Docker resources
docker system df

# View container logs
docker logs intelowl_nginx
docker logs intelowl_api

# Restart with clean state
./start prod down
./start prod up --malware_tools_analyzers
```

#### 2. API Key Authentication Fails
**Symptoms:** 401 Unauthorized errors
**Solutions:**
- Verify token in IntelOwl Admin Panel
- Check token format: `Authorization: Token YOUR_TOKEN`
- Regenerate token if expired
- Ensure no extra spaces in .env file

#### 3. Middleware Can't Connect to IntelOwl
**Symptoms:** `Connection refused` or empty analyzer list
**Solutions:**
```bash
# Test direct connection
curl http://localhost/api/playbook

# Check IntelOwl containers
docker ps | grep intelowl

# Verify INTELOWL_URL in .env
cat threatflow-middleware/.env
```

#### 4. Frontend Shows "Network Error"
**Symptoms:** Failed to load analyzers or execute workflows
**Solutions:**
- Ensure middleware is running on port 8030
- Check REACT_APP_API_URL in frontend/.env
- Restart frontend: `npm start`
- Check browser console for CORS errors

#### 5. File Upload Fails
**Symptoms:** Upload rejected or analysis fails
**Solutions:**
- Check file size limits (default: 100MB)
- Verify file type is supported
- Ensure file is not corrupted
- Check middleware logs for upload errors

#### 6. Workflow Execution Hangs
**Symptoms:** Status stays at "running" indefinitely
**Solutions:**
- Check IntelOwl analyzer health
- Verify selected analyzers are enabled
- Monitor IntelOwl logs for analyzer errors
- Try with fewer analyzers first

### Debug Commands
```bash
# Check all services
curl -s http://localhost:8030/health && echo " - Middleware OK"
curl -s http://localhost/health && echo " - IntelOwl OK"
curl -s -I http://localhost:3000 | head -1 && echo " - Frontend OK"

# View logs
docker logs intelowl_nginx --tail 50
# Middleware logs appear in terminal where uvicorn is running

# Test full workflow
echo "Testing complete pipeline..."
curl -X POST http://localhost:8030/api/execute \
  -F "workflow_json={\"nodes\":[], \"edges\":[]}" \
  -F "file=@test.txt" 2>/dev/null || echo "Workflow test failed"
```

## 📊 Available Analyzers

### File Analyzers (150+)
- **File_Info**: Basic file information and metadata
- **ClamAV**: Open-source antivirus engine
- **VirusTotal_v3_Get_File**: VirusTotal hash lookup
- **YARA**: Pattern matching with YARA rules
- **PEiD**: PE file packer/compiler detection
- **APKiD**: Android APK analysis
- **Androguard**: Android malware analysis
- **Qiling**: PE emulation and analysis
- **CAPA**: Behavioral analysis
- **Stringsifter**: String analysis and ranking

### Observable Analyzers (50+)
- **DNS**: DNS resolution and analysis
- **VirusTotal_v3_Get_Observable**: Domain/IP reputation
- **AbuseIPDB**: IP abuse reports
- **Shodan**: Internet-connected device search
- **AlienVault_OTX**: Threat intelligence
- **URLscan**: Website scanning and analysis

## 🔒 Security Considerations

### API Key Management
- Store API keys securely (environment variables)
- Use read-only tokens when possible
- Rotate keys regularly
- Never commit keys to version control

### Network Security
- IntelOwl should run on internal networks only
- Use HTTPS in production deployments
- Implement rate limiting
- Monitor API usage patterns

### File Handling
- Validate file types and sizes
- Scan uploads with multiple analyzers
- Implement file retention policies
- Use secure temporary directories

## 🚀 Production Deployment

### Docker Compose Setup
```yaml
# docker-compose.prod.yml
version: '3.8'
services:
  intelowl:
    image: intelowlproject/intelowl:latest
    # Production configuration...

  threatflow-middleware:
    build: ./threatflow-middleware
    environment:
      - INTELOWL_URL=http://intelowl:80
    # Production settings...

  threatflow-frontend:
    build: ./threatflow-frontend
    # Production build...
```

### Scaling Considerations
- **IntelOwl**: Scale analyzer containers horizontally
- **Middleware**: Use Gunicorn with multiple workers
- **Frontend**: Serve static files via nginx
- **Database**: Use managed PostgreSQL/Redis

## 📚 Documentation & Resources

### Official Documentation
- **IntelOwl Docs**: https://intelowlproject.github.io/docs/
- **PyIntelOwl SDK**: https://intelowlproject.github.io/docs/pyintelowl/
- **FastAPI Docs**: https://fastapi.tiangolo.com/
- **React Flow Docs**: https://reactflow.dev/

### Community Resources
- **IntelOwl GitHub**: https://github.com/intelowlproject/IntelOwl
- **IntelOwl Slack**: https://honeynetpublic.slack.com/
- **ThreatFlow Repository**: [Your repository URL]

### Phase 4 Documentation (Conditional Logic)
- **Complete Guide**: `Docs/README_PHASE-4.md` (5,000+ lines)
- **Quick Start**: `Docs/PHASE-4-QUICKSTART.md` (5-minute test)
- **Summary**: `Docs/PHASE-4-SUMMARY.md` (executive overview)
- **Checklist**: `Docs/PHASE-4-CHECKLIST.md` (implementation verification)

### API References
- **Middleware API**: http://localhost:8030/docs (Swagger)
- **IntelOwl API**: http://localhost/api/docs
- **Frontend Components**: Check component documentation

## 🤝 Contributing

1. **Fork the repository**
2. **Create feature branch**: `git checkout -b feature/new-analyzer`
3. **Make changes** with proper testing
4. **Update documentation**
5. **Submit pull request**

### Development Guidelines
- Follow existing code structure
- Add unit tests for new features
- Update documentation for API changes
- Use type hints (Python) and TypeScript types
- Handle errors gracefully

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **IntelOwl Project**: For the comprehensive malware analysis platform
- **Certego**: For developing and maintaining IntelOwl
- **The Honeynet Project**: For hosting the public demo
- **Open Source Community**: For the amazing tools and libraries

## 📞 Support

### Getting Help
1. **Check the troubleshooting section** above
2. **Review the phase-specific READMEs** in `/Docs/`
3. **Check IntelOwl documentation** for backend issues
4. **Open an issue** in the repository

### Contact Information
- **Project Issues**: GitHub Issues
- **IntelOwl Support**: IntelOwl Slack or GitHub
- **Security Issues**: Contact maintainers privately

---

**Last Updated:** November 23, 2025
**Version:** Phase 4 Complete - Conditional Logic Added
**Status:** ✅ Fully Functional with Dynamic Branching</content>
<parameter name="filePath">/home/anonymous/COLLEGE/ThreatFlow/README.md