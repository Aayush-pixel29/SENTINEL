import os
import json
from typing import Dict, Any
from anthropic import Anthropic, APIError

from sentinel.ai.prompts import SYSTEM_PROMPT
from sentinel.models import AIReviewResult, Finding, Classification, CheckStatus

def run_ai_review(context: str) -> AIReviewResult:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return AIReviewResult(
            summary="AI review unavailable. Set ANTHROPIC_API_KEY.",
            findings=[],
            status=CheckStatus.NOT_AVAILABLE
        )

    client = Anthropic(api_key=api_key)

    tools = [
        {
            "name": "report_findings",
            "description": "Report the findings of the code review",
            "input_schema": {
                "type": "object",
                "properties": {
                    "summary": {
                        "type": "string",
                        "description": "A brief summary of the review"
                    },
                    "findings": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "title": {"type": "string"},
                                "severity": {"type": "string", "enum": ["LOW", "MEDIUM", "HIGH", "CRITICAL"]},
                                "file": {"type": "string"},
                                "line": {"type": "integer"},
                                "description": {"type": "string"},
                                "reasoning": {"type": "string"},
                                "recommendation": {"type": "string"}
                            },
                            "required": ["title", "severity", "description", "reasoning", "recommendation"]
                        }
                    }
                },
                "required": ["summary", "findings"]
            }
        }
    ]

    try:
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            tools=tools,
            tool_choice={"type": "tool", "name": "report_findings"},
            messages=[
                {"role": "user", "content": context}
            ]
        )
        
        # Extract the tool use payload
        tool_use = next((block for block in response.content if block.type == 'tool_use'), None)
        if not tool_use:
             return AIReviewResult(
                summary="AI model failed to return structured findings.",
                findings=[],
                status=CheckStatus.ERROR
            )
            
        data = tool_use.input
        
        findings = []
        for item in data.get("findings", []):
            findings.append(Finding(
                id="ai-" + str(hash(item.get("title", "")))[:8],
                source="ai-critic",
                classification=Classification.UNCONFIRMED,
                severity=item.get("severity", "MEDIUM"),
                title=item.get("title"),
                description=item.get("description"),
                file=item.get("file"),
                line=item.get("line"),
                evidence=item.get("reasoning"),
                recommendation=item.get("recommendation")
            ))
            
        return AIReviewResult(
            summary=data.get("summary", "Review complete."),
            findings=findings,
            status=CheckStatus.PASSED
        )
        
    except APIError as e:
        return AIReviewResult(
            summary=f"API request failed: {str(e)}",
            findings=[],
            status=CheckStatus.ERROR
        )
    except Exception as e:
        return AIReviewResult(
            summary=f"AI review failed: {str(e)}",
            findings=[],
            status=CheckStatus.ERROR
        )
