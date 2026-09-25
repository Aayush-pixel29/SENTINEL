from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime, timezone


class EvalDimension(BaseModel):
    name: str
    total: int = 0
    passed: int = 0
    score: float = 0.0


class EvalTestCase(BaseModel):
    id: str
    name: str
    category: str = "general"
    input_text: str
    expected_tools: List[str] = Field(default_factory=list)
    forbidden_tools: List[str] = Field(default_factory=list)
    expected_decision: Optional[str] = None  # ALLOW, DENY, REVIEW
    expected_output_contains: Optional[str] = None
    forbidden_output_contains: Optional[str] = None
    max_latency_ms: Optional[float] = None
    max_cost_usd: Optional[float] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class EvalCaseResult(BaseModel):
    case_id: str
    name: str
    category: str
    passed: bool
    actual_decision: Optional[str] = None
    actual_tools: List[str] = Field(default_factory=list)
    latency_ms: float = 0.0
    cost_usd: float = 0.0
    failure_reasons: List[str] = Field(default_factory=list)
    details: Dict[str, Any] = Field(default_factory=dict)


class EvalRunReport(BaseModel):
    suite_name: str
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    total_cases: int = 0
    passed: int = 0
    failed: int = 0
    task_success_rate: float = 0.0
    total_duration_ms: float = 0.0
    dimension_scores: Dict[str, float] = Field(default_factory=dict)
    case_results: List[EvalCaseResult] = Field(default_factory=list)
