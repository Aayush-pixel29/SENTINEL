from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from sentinel.metrics.pricing import PricingAdapter


class ExecutionMetrics(BaseModel):
    model: str = "gemini-2.5-flash"
    provider: str = "gemini"
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    latency_ms: float = 0.0
    estimated_cost_usd: float = 0.0
    is_estimated: bool = True
    metadata: Dict[str, Any] = Field(default_factory=dict)


class CostTracker:
    """Tracks token consumption, latency benchmarks, and cost estimates across runs."""

    def __init__(self, pricing_adapter: Optional[PricingAdapter] = None):
        self.pricing_adapter = pricing_adapter or PricingAdapter()
        self._total_input_tokens = 0
        self._total_output_tokens = 0
        self._total_cost_usd = 0.0
        self._total_latency_ms = 0.0
        self._records = []

    def record_usage(
        self,
        model: str,
        provider: str,
        input_tokens: int,
        output_tokens: int,
        latency_ms: float,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ExecutionMetrics:
        cost = self.pricing_adapter.calculate_cost(model, input_tokens, output_tokens)
        metrics = ExecutionMetrics(
            model=model,
            provider=provider,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=input_tokens + output_tokens,
            latency_ms=round(latency_ms, 2),
            estimated_cost_usd=cost,
            is_estimated=True,
            metadata=metadata or {},
        )
        self._total_input_tokens += input_tokens
        self._total_output_tokens += output_tokens
        self._total_cost_usd += cost
        self._total_latency_ms += latency_ms
        self._records.append(metrics)
        return metrics

    def get_summary(self) -> Dict[str, Any]:
        return {
            "total_input_tokens": self._total_input_tokens,
            "total_output_tokens": self._total_output_tokens,
            "total_tokens": self._total_input_tokens + self._total_output_tokens,
            "total_estimated_cost_usd": round(self._total_cost_usd, 6),
            "total_latency_ms": round(self._total_latency_ms, 2),
            "record_count": len(self._records),
        }
