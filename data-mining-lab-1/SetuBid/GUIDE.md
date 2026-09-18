# SetuBid Tender Deduplication

## Lab 1 / Exam — From Interactable Comparison to a Tractable, Persistent Retrieval System

> **Objective:** Build a defensible tender-deduplication retrieval system that reduces an otherwise quadratic comparison problem to a sublinear candidate-retrieval problem, persists the retrieval structure in a relational database, identifies and mitigates pathological workload skew, and produces empirical evidence for every major design decision.

---

# 1. Problem Statement

SetuBid aggregates public procurement notices scraped from approximately **260 government portals**.

The same underlying procurement opportunity may appear:

* on multiple government portals,
* under different reference numbers,
* on different publication dates,
* with slightly different wording,
* after corrigenda,
* after reformatting by a nodal agency.

There is no universal identifier.

The current system effectively compares notices against one another. This is becoming computationally infeasible.

The corpus grows by approximately **4,000 notices/week**, while the production requirement is:

> **The complete nightly deduplication pipeline must fit inside a 20-minute window on one machine.**

The system must also account for asymmetric business risk:

1. **False merge:** two genuinely different tenders are merged.

   * Serious consequence: a bidder could miss a distinct opportunity/deadline and potentially sue SetuBid.
2. **False split:** two copies of the same tender remain separate.

   * Consequence: duplicate cards and a poorer product experience.

The system must therefore expose the asymmetry **numerically**, not merely describe it.

A second hard requirement is **stable identity**:

> A bidder's bookmarked card ID must continue to refer to the same underlying procurement opportunity after future pipeline reruns and after additional copies are absorbed.

---

# 2. Supplied Data

The repository will contain or be given access to:

```text
lab1/exam/data_2/
├── notices/
│   └── *.parquet
├── labelled_pairs.csv
└── portal_profiles.md
```

## 2.1 `notices/`

Parquet files containing:

```text
notice_id
portal_id
published_at
title
body
estimated_value
closing_date
```

`body` contains approximately 500–9,000 characters.

## 2.2 `labelled_pairs.csv`

Approximately 900 manually adjudicated notice pairs.

Expected conceptual structure:

```text
notice_id_a
notice_id_b
label
```

where:

```text
same
different
```

are the labels.

### Critical rule

**This is the only trustworthy ground-truth label source.**

Do not create synthetic labels and present them as ground truth.

Do not assume the dataset is balanced.

The first analysis must measure:

* number of pairs,
* number of `same`,
* number of `different`,
* class proportions,
* duplicate/reversed pairs if any,
* whether particular portals are overrepresented,
* similarity-score distribution by label.

---

# 3. Non-Negotiable Requirements

The implementation must satisfy all of the following.

## R1 — Mechanically defined similarity

Define a deterministic representation of a notice and a deterministic similarity score.

The representation must explicitly address:

* text granularity,
* monetary amounts,
* dates,
* reference numbers,
* portal boilerplate,
* other obvious noise.

The decision must be supported by measurements from this corpus.

---

## R2 — Reduced representation

The exact full representation of every notice cannot be retained for retrieval.

Choose a reduced representation size **before implementation**.

The size must be derived from an explicit accuracy requirement.

Do not choose:

> "64 because it is a common value."

Instead demonstrate:

```text
required estimation accuracy
        ↓
probabilistic/statistical requirement
        ↓
required representation size
        ↓
measured realised error
```

---

## R3 — Sublinear candidate retrieval

The system must not compare every notice against every other notice.

For each notice:

```text
notice
  ↓
retrieval index
  ↓
short candidate list
  ↓
exact similarity
  ↓
deduplication decision
```

The retrieval layer must have a tunable recall/work tradeoff.

Measure:

```text
true similarity
        vs
probability pair survives candidate retrieval
```

Plot the relationship and mark the selected operating point.

The operating point must explicitly incorporate the business cost asymmetry between false merges and false splits.

---

## R4 — Persistent relational retrieval structure

The retrieval structure must not exist only inside Python memory.

It must:

* survive process restart,
* be stored as relational data,
* be queryable by the application,
* support the retrieval operation.

The implementation must provide:

