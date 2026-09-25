from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field


class MCPToolSchema(BaseModel):
    name: str
    description: str = ""
    inputSchema: Dict[str, Any] = Field(default_factory=dict)


class MCPToolCallRequest(BaseModel):
    name: str
    arguments: Dict[str, Any] = Field(default_factory=dict)
    call_id: Optional[str] = None


class MCPToolCallResponse(BaseModel):
    call_id: Optional[str] = None
    tool_name: str
    success: bool
    output: Any = None
    sanitized: bool = False
    redactions: int = 0
    categories: List[str] = Field(default_factory=list)
    error: Optional[str] = None
    policy_decision: Optional[str] = None
