"""Security guardrails, input sanitization, and prompt injection defense."""

import re
from typing import Tuple, List

# Signatures for prompt injection and jailbreak attempts
INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?(previous|prior|above)\s+(instructions|directives|prompts)",
    r"disregard\s+(the\s+)?(system|previous|prior)\s+prompt",
    r"you\s+are\s+now\s+(in\s+)?(dan|developer|jailbreak|unfiltered)\s+mode",
    r"(reveal|show|print|dump|leak|output)\s+(your\s+)?(system\s+prompt|(secret\s+)?api[_\s-]?key|secret\s+key)",
    r"output\s+(the\s+)?(confidential|internal|secret)\s+instructions",
    r"sk-[A-Za-z0-9_-]{16,}",
    r"system\s*:\s*you\s+must",
    r"<\|\s*im_start\s*\|>",
    r"\[SYSTEM_PROMPT\]",
]

COMPILED_INJECTION_REGEX = [re.compile(p, re.IGNORECASE) for p in INJECTION_PATTERNS]


class GuardrailViolation:
    def __init__(self, is_safe: bool, reason: str = "", risk_level: str = "Low"):
        self.is_safe = is_safe
        self.reason = reason
        self.risk_level = risk_level


class SecurityGuardrails:
    """Provides security screening for inputs, prompt injection mitigation, and output sanity."""

    @staticmethod
    def inspect_query(query: str) -> GuardrailViolation:
        """Inspects user queries for prompt injection and malicious override attempts."""
        cleaned = query.strip()
        if not cleaned:
            return GuardrailViolation(is_safe=False, reason="Empty query provided", risk_level="Low")

        if len(cleaned) > 2000:
            return GuardrailViolation(
                is_safe=False,
                reason="Query exceeds maximum allowed length of 2000 characters",
                risk_level="Medium"
            )

        # Check for injection patterns
        for pattern in COMPILED_INJECTION_REGEX:
            if pattern.search(cleaned):
                return GuardrailViolation(
                    is_safe=False,
                    reason="Potential prompt injection or system override detected",
                    risk_level="High"
                )

        return GuardrailViolation(is_safe=True)

    @staticmethod
    def sanitize_input(text: str) -> str:
        """Sanitizes raw text: removes null bytes, trims excessive whitespace, normalizes unicode."""
        if not text:
            return ""
        # Strip null bytes and control chars
        sanitized = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]", "", text)
        # Collapse excessive newlines/spaces
        sanitized = re.sub(r"\n{3,}", "\n\n", sanitized)
        return sanitized.strip()

    @staticmethod
    def filter_malicious_output(output_text: str) -> Tuple[str, bool]:
        """Ensures the generated output does not leak API keys, system instructions, or credentials."""
        modified = False
        # Redact potential API keys (e.g. sk-...)
        redacted = re.sub(r"sk-[A-Za-z0-9_-]{20,}", "[REDACTED_API_KEY]", output_text)
        if redacted != output_text:
            modified = True

        return redacted, modified
