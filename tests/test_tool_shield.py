from sentinel.shield import (
    ToolShield,
    ToolRegistry,
    ToolDefinition,
    TrustLevel,
    RiskLevel,
    PolicyDecisionType,
)


def test_toolshield_allows_verified_tool():
    shield = ToolShield()
    decision = shield.check_tool_call("read_repository", operation="read", arguments={"path": "src/main.py"})
    assert decision.decision == PolicyDecisionType.ALLOW
    assert decision.is_allowed() is True
    assert decision.reason == "policy_verified_allowed"


def test_toolshield_denies_unregistered_tool():
    shield = ToolShield()
    decision = shield.check_tool_call("malicious_stealth_exfiltrate")
    assert decision.decision == PolicyDecisionType.DENY
    assert decision.reason == "tool_not_allowlisted"


def test_toolshield_denies_blocked_tool():
    shield = ToolShield()
    decision = shield.check_tool_call("raw_bash_exec")
    assert decision.decision == PolicyDecisionType.DENY
    assert decision.reason in ("tool_explicitly_blocked", "tool_disabled")


def test_toolshield_denies_path_traversal():
    shield = ToolShield()
    decision = shield.check_tool_call("read_repository", operation="read", arguments={"path": "../../etc/shadow"})
    assert decision.decision == PolicyDecisionType.DENY
    assert decision.reason == "unsafe_arguments_detected"


def test_toolshield_denies_unauthorized_operation():
    shield = ToolShield()
    decision = shield.check_tool_call("read_repository", operation="write_direct_to_disk", arguments={"data": "..."})
    assert decision.decision == PolicyDecisionType.DENY
    assert decision.reason == "operation_not_permitted"


def test_toolshield_requires_human_approval():
    registry = ToolRegistry()
    registry.register_tool(
        ToolDefinition(
            name="deploy_to_prod",
            trust_level=TrustLevel.VERIFIED,
            risk=RiskLevel.HIGH,
            require_human_approval=True,
            allowed_operations=["deploy"],
        )
    )
    shield = ToolShield(registry=registry)
    decision = shield.check_tool_call("deploy_to_prod", operation="deploy")
    assert decision.decision == PolicyDecisionType.REVIEW
    assert decision.requires_approval is True
    assert decision.reason == "human_approval_required"
