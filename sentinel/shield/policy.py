import re
from typing import Dict, Any, List, Optional, Tuple
from sentinel.shield.models import (
    ToolDefinition,
    PolicyCheckRequest,
    PolicyDecision,
    PolicyDecisionType,
    TrustLevel,
    RiskLevel,
)


class ArgumentValidator:
    """Detects security vulnerabilities in tool arguments like path traversal and command injection."""

    DANGEROUS_PATTERNS = [
        (r"\.\./|\.\.\\", "path_traversal_detected"),
        (r";\s*rm\s+-rf|;\s*del\s+|;\s*format\s+", "destructive_command_detected"),
        (r"\|\s*bash|\|\s*sh|\|\s*powershell", "pipe_to_shell_detected"),
        (r"(?i)\b(curl|wget)\s+http[s]?://[^\s]+\s*\|\s*(ba)?sh", "remote_script_execution_detected"),
        (r"(?i)eval\s*\(|exec\s*\(|__import__", "code_injection_payload_detected"),
        (r"(?i)cat\s+/etc/passwd|cat\s+/etc/shadow", "system_file_exfiltration_attempt"),
    ]

    @classmethod
    def validate(cls, arguments: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        def _check_val(val: Any) -> Optional[str]:
            if isinstance(val, str):
                for pattern, reason in cls.DANGEROUS_PATTERNS:
                    if re.search(pattern, val):
                        return reason
            elif isinstance(val, dict):
                for v in val.values():
                    err = _check_val(v)
                    if err:
                        return err
            elif isinstance(val, list):
                for v in val:
                    err = _check_val(v)
                    if err:
                        return err
            return None

        for k, v in arguments.items():
            issue = _check_val(v)
            if issue:
                return False, f"Argument '{k}' contained unsafe payload: {issue}"
        return True, None


class PolicyEngine:
    """Deterministic security policy engine for AI tool executions."""

    def __init__(self, strict_mode: bool = False):
        self.strict_mode = strict_mode

    def evaluate(self, tool: Optional[ToolDefinition], request: PolicyCheckRequest) -> PolicyDecision:
        tool_name = request.tool_name

        # 1. Existence check
        if tool is None:
            return PolicyDecision(
                decision=PolicyDecisionType.DENY,
                reason="tool_not_allowlisted",
                tool=tool_name,
                risk=RiskLevel.CRITICAL,
                rule_id="RULE_001_ALLOWLIST",
                details={"message": f"Tool '{tool_name}' is not registered in ToolShield registry."},
            )

        # 2. Enabled state
        if not tool.enabled:
            return PolicyDecision(
                decision=PolicyDecisionType.DENY,
                reason="tool_disabled",
                tool=tool_name,
                risk=tool.risk,
                rule_id="RULE_002_ENABLED",
                details={"message": f"Tool '{tool_name}' is currently disabled by policy."},
            )

        # 3. Trust level check
        if tool.trust_level == TrustLevel.BLOCKED:
            return PolicyDecision(
                decision=PolicyDecisionType.DENY,
                reason="tool_explicitly_blocked",
                tool=tool_name,
                risk=RiskLevel.CRITICAL,
                rule_id="RULE_003_BLOCKED_TRUST",
                details={"message": f"Tool '{tool_name}' is explicitly on the blocked trust list."},
            )

        if tool.trust_level == TrustLevel.UNKNOWN:
            return PolicyDecision(
                decision=PolicyDecisionType.DENY,
                reason="tool_trust_unknown",
                tool=tool_name,
                risk=RiskLevel.HIGH,
                rule_id="RULE_004_UNKNOWN_TRUST",
                details={"message": f"Tool '{tool_name}' has unknown trust level and cannot be auto-executed."},
            )

        # 4. Operation permissions check
        if "*" not in tool.allowed_operations and request.operation not in tool.allowed_operations:
            return PolicyDecision(
                decision=PolicyDecisionType.DENY,
                reason="operation_not_permitted",
                tool=tool_name,
                risk=tool.risk,
                rule_id="RULE_005_OPERATION_POLICY",
                details={
                    "requested_operation": request.operation,
                    "allowed_operations": tool.allowed_operations,
                },
            )

        # 5. Authentication check
        if tool.auth_required and not request.auth_provided:
            return PolicyDecision(
                decision=PolicyDecisionType.DENY,
                reason="authentication_required",
                tool=tool_name,
                risk=tool.risk,
                rule_id="RULE_006_AUTH_REQUIRED",
                details={"message": f"Tool '{tool_name}' requires valid credentials which were not provided."},
            )

        # 6. Argument security inspection
        valid_args, arg_error = ArgumentValidator.validate(request.arguments)
        if not valid_args:
            return PolicyDecision(
                decision=PolicyDecisionType.DENY,
                reason="unsafe_arguments_detected",
                tool=tool_name,
                risk=RiskLevel.HIGH,
                rule_id="RULE_007_ARG_VALIDATION",
                details={"error": arg_error},
            )

        # 7. Human approval requirement & risk evaluation
        if tool.require_human_approval or (self.strict_mode and tool.risk in (RiskLevel.HIGH, RiskLevel.CRITICAL)):
            return PolicyDecision(
                decision=PolicyDecisionType.REVIEW,
                reason="human_approval_required",
                tool=tool_name,
                risk=tool.risk,
                requires_approval=True,
                rule_id="RULE_008_HUMAN_APPROVAL",
                details={"message": f"Tool '{tool_name}' requires manual human approval before execution."},
            )

        # 8. All checks passed
        return PolicyDecision(
            decision=PolicyDecisionType.ALLOW,
            reason="policy_verified_allowed",
            tool=tool_name,
            risk=tool.risk,
            rule_id="RULE_000_PASSED",
            details={"message": f"Tool '{tool_name}' passed all ToolShield policy validations."},
        )