* schema,
* indexes,
* lookup query,
* query plan,
* actual rows examined,
* wall-clock measurements.

At least one alternative access strategy must be implemented or forced for comparison.

---

## R5 — Workload skew analysis

Run retrieval against the full corpus.

Do not only report:

```text
total runtime = X
```

Measure the distribution of candidate-generation work across notices.

Identify the pathological portion of the corpus empirically.

Use:

```text
portal_profiles.md
```

to interpret why that workload behaves differently.

Then:

1. explain the mechanical cause,
2. quantify the cost,
3. mitigate it,
4. rerun the workload,
5. measure the new distribution,
6. measure runtime,
7. measure retrieval-quality loss/gain on `labelled_pairs.csv`.

---

# 4. Recommended Repository Structure

The final repository should be easy for a reviewer to navigate.

Use:

```text
SetuBid/
│
├── README.md
├── pyproject.toml
├── .gitignore
│
├── data/
│   └── README.md
│
├── config/
│   ├── baseline.yaml
│   └── experiments.yaml
│
├── src/
│   └── setubid/
│       ├── __init__.py
│       │
│       ├── io/
│       │   ├── notices.py
│       │   └── labels.py
│       │
│       ├── normalization/
│       │   ├── text.py
│       │   ├── fields.py
│       │   └── pipeline.py
│       │
│       ├── similarity/
│       │   ├── representation.py
│       │   ├── exact.py
│       │   └── estimator.py
│       │
│       ├── retrieval/
│       │   ├── index.py
│       │   ├── candidate_generation.py
│       │   ├── evaluation.py
│       │   └── skew.py
│       │
│       ├── database/
│       │   ├── schema.sql
│       │   ├── queries.sql
│       │   └── benchmark.py
│       │
│       ├── deduplication/
│       │   ├── clustering.py
│       │   └── stable_ids.py
│       │
│       └── pipeline.py
│
├── scripts/
│   ├── inspect_dataset.py
│   ├── analyse_labels.py
│   ├── benchmark_similarity.py
│   ├── choose_representation.py
│   ├── build_index.py
│   ├── evaluate_retrieval.py
│   ├── benchmark_database.py
│   ├── analyse_skew.py
│   ├── run_mitigation.py
│   └── run_full_pipeline.py
│
├── sql/
│   ├── schema.sql
│   ├── indexes.sql
│   └── benchmark_queries.sql
│
├── experiments/
│   ├── 01_dataset_profile/
│   ├── 02_similarity/
│   ├── 03_representation_size/
│   ├── 04_retrieval/
│   ├── 05_database/
│   └── 06_skew_mitigation/
│
├── reports/
│   ├── figures/
│   ├── tables/
│   └── final_report.md
│
├── tests/
│   ├── test_normalization.py
│   ├── test_similarity.py
│   ├── test_estimator.py
│   ├── test_retrieval.py
│   ├── test_stable_ids.py
│   └── test_database.py
│
└── Makefile
```

The data itself should **not be committed** if it is large or supplied externally.

`data/README.md` should explain exactly where the evaluator should place:

```text
notices/
labelled_pairs.csv
portal_profiles.md
```

---

# 5. Execution Philosophy

The assistant must follow this sequence:

```text
Inspect
  ↓
Measure
  ↓
Form hypothesis
  ↓
Run controlled experiment
  ↓
Choose parameter
  ↓
Implement
  ↓
Benchmark
  ↓
Validate against labels
  ↓
Document evidence
```

Do **not** implement the final design first and manufacture justification afterward.

Every important parameter must have:

```text
parameter
reason for testing
candidate values
measurement
chosen value
trade-off
```

---

# 6. Phase 0 — Dataset Inspection

Create:

```text
scripts/inspect_dataset.py
```

It must produce a machine-readable and human-readable dataset profile.

Measure at minimum:

### Corpus

* total notices,
* number of Parquet files,
* notices per portal,
* notices per date range,
* body length distribution,
* title length distribution,
* missing values,
* estimated-value distribution,
* closing-date distribution.

### Portal behaviour

For each portal:

* notice count,
* average body length,
* average title length,
* common formatting patterns,
* repeated boilerplate,
* reference-number patterns,
* date patterns.

