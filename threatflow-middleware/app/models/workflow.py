"""
Pydantic models for request/response validation
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from enum import Enum

class NodeType(str, Enum):
    """Supported node types in workflow"""
    FILE = "file"
    ANALYZER = "analyzer"
    CONDITIONAL = "conditional"
    RESULT = "result"

class WorkflowNode(BaseModel):
    """Represents a single node in the workflow canvas"""
    id: str = Field(..., description="Unique node identifier")
    type: NodeType = Field(..., description="Node type")
    data: Dict[str, Any] = Field(default_factory=dict, description="Node configuration")
    position: Optional[Dict[str, float]] = None

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