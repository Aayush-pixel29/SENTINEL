from typing import List, Set, Tuple, Any, Dict, Union
from pydantic import BaseModel, Field
from sentinel.sanitizer.patterns import SANITIZATION_RULES


class SanitizationResult(BaseModel):
    sanitized: bool = False
    redactions: int = 0
    categories: List[str] = Field(default_factory=list)
    safe_content: str = ""
    original_length: int = 0
    safe_length: int = 0


class OutputSanitizer:
    """Zero-loss security sanitizer redacting credentials, secrets, PII, and unsafe endpoints."""

    def __init__(self, custom_rules: Union[List[Tuple[str, Any, str]], None] = None):
        self.rules = custom_rules or SANITIZATION_RULES

    def sanitize(self, content: Union[str, Dict[str, Any], List[Any], Any]) -> SanitizationResult:
        if content is None:
            return SanitizationResult(safe_content="")

        # Normalize content to string for text evaluation
        if isinstance(content, (dict, list)):
            import json
            raw_text = json.dumps(content, ensure_ascii=False)
        else:
            raw_text = str(content)

        orig_len = len(raw_text)
        current_text = raw_text
        total_redactions = 0
        detected_categories: Set[str] = set()

        for category, pattern, replacement in self.rules:
            matches = pattern.findall(current_text)
            if matches:
                count = len(matches)
                total_redactions += count
                detected_categories.add(category)
                current_text = pattern.sub(replacement, current_text)

        is_sanitized = total_redactions > 0
        return SanitizationResult(
            sanitized=is_sanitized,
            redactions=total_redactions,
            categories=sorted(list(detected_categories)),
            safe_content=current_text,
            original_length=orig_len,
            safe_length=len(current_text),
        )