Save:

```text
experiments/01_dataset_profile/
├── summary.json
├── portal_statistics.csv
└── report.md
```

---

# 7. Phase 1 — Audit the Labels

Create:

```text
scripts/analyse_labels.py
```

Determine:

```text
N
N_same
N_different
P(same)
P(different)
```

Also investigate:

* reversed pairs `(A,B)` vs `(B,A)`,
* self-pairs,
* portal-pair frequencies,
* label distribution by portal combination,
* publication-date distance,
* closing-date distance,
* value differences.

Plot:

```text
similarity / feature distributions
       grouped by
same vs different
```

This establishes the actual evaluation population.

---

# 8. Phase 2 — Define Similarity

## 8.1 Candidate representations

Evaluate at least two text decomposition choices.

For example:

### Candidate A

Word/token-level TF-IDF.

### Candidate B

Character n-gram representation.

The experiment should determine which handles:

* spelling variations,
* punctuation,
* reference-number changes,
* formatting changes,
* OCR/scraping differences,
* boilerplate.

Do not assume the answer.

---

# 9. Noise and Signal Treatment

Explicitly classify fields/tokens.

Potential categories:

### Signal

* project/work description,
* location,
* department/authority,
* work type,
* scope,
* quantities,
* important procurement terminology.

### Potential noise

* portal-specific boilerplate,
* navigation text,
* legal footer,
* scraped UI text,
* generic instructions.

### Special fields

Do not blindly discard:

* monetary values,
* dates,
* reference numbers.

Instead test their value.

For example, a tender reference number changing between portals may have low direct similarity value, while:

* location,
* work description,
* estimated value,
* closing date

may be much more useful.

The experiments must establish this empirically.

---

# 10. Required Similarity Experiment

For at least:

* one `same` pair,
* one `different` pair,

calculate similarity under **two tokenisation/counting choices**.

Example:

```text
same pair:
    word representation → 0.xx
    character representation → 0.yy

different pair:
    word representation → 0.aa
    character representation → 0.bb
```

Then explain:

* which representation separates the examples better,
* why,
* what computational/storage cost adoption introduces.

The final representation must be selected based on the corpus evidence.

---

# 11. Exact Similarity Definition

The final implementation must document a mathematical definition.

For example, if cosine similarity is used:

$$
sim(x,y)=
\frac{x\cdot y}
{\|x\|\|y\|}
$$

If multiple fields/features are combined, explicitly define:

$$
S(x,y)
=
w_tS_t(x,y)
+w_vS_v(x,y)
+w_dS_d(x,y)
+\cdots
$$

with:

```text
weights
normalisation
missing-value behaviour
thresholds
```

all documented.

Do not hide important logic inside code.

---

# 12. Phase 3 — Reduced Representation

The final retrieval system cannot retain the complete exact representation.

Choose a compact estimator.

A suitable direction is a **MinHash/LSH-style representation** if the selected similarity is Jaccard-like, or another locality-sensitive representation appropriate to the chosen similarity.

The important requirement is not the algorithm name.

The requirement is:

> **Derive the representation size from a stated estimation-error requirement.**

---

# 13. Representation-Size Derivation

Before choosing the final size, establish:

```text
acceptable similarity estimation error = ε
required confidence = 1 - δ
```

Then derive the required number of samples/features/hashes using the estimator's error relationship.

For a MinHash estimator, if:

$$
\hat J = \frac{k}{m}
$$

then:

$$
Var(\hat J)=\frac{J(1-J)}{m}
$$

Use this to determine an appropriate `m`.

Do not simply say:

> "We chose 128 hashes because it is standard."

Instead show the calculation.

Then evaluate practical candidates around the derived requirement.

For example:

```text
64
128
256
512
```

only if those values make sense relative to the derived bound.

---

# 14. Close the Estimation Loop

For `labelled_pairs.csv`:

1. compute the exact similarity,
2. compute the reduced-form estimate,
3. calculate estimation error.

Measure:

```text
absolute error
mean absolute error
RMSE
maximum absolute error
95th percentile absolute error
```

Also report error as a function of true similarity.

Example:

