"""Notice text representation module.

Implements token-level and character n-gram shingle representations for notices.
"""

from __future__ import annotations
import re
from typing import Set, List, Optional
from setubid.normalization.text import clean_text, strip_portal_boilerplate


def extract_word_tokens(text: str, lowercase: bool = True, strip_boilerplate: bool = False, portal_id: Optional[str] = None) -> Set[str]:
    """Candidate A: Word-level token representation.
    
    Splits cleaned text into unique words (length >= 2).
    """
    if strip_boilerplate:
        text = strip_portal_boilerplate(text, portal_id)
    cleaned = clean_text(text, lowercase=lowercase)
    tokens = re.findall(r"\b\w{2,}\b", cleaned)
    return set(tokens)


def extract_char_ngrams(text: str, n: int = 3, lowercase: bool = True, strip_boilerplate: bool = False, portal_id: Optional[str] = None) -> Set[str]:
    """Candidate B1: Fixed-size character n-gram representation."""
    if strip_boilerplate:
        text = strip_portal_boilerplate(text, portal_id)
    cleaned = clean_text(text, lowercase=lowercase)
    if len(cleaned) < n:
        return {cleaned} if cleaned else set()
    return {cleaned[i : i + n] for i in range(len(cleaned) - n + 1)}


def extract_char_ngrams_range(text: str, min_n: int = 3, max_n: int = 5, lowercase: bool = True, strip_boilerplate: bool = False, portal_id: Optional[str] = None) -> Set[str]:
    """Candidate B2: Multi-scale character n-gram representation (e.g. 3-grams to 5-grams)."""
    if strip_boilerplate:
        text = strip_portal_boilerplate(text, portal_id)
    cleaned = clean_text(text, lowercase=lowercase)
    ngrams = set()
    length = len(cleaned)
    for n in range(min_n, max_n + 1):
        if length >= n:
            ngrams.update(cleaned[i : i + n] for i in range(length - n + 1))
    if not ngrams and cleaned:
        ngrams.add(cleaned)
    return ngrams
