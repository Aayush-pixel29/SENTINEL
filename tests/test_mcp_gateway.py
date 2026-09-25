from sentinel.mcp import MCPGateway, MCPToolSchema, MCPToolCallRequest
from sentinel.shield import TrustLevel, RiskLevel


def test_mcp_gateway_allowed_and_sanitized_execution():
    gw = MCPGateway()

    schema = MCPToolSchema(
        name="get_database_status",
        description="Get database connection string and health status",
        inputSchema={"type": "object"},
    )

    def handler(args):
        return "Connected to postgres://service_user:hunter2_secret_pwd@10.0.0.5:5432/app_db"

    gw.register_mcp_tool(
        schema=schema,
        handler=handler,
        trust_level=TrustLevel.VERIFIED,
        risk=RiskLevel.LOW,
    )

    req = MCPToolCallRequest(name="get_database_status", arguments={})
    resp = gw.execute_tool(req)

    assert resp.success is True
    assert resp.sanitized is True
    assert "hunter2_secret_pwd" not in str(resp.output)
    assert resp.policy_decision == "ALLOW"


def test_mcp_gateway_denies_blocked_tool():
    gw = MCPGateway()

    schema = MCPToolSchema(
        name="execute_unrestricted_script",
        description="Runs raw scripts",
    )

    def handler(args):
        return "Executed"

    gw.register_mcp_tool(
        schema=schema,
        handler=handler,
        trust_level=TrustLevel.BLOCKED,
        risk=RiskLevel.CRITICAL,
    )

    req = MCPToolCallRequest(name="execute_unrestricted_script", arguments={})
    resp = gw.execute_tool(req)

    assert resp.success is False
    assert "Policy Blocked" in resp.error
    assert resp.policy_decision == "DENY"
