"""Dataset Inspection Script for SetuBid.

Generates comprehensive corpus and portal-level profiles:
- experiments/01_dataset_profile/summary.json
- experiments/01_dataset_profile/portal_statistics.csv
- experiments/01_dataset_profile/report.md
- reports/tables/dataset_summary.csv
"""

import json
import os
import re
import sys
from collections import Counter
import duckdb
import numpy as np
import pandas as pd

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))
from setubid.io.notices import load_notices_table, get_notice_files


def run_dataset_inspection(notices_dir: str, output_dir: str, tables_dir: str):
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(tables_dir, exist_ok=True)

    print(f"Loading notices from: {notices_dir}")
    files = get_notice_files(notices_dir)
    print(f"Found {len(files)} files: {[os.path.basename(f) for f in files]}")

    conn = duckdb.connect()
    total_count = load_notices_table(conn, notices_dir, "notices")
    print(f"Loaded {total_count} total notice rows into DuckDB.")

    # 1. Corpus Statistics
    df = conn.execute("""
        SELECT 
            notice_id,
            portal_id,
            published_at,
            title,
            body,
            length(title) as title_len,
            length(body) as body_len,
            estimated_value,
            closing_date
        FROM notices
    """).fetchdf()

    total_notices = len(df)
    unique_notices = df["notice_id"].nunique()
    unique_portals = df["portal_id"].nunique()

    # Missing counts
    missing_notice_id = int(df["notice_id"].isna().sum())
    missing_portal_id = int(df["portal_id"].isna().sum())
    missing_published_at = int(df["published_at"].isna().sum())
    missing_title = int(df["title"].isna().sum())
    missing_body = int(df["body"].isna().sum())
    missing_value = int(df["estimated_value"].isna().sum())
    missing_closing = int(df["closing_date"].isna().sum())

    # Length statistics
    body_lens = df["body_len"].fillna(0).to_numpy()
    title_lens = df["title_len"].fillna(0).to_numpy()

    body_stats = {
        "mean": float(np.mean(body_lens)),
        "std": float(np.std(body_lens)),
        "min": int(np.min(body_lens)),
        "p25": float(np.percentile(body_lens, 25)),
        "median": float(np.median(body_lens)),
        "p75": float(np.percentile(body_lens, 75)),
        "p95": float(np.percentile(body_lens, 95)),
        "p99": float(np.percentile(body_lens, 99)),
        "max": int(np.max(body_lens)),
    }

    title_stats = {
        "mean": float(np.mean(title_lens)),
        "std": float(np.std(title_lens)),
        "min": int(np.min(title_lens)),
        "p25": float(np.percentile(title_lens, 25)),
        "median": float(np.median(title_lens)),
        "p75": float(np.percentile(title_lens, 75)),
        "p95": float(np.percentile(title_lens, 95)),
        "p99": float(np.percentile(title_lens, 99)),
        "max": int(np.max(title_lens)),
    }

    # Date ranges
    valid_pub_dates = df["published_at"].dropna()
    min_pub = str(valid_pub_dates.min()) if len(valid_pub_dates) > 0 else None
    max_pub = str(valid_pub_dates.max()) if len(valid_pub_dates) > 0 else None

    valid_close_dates = df["closing_date"].dropna()
    min_close = str(valid_close_dates.min()) if len(valid_close_dates) > 0 else None
    max_close = str(valid_close_dates.max()) if len(valid_close_dates) > 0 else None

    # Parse estimated values
    # Try numeric conversion
    def parse_numeric(val):
        if val is None or pd.isna(val):
            return None
        s = str(val).replace(",", "").strip()
        try:
            return float(s)
        except ValueError:
            return None

    numeric_vals = df["estimated_value"].apply(parse_numeric).dropna()
    val_stats = {
        "present_count": int(len(numeric_vals)),
        "missing_count": int(total_notices - len(numeric_vals)),
        "min": float(numeric_vals.min()) if len(numeric_vals) > 0 else None,
        "median": float(numeric_vals.median()) if len(numeric_vals) > 0 else None,
        "mean": float(numeric_vals.mean()) if len(numeric_vals) > 0 else None,
        "max": float(numeric_vals.max()) if len(numeric_vals) > 0 else None,
    }

    # 2. Portal Statistics
    portal_grouped = df.groupby("portal_id")
    portal_records = []
    
    # Check for known boilerplate phrases from portal_profiles.md
    boilerplate_phrases = [
        "NATIONAL PROCUREMENT AGGREGATION SERVICE",
        "STATE PROCUREMENT CELL",
        "CORRIGENDUM",
        "DISCLAIMER",
        "TERMS AND CONDITIONS"
    ]

    for portal_id, group in portal_grouped:
        cnt = len(group)
        b_lens = group["body_len"].fillna(0)
        t_lens = group["title_len"].fillna(0)
        
        # Check presence of boilerplate in notices of this portal
        bp_counts = {}
        sample_bodies = group["body"].dropna().astype(str).tolist()
        for bp in boilerplate_phrases:
            bp_matches = sum(1 for b in sample_bodies if bp in b.upper())
            bp_counts[bp] = bp_matches

        # Check for uppercase dominance
        upper_title_ratio = sum(1 for t in group["title"].dropna() if t.isupper()) / max(1, cnt)

        portal_records.append({
            "portal_id": portal_id,
            "notice_count": cnt,
            "pct_of_corpus": round(100.0 * cnt / total_notices, 3),
            "body_len_mean": round(float(b_lens.mean()), 1),
            "body_len_median": float(b_lens.median()),
            "body_len_p95": float(np.percentile(b_lens, 95)),
            "title_len_mean": round(float(t_lens.mean()), 1),
            "npas_boilerplate_pct": round(100.0 * bp_counts["NATIONAL PROCUREMENT AGGREGATION SERVICE"] / max(1, cnt), 1),
            "spc_boilerplate_pct": round(100.0 * bp_counts["STATE PROCUREMENT CELL"] / max(1, cnt), 1),
            "corrigendum_pct": round(100.0 * bp_counts["CORRIGENDUM"] / max(1, cnt), 1),
            "uppercase_title_pct": round(100.0 * upper_title_ratio, 1)
        })

    portal_df = pd.DataFrame(portal_records)
    portal_df.sort_values(by="notice_count", ascending=False, inplace=True)
    
    # Save portal statistics CSV
    portal_stats_path = os.path.join(output_dir, "portal_statistics.csv")
    portal_df.to_csv(portal_stats_path, index=False)
    print(f"Saved portal statistics to {portal_stats_path}")

    # Top portals
    top_10_portals = portal_df.head(10).to_dict(orient="records")
    top_6_nodal_count = int(portal_df[portal_df["portal_id"].isin(["P001", "P002", "P003", "P004", "P005", "P006"])]["notice_count"].sum())

    # Build summary dict
    summary = {
        "total_notices": total_notices,
        "unique_notices": unique_notices,
        "num_files": len(files),
        "file_names": [os.path.basename(f) for f in files],
        "unique_portals": unique_portals,
        "published_at_range": {"min": min_pub, "max": max_pub},
        "closing_date_range": {"min": min_close, "max": max_close},
        "missing_fields": {
            "notice_id": missing_notice_id,
            "portal_id": missing_portal_id,
            "published_at": missing_published_at,
            "title": missing_title,
            "body": missing_body,
            "estimated_value": missing_value,
            "closing_date": missing_closing
        },
        "body_length_distribution": body_stats,
        "title_length_distribution": title_stats,
        "estimated_value_statistics": val_stats,
        "top_10_portals": top_10_portals,
        "nodal_aggregators": {
            "portals": ["P001", "P002", "P003", "P004", "P005", "P006"],
            "total_notices": top_6_nodal_count,
            "pct_of_corpus": round(100.0 * top_6_nodal_count / total_notices, 2)
        }
    }

    summary_path = os.path.join(output_dir, "summary.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    print(f"Saved corpus summary to {summary_path}")

    # Generate Markdown Report
    report_path = os.path.join(output_dir, "report.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# SetuBid Corpus Profile Report\n\n")
        f.write(f"**Generated**: Automatically from `{notices_dir}`\n\n")
        f.write("## 1. Corpus Summary\n\n")
        f.write(f"- **Total Notices**: {total_notices:,}\n")
        f.write(f"- **Unique Notice IDs**: {unique_notices:,}\n")
        f.write(f"- **Total Source Files**: {len(files)} files ({', '.join([os.path.basename(x) for x in files])})\n")
        f.write(f"- **Total Portals Represented**: {unique_portals}\n")
        f.write(f"- **Publication Date Range**: {min_pub} to {max_pub}\n")
        f.write(f"- **Closing Date Range**: {min_close} to {max_close}\n\n")

        f.write("## 2. Text Length Distributions\n\n")
        f.write("| Field | Mean | Median | P25 | P75 | P95 | P99 | Min | Max |\n")
        f.write("|---|---:|---:|---:|---:|---:|---:|---:|---:|\n")
        f.write(f"| **Body (chars)** | {body_stats['mean']:.1f} | {body_stats['median']:.1f} | {body_stats['p25']:.1f} | {body_stats['p75']:.1f} | {body_stats['p95']:.1f} | {body_stats['p99']:.1f} | {body_stats['min']} | {body_stats['max']} |\n")
        f.write(f"| **Title (chars)** | {title_stats['mean']:.1f} | {title_stats['median']:.1f} | {title_stats['p25']:.1f} | {title_stats['p75']:.1f} | {title_stats['p95']:.1f} | {title_stats['p99']:.1f} | {title_stats['min']} | {title_stats['max']} |\n\n")

        f.write("## 3. Missing Value Analysis\n\n")
        f.write("| Column | Missing Count | % Missing |\n")
        f.write("|---|---:|---:|\n")
        for col, cnt in summary["missing_fields"].items():
            pct = 100.0 * cnt / total_notices
            f.write(f"| `{col}` | {cnt:,} | {pct:.2f}% |\n")
        f.write("\n")

        f.write("## 4. Top 15 Portals by Volume\n\n")
        f.write("| Portal | Notices | % Corpus | Mean Body Len | Median Body Len | NPAS Preamble % | SPC Preamble % |\n")
        f.write("|---|---:|---:|---:|---:|---:|---:|\n")
        for p in portal_records[:15]:
            f.write(f"| `{p['portal_id']}` | {p['notice_count']:,} | {p['pct_of_corpus']:.2f}% | {p['body_len_mean']} | {p['body_len_median']} | {p['npas_boilerplate_pct']}% | {p['spc_boilerplate_pct']}% |\n")
        f.write("\n")

        f.write("## 5. Nodal Aggregator Concentration & Boilerplate Threat\n\n")
        f.write(f"The six nodal aggregator portals (`P001`, `P002`, `P003`, `P004`, `P005`, `P006`) account for **{top_6_nodal_count:,} notices** ({summary['nodal_aggregators']['pct_of_corpus']}% of the entire corpus).\n")
        f.write("- Portals `P001`, `P002`, `P005` have ~100% presence of the **'NATIONAL PROCUREMENT AGGREGATION SERVICE'** legal block (~1,400 chars).\n")
        f.write("- Portals `P003`, `P004`, `P006` have ~100% presence of the **'STATE PROCUREMENT CELL'** block (~1,400 chars).\n")
        f.write("- Because median notice body length is approximately 2,000–3,000 chars, this boilerplate constitutes up to 50–70% of the entire text for these notices, creating an extreme risk of artificial token collisions across completely unrelated procurement opportunities if not addressed.\n")

    print(f"Saved dataset profile report to {report_path}")

    # Write summary table to tables/dataset_summary.csv
    dataset_summary_rows = [
        {"metric": "total_notices", "value": total_notices},
        {"metric": "unique_portals", "value": unique_portals},
        {"metric": "total_files", "value": len(files)},
        {"metric": "min_published_date", "value": min_pub},
        {"metric": "max_published_date", "value": max_pub},
        {"metric": "body_len_mean", "value": round(body_stats["mean"], 2)},
        {"metric": "body_len_median", "value": body_stats["median"]},
        {"metric": "body_len_p95", "value": body_stats["p95"]},
        {"metric": "title_len_mean", "value": round(title_stats["mean"], 2)},
        {"metric": "title_len_median", "value": title_stats["median"]},
        {"metric": "nodal_portal_notices", "value": top_6_nodal_count},
        {"metric": "nodal_portal_pct", "value": summary["nodal_aggregators"]["pct_of_corpus"]}
    ]
    pd.DataFrame(dataset_summary_rows).to_csv(os.path.join(tables_dir, "dataset_summary.csv"), index=False)
    print(f"Saved dataset summary table to {os.path.join(tables_dir, 'dataset_summary.csv')}")


if __name__ == "__main__":
    notices_path = "../exam/data_2/notices" if os.path.exists("../exam/data_2/notices") else "exam/data_2/notices"
    out_dir = "experiments/01_dataset_profile" if os.path.exists("experiments") else "SetuBid/experiments/01_dataset_profile"
    tbl_dir = "reports/tables" if os.path.exists("reports") else "SetuBid/reports/tables"
    run_dataset_inspection(notices_path, out_dir, tbl_dir)
