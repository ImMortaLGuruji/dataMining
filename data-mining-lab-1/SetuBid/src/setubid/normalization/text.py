"""Text Normalization Module for SetuBid.

Handles text sanitization, case normalization, punctuation handling,
and optional boilerplate suppression.
"""

from __future__ import annotations
import re
import unicodedata
from typing import Optional


# Known preamble blocks from portal_profiles.md
NPAS_PREAMBLE_PATTERNS = [
    r"NATIONAL\s+PROCUREMENT\s+AGGREGATION\s+SERVICE.*?(?:TERMS\s+AND\s+CONDITIONS|APPLICABLE\s+LAW|DISCLAIMER)",
    r"NATIONAL\s+PROCUREMENT\s+AGGREGATION\s+SERVICE",
]

SPC_PREAMBLE_PATTERNS = [
    r"STATE\s+PROCUREMENT\s+CELL.*?(?:TERMS\s+AND\s+CONDITIONS|APPLICABLE\s+LAW|DISCLAIMER)",
    r"STATE\s+PROCUREMENT\s+CELL",
]

DISCLAIMER_PATTERNS = [
    r"DISCLAIMER:.*?(?:REPRESENTATION|WARRANTY|ALL\s+RIGHTS\s+RESERVED).*",
    r"DISCLAIMER:.*"
]


def clean_text(text: Optional[str], lowercase: bool = True) -> str:
    """Basic text sanitization: Unicode normalization, optional lowercasing, whitespace collapse."""
    if not text:
        return ""
    # NFKD normalization
    text = unicodedata.normalize("NFKD", str(text))
    if lowercase:
        text = text.lower()
    # Replace non-alphanumeric except basic spacing with single space
    text = re.sub(r"[^\w\s]", " ", text)
    # Collapse multiple whitespace
    text = re.sub(r"\s+", " ", text).strip()
    return text


def strip_portal_boilerplate(text: str, portal_id: Optional[str] = None) -> str:
    """Targeted boilerplate suppression based on portal profile analysis.
    
    Portals P001, P002, P005 carry ~1,400 chars of NPAS boilerplate.
    Portals P003, P004, P006 carry ~1,400 chars of SPC boilerplate.
    """
    if not text:
        return ""

    cleaned = text
    # If specific portal or general detection
    if portal_id in ("P001", "P002", "P005") or "NATIONAL PROCUREMENT AGGREGATION SERVICE" in text.upper():
        for pat in NPAS_PREAMBLE_PATTERNS:
            cleaned = re.sub(pat, " ", cleaned, flags=re.IGNORECASE | re.DOTALL)

    if portal_id in ("P003", "P004", "P006") or "STATE PROCUREMENT CELL" in text.upper():
        for pat in SPC_PREAMBLE_PATTERNS:
            cleaned = re.sub(pat, " ", cleaned, flags=re.IGNORECASE | re.DOTALL)

    # General disclaimer removal if at end
    for pat in DISCLAIMER_PATTERNS:
        cleaned = re.sub(pat, " ", cleaned, flags=re.IGNORECASE)

    return re.sub(r"\s+", " ", cleaned).strip()
