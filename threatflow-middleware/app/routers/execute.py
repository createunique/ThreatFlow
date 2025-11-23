"""Workflow execution endpoints"""

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from app.services.intelowl_service import intel_service
from app.services.workflow_parser import workflow_parser
from app.models.workflow import WorkflowRequest, JobStatusResponse, AnalyzerInfo
from typing import List, Dict, Any
import logging
import json
import shutil
import os

router = APIRouter(prefix="/api", tags=["execution"])
logger = logging.getLogger(__name__)

@router.post("/execute")
async def execute_workflow(
    workflow_json: str = Form(...),
    file: UploadFile = File(...)
):
    """Execute workflow: parse nodes/edges and submit to IntelOwl"""
    try:
        workflow_dict = json.loads(workflow_json)
        workflow = WorkflowRequest(**workflow_dict)
        
        logger.info(f"Received workflow with {len(workflow.nodes)} nodes, {len(workflow.edges)} edges")
        
        # Parse execution plan
        execution_plan = workflow_parser.parse(workflow.nodes, workflow.edges)
        
        # Save uploaded file temporarily
        temp_path = f"/tmp/threatflow_{file.filename}"
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        logger.info(f"File saved: {temp_path} ({os.path.getsize(temp_path)} bytes)")
        
        # Check if workflow has conditionals
        has_conditionals = execution_plan.get("has_conditionals", False)
        stages = execution_plan.get("stages", [])
        
        if has_conditionals:
            # Phase 4: Conditional workflow execution
            logger.info("Executing conditional workflow")
            
            result = await intel_service.execute_workflow_with_conditionals(
                file_path=temp_path,
                stages=stages,
                file_name=file.filename
            )
            
            # Cleanup temp file
            os.remove(temp_path)
            
            # Build routing metadata for frontend
            stage_routing = []
            for stage in stages:
                stage_routing.append({
                    "stage_id": stage["stage_id"],
                    "target_nodes": stage.get("target_nodes", []),
                    "executed": stage["stage_id"] in result["executed_stages"]
                })
            
            logger.info(f"Stage routing metadata: {stage_routing}")
            
            return {
                "success": True,
                "job_ids": result["job_ids"],
                "total_stages": len(stages),
                "executed_stages": result["executed_stages"],
                "skipped_stages": result["skipped_stages"],
                "has_conditionals": True,
                "stage_routing": stage_routing,  # NEW: Include routing metadata
                "message": f"Conditional workflow executed: {result['total_stages_executed']} of {len(stages)} stages"
            }
        else:
            # Phase 3: Simple linear execution (backwards compatible)
            logger.info("Executing linear workflow")
            
            stage_0 = stages[0] if stages else {"analyzers": []}
            analyzers = stage_0.get("analyzers", [])
            
            job_id = await intel_service.submit_file_analysis(
                file_path=temp_path,
                analyzers=analyzers,
                file_name=file.filename
            )
            
            # Cleanup temp file
            os.remove(temp_path)
            
            return {
                "success": True,
                "job_id": job_id,
                "job_ids": [job_id],
                "analyzers": analyzers,
                "has_conditionals": False,
                "message": f"Analysis started with {len(analyzers)} analyzers"
            }
        
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Execution failed: {e}")
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")

@router.get("/status/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: int):
    """Get current status of IntelOwl job"""
    try:
        status = await intel_service.get_job_status(job_id)
        return JobStatusResponse(**status)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/analyzers", response_model=Dict[str, Any])
async def list_analyzers(type: str = None):
    """List available IntelOwl analyzers with availability detection"""
    analyzers = await intel_service.get_available_analyzers(type)
    return analyzers