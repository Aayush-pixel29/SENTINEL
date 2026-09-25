from sentinel.metrics import PricingAdapter, CostTracker


def test_pricing_adapter_calculation():
    adapter = PricingAdapter()
    # 1000 input tokens, 500 output tokens on gemini-2.5-flash
    cost = adapter.calculate_cost("gemini-2.5-flash", input_tokens=1000, output_tokens=500)
    assert cost > 0
    assert cost < 0.01  # Should be tiny fraction of a cent


def test_cost_tracker_summary():
    tracker = CostTracker()
    m1 = tracker.record_usage(
        model="gemini-2.5-flash",
        provider="gemini",
        input_tokens=1200,
        output_tokens=240,
        latency_ms=821.5,
    )
    assert m1.total_tokens == 1440
    assert m1.latency_ms == 821.5
    assert m1.is_estimated is True
    assert m1.estimated_cost_usd > 0

    m2 = tracker.record_usage(
        model="gpt-4o-mini",
        provider="openai",
        input_tokens=500,
        output_tokens=100,
        latency_ms=450.0,
    )

    summary = tracker.get_summary()
    assert summary["total_input_tokens"] == 1700
    assert summary["total_output_tokens"] == 340
    assert summary["record_count"] == 2
