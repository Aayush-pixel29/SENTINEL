from typing import Callable, Dict, Any, Optional, List
from sentinel.shield import ToolShield, ToolDefinition, TrustLevel, RiskLevel, PolicyDecisionType
from sentinel.sanitizer import OutputSanitizer
from sentinel.events.recorder import EventRecorder
from sentinel.events.models import EventType, EventStatus
from sentinel.mcp.models import MCPToolSchema, MCPToolCallRequest, MCPToolCallResponse


class MCPGateway:
    """SENTINEL-X Tool Gateway for MCP and local tool execution."""

    def __init__(
        self,
        shield: Optional[ToolShield] = None,
        sanitizer: Optional[OutputSanitizer] = None,
        recorder: Optional[EventRecorder] = None,
    ):
        self.shield = shield or ToolShield(recorder=recorder)
        self.sanitizer = sanitizer or OutputSanitizer()
        self.recorder = recorder
        self._handlers: Dict[str, Callable[[Dict[str, Any]], Any]] = {}

    def register_mcp_tool(
        self,
        schema: MCPToolSchema,
        handler: Callable[[Dict[str, Any]], Any],
        trust_level: TrustLevel = TrustLevel.TRUSTED,
        risk: RiskLevel = RiskLevel.MEDIUM,
        auth_required: bool = False,
        require_human_approval: bool = False,
    ) -> None:
        """Register an MCP tool into the ToolShield registry and bind its execution handler."""
        tool_def = ToolDefinition(
            name=schema.name,
            description=schema.description,
            source="mcp",
            trust_level=trust_level,
            risk=risk,
            input_schema=schema.inputSchema,
            auth_required=auth_required,
            require_human_approval=require_human_approval,
            allowed_operations=["*"],
            enabled=True,
        )
        self.shield.registry.register_tool(tool_def)
        self._handlers[schema.name] = handler

    def execute_tool(
        self,
        request: MCPToolCallRequest,
        auth_provided: bool = False,
        context: Optional[Dict[str, Any]] = None,
    ) -> MCPToolCallResponse:
        """Evaluate policy -> execute handler if allowed -> sanitize output -> record telemetry."""
        tool_name = request.name
        args = request.arguments

        # 1. Policy Evaluation via ToolShield
        decision = self.shield.check_tool_call(
            tool_name=tool_name,
            operation="execute",
            arguments=args,
            auth_provided=auth_provided,
            context=context,
        )

        if not decision.is_allowed():
            return MCPToolCallResponse(
                call_id=request.call_id,
                tool_name=tool_name,
                success=False,
                error=f"Policy Blocked: {decision.reason}",
                policy_decision=decision.decision.value,
            )

        handler = self._handlers.get(tool_name)
        if not handler:
            return MCPToolCallResponse(
                call_id=request.call_id,
                tool_name=tool_name,
                success=False,
                error=f"No local handler registered for tool '{tool_name}'",
                policy_decision=decision.decision.value,
            )

        # 2. Execution with event tracking
        raw_result = None
        exec_error = None
        if self.recorder:
            with self.recorder.span(EventType.TOOL_CALL, component=f"tool:{tool_name}", metadata={"args": args}):
                try:
                    raw_result = handler(args)
                except Exception as ex:
                    exec_error = str(ex)
        else:
            try:
                raw_result = handler(args)
            except Exception as ex:
                exec_error = str(ex)

        if exec_error:
            return MCPToolCallResponse(
                call_id=request.call_id,
                tool_name=tool_name,
                success=False,
                error=exec_error,
                policy_decision=decision.decision.value,
            )

        # 3. Output Sanitization
        san_res = self.sanitizer.sanitize(raw_result)

        return MCPToolCallResponse(
            call_id=request.call_id,
            tool_name=tool_name,
            success=True,
            output=san_res.safe_content,
            sanitized=san_res.sanitized,
            redactions=san_res.redactions,
            categories=san_res.categories,
            policy_decision=decision.decision.value,
        )
