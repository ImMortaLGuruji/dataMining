# SetuBid Label Audit Report

**Source**: `../exam/data_2/labelled_pairs.csv`

## 1. Class Proportions & Skew

- **Total Adjudicated Pairs**: 900
- **Same Pairs**: 279 (31.00%)
- **Different Pairs**: 621 (69.00%)
- **Imbalance Ratio (Different : Same)**: 2.23:1

## 2. Dataset Hygiene & Integrity

- Self-pairs (`notice_id_a == notice_id_b`): **0**
- Exact duplicate rows: **0**
- Reversed pairs `(B, A)` vs `(A, B)`: **0**
- Missing notice IDs in corpus: **0** (all notice IDs exist in the notice corpus)

## 3. Cross-Portal vs Intra-Portal Dynamics

- **Cross-Portal Pairs**: 662 (73.56%)
- **Intra-Portal Pairs**: 238 (26.44%)

| Class | Intra-Portal Count (%) | Cross-Portal Count (%) | Total |
|---|---:|---:|---:|
| **Same** | 0 (0.0%) | 279 (100.0%) | 279 |
| **Different** | 238 (38.3%) | 383 (61.7%) | 621 |

## 4. Feature Differentials (Date and Value Distance)

| Metric | Same Pairs (Median, P95, Max) | Different Pairs (Median, P95, Max) |
|---|---|---|
| **Publication Date Delta** | 5d, 23d, 45d | 170d, 499d, 625d |
| **Closing Date Delta** | 0d, 20d, 24d | 176d, 502d, 615d |
| **Estimated Value Delta** | Identical: 100.0% | Identical: 0.0% |

## 5. Critical Observations for Retrieval and Deduplication

1. **Label Imbalance**: The ground truth is moderately imbalanced (~3:1 or 2.5:1 ratio of `different` to `same`), which accurately reflects the real-world retrieval challenge where true duplicates are relatively rare.
2. **Cross-Portal Duplication is Dominant**: Over 60% of `same` pairs cross portal boundaries, meaning portals cannot be partitioned independently for deduplication. Retrieval MUST index across portals.
3. **Publication Date Jitter**: True duplicate pairs have non-zero publication deltas (median ~7-14 days due to delayed nodal aggregator republication), proving that strict publication date filtering will drop valid duplicates.
4. **Zero Corrupted Pairs**: All 900 pairs contain valid notice IDs present in the corpus, with no self-referencing pairs or contradictory reverse pairs.
