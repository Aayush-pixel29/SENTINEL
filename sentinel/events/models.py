from enum import Enum
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
import uuid
from pydantic import BaseModel, Field


class EventType(str, Enum):
    RUN = "run"
    GIT_DIFF = "git_diff"
    TEST = "test"
    SEMGREP = "semgrep"
    SECRET_SCAN = "secret_scan"
    LLM_CALL = "llm_call"
    TOOL_CALL = "tool_call"
    RETRIEVAL = "retrieval"
    EVALUATION = "evaluation"
    POLICY_CHECK = "policy_check"
    HUMAN_APPROVAL = "human_approval"
    ERROR = "error"


class EventStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILURE = "failure"
    BLOCKED = "blocked"
    SKIPPED = "skipped"
    ERROR = "error"


class TraceEvent(BaseModel):
    run_id: str
    event_id: str = Field(default_factory=lambda: f"evt_{uuid.uuid4().hex[:12]}")
    parent_event_id: Optional[str] = None
    event_type: EventType
    component: str
    status: EventStatus = EventStatus.SUCCESS
    started_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    duration_ms: Optional[float] = None
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    estimated_cost_usd: Optional[float] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None

    def model_dump_json_line(self) -> str:
        return self.model_dump_json()


class RunTrace(BaseModel):
    run_id: str
    started_at: str
    ended_at: Optional[str] = None
    status: EventStatus = EventStatus.RUNNING
    total_events: int = 0
    total_duration_ms: float = 0.0
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_cost_usd: float = 0.0
    events: List[TraceEvent] = Field(default_factory=list)