```text
true similarity bucket | mean error | p95 error
------------------------------------------------
0.0–0.1                | ...
0.1–0.2                | ...
...
0.9–1.0                | ...
```

Then answer:

> Did the realised error behave as predicted by the theoretical argument?

If not, identify why.

Possible reasons must be investigated rather than hand-waved.

---

# 15. Phase 4 — Candidate Retrieval

The full pairwise comparison is approximately:

$$
O(N^2)
$$

This is unacceptable.

Build an index that retrieves only likely candidates.

A locality-sensitive hashing approach is a natural candidate, but alternatives may be evaluated if justified.

The retrieval API should look conceptually like:

```python
candidates = retrieve_candidates(notice_id)
```

and guarantee that the downstream exact-comparison stage never needs to inspect the complete corpus.

---

# 16. Retrieval Evaluation

For every labelled pair:

```text
if label == same:
    did the candidate generator retrieve the other notice?
```

Calculate:

$$
Recall_{candidate}
=
\frac{\text{same pairs retrieved}}
{\text{same pairs}}
$$

Also measure:

```text
average candidate count
median candidate count
p95 candidate count
p99 candidate count
maximum candidate count
```

The retrieval system must expose tunable parameters such as:

```text
number of bands
rows per band
number of tables
candidate cap
similarity threshold
```

where applicable.

---

# 17. Required Retrieval Curve

Characterise:

$$
P(\text{retrieved} \mid \text{true similarity})
$$

Create a plot such as:

```text
Candidate survival probability
1.0 |                         ********
    |                    *****
    |                ****
    |             ***
    |          ***
    |       ***
    |    ***
0.0 |****
    +-----------------------------------
      0.0   0.2   0.4   0.6   0.8   1.0
                True similarity
```

The actual plot must be generated from measurements.

Mark the chosen operating point.

---

# 18. Business-Risk Parameterisation

The product requirement explicitly states that:

```text
False merge ≠ False split
```

Do not merely write:

> "False merges are more expensive."

Represent the asymmetry numerically.

For example, define:

$$
C_{FM}
$$

= cost of a false merge.

$$
C_{FS}
$$

= cost of a false split.

Then define:

$$
R=\frac{C_{FM}}{C_{FS}}
$$

The actual ratio must be justified from the problem statement and, if necessary, expressed as a scenario/range rather than invented as a factual business number.

Use the ratio to explain why the chosen operating point prioritises the corresponding error.

For example:

```text
candidate configuration A
candidate configuration B
candidate configuration C

For each:
    false-merge exposure
    false-split exposure
    candidate workload
```

Do not choose the operating point merely because it produces the lowest runtime.

---

# 19. Phase 5 — Database Design

The retrieval structure must persist in a relational database.

PostgreSQL is a suitable implementation choice unless the environment dictates otherwise.

Create:

```text
sql/schema.sql
sql/indexes.sql
sql/benchmark_queries.sql
```

---

# 20. Suggested Relational Model

A possible conceptual schema:

```text
notices
-------
notice_id PK
portal_id
published_at
title
body
estimated_value
closing_date
...

retrieval_signatures
--------------------
notice_id FK
table_id
bucket_key
...

dedup_clusters
--------------
cluster_id PK
stable_card_id
...

cluster_members
---------------
cluster_id FK
notice_id FK
...
```

The exact schema may differ.

The assistant must justify:

* row granularity,
* primary keys,
* indexes,
* data types,
* partitioning if used,
* lookup path.

---

# 21. Access-Path Experiment

The final retrieval query must be benchmarked using the database's query planner.

Collect:

```text
EXPLAIN (ANALYZE, BUFFERS)
```

or the database-equivalent evidence.

Report:

* chosen access path,
* index scans / sequential scans,
* estimated rows,
* actual rows,
* rows examined,
* execution time,
* planning time,
* buffer activity where available.

---

# 22. Required Alternative

Choose at least one plausible alternative and force it for comparison.

Examples:

```text
indexed lookup
vs
sequential scan
```

or:

```text
B-tree
vs
hash index
```

or another physically meaningful alternative appropriate to the chosen schema.

The explanation must address **how rows are physically located**.

Do not merely say:

> "Indexing is faster."

