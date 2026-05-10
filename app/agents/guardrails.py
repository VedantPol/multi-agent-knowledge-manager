from __future__ import annotations

import re

from app.models import SafetyReport


INJECTION_PATTERNS = [
    re.compile(pattern, re.IGNORECASE)
    for pattern in [
        r"\bignore (all )?(previous|prior|above) (instructions|rules|prompts)\b",
        r"\breveal (the )?(system|developer) prompt\b",
        r"\bdisregard (safety|guardrails|policy)\b",
        r"\byou are now\b.*\bdeveloper mode\b",
        r"\bdo anything now\b",
        r"\bexfiltrate\b|\bapi[_ -]?key\b|\bsecret token\b",
    ]
]


def check_prompt_injection(text: str) -> SafetyReport:
    reasons = []
    for pattern in INJECTION_PATTERNS:
        if pattern.search(text):
            reasons.append(f"Matched injection pattern: {pattern.pattern}")
    return SafetyReport(blocked=bool(reasons), reasons=reasons)


def sanitize_context(text: str) -> str:
    lines = []
    for line in text.splitlines():
        report = check_prompt_injection(line)
        if report.blocked:
            lines.append("[Filtered possible prompt-injection instruction from source document.]")
        else:
            lines.append(line)
    return "\n".join(lines)


def split_claims(answer: str) -> list[str]:
    sentences = re.split(r"(?<=[.!?])\s+", answer.strip())
    claims = []
    for sentence in sentences:
        cleaned = sentence.strip()
        if len(cleaned) >= 24 and not cleaned.lower().startswith(("i cannot", "i don't know", "there is not enough")):
            claims.append(cleaned)
    return claims[:8]
