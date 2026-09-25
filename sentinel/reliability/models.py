from enum import Enum
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
import uuid
from pydantic import BaseModel, Field


class ExecutionStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    TIMED_OUT = "TIMED_OUT"
    CANCELLED = "CANCELLED"
    RETRYING = "RETRYING"


class ExecutionRecord(BaseModel):
    execution_id: str = Field(default_factory=lambda: f"exec_{uuid.uuid4().hex[:10]}")
    run_id: str
    tool_name: str
    status: ExecutionStatus = ExecutionStatus.PENDING
    start_time: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    end_time: Optional[str] = None
    duration_ms: Optional[float] = None
    timeout_seconds: float = 30.0
    retry_count: int = 0
    max_retries: int = 3
    idempotency_key: Optional[str] = None
    arguments: Dict[str, Any] = Field(default_factory=dict)
    result: Optional[Any] = None
    error: Optional[str] = None
    cached: bool = False


class Checkpoint(BaseModel):
    checkpoint_id: str = Field(default_factory=lambda: f"chk_{uuid.uuid4().hex[:10]}")
    run_id: str
    state: Dict[str, Any] = Field(default_factory=dict)
    completed_steps: List[str] = Field(default_factory=list)
    failed_step: Optional[str] = None
    resume_from: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: Dict[str, Any] = Field(default_factory=dict)
