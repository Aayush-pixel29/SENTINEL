from typing import Optional, Dict, Any
from sentinel.shield.models import (
    ToolDefinition,
    PolicyCheckRequest,
    PolicyDecision,
    PolicyDecisionType,
)
from sentinel.shield.registry import ToolRegistry
from sentinel.shield.policy import PolicyEngine
from sentinel.events.recorder import EventRecorder
from sentinel.events.models import EventType, EventStatus


class ToolShield:
    """SENTINEL-X ToolShield: The unified policy enforcement boundary for agent tool requests."""

    def __init__(
        self,
        registry: Optional[ToolRegistry] = None,
        policy_engine: Optional[PolicyEngine] = None,
        recorder: Optional[EventRecorder] = None,
    ):
        self.registry = registry or ToolRegistry()
        self.policy_engine = policy_engine or PolicyEngine()
        self.recorder = recorder

    def check_tool_call(
        self,
        tool_name: str,
        operation: str = "execute",
        arguments: Optional[Dict[str, Any]] = None,
        auth_provided: bool = False,
        context: Optional[Dict[str, Any]] = None,
    ) -> PolicyDecision:
        tool = self.registry.get_tool(tool_name)
        request = PolicyCheckRequest(
            tool_name=tool_name,
            operation=operation,
            arguments=arguments or {},
            auth_provided=auth_provided,
            context=context or {},
        )
        decision = self.policy_engine.evaluate(tool, request)

        # Log policy check trace event if recorder is present
        if self.recorder:
            status_map = {
                PolicyDecisionType.ALLOW: EventStatus.SUCCESS,
                PolicyDecisionType.DENY: EventStatus.BLOCKED,
                PolicyDecisionType.REVIEW: EventStatus.PENDING,
            }
            self.recorder.record_event(
                event_type=EventType.POLICY_CHECK,
                component="tool_shield",
                status=status_map.get(decision.decision, EventStatus.BLOCKED),
                metadata={
                    "tool": tool_name,
                    "operation": operation,
                    "decision": decision.decision.value,
                    "reason": decision.reason,
                    "risk": decision.risk.value,
                    "requires_approval": decision.requires_approval,
                    "rule_id": decision.rule_id,
                },
            )

        return decision
