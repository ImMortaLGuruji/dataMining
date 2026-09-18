# SetuBid Corpus Profile Report

**Generated**: Automatically from `../exam/data_2/notices`

## 1. Corpus Summary

- **Total Notices**: 12,000
- **Unique Notice IDs**: 12,000
- **Total Source Files**: 8 files (part-000.csv, part-001.csv, part-002.csv, part-003.csv, part-004.csv, part-005.csv, part-006.csv, part-007.csv)
- **Total Portals Represented**: 260
- **Publication Date Range**: 2024-01-01 to 2025-11-27
- **Closing Date Range**: 2024-01-16 to 2025-12-08

## 2. Text Length Distributions

| Field | Mean | Median | P25 | P75 | P95 | P99 | Min | Max |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| **Body (chars)** | 4527.3 | 4482.0 | 3717.0 | 5273.0 | 6710.0 | 7423.0 | 1500 | 8127 |
| **Title (chars)** | 80.6 | 80.0 | 71.0 | 90.0 | 105.0 | 114.0 | 40 | 131 |

## 3. Missing Value Analysis

| Column | Missing Count | % Missing |
|---|---:|---:|
| `notice_id` | 0 | 0.00% |
| `portal_id` | 0 | 0.00% |
| `published_at` | 0 | 0.00% |
| `title` | 0 | 0.00% |
| `body` | 0 | 0.00% |
| `estimated_value` | 0 | 0.00% |
| `closing_date` | 0 | 0.00% |

## 4. Top 15 Portals by Volume

| Portal | Notices | % Corpus | Mean Body Len | Median Body Len | NPAS Preamble % | SPC Preamble % |
|---|---:|---:|---:|---:|---:|---:|
| `P001` | 778 | 6.48% | 5838.8 | 5847.0 | 100.0% | 0.0% |
| `P002` | 800 | 6.67% | 5819.3 | 5761.0 | 100.0% | 0.0% |
| `P003` | 772 | 6.43% | 5008.2 | 4995.5 | 0.0% | 100.0% |
| `P004` | 755 | 6.29% | 4972.7 | 4919.0 | 0.0% | 100.0% |
| `P005` | 768 | 6.40% | 5842.8 | 5834.5 | 100.0% | 0.0% |
| `P006` | 792 | 6.60% | 5070.1 | 5067.5 | 0.0% | 100.0% |
| `P007` | 11 | 0.09% | 4204.0 | 4222.0 | 0.0% | 0.0% |
| `P008` | 10 | 0.08% | 1500.0 | 1500.0 | 0.0% | 0.0% |
| `P009` | 4 | 0.03% | 4075.2 | 4197.0 | 0.0% | 0.0% |
| `P010` | 7 | 0.06% | 4321.6 | 4588.0 | 0.0% | 0.0% |
| `P011` | 11 | 0.09% | 1500.0 | 1500.0 | 0.0% | 0.0% |
| `P012` | 7 | 0.06% | 3905.0 | 3496.0 | 0.0% | 0.0% |
| `P013` | 110 | 0.92% | 1500.0 | 1500.0 | 0.0% | 0.0% |
| `P014` | 36 | 0.30% | 4198.6 | 4128.0 | 0.0% | 0.0% |
| `P015` | 8 | 0.07% | 1500.0 | 1500.0 | 0.0% | 0.0% |

## 5. Nodal Aggregator Concentration & Boilerplate Threat

The six nodal aggregator portals (`P001`, `P002`, `P003`, `P004`, `P005`, `P006`) account for **4,665 notices** (38.88% of the entire corpus).
- Portals `P001`, `P002`, `P005` have ~100% presence of the **'NATIONAL PROCUREMENT AGGREGATION SERVICE'** legal block (~1,400 chars).
- Portals `P003`, `P004`, `P006` have ~100% presence of the **'STATE PROCUREMENT CELL'** block (~1,400 chars).
- Because median notice body length is approximately 2,000–3,000 chars, this boilerplate constitutes up to 50–70% of the entire text for these notices, creating an extreme risk of artificial token collisions across completely unrelated procurement opportunities if not addressed.
