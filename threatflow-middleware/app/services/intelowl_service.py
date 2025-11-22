"""
IntelOwl API wrapper service
Uses pyintelowl v5.1.0 client
"""

from pyintelowl import IntelOwl, IntelOwlClientException
from app.config import settings
import logging
import asyncio
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class IntelOwlService:
    """
    Wrapper around pyintelowl client for async operations
    Handles file analysis submission and result polling
    """
    
    def __init__(self):
        """Initialize IntelOwl client"""
        self.client = IntelOwl(
            settings.INTELOWL_API_KEY,
            settings.INTELOWL_URL,
            None,  # certificate
            None   # proxies
        )
        logger.info(f"IntelOwl client initialized for {settings.INTELOWL_URL}")
    
    async def submit_file_analysis(
        self,
        file_path: str,
        analyzers: List[str],
        file_name: str,
        tlp: str = "CLEAR"
    ) -> int:
        """
        Submit file for analysis to IntelOwl
        
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
            
            # Use real pyintelowl client to submit analysis
            result = self.client.send_file_analysis_request(
                filename=file_name,
                binary=file_binary,
                analyzers_requested=analyzers,
                tlp=tlp,
                runtime_configuration={},
                tags_labels=["threatflow"]
            )
            
            job_id = result["job_id"]
            logger.info(f"Real analysis submitted to IntelOwl: Job ID {job_id} for analyzers {analyzers}")
            return job_id
            
        except IntelOwlClientException as e:
            logger.error(f"IntelOwl API error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during submission: {e}")
            raise
    
    async def get_job_status(self, job_id: int) -> Dict[str, Any]:
        """Get current status of an IntelOwl job"""
        try:
            # Use real pyintelowl client to get job status
            job = self.client.get_job_by_id(job_id)
            
            # Convert to expected format
            status_dict = {
                "job_id": job_id,
                "status": job.get("status", "unknown"),
                "progress": None,  # IntelOwl doesn't provide progress
                "analyzers_completed": len(job.get("analyzer_reports", [])),
                "analyzers_total": len(job.get("analyzers_to_execute", [])),
                "results": job if job.get("status") in ["reported_without_fails", "reported_with_fails"] else None
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
    
    async def get_available_analyzers(self, analyzer_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get list of available analyzers from IntelOwl"""
        try:
            import httpx
            
            headers = {"Authorization": f"Token {settings.INTELOWL_API_KEY}"}
            url = f"{settings.INTELOWL_URL}/api/get_analyzer_configs"
            
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                all_analyzers = response.json()
            
            if analyzer_type:
                all_analyzers = [
                    a for a in all_analyzers
                    if a.get("type") == analyzer_type
                ]
            
            return [
                {
                    "name": a["name"],
                    "type": a.get("type", "unknown"),
                    "description": a.get("description", ""),
                    "supported_filetypes": a.get("supported_filetypes", []),
                    "disabled": a.get("disabled", False)
                }
                for a in all_analyzers
                if not a.get("disabled", False)
            ]
            
        except Exception as e:
            logger.warning(f"Failed to fetch analyzers from API: {e}. Using mock analyzers for testing.")
            # Return mock analyzers for testing when API is not available
            mock_analyzers = [
                {
                    "name": "File_Info",
                    "type": "file",
                    "description": "Basic file information extractor",
                    "supported_filetypes": ["*"],
                    "disabled": False
                },
                {
                    "name": "ClamAV",
                    "type": "file", 
                    "description": "ClamAV antivirus scanner",
                    "supported_filetypes": ["*"],
                    "disabled": False
                },
                {
                    "name": "VirusTotal_v3_Get_File",
                    "type": "file",
                    "description": "VirusTotal file analysis",
                    "supported_filetypes": ["*"],
                    "disabled": False
                }
            ]
            
            if analyzer_type:
                mock_analyzers = [a for a in mock_analyzers if a.get("type") == analyzer_type]
            
            return mock_analyzers

# Global service instance
intel_service = IntelOwlService()