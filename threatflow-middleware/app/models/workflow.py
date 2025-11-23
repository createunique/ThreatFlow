"""
Pydantic models for request/response validation
Enhanced with conditional logic support for Phase 4
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from enum import Enum

class NodeType(str, Enum):
    """Supported node types in workflow"""
    FILE = "file"
    ANALYZER = "analyzer"
    CONDITIONAL = "conditional"  # NEW: Phase 4
    RESULT = "result"

class ConditionType(str, Enum):
    """Types of conditions for conditional nodes"""
    VERDICT_MALICIOUS = "verdict_malicious"
    VERDICT_SUSPICIOUS = "verdict_suspicious"
    VERDICT_CLEAN = "verdict_clean"
    ANALYZER_SUCCESS = "analyzer_success"
    ANALYZER_FAILED = "analyzer_failed"
    CUSTOM_FIELD = "custom_field"

class ConditionalData(BaseModel):
    """Configuration data for conditional nodes"""
    condition_type: ConditionType
    source_analyzer: str  # Which analyzer's results to check
    field_path: Optional[str] = None  # JSON path for custom field checks
    expected_value: Optional[Any] = None  # Expected value for comparison

class WorkflowNode(BaseModel):
    """Represents a single node in the workflow canvas"""
    id: str = Field(..., description="Unique node identifier")
    type: NodeType = Field(..., description="Node type")
    data: Dict[str, Any] = Field(default_factory=dict, description="Node configuration")
    position: Optional[Dict[str, float]] = None
    conditional_data: Optional[ConditionalData] = None  # NEW: Phase 4

class WorkflowEdge(BaseModel):
    """Represents a connection between nodes"""
    id: str
    source: str = Field(..., description="Source node ID")
    target: str = Field(..., description="Target node ID")
    sourceHandle: Optional[str] = None
    targetHandle: Optional[str] = None

class WorkflowRequest(BaseModel):
    """Request model for workflow execution"""
    nodes: List[WorkflowNode]
    edges: List[WorkflowEdge]

class JobStatusResponse(BaseModel):
    """Response model for job status polling"""
    job_id: int
    status: str
    progress: Optional[int] = None
    analyzers_completed: int = 0
    analyzers_total: int = 0
    results: Optional[Dict[str, Any]] = None

class AnalyzerInfo(BaseModel):
    """Analyzer metadata"""
    name: str
    type: str
    description: Optional[str] = None
    supported_filetypes: Optional[List[str]] = None
    observable_supported: Optional[List[str]] = None