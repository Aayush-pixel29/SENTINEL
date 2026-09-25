from sentinel.ai.router import ModelRouter, TaskRequirements, QualityTier


def test_model_router_cheap_tier():
    router = ModelRouter()
    req = TaskRequirements(
        task_type="quick_lint",
        quality_tier=QualityTier.CHEAP,
    )
    route = router.route(req)
    assert route.tier == QualityTier.CHEAP
    assert route.model_name in ("gemini-2.5-flash", "gpt-4o-mini")


def test_model_router_reasoning_tier():
    router = ModelRouter()
    req = TaskRequirements(
        task_type="security_audit",
        quality_tier=QualityTier.REASONING,
    )
    route = router.route(req)
    assert route.tier == QualityTier.REASONING
    assert route.model_name in ("o3-mini", "gemini-1.5-pro", "claude-3-5-sonnet")


def test_model_router_low_latency_override():
    router = ModelRouter()
    req = TaskRequirements(
        task_type="code_verification",
        quality_tier=QualityTier.REASONING,
        max_latency_ms=800,  # Strict sub-second SLA
    )
    route = router.route(req)
    # Low latency SLA overrides to Flash model
    assert route.model_name == "gemini-2.5-flash"
