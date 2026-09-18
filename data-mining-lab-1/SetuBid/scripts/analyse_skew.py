"""Full Corpus Workload Skew Analysis Script for SetuBid (Checkpoint 6).

Runs the complete 12,000 notice corpus through candidate retrieval without mitigation,
measures per-notice candidate workloads, identifies pathological skew,
and maps heavy-hitter portals to portal_profiles.md.

Outputs:
- experiments/06_skew_mitigation/skew_before.json
- experiments/06_skew_mitigation/per_notice_workload_before.csv
- experiments/06_skew_mitigation/report_before.md
- reports/tables/skew_before.csv
- reports/figures/candidate_count_distribution_before.png
- reports/figures/candidate_work_cumulative_before.png
- reports/figures/portal_workload_before.png
"""

import json
import os
import sys
import time
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))
from setubid.io.notices import load_notices_dict
from setubid.similarity.representation import extract_char_ngrams_range
from setubid.similarity.estimator import MinHashGenerator
from setubid.retrieval.index import LSHIndex
from setubid.retrieval.skew import compute_workload_metrics


def run_skew_analysis(notices_dir: str, output_dir: str, figures_dir: str, tables_dir: str):
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(figures_dir, exist_ok=True)
    os.makedirs(tables_dir, exist_ok=True)

    print("--- Checkpoint 6: Full Corpus Workload Skew Analysis (Before Mitigation) ---")
    print(f"Loading complete notice corpus from: {notices_dir}")
    notices_dict = load_notices_dict(notices_dir)
    total_notices = len(notices_dict)
    print(f"Loaded {total_notices:,} notices.")

    # 1. Compute MinHash signatures (b=32, r=8, m=256) on raw text
    print("Computing MinHash signatures across complete corpus (raw text)...")
    gen = MinHashGenerator(num_hashes=256, seed=42)
    lsh = LSHIndex(num_bands=32, rows_per_band=8)
    
    notice_portals = {}
    signatures_dict = {}
    
    t_start = time.perf_counter()
    for nid, item in notices_dict.items():
        notice_portals[nid] = item["portal_id"]
        shingles = extract_char_ngrams_range(item["body"], min_n=3, max_n=5, strip_boilerplate=False)
        sig = gen.compute_signature(shingles)
        signatures_dict[nid] = sig
        lsh.insert(nid, sig)
    t_index_build = (time.perf_counter() - t_start)
    print(f"LSH index built in {t_index_build:.2f} seconds.")

    # 2. Query candidates for every notice in the corpus
    print(f"Executing candidate retrieval across all {total_notices:,} notices...")
    per_notice_candidates = {}
    per_notice_records = []
    
    t_query_start = time.perf_counter()
    for nid in notices_dict.keys():
        t0 = time.perf_counter()
        candidates = lsh.query_candidates(nid)
        dt_ms = (time.perf_counter() - t0) * 1000.0
        c_count = len(candidates)
        per_notice_candidates[nid] = c_count
        per_notice_records.append({
            "notice_id": nid,
            "portal_id": notice_portals[nid],
            "candidate_count": c_count,
            "retrieval_time_ms": round(dt_ms, 3)
        })
    total_retrieval_time = (time.perf_counter() - t_query_start)
    print(f"Full-corpus retrieval completed in {total_retrieval_time:.2f} seconds.")

    workload_df = pd.DataFrame(per_notice_records)
    workload_df.to_csv(os.path.join(output_dir, "per_notice_workload_before.csv"), index=False)

    # 3. Compute Skew Metrics
    metrics = compute_workload_metrics(per_notice_candidates, notice_portals)
    portal_df = metrics["portal_workload_df"]

    # Save summary JSON
    summary_data = {
        "status": "before_mitigation",
        "total_notices": total_notices,
        "total_candidate_comparisons": metrics["total_candidate_comparisons"],
        "index_build_seconds": round(t_index_build, 2),
        "retrieval_seconds": round(total_retrieval_time, 2),
        "distribution": metrics["distribution"],
        "cumulative_concentration": metrics["cumulative_concentration"],
        "top_10_heavy_portals": portal_df.head(10).to_dict(orient="records"),
        "nodal_aggregators_pct_of_total_work": round(
            float(portal_df[portal_df["portal_id"].isin(["P001", "P002", "P003", "P004", "P005", "P006"])]["pct_of_total_work"].sum()), 2
        )
    }

    with open(os.path.join(output_dir, "skew_before.json"), "w", encoding="utf-8") as f:
        json.dump(summary_data, f, indent=2)
    print(f"Saved skew summary to {os.path.join(output_dir, 'skew_before.json')}")

    # Write Table: reports/tables/skew_before.csv
    table_rows = [
        {"metric": "total_notices", "value": total_notices},
        {"metric": "total_candidate_comparisons", "value": metrics["total_candidate_comparisons"]},
        {"metric": "candidate_count_mean", "value": metrics["distribution"]["mean"]},
        {"metric": "candidate_count_median", "value": metrics["distribution"]["median"]},
        {"metric": "candidate_count_p90", "value": metrics["distribution"]["p90"]},
        {"metric": "candidate_count_p95", "value": metrics["distribution"]["p95"]},
        {"metric": "candidate_count_p99", "value": metrics["distribution"]["p99"]},
        {"metric": "candidate_count_max", "value": metrics["distribution"]["max"]},
        {"metric": "top_1_pct_notices_work_share_pct", "value": metrics["cumulative_concentration"]["top_1_pct_notices_generate_work_pct"]},
        {"metric": "top_5_pct_notices_work_share_pct", "value": metrics["cumulative_concentration"]["top_5_pct_notices_generate_work_pct"]},
        {"metric": "top_10_pct_notices_work_share_pct", "value": metrics["cumulative_concentration"]["top_10_pct_notices_generate_work_pct"]},
        {"metric": "nodal_aggregators_work_share_pct", "value": summary_data["nodal_aggregators_pct_of_total_work"]}
    ]
    pd.DataFrame(table_rows).to_csv(os.path.join(tables_dir, "skew_before.csv"), index=False)
    print(f"Saved skew_before table to {os.path.join(tables_dir, 'skew_before.csv')}")

    # 4. Generate Figures
    counts = np.array(list(per_notice_candidates.values()))

    # Figure 1: reports/figures/candidate_count_distribution_before.png
    plt.figure(figsize=(9, 5))
    plt.hist(counts, bins=50, color="#e74c3c", edgecolor="black", alpha=0.7)
    plt.axvline(metrics["distribution"]["median"], color="#2c3e50", linestyle="--", linewidth=2, label=f"Median: {metrics['distribution']['median']}")
    plt.axvline(metrics["distribution"]["p95"], color="#d35400", linestyle=":", linewidth=2, label=f"P95: {metrics['distribution']['p95']}")
    plt.title("Candidate Workload Distribution per Notice (Before Mitigation)", fontsize=12, fontweight="bold")
    plt.xlabel("Candidate Count per Notice", fontsize=11)
    plt.ylabel("Number of Notices", fontsize=11)
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.legend()
    plt.tight_layout()
    fig1 = os.path.join(figures_dir, "candidate_count_distribution_before.png")
    plt.savefig(fig1, dpi=300)
    plt.close()
    print(f"Saved figure {fig1}")

    # Figure 2: reports/figures/candidate_work_cumulative_before.png (Lorenz curve)
    plt.figure(figsize=(8, 6))
    sorted_counts = np.sort(counts)[::-1]
    cum_work = np.cumsum(sorted_counts) / np.sum(sorted_counts) * 100.0
    notice_pct = np.linspace(0, 100, len(counts))
    plt.plot(notice_pct, cum_work, color="#c0392b", linewidth=2.5, label="Actual Workload Concentration")
    plt.plot([0, 100], [0, 100], color="#7f8c8d", linestyle="--", label="Perfect Uniform Workload")
    
    # Annotate Top 1% and Top 5%
    top1_w = metrics["cumulative_concentration"]["top_1_pct_notices_generate_work_pct"]
    top5_w = metrics["cumulative_concentration"]["top_5_pct_notices_generate_work_pct"]
    plt.scatter([1.0], [top1_w], color="#e74c3c", s=70, zorder=5)
    plt.annotate(f"Top 1% -> {top1_w}% Work", xy=(1.0, top1_w), xytext=(8, -10),
                 textcoords="offset points", fontweight="bold", color="#c0392b")
    plt.scatter([5.0], [top5_w], color="#e74c3c", s=70, zorder=5)
    plt.annotate(f"Top 5% -> {top5_w}% Work", xy=(5.0, top5_w), xytext=(8, -10),
                 textcoords="offset points", fontweight="bold", color="#c0392b")

    plt.title("Cumulative Candidate Workload Curve (Before Mitigation)", fontsize=12, fontweight="bold")
    plt.xlabel("Percentage of Notices (Sorted Descending by Workload)", fontsize=11)
    plt.ylabel("Percentage of Total Candidate Comparisons", fontsize=11)
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.legend(loc="lower right")
    plt.tight_layout()
    fig2 = os.path.join(figures_dir, "candidate_work_cumulative_before.png")
    plt.savefig(fig2, dpi=300)
    plt.close()
    print(f"Saved figure {fig2}")

    # Figure 3: reports/figures/portal_workload_before.png
    plt.figure(figsize=(10, 5))
    top_portals = portal_df.head(10)
    colors = ["#c0392b" if p in ["P001", "P002", "P003", "P004", "P005", "P006"] else "#2980b9" for p in top_portals["portal_id"]]
    plt.bar(top_portals["portal_id"], top_portals["total_candidate_work"], color=colors, edgecolor="black")
    plt.title("Total Candidate Comparisons by Top 10 Portals (Before Mitigation)\n(Red = Nodal Aggregators with Legal Boilerplate)", fontsize=11, fontweight="bold")
    plt.xlabel("Portal ID", fontsize=11)
    plt.ylabel("Total Candidate Comparisons", fontsize=11)
    plt.grid(axis="y", linestyle="--", alpha=0.5)
    plt.tight_layout()
    fig3 = os.path.join(figures_dir, "portal_workload_before.png")
    plt.savefig(fig3, dpi=300)
    plt.close()
    print(f"Saved figure {fig3}")

    # 5. Markdown Report
    report_path = os.path.join(output_dir, "report_before.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# Full-Corpus Workload Skew Analysis Report (Before Mitigation)\n\n")
        f.write("## 1. Corpus Workload Metrics\n\n")
        f.write(f"- Total Notices Processed: **{total_notices:,}**\n")
        f.write(f"- Total Candidate Comparisons Generated: **{metrics['total_candidate_comparisons']:,}**\n")
        f.write(f"- Mean Candidates per Notice: **{metrics['distribution']['mean']}**\n")
        f.write(f"- Median Candidates per Notice: **{metrics['distribution']['median']}**\n")
        f.write(f"- P95 Candidates: **{metrics['distribution']['p95']}**\n")
        f.write(f"- P99 Candidates: **{metrics['distribution']['p99']}**\n")
        f.write(f"- Maximum Candidates on a Single Notice: **{metrics['distribution']['max']}**\n\n")

        f.write("## 2. Workload Concentration & Skew\n\n")
        f.write(f"- **Top 1% of notices** generate **{top1_w}%** of all candidate comparisons.\n")
        f.write(f"- **Top 5% of notices** generate **{top5_w}%** of all candidate comparisons.\n")
        f.write(f"- **Top 10% of notices** generate **{metrics['cumulative_concentration']['top_10_pct_notices_generate_work_pct']}%** of all candidate comparisons.\n\n")

        f.write("## 3. Pathological Mechanism & Connection to Portal Profiles\n\n")
        f.write("Cross-referencing the empirically measured high-work portals with `portal_profiles.md` reveals the exact mechanical cause:\n\n")
        f.write("1. **The Nodal Aggregators (`P001` through `P006`)** account for **" + str(summary_data['nodal_aggregators_pct_of_total_work']) + "% of all candidate comparisons** in the entire corpus!\n")
        f.write("2. As noted in `portal_profiles.md`, portals `P001`, `P002`, and `P005` prepend an identical ~1,400 character 'NATIONAL PROCUREMENT AGGREGATION SERVICE' legal preamble, while `P003`, `P004`, and `P006` prepend an identical ~1,400 character 'STATE PROCUREMENT CELL' block.\n")
        f.write("3. **Bucket Explosion**: In the LSH index, bands that sample min-hashes falling within this legal boilerplate produce identical bucket keys across thousands of notices. Every notice published on these nodal portals consequently collides in these preamble buckets, causing a quadratic candidate explosion ($O(N_{\\text{nodal}}^2)$) where completely unrelated notices are needlessly retrieved and compared.\n")

    print(f"Saved report to {report_path}")


if __name__ == "__main__":
    ntc_dir = "../exam/data_2/notices" if os.path.exists("../exam/data_2/notices") else "exam/data_2/notices"
    out_dir = "experiments/06_skew_mitigation" if os.path.exists("experiments") else "SetuBid/experiments/06_skew_mitigation"
    fig_dir = "reports/figures" if os.path.exists("reports") else "SetuBid/reports/figures"
    tbl_dir = "reports/tables" if os.path.exists("reports") else "SetuBid/reports/tables"
    run_skew_analysis(ntc_dir, out_dir, fig_dir, tbl_dir)
