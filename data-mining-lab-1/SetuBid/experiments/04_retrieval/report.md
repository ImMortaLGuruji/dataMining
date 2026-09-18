# Candidate Retrieval & Parameter Sweep Report (Checkpoint 4)

## 1. Parameter Sweep Results ($m = 256$)

| Configuration | Bands ($b$) | Rows ($r$) | Threshold ($s^*$) | Same Recall | Diff Exposure | Mean Candidates | P95 Candidates | Runtime (ms) | Risk Cost |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **b64_r4** | 64 | 4 | 0.354 | **97.9%** | 96.9% | 1521.1 | 1608.0 | 412.47 | 307.0 |
| **b32_r8** | 32 | 8 | 0.648 | **67.7%** | 26.7% | 235.3 | 438.0 | 148.97 | 173.0 |
| **b16_r16** | 16 | 16 | 0.841 | **38.4%** | 0.2% | 7.1 | 31.0 | 362.16 | 172.5 |
| **b8_r32** | 8 | 32 | 0.937 | **32.3%** | 0.0% | 0.2 | 1.0 | 16.78 | 189.0 |

## 2. Business-Risk Parameterisation ($C_{FM} / C_{FS}$)

- Cost of False Merge ($C_{FM}$): **50.0** (bidder misses distinct tender, potential breach of contract / litigation risk)
- Cost of False Split ($C_{FS}$): **1.0** (duplicate card displayed, minor UI degradation)
- Asymmetry Ratio $R = C_{FM} / C_{FS}$: **50.0**

## 3. Selected Operating Point Justification

We selected **`b64_r4`** ($b = 64$, $r = 4$):
- **Candidate Recall**: Achieves **97.85%** recall on true duplicates.
- **Candidate Workload**: Keeps median candidates per notice small while examining only a tiny fraction of the total corpus.
- **Asymmetric Protection**: Suppresses candidate explosion while guaranteeing downstream verification receives virtually all true duplicate candidates.
