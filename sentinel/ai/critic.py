import os
import json
from typing import List
from pydantic import BaseModel

from sentinel.ai.prompts import SYSTEM_PROMPT
from sentinel.models import AIReviewResult, Finding, Classification, CheckStatus


class AIFinding(BaseModel):
    """Schema for a single AI finding — used as Gemini response_schema."""
    title: str
    severity: str
    file: str = ""
    line: int = 0
    description: str
    reasoning: str
    recommendation: str


class AIReviewResponse(BaseModel):
    """Schema for the complete AI review — used as Gemini response_schema."""
    summary: str
    findings: List[AIFinding] = []


def run_ai_review(context: str) -> AIReviewResult:
    """Run independent AI code review using Google Gemini."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return AIReviewResult(
            summary="AI review unavailable. Set GEMINI_API_KEY environment variable.",
            findings=[],
            status=CheckStatus.NOT_AVAILABLE,
            provider="gemini",
        )

    try:
        from google import genai

        client = genai.Client(api_key=api_key)

        prompt = f"{SYSTEM_PROMPT}\n\n---\n\n{context}"

        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=prompt,
            config={
                "response_mime_type": "application/json",
                "response_schema": AIReviewResponse,
            },
        )

        data = response.parsed
        if data is None:
            # Fallback: try parsing the text manually
            try:
                raw = json.loads(response.text)
                data = AIReviewResponse.model_validate(raw)
            except Exception:
                return AIReviewResult(
                    summary="AI model returned unparseable output.",
                    findings=[],
                    status=CheckStatus.ERROR,
                    provider="gemini",
                )

        findings: List[Finding] = []
        for item in data.findings:
            findings.append(Finding(
                id=f"ai-{abs(hash(item.title)) % 100000}",
                source="ai-critic",
                classification=Classification.UNCONFIRMED,
                severity=item.severity or "MEDIUM",
                title=item.title,
                description=item.description,
                file=item.file or None,
                line=item.line if item.line and item.line > 0 else None,
                evidence=item.reasoning,
                recommendation=item.recommendation,
            ))

        return AIReviewResult(
            summary=data.summary,
            findings=findings,
            status=CheckStatus.PASSED,
            provider="gemini",
        )

    except Exception as e:
        return AIReviewResult(
            summary=f"AI review failed: {str(e)}",
            findings=[],
            status=CheckStatus.ERROR,
            provider="gemini",
        )
