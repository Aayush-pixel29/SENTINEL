from typing import Dict, List, Optional
from sentinel.shield.models import ToolDefinition, TrustLevel, RiskLevel


class ToolRegistry:
    """Explicit tool registry storing verified metadata and security contracts."""

    def __init__(self):
        self._tools: Dict[str, ToolDefinition] = {}
        self._register_default_tools()

    def _register_default_tools(self):
        # Default safe tools
        self.register_tool(
            ToolDefinition(
                name="read_repository",
                description="Safely read repository files and directory structures",
                source="builtin",
                trust_level=TrustLevel.VERIFIED,
                risk=RiskLevel.LOW,
                allowed_operations=["read", "list", "search"],
                enabled=True,
            )
        )
        self.register_tool(
            ToolDefinition(
                name="git_diff_viewer",
                description="View staged and unstaged git diffs",
                source="builtin",
                trust_level=TrustLevel.VERIFIED,
                risk=RiskLevel.LOW,
                allowed_operations=["diff", "status"],
                enabled=True,
            )
        )
        self.register_tool(
            ToolDefinition(
                name="run_tests",
                description="Run deterministic local test suites (pytest)",
                source="builtin",
                trust_level=TrustLevel.VERIFIED,
                risk=RiskLevel.MEDIUM,
                allowed_operations=["pytest"],
                enabled=True,
            )
        )
        self.register_tool(
            ToolDefinition(
                name="code_linter",
                description="Run static code analysis and linting (ruff, semgrep)",
                source="builtin",
                trust_level=TrustLevel.VERIFIED,
                risk=RiskLevel.LOW,
                allowed_operations=["lint", "scan"],
                enabled=True,
            )
        )
        # Blocked dangerous tool examples
        self.register_tool(
            ToolDefinition(
                name="raw_bash_exec",
                description="Execute unrestricted arbitrary shell commands on host",
                source="untrusted",
                trust_level=TrustLevel.BLOCKED,
                risk=RiskLevel.CRITICAL,
                allowed_operations=[],
                enabled=False,
            )
        )
        self.register_tool(
            ToolDefinition(
                name="arbitrary_network_fetch",
                description="Unrestricted outbound HTTP requests to internal/external networks",
                source="untrusted",
                trust_level=TrustLevel.BLOCKED,
                risk=RiskLevel.CRITICAL,
                allowed_operations=[],
                enabled=False,
            )
        )

    def register_tool(self, tool: ToolDefinition) -> None:
        self._tools[tool.name] = tool

    def unregister_tool(self, tool_name: str) -> None:
        self._tools.pop(tool_name, None)

    def get_tool(self, tool_name: str) -> Optional[ToolDefinition]:
        return self._tools.get(tool_name)

    def list_tools(self) -> List[ToolDefinition]:
        return list(self._tools.values())

    def has_tool(self, tool_name: str) -> bool:
        return tool_name in self._tools