Explain the access path.

Then provide measured evidence.

---

# 23. Phase 6 — Full-Corpus Workload Analysis

Run the retrieval system across the entire corpus.

For every notice record:

```text
notice_id
portal_id
candidate_count
retrieval_time
```

At minimum calculate:

```text
mean
median
p90
p95
p99
max
```

Do not stop at aggregate runtime.

---

# 24. Detect Workload Skew

Create distributions such as:

### Candidate-count histogram

```text
candidate count
       vs
number of notices
```

### Per-portal distribution

```text
portal
  → notices
  → mean candidates
  → p95 candidates
  → total candidate work
```

### Cumulative workload

Calculate:

> What percentage of notices generates what percentage of candidate comparisons?

For example:

```text
top 1% of notices → X% of candidate work
top 5%            → Y%
top 10%           → Z%
```

These numbers must come from the corpus.

---

# 25. Identify the Pathology

Use:

```text
portal_profiles.md
```

to interpret the empirically identified high-work portals/notices.

Possible mechanisms include:

* repeated boilerplate,
* low-information text,
* common templates,
* shared procurement language,
* unusually short documents,
* aggressive reformatting,
* highly common tokens,
* one-to-many LSH buckets.

The explanation must connect:

```text
data property
      ↓
representation
      ↓
index/bucket behaviour
      ↓
candidate explosion
      ↓
runtime
```

---

# 26. Quantify the 20-Minute Requirement

Report:

```text
baseline runtime
20-minute budget
budget utilisation
```

Example:

```text
Baseline:
    31 hours

Required:
    ≤ 20 minutes

Required speedup:
    ...
```

Do not claim production feasibility based on a single toy benchmark.

Measure the full supplied corpus.

---

# 27. Mitigation

Design and implement a mitigation for the identified pathological workload.

Potential mechanisms include:

* stop-word/boilerplate suppression,
* portal-aware preprocessing,
* high-frequency token suppression,
* bucket-size controls,
* adaptive LSH parameters,
* common-signature filtering,
* multi-stage retrieval,
* portal-specific representation,
* capped/common bucket handling.

**Do not choose one in advance.**

The mitigation must directly target the empirically identified failure mechanism.

---

# 28. Before/After Experiment

The mitigation experiment must report:

| Metric                         | Before | After |
| ------------------------------ | -----: | ----: |
| Total runtime                  |        |       |
| Median candidates              |        |       |
| P95 candidates                 |        |       |
| P99 candidates                 |        |       |
| Maximum candidates             |        |       |
| Candidate comparisons          |        |       |
| Labelled-pair retrieval recall |        |       |
| Same-pair recall               |        |       |
| Different-pair exposure        |        |       |

The final report must explicitly state:

> What did the mitigation cost in retrieval quality?

A mitigation without a measured quality trade-off is incomplete.

---

# 29. Stable Opportunity Identity

Although the main lab focuses on retrieval, the production requirement includes stable card IDs.

The implementation must therefore separate:

```text
notice_id
```

from:

```text
stable opportunity/card ID
```

A notice is a source observation.

An opportunity is the underlying procurement entity.

Conceptually:

```text
                    ┌── notice A
Opportunity CARD ───┼── notice B
                    ├── notice C
                    └── notice D
```

The stable card identifier must not depend on:

* the latest notice,
* row ordering,
* hash-table ordering,
* cluster numbering generated from scratch.

---

# 30. Stable-ID Design

The system must ensure that rerunning the pipeline does not arbitrarily change IDs.

A robust strategy may use:

```text
stable immutable opportunity UUID
```

with a persistent mapping:

```text
notice_id → opportunity_id
```

When new duplicate notices arrive:

```text
existing opportunity found
        ↓
attach notice
        ↓
retain opportunity_id
```

When a genuinely new opportunity appears:

```text
create new opportunity_id
```

If clustering is rebuilt globally, the implementation must reconcile old and new clusters rather than blindly assigning new IDs.

---

# 31. Stability Tests

Create tests proving:

### Restart stability

```text
build index
restart process
lookup
→ same results
```

### Repeated-run stability

```text
run pipeline
run again
→ same stable card IDs
```

