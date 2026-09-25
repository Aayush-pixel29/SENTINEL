from typing import Dict, Tuple, Optional
from pydantic import BaseModel


class ModelPricing(BaseModel):
    provider: str
    model_name: str
    input_cost_per_million: float
    output_cost_per_million: float


class PricingAdapter:
    """Calculates estimated token costs using normalized provider rate tables."""

    # Default per-1M tokens USD pricing estimates
    DEFAULT_RATES: Dict[str, ModelPricing] = {
        # Gemini rates
        "gemini-2.5-flash": ModelPricing(
            provider="gemini",
            model_name="gemini-2.5-flash",
            input_cost_per_million=0.075,
            output_cost_per_million=0.30,
        ),
        "gemini-1.5-pro": ModelPricing(
            provider="gemini",
            model_name="gemini-1.5-pro",
            input_cost_per_million=1.25,
            output_cost_per_million=5.00,
        ),
        # OpenAI rates
        "gpt-4o-mini": ModelPricing(
            provider="openai",
            model_name="gpt-4o-mini",
            input_cost_per_million=0.15,
            output_cost_per_million=0.60,
        ),
        "gpt-4o": ModelPricing(
            provider="openai",
            model_name="gpt-4o",
            input_cost_per_million=2.50,
            output_cost_per_million=10.00,
        ),
        "o3-mini": ModelPricing(
            provider="openai",
            model_name="o3-mini",
            input_cost_per_million=1.10,
            output_cost_per_million=4.40,
        ),
        # Anthropic rates
        "claude-3-5-sonnet": ModelPricing(
            provider="anthropic",
            model_name="claude-3-5-sonnet",
            input_cost_per_million=3.00,
            output_cost_per_million=15.00,
        ),
        # Local / Offline
        "local": ModelPricing(
            provider="local",
            model_name="local-model",
            input_cost_per_million=0.0,
            output_cost_per_million=0.0,
        ),
    }

    def __init__(self, custom_rates: Optional[Dict[str, ModelPricing]] = None):
        self.rates = dict(self.DEFAULT_RATES)
        if custom_rates:
            self.rates.update(custom_rates)

    def calculate_cost(
        self,
        model_name: str,
        input_tokens: int,
        output_tokens: int,
    ) -> float:
        pricing = self.rates.get(model_name.lower())
        if not pricing:
            # Fallback heuristic: assume standard tier rate
            pricing = self.rates["gemini-2.5-flash"]

        in_cost = (input_tokens / 1_000_000.0) * pricing.input_cost_per_million
        out_cost = (output_tokens / 1_000_000.0) * pricing.output_cost_per_million
        return round(in_cost + out_cost, 6)
