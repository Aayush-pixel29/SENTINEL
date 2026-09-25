from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class Verdict(str, Enum):
    BLOCKED = "BLOCKED"
    REVIEW = "REVIEW"
    VERIFIED = "VERIFIED"
    INCOMPLETE = "INCOMPLETE"


class CheckStatus(str, Enum):
    PASSED = "PASSED"
    FAILED = "FAILED"
    NOT_AVAILABLE = "NOT_AVAILABLE"
    SKIPPED = "SKIPPED"
    ERROR = "ERROR"


class Classification(str, Enum):
    CONFIRMED = "CONFIRMED"
    UNCONFIRMED = "UNCONFIRMED"


class Finding(BaseModel):
    id: str
    source: str
    classification: Classification
    severity: str
    title: str
    description: str
    file: Optional[str] = None
    line: Optional[int] = None
    evidence: Optional[str] = None
    recommendation: Optional[str] = None


class CheckResult(BaseModel):
    name: str
    status: CheckStatus
    exit_code: int
    duration: float
    stdout: str = ""
    stderr: str = ""
    findings: List[Finding] = []


class GitChangeSummary(BaseModel):
    files_changed: int
    lines_added: int
    lines_removed: int
    changed_files_list: List[str]
    diff_text: str
    diff_source: str = "working-tree"  # "staged" or "working-tree"


class AIReviewResult(BaseModel):
    summary: str
    findings: List[Finding] = []
    status: CheckStatus = CheckStatus.PASSED
    provider: str = "gemini"
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    duration_ms: Optional[float] = None
    estimated_cost_usd: Optional[float] = None


class VerificationReport(BaseModel):
    version: str = "2.0"
    run_id: str = ""
    verdict: Verdict
    repository: str = ""
    branch: str = ""
    commit: str = "unknown"
    timestamp: str = ""
    task_description: str = ""
    changed_files: List[str] = []
    checks: List[CheckResult] = []
    confirmed_findings: List[Finding] = []
    unconfirmed_findings: List[Finding] = []
    ai_review: Dict[str, Any] = Field(default_factory=dict)
    ai_provider: str = ""
    tool_decisions: List[Dict[str, Any]] = Field(default_factory=list)
    tool_executions: List[Dict[str, Any]] = Field(default_factory=list)
    eval_report: Optional[Dict[str, Any]] = None
    metrics: Optional[Dict[str, Any]] = None
    events: List[Dict[str, Any]] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