### New-copy stability

```text
initial notices
        ↓
assign card ID

add duplicate notice
        ↓
rerun

original card ID remains unchanged
```

### Cluster merge stability

If two notices become linked by a newly discovered duplicate, define and test the policy for which existing card survives.

This policy must be deterministic and documented.

---

# 32. Testing Requirements

At minimum:

```text
tests/test_normalization.py
tests/test_similarity.py
tests/test_estimator.py
tests/test_retrieval.py
tests/test_stable_ids.py
tests/test_database.py
```

Tests should cover:

* empty text,
* missing fields,
* Unicode,
* punctuation,
* numbers,
* dates,
* reference numbers,
* duplicate notices,
* highly boilerplate-heavy notices,
* stable IDs,
* database persistence.

---

# 33. Reproducibility

All experiments must be reproducible.

Record:

```text
Python version
package versions
database version
CPU
RAM
OS
dataset statistics
configuration
random seeds
timestamp
```

If randomness exists, set a deterministic seed where practical.

Each experiment should save its configuration.

Example:

```text
experiments/04_retrieval/
├── config.yaml
├── metrics.json
├── pairs.csv
├── candidate_distribution.csv
├── retrieval_curve.csv
├── retrieval_curve.png
└── report.md
```

---

# 34. Configuration

Do not scatter experimental constants through source code.

Use configuration files.

Example:

```yaml
similarity:
  representation: character_ngrams
  ngram_min: 3
  ngram_max: 5

estimator:
  hashes: 256

retrieval:
  bands: 32
  rows_per_band: 8

risk:
  false_merge_cost: 100
  false_split_cost: 1
```

The numerical risk values must be treated as the **declared experimental model**, not as factual financial valuations unless supplied by SetuBid.

---

# 35. Performance Budget

The final full pipeline must report:

```text
ingestion time
normalisation time
representation time
index-build time
candidate retrieval time
exact comparison time
cluster/update time
total wall-clock time
```

The primary production target is:

```text
TOTAL ≤ 20 minutes
```

on one machine.

If the supplied machine cannot reproduce the target, report:

* hardware,
* measured runtime,
* bottleneck,
* scaling estimate,
* remaining gap.

Do not hide a failed target.

---

# 36. Required Final Report

Generate:

```text
reports/final_report.md
```

with exactly these major sections:

```text
1. Executive Summary

2. Dataset and Label Audit

3. What "Similar" Means

4. Similarity Representation Experiment

5. Reduced Representation and Error Bound

6. Candidate Retrieval

7. Business-Risk Operating Point

8. Database Schema and Access Path

9. Full-Corpus Workload Skew

10. Skew Mitigation

11. Before/After Results

12. Stable Opportunity IDs

13. Runtime Against 20-Minute Budget

14. Limitations

15. Reproducibility
```

---

# 37. Required Figures

At minimum:

```text
figures/
├── label_distribution.png
├── similarity_by_label.png
├── tokenisation_comparison.png
├── estimator_error.png
├── estimator_error_by_similarity.png
├── retrieval_probability_vs_similarity.png
├── candidate_count_distribution_before.png
├── candidate_work_cumulative_before.png
├── portal_workload_before.png
├── candidate_count_distribution_after.png
├── candidate_work_cumulative_after.png
└── portal_workload_after.png
```

---

# 38. Required Tables

At minimum:

```text
tables/
├── dataset_summary.csv
├── label_summary.csv
├── similarity_comparison.csv
├── representation_size_results.csv
├── estimator_accuracy.csv
├── retrieval_parameter_sweep.csv
├── database_benchmark.csv
├── skew_before.csv
├── skew_after.csv
└── final_metrics.csv
```

---

# 39. Foolproof Implementation Order

The coding assistant must execute the following order.

## Step 1 — Inspect repository

Determine:

```text
available files
Python version
database availability
installed dependencies
hardware
```

Do not modify data.

---

## Step 2 — Profile corpus

Run:

```bash
python scripts/inspect_dataset.py
```

Produce dataset statistics.

---

## Step 3 — Audit labels

Run:

```bash
python scripts/analyse_labels.py
```

Confirm the label skew.

**Do not continue until this is understood.**

