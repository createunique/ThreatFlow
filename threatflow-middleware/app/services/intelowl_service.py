"""
IntelOwl API wrapper service
Uses pyintelowl v5.1.0 client
Also implements direct database query workaround for broken pagination
Enhanced with container detection for analyzer availability
Enterprise-grade error handling with schema-based validation and recovery
"""

from pyintelowl import IntelOwl, IntelOwlClientException
from app.config import settings
from app.services.analyzer_schema import schema_manager, AnalyzerSchemaManager
from app.services.condition_evaluator import ConditionEvaluatorMixin
import logging
import asyncio
import subprocess
import json
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


@dataclass
class EvaluationResult:
    """Result of condition evaluation with confidence and error tracking"""
    result: bool
    confidence: float  # 0.0 to 1.0
    errors: List[str]
    recovery_used: Optional[str]  # None, 'schema_fallback', 'generic_fallback', 'safe_default'
    evaluation_path: str  # Which evaluation strategy succeeded


class RecoveryStrategy(Enum):
    """Recovery strategies for condition evaluation failures"""
    PRIMARY = "primary"
    SCHEMA_FALLBACK = "schema_fallback"
    GENERIC_FALLBACK = "generic_fallback"
    SAFE_DEFAULT = "safe_default"

class IntelOwlService(ConditionEvaluatorMixin):
    """
    Wrapper around pyintelowl client for async operations
    Handles file analysis submission, result polling, and analyzer availability detection
    Enhanced with schema-based validation and multi-level error recovery
    """
    
    # Analyzers that are available in malware_tools_analyzers container
    MALWARE_TOOLS_ANALYZERS = {
        "File_Info", "ClamAV", "PE_Info", "Capa_Info", "Capa_Info_Shellcode",
        "Flare_Capa", "Yara", "Signature_Info", "Doc_Info", "PDF_Info", 
        "Xlm_Macro_Deobfuscator", "Rtf_Info", "Strings_Info", "BoxJS",
        "Androguard", "APKiD", "APK_Artifacts", "MobSF", "Quark_Engine"
    }
    
    # Analyzers requiring APK container
    APK_ANALYZERS = {
        "MobSF", "MobSF_Service", "Droidlysis", "Permhash", "Apkid"
    }
    
    # Analyzers requiring all_analyzers
    ADVANCED_ANALYZERS = {
        "SpeakEasy", "SpeakEasy_Shellcode", "DetectItEasy", "GoReSym", 
        "ELF_Info", "Blint", "Debloat", "PEframe_Scan", "OneNote_Info", 
        "Lnk_Info", "Suricata", "IocExtract", "IocFinder"
    }
    
    # Observable analyzers requiring observable_analyzers container
    OBSERVABLE_ANALYZERS = {
        "Classic_DNS", "CloudFlare_DNS", "CloudFlare_Malicious_Detector",
        "Google_DNS", "Quad9_DNS", "Quad9_Malicious_Detector",
        "DNS0_EU", "DNS0_EU_Malicious_Detector", "DNStwist", "AILTypoSquatting",
        "CheckDMARC", "Knock", "Thug_URL_Info", "CyberChef", "TorProject",
        "Feodo_Tracker", "FireHol_IPList", "Stratosphere_Blacklist", "TalosReputation",
        "AdGuard", "PhishingArmy", "Spamhaus_DROP", "VirusTotal_v3_Get_IP",
        "VirusTotal_v3_Get_Domain", "VirusTotal_v3_Get_URL", "VirusTotal_v3_Get_File"
    }
    
    def __init__(self):
        """Initialize IntelOwl client"""
        self.client = IntelOwl(
            settings.INTELOWL_API_KEY,
            settings.INTELOWL_URL,
            None,  # certificate
            None   # proxies
        )
        logger.info(f"IntelOwl client initialized for {settings.INTELOWL_URL}")
        
        # Cache for container detection (expires after 5 minutes)
        self._container_cache = None
        self._cache_time = None
    
    def _detect_installed_containers(self) -> Dict[str, bool]:
        """
        Detect which IntelOwl containers are running
        Returns dict with container availability status
        """
        try:
            logger.info("[INFO] Detecting installed IntelOwl containers...")
            
            result = subprocess.run(
                ["docker", "ps", "--format", "{{.Names}}"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            running_containers = result.stdout.strip().split('\n')
            logger.debug(f"[DEBUG] Running containers: {running_containers}")
            
            containers = {
                "core": True,  # Always available (uwsgi runs core)
                "malware_tools": "intelowl_malware_tools_analyzers" in running_containers,
                "apk_analyzers": "intelowl_apk_analyzers" in running_containers,
                "advanced_analyzers": any("advanced" in c for c in running_containers if c),
                "observable_analyzers": any("observable" in c for c in running_containers if c)
            }
            
            logger.info(f"[INFO] Container detection complete: {containers}")
            return containers
            
        except Exception as e:
            logger.error(f"[ERROR] Failed to detect containers: {e}")
            # Default to core only if detection fails
            return {
                "core": True,
                "malware_tools": False,
                "apk_analyzers": False,
                "advanced_analyzers": False,
                "observable_analyzers": False
            }
    
    def _is_analyzer_available(self, analyzer_name: str, containers: Dict[str, bool]) -> bool:
        """Check if an analyzer is available based on installed containers"""
        
        # Malware tools analyzers
        if analyzer_name in self.MALWARE_TOOLS_ANALYZERS:
            is_available = containers.get("malware_tools", False)
            logger.debug(f"[DEBUG] {analyzer_name}: malware_tools={is_available}")
            return is_available
        
        # APK analyzers
        if analyzer_name in self.APK_ANALYZERS:
            is_available = containers.get("apk_analyzers", False)
            logger.debug(f"[DEBUG] {analyzer_name}: apk_analyzers={is_available}")
            return is_available
        
        # Advanced analyzers
        if analyzer_name in self.ADVANCED_ANALYZERS:
            is_available = containers.get("advanced_analyzers", False)
            logger.debug(f"[DEBUG] {analyzer_name}: advanced_analyzers={is_available}")
            return is_available
        
        # Observable analyzers
        if analyzer_name in self.OBSERVABLE_ANALYZERS:
            is_available = containers.get("observable_analyzers", False)
            logger.debug(f"[DEBUG] {analyzer_name}: observable_analyzers={is_available}")
            return is_available
        
        # Unknown analyzers - assume not available
        logger.debug(f"[DEBUG] {analyzer_name}: UNKNOWN - assuming not available")
        return False
    
    def _get_unavailable_reason(self, analyzer_name: str) -> str:
        """Get reason why analyzer is not available"""
        if analyzer_name in self.APK_ANALYZERS:
            return "Requires APK analyzers container (--apk_analyzers)"
        elif analyzer_name in self.ADVANCED_ANALYZERS:
            return "Requires advanced analyzers container (--all_analyzers)"
        elif analyzer_name in self.OBSERVABLE_ANALYZERS:
            return "Requires observable analyzers container (--observable_analyzers)"
        else:
            return "Container not installed"
    
    async def submit_file_analysis(
        self,
        file_path: str,
        analyzers: List[str],
        file_name: str,
        tlp: str = "CLEAR"
    ) -> int:
        """
        Submit file for analysis to IntelOwl using official pyintelowl SDK
        
        Args:
            file_path: Local path to file
            analyzers: List of analyzer names to run
            file_name: Original filename
            tlp: Traffic Light Protocol (CLEAR, GREEN, AMBER, RED)
        
        Returns:
            job_id: IntelOwl job identifier
        """
        try:
            # Read file content as bytes
            with open(file_path, "rb") as f:
                file_binary = f.read()
            
            # Use official pyintelowl SDK method
            result = self.client.send_file_analysis_request(
                filename=file_name,
                binary=file_binary,
                analyzers_requested=analyzers,
                tlp=tlp,
                connectors_requested=[],
                runtime_configuration={},
                tags_labels=["threatflow"]
            )
            
            job_id = result["job_id"]
            logger.info(f"Analysis submitted to IntelOwl: Job ID {job_id} for analyzers {analyzers}")
            return job_id
            
        except IntelOwlClientException as e:
            logger.error(f"IntelOwl API error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during submission: {e}")
            raise
    
    async def get_job_status(self, job_id: int) -> Dict[str, Any]:
        """Get current status of an IntelOwl job using official SDK"""
        try:
            # Use official pyintelowl SDK method
            job = self.client.get_job_by_id(job_id)
            
            # Convert to expected format for middleware compatibility
            status_dict = {
                "job_id": job_id,
                "status": job.get("status", "unknown"),
                "progress": None,  # IntelOwl doesn't provide progress
                "analyzers_completed": len(job.get("analyzer_reports", [])),
                "analyzers_total": len(job.get("analyzers_to_execute", [])),
                "results": job if job.get("status") in ["reported_without_fails", "reported_with_fails", "failed"] else None
            }
            
            return status_dict
            
        except IntelOwlClientException as e:
            logger.error(f"IntelOwl API error getting job status: {e}")
            raise ValueError(f"Job {job_id} not found")
        except Exception as e:
            logger.error(f"Failed to get job status: {e}")
            raise ValueError(f"Job {job_id} not found")
    
    async def wait_for_completion(
        self,
        job_id: int,
        timeout: int = 300,
        poll_interval: int = 5
    ) -> Dict[str, Any]:
        """Poll job until completion or timeout"""
        max_attempts = timeout // poll_interval
        
        for attempt in range(max_attempts):
            status_dict = await self.get_job_status(job_id)
            
            if status_dict["results"]:
                logger.info(f"Job {job_id} completed after {attempt * poll_interval}s")
                return status_dict["results"]
            
            await asyncio.sleep(poll_interval)
        
        raise TimeoutError(f"Job {job_id} did not complete within {timeout}s")
    
    async def ask_analysis_availability(self, md5: str, analyzers: Optional[List[str]] = None, minutes_ago: Optional[int] = None) -> Dict[str, Any]:
        """
        Check if analysis already exists using official pyintelowl SDK
        
        Args:
            md5: MD5 hash of the file
            analyzers: Optional list of analyzers to check
            minutes_ago: Optional time limit for existing analysis
        
        Returns:
            Dict with availability status
        """
        try:
            result = self.client.ask_analysis_availability(
                md5=md5,
                analyzers=analyzers,
                minutes_ago=minutes_ago
            )
            return result
        except IntelOwlClientException as e:
            logger.error(f"IntelOwl ask availability error: {e}")
            raise
        except Exception as e:
            logger.error(f"ask_analysis_availability unexpected error: {e}")
            raise
    
    async def submit_file_to_playbook(self, file_path: str, playbook: str, file_name: str, tlp: str = "CLEAR", runtime_configuration: Optional[Dict] = None, tags: Optional[List[str]] = None) -> int:
        """
        Submit file to server-side Playbook using official pyintelowl SDK
        
        Args:
            file_path: Local path to file
            playbook: Name of the playbook to run
            file_name: Original filename
            tlp: Traffic Light Protocol
            runtime_configuration: Optional runtime config
            tags: Optional tags
        
        Returns:
            job_id: IntelOwl job identifier
        """
        runtime_configuration = runtime_configuration or {}
        tags = tags or []
        
        try:
            with open(file_path, "rb") as f:
                binary = f.read()
            
            result = self.client.send_file_analysis_playbook_request(
                filename=file_name,
                binary=binary,
                playbook_requested=playbook,
                tlp=tlp,
                runtime_configuration=runtime_configuration,
                tags_labels=tags
            )
            
            job_id = result.get("job_id")
            logger.info(f"Playbook analysis submitted: Job ID {job_id} for playbook {playbook}")
            return job_id
            
        except IntelOwlClientException as e:
            logger.error(f"IntelOwl playbook submit error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during playbook submission: {e}")
            raise
    
    async def download_sample_bytes(self, job_id: int) -> bytes:
        """
        Download sample bytes from a completed job using official pyintelowl SDK
        
        Args:
            job_id: Job ID to download sample from
        
        Returns:
            Raw bytes of the sample file
        """
        try:
            sample_bytes = self.client.download_sample(job_id)
            return sample_bytes
        except IntelOwlClientException as e:
            logger.error(f"IntelOwl download_sample error for job {job_id}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error downloading sample: {e}")
            raise
    
    def _fetch_all_analyzers_via_django(self) -> List[Dict[str, Any]]:
        """
        Fetch ALL 205 analyzers directly from IntelOwl's database using Django ORM.
        
        REASON: The REST API at `/api/analyzer` has a broken pagination implementation.
        It claims to have 205 total analyzers but pagination parameters (offset, page, limit)
        don't work - all pages return the same first 10 items.
        
        SOLUTION: Call Django's manage.py shell to query the database directly, bypassing
        the broken REST framework pagination logic.
        
        This mirrors how the Django admin panel works - it queries the database directly
        instead of going through the REST API.
        """
        try:
            logger.info("[INFO] Using DIRECT DATABASE QUERY to fetch all analyzers (bypassing broken REST API pagination)")
            
            # Use Docker exec to run Django shell inside IntelOwl container
            # This queries the database directly, getting all 205 analyzers
            docker_command = [
                "docker", "exec", "-i", "intelowl_uwsgi",
                "bash", "-c", 
                "cd /opt/deploy/intel_owl && python3 manage.py shell"
            ]
            
            # Django shell script to query all analyzers
            django_script = """
from api_app.analyzers_manager.models import AnalyzerConfig
import json

# Query ALL analyzers directly from database (no pagination!)
analyzers_qs = AnalyzerConfig.objects.all().values(
    'id', 'name', 'type', 'description', 'disabled',
    'docker_based', 'maximum_tlp', 'supported_filetypes',
    'not_supported_filetypes', 'observable_supported'
).order_by('name')

analyzers_list = list(analyzers_qs)

# Output as JSON to be parsed by middleware
result = {
    'count': len(analyzers_list),
    'results': analyzers_list,
    'source': 'django_database'
}

print(json.dumps(result))
"""
            
            # Execute Docker command with Django script as stdin
            process = subprocess.Popen(
                docker_command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            stdout, stderr = process.communicate(input=django_script, timeout=10)
            
            if process.returncode != 0:
                logger.error(f"[ERROR] Django query failed with return code {process.returncode}")
                logger.error(f"[ERROR] Stderr: {stderr}")
                raise RuntimeError(f"Django shell error: {stderr}")
            
            # Parse JSON output
            try:
                result = json.loads(stdout)
                analyzers_list = result.get("results", [])
                
                logger.info(f"[SUCCESS] Fetched {len(analyzers_list)} analyzers DIRECTLY from database!")
                logger.info(f"[INFO] Source: {result.get('source', 'unknown')}")
                
                return analyzers_list
                
            except json.JSONDecodeError as e:
                logger.error(f"[ERROR] Failed to parse JSON from Django output: {e}")
                logger.error(f"[ERROR] Output was: {stdout[:500]}")
                raise RuntimeError(f"Failed to parse Django output: {str(e)}")
            
        except subprocess.TimeoutExpired:
            logger.error("[ERROR] Django query timed out after 10 seconds")
            raise RuntimeError("Database query timeout")
        except Exception as e:
            logger.error(f"[ERROR] Direct database query failed: {type(e).__name__}: {e}")
            logger.warning("[WARNING] Will fall back to broken REST API pagination...")
            raise
    
    def _fetch_all_analyzers_paginated(self) -> List[Dict[str, Any]]:
        """
        Fetch all analyzers from IntelOwl by iterating through paginated API responses.
        
        ISSUE: IntelOwl's /api/analyzer pagination is broken - ALL pages return the same 10 items
        regardless of offset/page/page_number parameters.
        
        SOLUTION: Since pagination is broken in the REST API, we iterate through pages and 
        track unique analyzers by ID. When we stop getting new unique items, we're done.
        
        Reference: The admin interface works because Django's ORM directly queries the database,
        bypassing the broken REST API. We approximate this by requesting all pages to ensure
        we collect all unique analyzers.
        """
        try:
            url = f"{settings.INTELOWL_URL}/api/analyzer"
            all_unique_analyzers = {}  # Use dict to track by ID (deduplicate automatically)
            
            logger.info(f"[INFO] Fetching ALL analyzers from: {url}")
            logger.info("[INFO] Workaround: Iterating through ALL pages to collect unique analyzers")
            logger.info("[INFO] (IntelOwl pagination is broken - each page returns same data)")
            
            # Get first page to determine total
            response = self.client.session.get(
                url,
                headers={"Authorization": f"Token {settings.INTELOWL_API_KEY}"},
                params={"page": 1}
            )
            response.raise_for_status()
            response_data = response.json()
            
            total_count = response_data.get("count", 0)
            total_pages = response_data.get("total_pages", 0)
            
            logger.info(f"[INFO] API says: count={total_count}, total_pages={total_pages}")
            
            # Add first page results
            for analyzer in response_data.get("results", []):
                analyzer_id = analyzer.get("id")
                if analyzer_id:
                    all_unique_analyzers[analyzer_id] = analyzer
            
            logger.info(f"[INFO] Page 1: added {len(response_data.get('results', []))} items, unique so far: {len(all_unique_analyzers)}")
            
            # If total_pages is provided, iterate through all pages
            # Since pagination returns same data, we'll detect when we stop getting NEW analyzers
            if total_pages > 1:
                last_new_count = len(all_unique_analyzers)
                consecutive_no_new = 0
                
                for page_num in range(2, min(total_pages + 1, 50)):  # Cap at 50 to prevent infinite loops
                    response = self.client.session.get(
                        url,
                        headers={"Authorization": f"Token {settings.INTELOWL_API_KEY}"},
                        params={"page": page_num}
                    )
                    response.raise_for_status()
                    page_data = response.json()
                    
                    # Add results from this page
                    new_items_on_page = 0
                    for analyzer in page_data.get("results", []):
                        analyzer_id = analyzer.get("id")
                        if analyzer_id and analyzer_id not in all_unique_analyzers:
                            all_unique_analyzers[analyzer_id] = analyzer
                            new_items_on_page += 1
                    
                    current_unique = len(all_unique_analyzers)
                    logger.info(f"[INFO] Page {page_num}: {len(page_data.get('results', []))} items, {new_items_on_page} new unique, total unique: {current_unique}")
                    
                    # If no new items found for this page, pagination might be repeating
                    if new_items_on_page == 0:
                        consecutive_no_new += 1
                        if consecutive_no_new >= 3:  # If 3 consecutive pages have no new items, stop
                            logger.warning(f"[WARNING] No new analyzers found in last 3 pages - pagination appears to be repeating")
                            break
                    else:
                        consecutive_no_new = 0
            
            unique_analyzers_list = list(all_unique_analyzers.values())
            logger.info(f"[SUCCESS] Fetched {len(unique_analyzers_list)} UNIQUE analyzers (expected {total_count})")
            
            if len(unique_analyzers_list) < total_count:
                logger.warning(f"[WARNING] Got {len(unique_analyzers_list)} but API reports {total_count} total - pagination bug detected!")
            
            return unique_analyzers_list
                    
        except Exception as e:
            logger.error(f"[ERROR] Error fetching analyzers: {type(e).__name__}: {e}")
            import traceback
            logger.error(f"[ERROR] Traceback: {traceback.format_exc()}")
            raise
    
    async def get_available_analyzers(self, analyzer_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Get list of available and unavailable analyzers from IntelOwl
        
        Args:
            analyzer_type: Filter by type ('file' or 'observable')
        
        Returns:
            Dict with 'available', 'unavailable', and 'summary' keys
            {
                "available": [{"name": "ClamAV", "type": "file", ...}, ...],
                "unavailable": [{"name": "MobSF", "type": "file", "unavailable_reason": "..."}, ...],
                "summary": {
                    "available_count": 15,
                    "unavailable_count": 189,
                    "containers_detected": {...}
                }
            }
        """
        try:
            logger.info("[INFO] Fetching analyzers with availability detection...")
            
            # Detect installed containers
            containers = self._detect_installed_containers()
            logger.info(f"[INFO] Containers detected: {containers}")
            
            # Run the synchronous request in a thread pool
            loop = asyncio.get_event_loop()
            
            # Try direct database query FIRST (most reliable)
            try:
                logger.info("[INFO] Attempting direct database query...")
                all_analyzers = await loop.run_in_executor(
                    None,
                    self._fetch_all_analyzers_via_django
                )
                logger.info(f"[SUCCESS] Got {len(all_analyzers)} analyzers via direct database query!")
                
            except Exception as db_error:
                logger.warning(f"[WARNING] Direct database query failed: {db_error}")
                logger.warning("[WARNING] Falling back to REST API pagination workaround...")
                
                # Fall back to REST API with pagination workaround
                all_analyzers = await loop.run_in_executor(
                    None,
                    self._fetch_all_analyzers_paginated
                )
                logger.info(f"[INFO] Got {len(all_analyzers)} analyzers via REST API")
            
            logger.info(f"[INFO] Total analyzers fetched: {len(all_analyzers)}")
            
            # Filter by type if specified
            if analyzer_type:
                before_filter = len(all_analyzers)
                all_analyzers = [
                    a for a in all_analyzers
                    if a.get("type") == analyzer_type
                ]
                logger.info(f"[INFO] Filtered {before_filter} → {len(all_analyzers)} by type '{analyzer_type}'")
            
            # Separate into available and unavailable
            available_analyzers = []
            unavailable_analyzers = []
            
            for analyzer in all_analyzers:
                # Skip disabled analyzers
                if analyzer.get("disabled", False):
                    logger.debug(f"[DEBUG] Skipping disabled analyzer: {analyzer.get('name')}")
                    continue
                
                analyzer_name = analyzer["name"]
                is_available = self._is_analyzer_available(analyzer_name, containers)
                
                analyzer_dict = {
                    "id": analyzer.get("id"),
                    "name": analyzer_name,
                    "type": analyzer.get("type", "unknown"),
                    "description": analyzer.get("description", ""),
                    "supported_filetypes": analyzer.get("supported_filetypes", []),
                    "not_supported_filetypes": analyzer.get("not_supported_filetypes", []),
                    "observable_supported": analyzer.get("observable_supported", []),
                }
                
                if is_available:
                    analyzer_dict["available"] = True
                    available_analyzers.append(analyzer_dict)
                    logger.debug(f"[DEBUG] {analyzer_name} -> AVAILABLE")
                else:
                    analyzer_dict["available"] = False
                    analyzer_dict["unavailable_reason"] = self._get_unavailable_reason(analyzer_name)
                    unavailable_analyzers.append(analyzer_dict)
                    logger.debug(f"[DEBUG] {analyzer_name} -> UNAVAILABLE ({analyzer_dict['unavailable_reason']})")
            
            logger.info(f"[SUCCESS] Analysis complete: {len(available_analyzers)} available, {len(unavailable_analyzers)} unavailable")
            
            result = {
                "available": available_analyzers,
                "unavailable": unavailable_analyzers,
                "summary": {
                    "available_count": len(available_analyzers),
                    "unavailable_count": len(unavailable_analyzers),
                    "total_count": len(available_analyzers) + len(unavailable_analyzers),
                    "containers_detected": containers
                }
            }
            
            logger.info(f"[SUCCESS] Returning analyzer data: {result['summary']}")
            return result
            
        except Exception as e:
            logger.error(f"[ERROR] Failed to fetch analyzers: {type(e).__name__}: {e}")
            import traceback
            logger.error(traceback.format_exc())
            
            # Return empty structure with error
            return {
                "available": [],
                "unavailable": [],
                "summary": {
                    "available_count": 0,
                    "unavailable_count": 0,
                    "total_count": 0,
                    "error": str(e),
                    "containers_detected": {}
                }
            }
    
    async def execute_workflow_with_conditionals(
        self,
        file_path: str,
        stages: List[Dict[str, Any]],
        file_name: str,
        tlp: str = "CLEAR"
    ) -> Dict[str, Any]:
        """
        Execute workflow with conditional logic (Phase 4)
        
        Args:
            file_path: Local path to file
            stages: List of execution stages from parser
            file_name: Original filename
            tlp: Traffic Light Protocol
        
        Returns:
            {
                "job_ids": [1, 2, 3],
                "all_results": {
                    "stage_0": {...},
                    "stage_1": {...}
                },
                "total_stages_executed": 2,
                "skipped_stages": [2]
            }
        """
        all_results = {}
        job_ids = []
        executed_stages = []
        skipped_stages = []
        
        logger.info(f"Starting conditional workflow execution with {len(stages)} total stages")
        
        for stage in stages:
            stage_id = stage["stage_id"]
            depends_on = stage.get("depends_on")
            condition = stage.get("condition")
            analyzers = stage["analyzers"]
            target_nodes = stage.get("target_nodes", [])
            
            # Check if stage should execute
            if depends_on is None:
                # Stage 0: Always execute
                should_execute = True
                logger.info(f"📋 Stage {stage_id}: Initial stage, executing analyzers={analyzers}")
            else:
                # Conditional stage: evaluate condition
                should_execute = self._evaluate_condition(condition, all_results)
                condition_desc = condition.get('type', 'unknown')
                if condition.get('negate'):
                    condition_desc = f"NOT {condition_desc}"
                logger.info(
                    f"🔀 Stage {stage_id}: Condition '{condition_desc}' evaluated to {should_execute}, "
                    f"target_nodes={target_nodes}"
                )
            
            if should_execute:
                # Check if stage has analyzers to execute
                if not analyzers or len(analyzers) == 0:
                    # Result-only stage (no analyzers, just routing to result nodes)
                    logger.info(
                        f"✅ Stage {stage_id}: Result-only (no analyzers), routing to {target_nodes}"
                    )
                    all_results[f"stage_{stage_id}"] = {
                        "stage_id": stage_id,
                        "type": "result_only",
                        "target_nodes": target_nodes,
                        "message": "Routing to result nodes based on condition"
                    }
                    executed_stages.append(stage_id)
                    continue
                
                try:
                    logger.info(f"▶️  Stage {stage_id}: Executing with analyzers={analyzers}")
                    
                    # Submit analysis
                    job_id = await self.submit_file_analysis(
                        file_path=file_path,
                        analyzers=analyzers,
                        file_name=file_name,
                        tlp=tlp
                    )
                    
                    job_ids.append(job_id)
                    
                    # Wait for completion
                    stage_results = await self.wait_for_completion(job_id)
                    all_results[f"stage_{stage_id}"] = stage_results
                    executed_stages.append(stage_id)
                    
                    logger.info(f"✅ Stage {stage_id} completed successfully")
                    
                except Exception as e:
                    logger.error(f"❌ Stage {stage_id} failed: {e}")
                    all_results[f"stage_{stage_id}"] = {"error": str(e)}
            else:
                logger.info(
                    f"⏭️  Stage {stage_id}: SKIPPED (condition not met), "
                    f"would have routed to {target_nodes}"
                )
                skipped_stages.append(stage_id)
                continue  # CRITICAL: Actually skip this stage
        
        return {
            "job_ids": job_ids,
            "all_results": all_results,
            "total_stages_executed": len(executed_stages),
            "executed_stages": executed_stages,
            "skipped_stages": skipped_stages
        }
    
    def _evaluate_condition(
        self,
        condition: Optional[Dict[str, Any]],
        results: Dict[str, Any]
    ) -> bool:
        """
        Evaluate condition with enterprise-grade error handling and recovery
        
        Uses multi-level fallback strategy:
        1. Primary: Direct field evaluation
        2. Schema Fallback: Use schema-defined patterns
        3. Generic Fallback: Pattern matching
        4. Safe Default: Conservative assumption
        """
        if not condition:
            return True
        
        # Check for negate flag (for FALSE branches)
        should_negate = condition.get("negate", False)
        
        # Handle legacy NOT wrapper for backwards compatibility
        if condition.get("type") == "NOT":
            inner_condition = condition.get("inner")
            if inner_condition:
                # Evaluate inner condition and negate result
                inner_result = self._evaluate_condition(inner_condition, results)
                logger.debug(f"NOT condition: inner={inner_result}, result={not inner_result}")
                return not inner_result
            else:
                logger.warning("NOT condition missing 'inner' field, defaulting to False")
                return False
        
        # Evaluate the condition
        eval_result = self._evaluate_with_recovery(condition, results)
        
        # Log evaluation details
        if eval_result.confidence < 1.0:
            logger.warning(
                f"Condition evaluation used fallback strategy: {eval_result.recovery_used}, "
                f"confidence: {eval_result.confidence}, errors: {eval_result.errors}"
            )
        
        # Apply negation if needed
        final_result = not eval_result.result if should_negate else eval_result.result
        
        if should_negate:
            logger.debug(f"Negated condition: original={eval_result.result}, final={final_result}")
        
        return final_result
    
    def _evaluate_with_recovery(
        self,
        condition: Dict[str, Any],
        results: Dict[str, Any]
    ) -> EvaluationResult:
        """
        Evaluate condition with multiple fallback strategies
        Returns detailed evaluation result with confidence scoring
        """
        errors = []
        
        # Validate condition structure
        is_valid, validation_errors = schema_manager.validate_condition(condition)
        if not is_valid:
            logger.warning(f"Condition validation failed: {validation_errors}")
            errors.extend(validation_errors)
        
        logger.debug(f"Evaluating condition: {condition}")
        logger.debug(f"Available results: {list(results.keys())}")
        
        cond_type = condition.get("type")
        source_analyzer = condition.get("source_analyzer")
        
        # Handle NOT condition
        if cond_type == "NOT":
            inner_condition = condition.get("inner")
            inner_result = self._evaluate_with_recovery(inner_condition, results)
            return EvaluationResult(
                result=not inner_result.result,
                confidence=inner_result.confidence,
                errors=inner_result.errors,
                recovery_used=inner_result.recovery_used,
                evaluation_path=f"NOT({inner_result.evaluation_path})"
            )
        
        # Find analyzer results
        analyzer_report = self._find_analyzer_report(source_analyzer, results)
        
        if not analyzer_report:
            logger.warning(f"Analyzer {source_analyzer} results not found")
            return EvaluationResult(
                result=False,
                confidence=0.0,
                errors=[f"Analyzer {source_analyzer} results not found"],
                recovery_used=RecoveryStrategy.SAFE_DEFAULT.value,
                evaluation_path="analyzer_not_found"
            )
        
        # Strategy 1: PRIMARY - Direct evaluation
        try:
            result = self._evaluate_primary(condition, analyzer_report)
            return EvaluationResult(
                result=result,
                confidence=1.0,
                errors=[],
                recovery_used=None,
                evaluation_path="primary"
            )
        except Exception as e:
            logger.debug(f"Primary evaluation failed: {e}")
            errors.append(f"Primary: {str(e)}")
        
        # Strategy 2: SCHEMA FALLBACK - Use schema-defined patterns
        try:
            result = self._evaluate_with_schema_fallback(condition, analyzer_report)
            return EvaluationResult(
                result=result,
                confidence=0.8,
                errors=errors,
                recovery_used=RecoveryStrategy.SCHEMA_FALLBACK.value,
                evaluation_path="schema_fallback"
            )
        except Exception as e:
            logger.debug(f"Schema fallback failed: {e}")
            errors.append(f"Schema: {str(e)}")
        
        # Strategy 3: GENERIC FALLBACK - Pattern matching
        try:
            result = self._evaluate_generic_fallback(condition, analyzer_report)
            return EvaluationResult(
                result=result,
                confidence=0.5,
                errors=errors,
                recovery_used=RecoveryStrategy.GENERIC_FALLBACK.value,
                evaluation_path="generic_fallback"
            )
        except Exception as e:
            logger.debug(f"Generic fallback failed: {e}")
            errors.append(f"Generic: {str(e)}")
        
        # Strategy 4: SAFE DEFAULT
        result = self._get_safe_default(condition)
        return EvaluationResult(
            result=result,
            confidence=0.0,
            errors=errors,
            recovery_used=RecoveryStrategy.SAFE_DEFAULT.value,
            evaluation_path="safe_default"
        )
    
    def _find_analyzer_report(self, analyzer_name: str, results: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Find analyzer report from results"""
        for stage_key, stage_data in results.items():
            if isinstance(stage_data, dict) and "analyzer_reports" in stage_data:
                for report in stage_data.get("analyzer_reports", []):
                    if report.get("name") == analyzer_name:
                        return report
        return None
    
    def _evaluate_primary(self, condition: Dict[str, Any], analyzer_report: Dict[str, Any]) -> bool:
        """
        Primary evaluation strategy - direct field access
        
        UPDATED: Based on actual IntelOwl analyzer responses from comprehensive testing.
        Field paths are verified against real response data.
        """
        cond_type = condition.get("type")
        report_data = analyzer_report.get("report", {})
        analyzer_name = analyzer_report.get("name", "")
        
        # Verdict-based conditions
        if cond_type == "verdict_malicious":
            return self._check_malicious(analyzer_name, report_data, analyzer_report)
        
        elif cond_type == "verdict_suspicious":
            return self._check_suspicious(analyzer_name, report_data, analyzer_report)
        
        elif cond_type == "verdict_clean":
            return self._check_clean(analyzer_name, report_data, analyzer_report)
        
        elif cond_type == "analyzer_success":
            status = analyzer_report.get("status")
            return status == "SUCCESS"
        
        elif cond_type == "analyzer_failed":
            status = analyzer_report.get("status")
            return status != "SUCCESS"
        
        # Field-based conditions
        elif cond_type in ["field_equals", "field_contains", "field_greater_than", "field_less_than"]:
            field_path = condition.get("field_path", "")
            expected_value = condition.get("expected_value")
            
            if not field_path or expected_value is None:
                raise ValueError(f"Field path or expected value missing for {cond_type}")
            
            # Navigate JSON path using mixin method
            current = self._navigate_field_path(report_data, field_path)
            
            if current is None:
                raise ValueError(f"Field path '{field_path}' not found in report")
            
            if cond_type == "field_equals":
                result = current == expected_value
                logger.debug(f"field_equals: {current} == {expected_value} -> {result}")
                return result
            elif cond_type == "field_contains":
                result = self._check_contains(current, expected_value)
                logger.debug(f"field_contains: '{expected_value}' in '{current}' -> {result}")
                return result
            elif cond_type == "field_greater_than":
                try:
                    result = float(current) > float(expected_value)
                    logger.debug(f"field_greater_than: {current} > {expected_value} -> {result}")
                    return result
                except (ValueError, TypeError):
                    raise ValueError(f"Cannot compare {current} > {expected_value}")
            elif cond_type == "field_less_than":
                try:
                    result = float(current) < float(expected_value)
                    logger.debug(f"field_less_than: {current} < {expected_value} -> {result}")
                    return result
                except (ValueError, TypeError):
                    raise ValueError(f"Cannot compare {current} < {expected_value}")
        
        elif cond_type == "yara_rule_match":
            # Check if YARA analyzer found matches
            # Real response: Multiple rule set fields, each containing array of matches
            # Also check data_model.signatures
            
            # Check data_model.signatures first (from job level)
            job_data_model = analyzer_report.get("data_model", {})
            signatures = job_data_model.get("signatures", [])
            if isinstance(signatures, list) and len(signatures) > 0:
                logger.debug(f"YARA data_model.signatures: {len(signatures)} matches -> True")
                return True
            
            # Check individual rule set fields
            yara_rule_sets = [
                "yara-rules_rules", "elastic_protections-artifacts",
                "advanced-threat-research_yara-rules", "neo23x0_signature-base",
                "bartblaze_yara-rules", "intezer_yara-rules", "inquest_yara-rules"
            ]
            
            for rule_set in yara_rule_sets:
                matches = report_data.get(rule_set, [])
                if isinstance(matches, list) and len(matches) > 0:
                    # Filter out utility rules
                    for match in matches:
                        rule_path = match.get("path", "") if isinstance(match, dict) else ""
                        if "utils/" not in rule_path:
                            logger.debug(f"YARA {rule_set} match found -> True")
                            return True
            
            logger.debug("No significant YARA matches found -> False")
            return False
        
        elif cond_type == "capability_detected":
            # Check if analyzer detected specific capabilities
            capabilities = report_data.get("capabilities", [])
            expected_capability = condition.get("expected_value", "")
            if isinstance(capabilities, list):
                result = expected_capability in capabilities
                logger.debug(f"capability_detected: '{expected_capability}' in {capabilities} -> {result}")
                return result
            logger.debug(f"capabilities field not found or not a list: {capabilities}")
            return False
        
        elif cond_type == "has_detections":
            # Check if analyzer has any detections
            # Use analyzer-specific detection fields based on real responses
            analyzer_lower = analyzer_name.lower() if analyzer_name else ""
            
            # ClamAV: report.detections[]
            if analyzer_lower == "clamav":
                detections = report_data.get("detections", [])
                has_det = isinstance(detections, list) and len(detections) > 0
                logger.debug(f"ClamAV has_detections: {has_det}")
                return has_det
            
            # Yara: Check data_model.signatures and rule set fields
            if analyzer_lower == "yara":
                job_data_model = analyzer_report.get("data_model", {})
                signatures = job_data_model.get("signatures", [])
                if isinstance(signatures, list) and len(signatures) > 0:
                    logger.debug(f"Yara has_detections via signatures: True")
                    return True
                # Check rule sets
                for key, value in report_data.items():
                    if isinstance(value, list) and len(value) > 0:
                        logger.debug(f"Yara has_detections via {key}: True")
                        return True
                return False
            
            # Doc_Info: mraptor != "ok"
            if analyzer_lower == "doc_info":
                mraptor = report_data.get("mraptor", "")
                has_det = mraptor != "ok" and mraptor != ""
                logger.debug(f"Doc_Info has_detections (mraptor={mraptor}): {has_det}")
                return has_det
            
            # Quark_Engine: crimes[] or score > 0
            if analyzer_lower == "quark_engine":
                crimes = report_data.get("crimes", [])
                score = report_data.get("total_score", 0)
                has_det = (isinstance(crimes, list) and len(crimes) > 0) or score > 0
                logger.debug(f"Quark_Engine has_detections: {has_det}")
                return has_det
            
            # APK_Artifacts: permissions[] (any permission counts as detection)
            if analyzer_lower == "apk_artifacts":
                permissions = report_data.get("permission", [])
                has_det = isinstance(permissions, list) and len(permissions) > 0
                logger.debug(f"APK_Artifacts has_detections (permissions): {has_det}")
                return has_det
            
            # Rtf_Info: ole_objects[] or follina[]
            if analyzer_lower == "rtf_info":
                rtfobj = report_data.get("rtfobj", {})
                ole_objects = rtfobj.get("ole_objects", []) if isinstance(rtfobj, dict) else []
                follina = report_data.get("follina", [])
                has_det = (isinstance(ole_objects, list) and len(ole_objects) > 0) or \
                          (isinstance(follina, list) and len(follina) > 0)
                logger.debug(f"Rtf_Info has_detections: {has_det}")
                return has_det
            
            # BoxJS: IOC.json[]
            if analyzer_lower == "boxjs":
                ioc = report_data.get("IOC.json", [])
                has_det = isinstance(ioc, list) and len(ioc) > 0
                logger.debug(f"BoxJS has_detections: {has_det}")
                return has_det
            
            # APKiD: files[]
            if analyzer_lower == "apkid":
                files = report_data.get("files", [])
                has_det = isinstance(files, list) and len(files) > 0
                logger.debug(f"APKiD has_detections: {has_det}")
                return has_det
            
            # Generic fallback: check common detection fields
            detection_fields = ["detections", "signatures", "rules", "alerts", "threats", "matches", "crimes"]
            for field in detection_fields:
                if field in report_data:
                    value = report_data[field]
                    if isinstance(value, list) and len(value) > 0:
                        logger.debug(f"Generic has_detections via {field}: True")
                        return True
            
            logger.debug(f"has_detections: No detections found -> False")
            return False
        
        elif cond_type == "has_errors":
            # Check if analyzer report contains errors
            errors = report_data.get("errors", [])
            if isinstance(errors, list) and len(errors) > 0:
                logger.debug(f"Errors found: {errors} -> True")
                return True
            logger.debug("No errors found -> False")
            return False
        
        elif cond_type == "custom_field":
            # Legacy support for custom field conditions
            field_path = condition.get("field_path", "")
            expected_value = condition.get("expected_value")
            
            # Navigate JSON path using mixin method
            current = self._navigate_field_path(report_data, field_path)
            return current == expected_value
        
        # Unknown condition type
        raise ValueError(f"Unknown condition type: {cond_type}")
    
    def _check_malicious(self, analyzer_name: str, report_data: Dict[str, Any], analyzer_report: Dict[str, Any]) -> bool:
        """
        Check if analyzer detected malware/malicious content.
        
        VERIFIED FIELD PATHS from actual IntelOwl responses:
        - ClamAV: report.detections[] - array of detection names (e.g., ['Eicar-Signature'])
        - Yara: Check multiple rule set fields for any matches
        - Doc_Info: report.mraptor = "suspicious" indicates macro malware
        - Quark_Engine: report.threat_level and report.total_score
        - APK_Artifacts: report.permission[] for dangerous permissions
        - BoxJS: report.IOC.json for indicators of compromise
        - File_Info, Strings_Info: metadata only, cannot detect malware
        """
        analyzer_lower = analyzer_name.lower() if analyzer_name else ""
        
        # ====== ClamAV ======
        # Real response: {"detections": ["Eicar-Signature"], "raw_report": "...FOUND..."}
        if analyzer_lower == "clamav":
            detections = report_data.get("detections", [])
            if isinstance(detections, list) and len(detections) > 0:
                logger.debug(f"ClamAV detections: {detections} -> True")
                return True
            # Also check raw_report for "Infected files: X" where X > 0
            raw_report = report_data.get("raw_report", "")
            if "FOUND" in raw_report:
                logger.debug(f"ClamAV raw_report contains 'FOUND' -> True")
                return True
            logger.debug(f"ClamAV no detections -> False")
            return False
        
        # ====== Yara ======
        # Real response: Multiple fields like 'yara-rules_rules', 'elastic_protections-artifacts', etc.
        # Each field is an array of matched rules. Check if ANY field has matches.
        # Also check data_model.evaluation == "malicious"
        if analyzer_lower == "yara":
            # Check data_model.evaluation first (from job level)
            job_data_model = analyzer_report.get("data_model", {})
            if job_data_model.get("evaluation") == "malicious":
                logger.debug(f"Yara data_model.evaluation = 'malicious' -> True")
                return True
            
            # Check data_model.signatures
            signatures = job_data_model.get("signatures", [])
            if isinstance(signatures, list) and len(signatures) > 0:
                logger.debug(f"Yara data_model.signatures has {len(signatures)} matches -> True")
                return True
            
            # Check individual rule set fields in report
            # These are the actual field names from real responses
            yara_rule_sets = [
                "yara-rules_rules",
                "elastic_protections-artifacts", 
                "advanced-threat-research_yara-rules",
                "neo23x0_signature-base",
                "bartblaze_yara-rules",
                "intezer_yara-rules",
                "inquest_yara-rules",
                "reversinglabs_reversinglabs-yara-rules",
                "mandiant_red_team_tool_countermeasures",
                "dr4k0nia_yara-rules",
                "embee-research_yara",
                "fboldewin_yara-rules",
                "jpcertcc_jpcert-yara",
                "sbousseaden_yarahunts",
                "strangerealintel_dailyioc",
                "stratosphereips_yara-rules",
                "sifalcon_detection",
                "elceef_yara-rulz",
                "yaraify-api.abuse.ch_yaraify-rules"
            ]
            
            for rule_set in yara_rule_sets:
                matches = report_data.get(rule_set, [])
                if isinstance(matches, list) and len(matches) > 0:
                    # Check if it's a security-relevant match (not just domain.yar utility rule)
                    for match in matches:
                        rule_path = match.get("path", "") if isinstance(match, dict) else ""
                        rule_match = match.get("match", "") if isinstance(match, dict) else ""
                        # Skip utility rules that aren't malware indicators
                        if "utils/domain.yar" in rule_path or "utils/url.yar" in rule_path:
                            continue
                        # This is a real malware detection
                        logger.debug(f"Yara {rule_set}: {rule_match} -> True")
                        return True
            
            logger.debug(f"Yara no significant matches -> False")
            return False
        
        # ====== Doc_Info ======
        # Real response: {"mraptor": "suspicious"} for malicious macros, "ok" for clean
        if analyzer_lower == "doc_info":
            mraptor = report_data.get("mraptor", "")
            if mraptor == "suspicious":
                logger.debug(f"Doc_Info mraptor = 'suspicious' -> True")
                return True
            # Check olevba for suspicious VBA keywords
            olevba = report_data.get("olevba", {})
            if isinstance(olevba, dict):
                macro_data = olevba.get("macro_data", [])
                for macro in macro_data:
                    if isinstance(macro, dict):
                        suspicious_keywords = macro.get("suspicious_keywords", [])
                        if suspicious_keywords:
                            logger.debug(f"Doc_Info olevba suspicious keywords: {suspicious_keywords} -> True")
                            return True
            logger.debug(f"Doc_Info no suspicious indicators -> False")
            return False
        
        # ====== Quark_Engine ======
        # Real response: {"threat_level": "Low Risk", "total_score": 0, "crimes": []}
        if analyzer_lower == "quark_engine":
            threat_level = report_data.get("threat_level", "")
            total_score = report_data.get("total_score", 0)
            crimes = report_data.get("crimes", [])
            
            # Threat level indicators
            high_risk_levels = ["High Risk", "Critical", "Malicious"]
            if threat_level in high_risk_levels:
                logger.debug(f"Quark_Engine threat_level = '{threat_level}' -> True")
                return True
            
            # Score-based detection (score > 50 is concerning)
            if isinstance(total_score, (int, float)) and total_score > 50:
                logger.debug(f"Quark_Engine total_score = {total_score} > 50 -> True")
                return True
            
            # Crimes detected
            if isinstance(crimes, list) and len(crimes) > 0:
                logger.debug(f"Quark_Engine crimes detected: {len(crimes)} -> True")
                return True
            
            logger.debug(f"Quark_Engine threat_level={threat_level}, score={total_score} -> False")
            return False
        
        # ====== APK_Artifacts ======
        # Real response: {"permission": ["android.permission.INTERNET", "android.permission.READ_SMS"]}
        if analyzer_lower == "apk_artifacts":
            permissions = report_data.get("permission", [])
            dangerous_permissions = [
                "android.permission.READ_SMS",
                "android.permission.SEND_SMS", 
                "android.permission.RECEIVE_SMS",
                "android.permission.READ_CONTACTS",
                "android.permission.CALL_PHONE",
                "android.permission.RECORD_AUDIO",
                "android.permission.CAMERA",
                "android.permission.READ_CALL_LOG",
                "android.permission.PROCESS_OUTGOING_CALLS"
            ]
            for perm in permissions:
                if perm in dangerous_permissions:
                    logger.debug(f"APK_Artifacts dangerous permission: {perm} -> True")
                    return True
            logger.debug(f"APK_Artifacts no dangerous permissions -> False")
            return False
        
        # ====== APKiD ======
        # Real response: {"files": [], "apkid_version": "..."}
        # files contains packer/obfuscator detections
        if analyzer_lower == "apkid":
            files = report_data.get("files", [])
            if isinstance(files, list) and len(files) > 0:
                logger.debug(f"APKiD files detected: {files} -> True")
                return True
            logger.debug(f"APKiD no detections -> False")
            return False
        
        # ====== Rtf_Info ======
        # Real response: {"rtfobj": {"ole_objects": []}, "follina": []}
        if analyzer_lower == "rtf_info":
            rtfobj = report_data.get("rtfobj", {})
            ole_objects = rtfobj.get("ole_objects", []) if isinstance(rtfobj, dict) else []
            follina = report_data.get("follina", [])
            
            if isinstance(ole_objects, list) and len(ole_objects) > 0:
                logger.debug(f"Rtf_Info OLE objects: {len(ole_objects)} -> True")
                return True
            if isinstance(follina, list) and len(follina) > 0:
                logger.debug(f"Rtf_Info Follina exploit detected -> True")
                return True
            logger.debug(f"Rtf_Info no malicious content -> False")
            return False
        
        # ====== BoxJS ======
        # Real response: {"IOC.json": [...], "snippets.json": {...}}
        if analyzer_lower == "boxjs":
            ioc = report_data.get("IOC.json", [])
            if isinstance(ioc, list) and len(ioc) > 0:
                # Check for actual IOCs (not just sample name metadata)
                for item in ioc:
                    if isinstance(item, dict):
                        ioc_type = item.get("type", "")
                        if ioc_type not in ["Sample Name"]:  # Exclude non-threat IOCs
                            logger.debug(f"BoxJS IOC detected: {ioc_type} -> True")
                            return True
            logger.debug(f"BoxJS no malicious IOCs -> False")
            return False
        
        # ====== Strings_Info ======
        # Real response: {"data": [...], "uris": []}
        # Check for suspicious patterns in strings
        if analyzer_lower == "strings_info":
            data = report_data.get("data", [])
            suspicious_patterns = [
                "powershell", "cmd.exe", "wscript", "cscript",
                "malicious", "exploit", "payload", "shellcode",
                "c2-server", "command-and-control", "backdoor"
            ]
            for string in data:
                string_lower = str(string).lower()
                for pattern in suspicious_patterns:
                    if pattern in string_lower:
                        logger.debug(f"Strings_Info suspicious pattern '{pattern}' found -> True")
                        return True
            logger.debug(f"Strings_Info no suspicious patterns -> False")
            return False
        
        # ====== File_Info ======
        # Metadata only analyzer - cannot detect malware
        if analyzer_lower == "file_info":
            logger.debug(f"File_Info is metadata-only, cannot detect malware -> False")
            return False
        
        # ====== Androguard ======
        # Usually fails on non-APK files, but when it works:
        if analyzer_lower == "androguard":
            # Check status first
            status = analyzer_report.get("status")
            if status != "SUCCESS":
                logger.debug(f"Androguard status={status} -> False")
                return False
            # Add specific field checks when you have sample output
            logger.debug(f"Androguard no malware indicators -> False")
            return False
        
        # ====== Generic fallback for unknown analyzers ======
        # Check common malware indicator fields
        detections = report_data.get("detections", [])
        if isinstance(detections, list) and len(detections) > 0:
            logger.debug(f"Generic detections found: {detections} -> True")
            return True
        
        verdict = str(report_data.get("verdict", "")).lower()
        if "malicious" in verdict or "malware" in verdict:
            logger.debug(f"Generic verdict indicates malware -> True")
            return True
        
        logger.debug(f"{analyzer_name} no malware indicators found -> False")
        return False
    
    def _check_suspicious(self, analyzer_name: str, report_data: Dict[str, Any], analyzer_report: Dict[str, Any]) -> bool:
        """
        Check if analyzer found suspicious (but not definitively malicious) content.
        
        VERIFIED FIELD PATHS from actual responses:
        - Doc_Info: mraptor = "suspicious"
        - Quark_Engine: threat_level = "Medium Risk" or moderate score
        - Yara: utility rule matches without malware rules
        """
        analyzer_lower = analyzer_name.lower() if analyzer_name else ""
        
        # Doc_Info suspicious macros
        if analyzer_lower == "doc_info":
            mraptor = report_data.get("mraptor", "")
            if mraptor == "suspicious":
                logger.debug(f"Doc_Info mraptor = 'suspicious' -> True")
                return True
        
        # Quark_Engine medium risk
        if analyzer_lower == "quark_engine":
            threat_level = report_data.get("threat_level", "")
            total_score = report_data.get("total_score", 0)
            
            if threat_level == "Medium Risk":
                logger.debug(f"Quark_Engine threat_level = 'Medium Risk' -> True")
                return True
            
            if isinstance(total_score, (int, float)) and 20 <= total_score <= 50:
                logger.debug(f"Quark_Engine score {total_score} in suspicious range -> True")
                return True
        
        # APK_Artifacts with some suspicious permissions
        if analyzer_lower == "apk_artifacts":
            permissions = report_data.get("permission", [])
            suspicious_permissions = [
                "android.permission.INTERNET",
                "android.permission.ACCESS_NETWORK_STATE",
                "android.permission.READ_PHONE_STATE"
            ]
            count = sum(1 for p in permissions if p in suspicious_permissions)
            if count >= 2:  # Multiple suspicious but not dangerous permissions
                logger.debug(f"APK_Artifacts {count} suspicious permissions -> True")
                return True
        
        # Generic verdict check
        verdict = str(report_data.get("verdict", "")).lower()
        if "suspicious" in verdict:
            logger.debug(f"Generic verdict suspicious -> True")
            return True
        
        logger.debug(f"{analyzer_name} no suspicious indicators -> False")
        return False
    
    def _check_clean(self, analyzer_name: str, report_data: Dict[str, Any], analyzer_report: Dict[str, Any]) -> bool:
        """
        Check if analyzer verified file as clean/safe.
        
        VERIFIED FIELD PATHS from actual responses:
        - ClamAV: detections = [] and raw_report contains "Infected files: 0"
        - Doc_Info: mraptor = "ok"
        - Quark_Engine: threat_level = "Low Risk" and score = 0
        """
        analyzer_lower = analyzer_name.lower() if analyzer_name else ""
        
        # Check if analyzer succeeded first
        status = analyzer_report.get("status")
        if status != "SUCCESS":
            logger.debug(f"{analyzer_name} status={status}, not clean -> False")
            return False
        
        # ClamAV clean check
        if analyzer_lower == "clamav":
            detections = report_data.get("detections", [])
            if not detections or (isinstance(detections, list) and len(detections) == 0):
                raw_report = report_data.get("raw_report", "")
                if "Infected files: 0" in raw_report or "FOUND" not in raw_report:
                    logger.debug(f"ClamAV no detections, clean -> True")
                    return True
            logger.debug(f"ClamAV has detections -> False")
            return False
        
        # Doc_Info clean check
        if analyzer_lower == "doc_info":
            mraptor = report_data.get("mraptor", "")
            if mraptor == "ok":
                logger.debug(f"Doc_Info mraptor = 'ok' -> True")
                return True
            logger.debug(f"Doc_Info mraptor = '{mraptor}' -> False")
            return False
        
        # Quark_Engine clean check
        if analyzer_lower == "quark_engine":
            threat_level = report_data.get("threat_level", "")
            total_score = report_data.get("total_score", 0)
            crimes = report_data.get("crimes", [])
            
            if threat_level == "Low Risk" and total_score == 0 and not crimes:
                logger.debug(f"Quark_Engine Low Risk, score=0, no crimes -> True")
                return True
            logger.debug(f"Quark_Engine not clean: level={threat_level}, score={total_score} -> False")
            return False
        
        # Yara clean check - no matches in any rule set
        if analyzer_lower == "yara":
            # Check data_model first
            job_data_model = analyzer_report.get("data_model", {})
            if job_data_model.get("evaluation") == "malicious":
                return False
            
            signatures = job_data_model.get("signatures", [])
            if signatures:
                return False
            
            # All rule sets should be empty for clean
            for key, value in report_data.items():
                if isinstance(value, list) and len(value) > 0:
                    return False
            
            logger.debug(f"Yara no matches -> True")
            return True
        
        # File_Info - always considered "clean" as it's metadata only
        if analyzer_lower == "file_info":
            logger.debug(f"File_Info metadata analyzer -> True")
            return True
        
        # Strings_Info - clean if no suspicious patterns found
        if analyzer_lower == "strings_info":
            # Inverse of malicious check
            if not self._check_malicious(analyzer_name, report_data, analyzer_report):
                logger.debug(f"Strings_Info no suspicious patterns -> True")
                return True
            return False
        
        # Generic clean check
        verdict = str(report_data.get("verdict", "")).lower()
        if "clean" in verdict or "safe" in verdict or "benign" in verdict:
            logger.debug(f"Generic verdict clean -> True")
            return True
        
        # If no explicit clean indicator, assume clean if no malicious indicators
        if not self._check_malicious(analyzer_name, report_data, analyzer_report):
            logger.debug(f"{analyzer_name} no malicious indicators, assuming clean -> True")
            return True
        
        logger.debug(f"{analyzer_name} not verified clean -> False")
        return False

# Global service instance
intel_service = IntelOwlService()