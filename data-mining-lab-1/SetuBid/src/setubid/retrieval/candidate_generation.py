"""Candidate Generation Module for SetuBid.

High-level candidate retrieval orchestration across corpus and labelled pairs.
"""

from __future__ import annotations
from typing import Dict, List, Set, Tuple, Any, Optional
import numpy as np
from setubid.retrieval.index import LSHIndex


def build_lsh_index(signatures_dict: Dict[str, np.ndarray], num_bands: int = 32, rows_per_band: int = 8) -> LSHIndex:
    """Builds and populates an LSHIndex from a dictionary of notice signatures."""
    idx = LSHIndex(num_bands=num_bands, rows_per_band=rows_per_band)
    for nid, sig in signatures_dict.items():
        idx.insert(nid, sig)
    return idx


def generate_candidates_for_notice(
    index: LSHIndex,
    notice_id: str,
    signature: Optional[np.ndarray] = None,
    candidate_cap: Optional[int] = None
) -> Set[str]:
    """Retrieves candidates for a specific notice from the index."""
    return index.query_candidates(notice_id, signature=signature, candidate_cap=candidate_cap)
