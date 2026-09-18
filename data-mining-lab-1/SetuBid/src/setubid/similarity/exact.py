"""Exact Similarity Calculation Module for SetuBid.

Defines deterministic mathematical similarity functions between shingle sets
and composite notice similarity.
"""

from __future__ import annotations
from typing import Set, Dict, Any, Optional
from datetime import datetime


def jaccard_similarity(set_a: Set[Any], set_b: Set[Any]) -> float:
    """Exact Jaccard similarity between two sets:
    
    J(A, B) = |A ∩ B| / |A ∪ B|
    """
    if not set_a and not set_b:
        return 1.0
    if not set_a or not set_b:
        return 0.0
    intersection_len = len(set_a.intersection(set_b))
    union_len = len(set_a) + len(set_b) - intersection_len
    if union_len == 0:
        return 0.0
    return float(intersection_len) / float(union_len)


def compute_exact_notice_similarity(
    rep_body_a: Set[Any],
    rep_body_b: Set[Any],
    rep_title_a: Optional[Set[Any]] = None,
    rep_title_b: Optional[Set[Any]] = None,
    weight_body: float = 0.8,
    weight_title: float = 0.2
) -> float:
    """Computes exact composite text similarity between two notices.
    
    S_text(A, B) = w_body * J(body_A, body_B) + w_title * J(title_A, title_B)
    """
    sim_body = jaccard_similarity(rep_body_a, rep_body_b)
    if rep_title_a is not None and rep_title_b is not None:
        sim_title = jaccard_similarity(rep_title_a, rep_title_b)
        return float(weight_body * sim_body + weight_title * sim_title)
    return float(sim_body)


def evaluate_field_compatibility(notice_a: Dict[str, Any], notice_b: Dict[str, Any]) -> Dict[str, Any]:
    """Evaluates non-text field compatibility (value and closing date)."""
    # Estimated Value comparison
    val_a = notice_a.get("estimated_value")
    val_b = notice_b.get("estimated_value")
    val_match = False
    val_diff = None
    if val_a is not None and val_b is not None:
        try:
            fa = float(str(val_a).replace(",", ""))
            fb = float(str(val_b).replace(",", ""))
            val_diff = abs(fa - fb)
            val_match = (val_diff == 0.0)
        except ValueError:
            pass

    # Closing date comparison
    cls_a = notice_a.get("closing_date")
    cls_b = notice_b.get("closing_date")
    cls_delta = None
    if cls_a and cls_b:
        try:
            da = datetime.strptime(str(cls_a)[:10], "%Y-%m-%d")
            db = datetime.strptime(str(cls_b)[:10], "%Y-%m-%d")
            cls_delta = abs((da - db).days)
        except ValueError:
            pass

    return {
        "val_match": val_match,
        "val_diff": val_diff,
        "cls_delta_days": cls_delta
    }
