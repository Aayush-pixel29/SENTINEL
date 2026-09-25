from enum import Enum
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class QualityTier(str, Enum):
    CHEAP = "cheap"
    STANDARD = "standard"
    REASONING = "reasoning"


class TaskRequirements(BaseModel):
    task_type: str = "code_verification"  # code_verification, critic, security_audit, summarization
    quality_tier: QualityTier = QualityTier.STANDARD
    max_cost_usd: Optional[float] = None
    max_latency_ms: Optional[float] = None
    require_structured_output: bool = True
    provider_preference: Optional[str] = None


class ModelRoute(BaseModel):
    provider: str
    model_name: str
    tier: QualityTier
    supports_structured_output: bool = True
    reasoning: str = ""
    fallback_chain: List[str] = Field(default_factory=list)


class ModelRouter:
    """Deterministic, rule-based router matching task requirements to model tiers."""

    MODELS_BY_TIER: Dict[QualityTier, List[Dict[str, Any]]] = {
        QualityTier.CHEAP: [
            {"provider": "gemini", "model_name": "gemini-2.5-flash", "cost_rank": 1},
            {"provider": "openai", "model_name": "gpt-4o-mini", "cost_rank": 2},
        ],
        QualityTier.STANDARD: [
            {"provider": "gemini", "model_name": "gemini-2.5-flash", "cost_rank": 1},
            {"provider": "openai", "model_name": "gpt-4o", "cost_rank": 3},
        ],
        QualityTier.REASONING: [
            {"provider": "openai", "model_name": "o3-mini", "cost_rank": 4},
            {"provider": "gemini", "model_name": "gemini-1.5-pro", "cost_rank": 4},
            {"provider": "anthropic", "model_name": "claude-3-5-sonnet", "cost_rank": 5},
        ],
    }

    def route(self, requirements: TaskRequirements) -> ModelRoute:
        tier = requirements.quality_tier

        # If strict low budget, enforce cheap tier
        if requirements.max_cost_usd is not None and requirements.max_cost_usd < 0.001:
            tier = QualityTier.CHEAP

        # If strict low latency (< 1000ms), prefer flash models
        if requirements.max_latency_ms is not None and requirements.max_latency_ms < 1000:
            return ModelRoute(
                provider="gemini",
                model_name="gemini-2.5-flash",
                tier=QualityTier.CHEAP,
                supports_structured_output=True,
                reasoning="Selected low-latency tier flash model for <1000ms latency budget.",
                fallback_chain=["gpt-4o-mini"],
            )

        candidates = self.MODELS_BY_TIER[tier]

        # Respect provider preference if provided
        if requirements.provider_preference:
            pref = [c for c in candidates if c["provider"] == requirements.provider_preference.lower()]
            if pref:
                chosen = pref[0]
                fallbacks = [c["model_name"] for c in candidates if c["model_name"] != chosen["model_name"]]
                return ModelRoute(
                    provider=chosen["provider"],
                    model_name=chosen["model_name"],
                    tier=tier,
                    supports_structured_output=True,
                    reasoning=f"Selected {chosen['model_name']} based on {tier.value} tier and provider preference '{requirements.provider_preference}'.",
                    fallback_chain=fallbacks,
                )

        # Default selection
        chosen = candidates[0]
        fallbacks = [c["model_name"] for c in candidates[1:]]

        return ModelRoute(
            provider=chosen["provider"],
            model_name=chosen["model_name"],
            tier=tier,
            supports_structured_output=True,
            reasoning=f"Selected {chosen['model_name']} for {tier.value} tier task requirements.",
            fallback_chain=fallbacks,
        )
