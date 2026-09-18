"""Labelled pairs dataset I/O module.

Loads and structures ground-truth pairs for similarity benchmarking and evaluation.
"""

from __future__ import annotations
import csv
import os
from typing import Dict, List, Tuple, Any
import pandas as pd


def load_labelled_pairs(filepath: str) -> List[Dict[str, Any]]:
    """Load labelled pairs from CSV into list of dicts.
    
    Fields: notice_id_a, notice_id_b, label, adjudicated_by, adjudicated_on
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Labelled pairs file not found: {filepath}")

    pairs = []
    with open(filepath, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            pairs.append({
                "notice_id_a": row["notice_id_a"].strip(),
                "notice_id_b": row["notice_id_b"].strip(),
                "label": row["label"].strip().lower(),
                "adjudicated_by": row.get("adjudicated_by", "").strip(),
                "adjudicated_on": row.get("adjudicated_on", "").strip()
            })
    return pairs


def load_labelled_pairs_df(filepath: str) -> pd.DataFrame:
    """Load labelled pairs into pandas DataFrame."""
    pairs = load_labelled_pairs(filepath)
    return pd.DataFrame(pairs)
