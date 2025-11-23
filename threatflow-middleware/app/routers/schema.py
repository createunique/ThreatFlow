"""
Schema and Validation API Endpoints
Provides analyzer schemas, condition templates, and workflow validation
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from app.services.analyzer_schema import schema_manager
from app.services.workflow_validator import workflow_validator
from app.models.workflow import WorkflowNode, WorkflowEdge
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/schema", tags=["schema"])


# ============= Request/Response Models =============

class FieldPathValidationRequest(BaseModel):
    analyzer_name: str
    field_path: str

class FieldPathValidationResponse(BaseModel):
    is_valid: bool
    message: str
    suggestions: List[str] = []

class ConditionValidationRequest(BaseModel):
    condition_type: str
    source_analyzer: str
    field_path: Optional[str] = None
    expected_value: Optional[Any] = None

class ConditionValidationResponse(BaseModel):
    is_valid: bool
    errors: List[str] = []

class WorkflowValidationRequest(BaseModel):
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]

class ValidationIssueResponse(BaseModel):
    severity: str
    message: str
    node_id: Optional[str] = None
    field: Optional[str] = None
    suggestions: List[str] = []
    auto_fix: Optional[Dict[str, Any]] = None

class WorkflowValidationResponse(BaseModel):
    is_valid: bool
    issues: List[ValidationIssueResponse]
    errors_count: int
    warnings_count: int
    info_count: int


# ============= Endpoints =============

@router.get("/analyzers")
async def get_analyzer_schemas():
    """
    Get list of all analyzers with schema information
    
    Returns analyzer names, descriptions, and available fields
    """
    try:
        analyzers = []
        for analyzer_name in schema_manager.get_all_analyzers():
            schema = schema_manager.get_analyzer_schema(analyzer_name)
            if schema:
                analyzers.append({
                    "name": analyzer_name,
                    "description": schema.get("description", ""),
                    "field_count": len(schema.get("output_fields", [])),
                    "template_count": len(schema.get("condition_templates", [])),
                    "malware_indicators": schema.get("malware_indicators", [])
                })
        
        return {
            "analyzers": analyzers,
            "total_count": len(analyzers)
        }
    
    except Exception as e:
        logger.error(f"Error fetching analyzer schemas: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analyzers/{analyzer_name}")
async def get_analyzer_schema(analyzer_name: str):
    """
    Get detailed schema for specific analyzer
    
    Returns output fields, condition templates, and malware indicators
    """
    try:
        schema = schema_manager.get_analyzer_schema(analyzer_name)
        if not schema:
            raise HTTPException(status_code=404, detail=f"Analyzer '{analyzer_name}' not found")
        
        # Convert SchemaField objects to dict
        output_fields = []
        for field in schema.get("output_fields", []):
            output_fields.append({
                "path": field.path,
                "type": field.field_type.value,
                "description": field.description,
                "examples": field.examples,
                "required": field.required
            })
        
        # Convert ConditionTemplate objects to dict
        templates = []
        for template in schema.get("condition_templates", []):
            templates.append({
                "name": template.name,
                "description": template.description,
                "condition_type": template.condition_type,
                "field_path": template.field_path,
                "expected_value": template.expected_value,
                "use_case": template.use_case
            })
        
        return {
            "name": analyzer_name,
            "description": schema.get("description", ""),
            "output_fields": output_fields,
            "condition_templates": templates,
            "malware_indicators": schema.get("malware_indicators", []),
            "success_patterns": schema.get("success_patterns", [])
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching schema for {analyzer_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analyzers/{analyzer_name}/fields")
async def get_analyzer_fields(analyzer_name: str, search: Optional[str] = None):
    """
    Get output fields for analyzer with optional search filter
    
    Useful for field path autocomplete in UI
    """
    try:
        fields = schema_manager.get_output_fields(analyzer_name)
        if not fields:
            raise HTTPException(status_code=404, detail=f"Analyzer '{analyzer_name}' not found")
        
        # Filter by search term if provided
        if search:
            fields = [f for f in fields if search.lower() in f.path.lower()]
        
        return {
            "analyzer": analyzer_name,
            "fields": [
                {
                    "path": f.path,
                    "type": f.field_type.value,
                    "description": f.description,
                    "examples": f.examples
                }
                for f in fields
            ],
            "total_count": len(fields)
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching fields for {analyzer_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analyzers/{analyzer_name}/templates")
async def get_condition_templates(analyzer_name: str):
    """
    Get pre-built condition templates for analyzer
    
    Returns common use cases and recommended conditions
    """
    try:
        templates = schema_manager.get_condition_templates(analyzer_name)
        if templates is None:
            raise HTTPException(status_code=404, detail=f"Analyzer '{analyzer_name}' not found")
        
        return {
            "analyzer": analyzer_name,
            "templates": [
                {
                    "name": t.name,
                    "description": t.description,
                    "condition_type": t.condition_type,
                    "field_path": t.field_path,
                    "expected_value": t.expected_value,
                    "use_case": t.use_case
                }
                for t in templates
            ],
            "total_count": len(templates)
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching templates for {analyzer_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/validate/field-path", response_model=FieldPathValidationResponse)
async def validate_field_path(request: FieldPathValidationRequest):
    """
    Validate if field path exists in analyzer output schema
    
    Returns validation result with suggestions
    """
    try:
        is_valid, message = schema_manager.validate_field_path(
            request.analyzer_name,
            request.field_path
        )
        
        suggestions = schema_manager.suggest_field_paths(
            request.analyzer_name,
            request.field_path
        ) if not is_valid else []
        
        return FieldPathValidationResponse(
            is_valid=is_valid,
            message=message,
            suggestions=suggestions
        )
    
    except Exception as e:
        logger.error(f"Error validating field path: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/validate/condition", response_model=ConditionValidationResponse)
async def validate_condition(request: ConditionValidationRequest):
    """
    Validate condition configuration
    
    Returns validation result with specific error messages
    """
    try:
        condition = {
            "type": request.condition_type,
            "source_analyzer": request.source_analyzer,
            "field_path": request.field_path,
            "expected_value": request.expected_value
        }
        
        is_valid, errors = schema_manager.validate_condition(condition)
        
        return ConditionValidationResponse(
            is_valid=is_valid,
            errors=errors
        )
    
    except Exception as e:
        logger.error(f"Error validating condition: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/validate/workflow", response_model=WorkflowValidationResponse)
async def validate_workflow(request: WorkflowValidationRequest):
    """
    Validate entire workflow before execution
    
    Performs structural, conditional, and dependency validation
    Returns all issues with severity levels
    """
    try:
        # Convert dict to WorkflowNode/WorkflowEdge objects
        nodes = [WorkflowNode(**node) for node in request.nodes]
        edges = [WorkflowEdge(**edge) for edge in request.edges]
        
        # Validate workflow
        issues = workflow_validator.validate_workflow(nodes, edges)
        
        # Count issues by severity
        errors_count = sum(1 for i in issues if i.severity.value == "error")
        warnings_count = sum(1 for i in issues if i.severity.value == "warning")
        info_count = sum(1 for i in issues if i.severity.value == "info")
        
        return WorkflowValidationResponse(
            is_valid=(errors_count == 0),
            issues=[
                ValidationIssueResponse(
                    severity=i.severity.value,
                    message=i.message,
                    node_id=i.node_id,
                    field=i.field,
                    suggestions=i.suggestions or [],
                    auto_fix=i.auto_fix
                )
                for i in issues
            ],
            errors_count=errors_count,
            warnings_count=warnings_count,
            info_count=info_count
        )
    
    except Exception as e:
        logger.error(f"Error validating workflow: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/field-suggestions/{analyzer_name}")
async def get_field_suggestions(analyzer_name: str, partial: str = ""):
    """
    Get autocomplete suggestions for field paths
    
    Used for real-time field path suggestions in UI
    """
    try:
        suggestions = schema_manager.suggest_field_paths(analyzer_name, partial)
        
        return {
            "analyzer": analyzer_name,
            "partial": partial,
            "suggestions": suggestions,
            "count": len(suggestions)
        }
    
    except Exception as e:
        logger.error(f"Error getting field suggestions: {e}")
        raise HTTPException(status_code=500, detail=str(e))
