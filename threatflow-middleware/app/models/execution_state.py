"""
ThreatFlow Workflow Execution State Models
Implements persistent state storage for checkpoint/resume functionality
"""

from sqlalchemy import Column, String, Integer, DateTime, JSON, Enum, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
import uuid

Base = declarative_base()


class ExecutionStatus(enum.Enum):
    """Workflow execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"
    CANCELLED = "cancelled"


class WorkflowExecution(Base):
    """
    Persistent storage for workflow execution state
    Enables checkpoint/resume functionality
    """
    __tablename__ = "workflow_executions"
    
    # Primary key
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Workflow definition
    workflow_json = Column(JSON, nullable=False)  # Original React Flow JSON
    workflow_name = Column(String(255))
    
    # Execution metadata
    status = Column(Enum(ExecutionStatus), default=ExecutionStatus.PENDING, nullable=False)
    current_stage_id = Column(Integer, default=0)
    total_stages = Column(Integer, nullable=False)
    
    # IntelOwl integration
    intelowl_job_id = Column(Integer)  # Current IntelOwl job ID
    
    # Results storage
    stage_results = Column(JSON, default=dict)  # {stage_0: {...}, stage_1: {...}}
    final_results = Column(JSON)  # Aggregated results
    routing_metadata = Column(JSON)  # stage_routing for frontend
    
    # Error tracking
    error_message = Column(Text)
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    last_updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Configuration
    config = Column(JSON, default=dict)  # Execution options (fail_fast, timeout, etc.)
    
    # Relationships
    checkpoints = relationship("ExecutionCheckpoint", back_populates="execution", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<WorkflowExecution(id={self.id}, status={self.status.value}, stage={self.current_stage_id}/{self.total_stages})>"
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            "id": self.id,
            "workflow_name": self.workflow_name,
            "status": self.status.value,
            "current_stage": self.current_stage_id,
            "total_stages": self.total_stages,
            "progress_pct": (self.current_stage_id / self.total_stages * 100) if self.total_stages > 0 else 0,
            "intelowl_job_id": self.intelowl_job_id,
            "stage_results": self.stage_results,
            "final_results": self.final_results,
            "routing_metadata": self.routing_metadata,
            "error_message": self.error_message,
            "retry_count": self.retry_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "last_updated_at": self.last_updated_at.isoformat() if self.last_updated_at else None
        }


class ExecutionCheckpoint(Base):
    """
    Granular checkpoint for each stage execution
    Enables fine-grained resume from specific stage
    """
    __tablename__ = "execution_checkpoints"
    
    # Primary key
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Foreign key to workflow execution
    execution_id = Column(String(36), ForeignKey("workflow_executions.id"), nullable=False)
    
    # Stage information
    stage_id = Column(Integer, nullable=False)
    stage_name = Column(String(255))
    stage_config = Column(JSON)  # Stage definition {analyzers, condition, target_nodes}
    
    # Execution details
    status = Column(Enum(ExecutionStatus), nullable=False)
    intelowl_job_id = Column(Integer)
    
    # Results
    analyzer_results = Column(JSON)  # Raw analyzer reports
    condition_evaluated = Column(JSON)  # {type: "verdict_malicious", result: True, confidence: 0.95}
    
    # Timing
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    duration_seconds = Column(Integer)
    
    # Error tracking
    error_message = Column(Text)
    retry_count = Column(Integer, default=0)
    
    # Relationships
    execution = relationship("WorkflowExecution", back_populates="checkpoints")
    
    def __repr__(self):
        return f"<ExecutionCheckpoint(stage={self.stage_id}, status={self.status.value})>"
    
    def to_dict(self):
        return {
            "id": self.id,
            "execution_id": self.execution_id,
            "stage_id": self.stage_id,
            "stage_name": self.stage_name,
            "status": self.status.value,
            "intelowl_job_id": self.intelowl_job_id,
            "condition_evaluated": self.condition_evaluated,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration_seconds": self.duration_seconds,
            "error_message": self.error_message
        }


class RateLimitBucket(Base):
    """
    Token bucket rate limiter state storage
    Enables distributed rate limiting across multiple workers
    """
    __tablename__ = "rate_limit_buckets"
    
    # Composite primary key (api_name + time_window)
    api_name = Column(String(50), primary_key=True)  # "virustotal", "intelowl", etc.
    
    # Token bucket state
    tokens_available = Column(Integer, nullable=False)
    max_tokens = Column(Integer, nullable=False)
    refill_rate = Column(Integer, nullable=False)  # Tokens per second
    
    # Timing
    last_refill_at = Column(DateTime, default=datetime.utcnow)
    next_refill_at = Column(DateTime)
    
    # Statistics
    total_requests = Column(Integer, default=0)
    rejected_requests = Column(Integer, default=0)
    
    def __repr__(self):
        return f"<RateLimitBucket(api={self.api_name}, tokens={self.tokens_available}/{self.max_tokens})>"


# Database initialization
def init_db(engine):
    """Create all tables"""
    Base.metadata.create_all(engine)


def drop_db(engine):
    """Drop all tables (use with caution!)"""
    Base.metadata.drop_all(engine)