---

## Step 4 — Build similarity candidates

Implement at least two plausible representations.

Evaluate them on `labelled_pairs.csv`.

---

## Step 5 — Choose exact representation

Use measured evidence.

Document:

```text
representation
tokenisation
noise handling
field treatment
similarity formula
```

---

## Step 6 — Derive reduced-form size

State:

```text
required error
required confidence
mathematical derivation
candidate sizes
chosen size
```

before finalising the implementation.

---

## Step 7 — Validate estimator

Compare reduced-form estimates with exact similarities.

Reject the configuration if the measured accuracy does not satisfy the stated requirement.

---

## Step 8 — Build candidate retrieval

Implement the chosen retrieval algorithm.

Sweep meaningful parameters.

Measure:

```text
recall
candidate count
runtime
```

---

## Step 9 — Produce retrieval curve

Generate:

$$
P(\text{candidate survives}|\text{true similarity})
$$

Choose the operating point using the explicitly declared risk model.

---

## Step 10 — Build persistent database index

Create schema and indexes.

Load retrieval signatures.

Verify that the index survives process restart.

---

## Step 11 — Benchmark database access

Run:

```text
EXPLAIN ANALYZE
```

for the production lookup.

Force the selected alternative.

Record actual measurements for both.

---

## Step 12 — Run complete corpus

Run candidate retrieval for every notice.

Save per-notice metrics.

---

## Step 13 — Find skew

Calculate:

```text
p50
p90
p95
p99
max
top-1%
top-5%
top-10%
```

Identify the high-cost portals/buckets/notices.

---

## Step 14 — Read portal profiles

Connect the measured pathology to actual portal formatting behaviour.

Do not use `portal_profiles.md` as proof of performance.

Use it to interpret measured behaviour.

---

## Step 15 — Implement targeted mitigation

Target the actual cause.

Do not blindly add filters.

---

## Step 16 — Rerun everything

Measure:

```text
runtime
candidate distribution
retrieval recall
labelled-pair behaviour
```

---

## Step 17 — Implement stable opportunity IDs

Separate:

```text
source notice identity
```

from:

```text
underlying opportunity identity
```

and add deterministic persistence.

---

## Step 18 — Run stability tests

Test:

```text
rerun
restart
new duplicate
new unrelated notice
cluster reconciliation
```

---

## Step 19 — Run final pipeline

Execute:

```bash
python scripts/run_full_pipeline.py
```

The script must produce all final metrics and artifacts.

---

## Step 20 — Generate final report

Everything in `reports/final_report.md` must trace back to:

* source data,
* experiment output,
* SQL benchmark,
* reproducible script.

No unsupported claims.

---

# 40. Definition of Done

The task is complete only if all of these are true:

* [ ] Dataset has been profiled.
* [ ] Label imbalance has been measured.
* [ ] Similarity has a precise mathematical definition.
* [ ] At least two representation/counting choices were empirically compared.
* [ ] Signal/noise treatment is justified from the corpus.
* [ ] Reduced representation size was derived from an accuracy requirement.
* [ ] Estimator error was measured against labelled pairs.
* [ ] Candidate retrieval is sublinear.
* [ ] Retrieval recall is measured.
* [ ] Candidate workload is measured.
* [ ] Retrieval probability vs true similarity is plotted.
* [ ] Operating point is explicitly justified using numerical asymmetric costs.
* [ ] Retrieval structure is persisted relationally.
* [ ] Database access path is benchmarked.
* [ ] Alternative access method is benchmarked.
* [ ] `EXPLAIN ANALYZE` evidence is included.
* [ ] Full-corpus workload distribution is measured.
* [ ] Workload skew is empirically identified.
* [ ] Portal profiles are used to interpret the skew.
* [ ] Mitigation is implemented.
* [ ] Before/after runtime is measured.
* [ ] Before/after retrieval quality is measured.
* [ ] Stable opportunity/card IDs are implemented.
* [ ] ID stability is tested across reruns and newly arriving duplicates.
* [ ] Total runtime is compared against the 20-minute requirement.
* [ ] All experiments are reproducible.
* [ ] Final report contains actual measurements.
* [ ] No parameter is justified solely because it is a conventional/tutorial value.

