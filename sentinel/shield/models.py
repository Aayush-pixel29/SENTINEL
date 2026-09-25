from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime, timezone


class TrustLevel(str, Enum):
    VERIFIED = "verified"
    TRUSTED = "trusted"
    UNKNOWN = "unknown"
    BLOCKED = "blocked"


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class PolicyDecisionType(str, Enum):
    ALLOW = "ALLOW"
    DENY = "DENY"
    REVIEW = "REVIEW"


class ToolDefinition(BaseModel):
    name: str
    description: str = ""
    version: str = "1.0.0"
    source: str = "builtin"
    trust_level: TrustLevel = TrustLevel.UNKNOWN
    risk: RiskLevel = RiskLevel.MEDIUM
    allowed_operations: List[str] = Field(default_factory=lambda: ["*"])
    input_schema: Optional[Dict[str, Any]] = None
    auth_required: bool = False
    enabled: bool = True
    require_human_approval: bool = False


class PolicyCheckRequest(BaseModel):
    tool_name: str
    operation: str = "execute"
    arguments: Dict[str, Any] = Field(default_factory=dict)
    auth_provided: bool = False
    context: Dict[str, Any] = Field(default_factory=dict)


class PolicyDecision(BaseModel):
    decision: PolicyDecisionType
    reason: str
    tool: str
    risk: RiskLevel = RiskLevel.MEDIUM
    requires_approval: bool = False
    rule_id: Optional[str] = None
    details: Dict[str, Any] = Field(default_factory=dict)
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def is_allowed(self) -> bool:
        return self.decision == PolicyDecisionType.ALLOW
