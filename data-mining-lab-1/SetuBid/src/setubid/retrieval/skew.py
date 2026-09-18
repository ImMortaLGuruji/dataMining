"""Workload Skew and Mitigation Module for SetuBid.

Analyzes candidate distribution skew and implements targeted mitigations.
"""

from __future__ import annotations
from collections import defaultdict
from typing import Dict, List, Tuple, Any, Optional
import numpy as np
import pandas as pd


def compute_workload_metrics(per_notice_candidates: Dict[str, int], notice_portals: Dict[str, str]) -> Dict[str, Any]:
    """Computes comprehensive workload statistics: percentiles, cumulative work, portal breakdown."""
    nids = list(per_notice_candidates.keys())
    counts = np.array([per_notice_candidates[nid] for nid in nids])
    total_notices = len(counts)
    total_comparisons = int(np.sum(counts))

    mean_c = float(np.mean(counts))
    median_c = float(np.median(counts))
    p90_c = float(np.percentile(counts, 90))
    p95_c = float(np.percentile(counts, 95))
    p99_c = float(np.percentile(counts, 99))
    max_c = int(np.max(counts))

    # Cumulative workload analysis
    sorted_indices = np.argsort(counts)[::-1]  # descending
    sorted_counts = counts[sorted_indices]

    def work_pct_at_quantile(top_fraction: float) -> float:
        top_k = int(np.ceil(total_notices * top_fraction))
        work_top_k = np.sum(sorted_counts[:top_k])
        return round(100.0 * work_top_k / max(1, total_comparisons), 2)

    top_1_pct_work = work_pct_at_quantile(0.01)
    top_5_pct_work = work_pct_at_quantile(0.05)
    top_10_pct_work = work_pct_at_quantile(0.10)
    top_20_pct_work = work_pct_at_quantile(0.20)

    # Per-portal workload breakdown
    portal_work = defaultdict(list)
    for nid, cnt in per_notice_candidates.items():
        p = notice_portals.get(nid, "UNKNOWN")
        portal_work[p].append(cnt)

    portal_records = []
    for p, p_counts in portal_work.items():
        arr = np.array(p_counts)
        tot_work = int(np.sum(arr))
        portal_records.append({
            "portal_id": p,
            "notices": len(arr),
            "mean_candidates": round(float(np.mean(arr)), 1),
            "median_candidates": float(np.median(arr)),
            "p95_candidates": float(np.percentile(arr, 95)),
            "max_candidates": int(np.max(arr)),
            "total_candidate_work": tot_work,
            "pct_of_total_work": round(100.0 * tot_work / max(1, total_comparisons), 2)
        })

    portal_df = pd.DataFrame(portal_records).sort_values(by="total_candidate_work", ascending=False)

    return {
        "total_notices": total_notices,
        "total_candidate_comparisons": total_comparisons,
        "distribution": {
            "mean": round(mean_c, 1),
            "median": median_c,
            "p90": p90_c,
            "p95": p95_c,
            "p99": p99_c,
            "max": max_c
        },
        "cumulative_concentration": {
            "top_1_pct_notices_generate_work_pct": top_1_pct_work,
            "top_5_pct_notices_generate_work_pct": top_5_pct_work,
            "top_10_pct_notices_generate_work_pct": top_10_pct_work,
            "top_20_pct_notices_generate_work_pct": top_20_pct_work
        },
        "portal_workload_df": portal_df
    }