---

# 41. Critical Rules for the AI Coding Assistant

### Rule 1 — Never fabricate results

If an experiment has not been run, do not write its result.

Use:

```text
NOT YET MEASURED
```

internally until the experiment executes.

---

### Rule 2 — Never fabricate business costs

The problem establishes asymmetric consequences but does not provide monetary legal/customer costs.

If numerical costs are required, explicitly define them as an **experimental cost ratio/model**, explain the sensitivity to that ratio, and do not present them as actual SetuBid financial data.

---

### Rule 3 — Never optimise only for recall

A candidate generator that retrieves everything is technically high-recall but fails the computational objective.

Always report:

```text
retrieval recall
AND
candidate workload
AND
runtime
```

---

### Rule 4 — Never optimise only for runtime

A fast retrieval system that misses true duplicates is unacceptable.

Every optimisation must be evaluated against `labelled_pairs.csv`.

---

### Rule 5 — Never use the labels to secretly tune everything

Avoid overfitting the 900 labelled pairs.

Where practical:

* separate parameter-selection and final-evaluation subsets,
* or use cross-validation/bootstrap evaluation,
* document the procedure.

The labelled dataset is small and potentially skewed.

---

### Rule 6 — Do not confuse retrieval with final deduplication

The architecture has separate stages:

```text
retrieval
    ↓
candidate pairs
    ↓
exact similarity / decision
    ↓
opportunity clustering
    ↓
stable card ID
```

A retrieval false negative means the downstream system never gets the chance to recover the pair.

---

### Rule 7 — Preserve provenance

Every merged opportunity should retain:

```text
opportunity_id
source notice IDs
portal IDs
timestamps
```

This is necessary for auditability.

---

# 42. Final Architecture

The intended final system should conceptually resemble:

```text
                    ┌───────────────────┐
                    │ Government Portals│
                    └─────────┬─────────┘
                              │
                              ▼
                    ┌───────────────────┐
                    │ Notice Ingestion  │
                    └─────────┬─────────┘
                              │
                              ▼
                    ┌───────────────────┐
                    │ Normalisation     │
                    │ + signal filtering│
                    └─────────┬─────────┘
                              │
                 ┌────────────┴────────────┐
                 ▼                         ▼
        ┌─────────────────┐       ┌─────────────────┐
        │ Exact similarity│       │ Reduced form    │
        │ representation  │       │ / signatures    │
        └────────┬────────┘       └────────┬────────┘
                 │                         │
                 │                         ▼
                 │                ┌─────────────────┐
                 │                │ Persistent      │
                 │                │ retrieval index │
                 │                └────────┬────────┘
                 │                         │
                 │                         ▼
                 │                ┌─────────────────┐
                 └───────────────►│ Candidate pairs │
                                  └────────┬────────┘
                                           │
                                           ▼
                                  ┌─────────────────┐
                                  │ Exact comparison│
                                  └────────┬────────┘
                                           │
                                           ▼
                                  ┌─────────────────┐
                                  │ Opportunity     │
                                  │ clustering      │
                                  └────────┬────────┘
                                           │
                                           ▼
                                  ┌─────────────────┐
                                  │ Stable Card ID  │
                                  └─────────────────┘
```

---

# 43. Final Success Criterion

The finished system must demonstrate, with reproducible measurements, that:

$$
\boxed{
\text{candidate retrieval}
\ll
\text{all-pairs comparison}
}
$$

while maintaining a retrieval recall appropriate to the asymmetric business risk, fitting the required computational budget as closely as the supplied hardware permits, persisting its retrieval structure in a relational database, mitigating observed workload skew, and preserving stable opportunity identities across pipeline reruns.

The final report should allow a reviewer to answer five questions immediately:

1. **What exactly does "similar" mean?**
2. **Why was this representation size chosen?**
3. **Why does the retrieval operating point accept its particular risk/work trade-off?**
4. **Why does the database access path scale better than the rejected alternative?**
5. **What pathological workload was found, how was it fixed, and what did the fix cost in retrieval quality?**

If any of those five answers relies primarily on an assertion rather than an experiment, the implementation is not finished.
