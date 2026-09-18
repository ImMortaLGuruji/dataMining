# Full-Corpus Workload Skew Analysis Report (Before Mitigation)

## 1. Corpus Workload Metrics

- Total Notices Processed: **12,000**
- Total Candidate Comparisons Generated: **18,175,838**
- Mean Candidates per Notice: **1514.7**
- Median Candidates per Notice: **1533.0**
- P95 Candidates: **2592.0**
- P99 Candidates: **3027.01**
- Maximum Candidates on a Single Notice: **3641**

## 2. Workload Concentration & Skew

- **Top 1% of notices** generate **2.11%** of all candidate comparisons.
- **Top 5% of notices** generate **9.42%** of all candidate comparisons.
- **Top 10% of notices** generate **17.58%** of all candidate comparisons.

## 3. Pathological Mechanism & Connection to Portal Profiles

Cross-referencing the empirically measured high-work portals with `portal_profiles.md` reveals the exact mechanical cause:

1. **The Nodal Aggregators (`P001` through `P006`)** account for **44.21% of all candidate comparisons** in the entire corpus!
2. As noted in `portal_profiles.md`, portals `P001`, `P002`, and `P005` prepend an identical ~1,400 character 'NATIONAL PROCUREMENT AGGREGATION SERVICE' legal preamble, while `P003`, `P004`, and `P006` prepend an identical ~1,400 character 'STATE PROCUREMENT CELL' block.
3. **Bucket Explosion**: In the LSH index, bands that sample min-hashes falling within this legal boilerplate produce identical bucket keys across thousands of notices. Every notice published on these nodal portals consequently collides in these preamble buckets, causing a quadratic candidate explosion ($O(N_{\text{nodal}}^2)$) where completely unrelated notices are needlessly retrieved and compared.
