# SetuBid Similarity Representation Benchmark Report

## 1. Candidate Representations Evaluated

We evaluated 5 deterministic representation strategies across all 900 ground-truth pairs:
1. **Candidate A (Word Tokens)**: Tokenizes cleaned text into discrete whitespace/punctuation-delimited words.
2. **Candidate B1 (Character 3-grams)**: Substring shingles of length 3 sliding across body text.
3. **Candidate B2 (Character 3-to-5-grams)**: Multi-scale character n-grams spanning length 3 to 5.
4. **Candidate C (Composite: 0.7 Body + 0.3 Title, Char 3-5-grams)**: Fused representation capturing both detailed body specifications and concise tender titles.
5. **Candidate C+Mitigation (Stripped Composite)**: Preamble-stripped composite representation.

## 2. Empirical Benchmark Results

| Representation | Same Mean (Median) | Diff Mean (Median) | Mean Gap | AUC |
|---|---:|---:|---:|---:|
| **Candidate A (Word Tokens)** | 0.7355 (0.7351) | 0.4414 (0.444) | 0.2941 | **0.8707** |
| **Candidate B1 (Char 3-grams)** | 0.8071 (0.8174) | 0.5999 (0.6) | 0.2071 | **0.8581** |
| **Candidate B2 (Char 3-5-grams)** | 0.7414 (0.7357) | 0.4815 (0.4804) | 0.2599 | **0.859** |
| **Candidate C (Composite: 0.7 Body + 0.3 Title)** | 0.7475 (0.7494) | 0.3661 (0.3617) | 0.3814 | **0.9948** |
| **Candidate C+Mitigation (Stripped Composite)** | 0.7307 (0.751) | 0.3375 (0.351) | 0.3932 | **0.9607** |

## 3. Pair-Level Case Study (Section 10 Requirement)

### Same Pair Example (`N010018` vs `N010020`):
- Notice A Portal: `P004` | Notice B Portal: `P008`
- Word Tokens Similarity: **0.3053**
- Char 3-5-grams Similarity: **0.3397**
- Composite (0.7 Body + 0.3 Title) Similarity: **0.4524**

### Different Pair Example (`N007876` vs `N008565`):
- Notice A Portal: `P001` | Notice B Portal: `P006`
- Word Tokens Similarity: **0.4201**
- Char 3-5-grams Similarity: **0.4508**
- Composite (0.7 Body + 0.3 Title) Similarity: **0.3189**

## 4. Mathematical Similarity Definition (Section 11 Requirement)

The deterministic similarity function $S(x, y)$ is defined as:

$$S(x, y) = 0.70 \cdot J\big(\text{shingles}(\text{body}_x), \text{shingles}(\text{body}_y)\big) + 0.30 \cdot J\big(\text{shingles}(\text{title}_x), \text{shingles}(\text{title}_y)\big)$$

where:
- $\text{shingles}(t)$ extracts character 3-to-5-grams over normalized text.
- $J(A, B) = \frac{|A \cap B|}{|A \cup B|}$ is the standard exact Jaccard similarity.
- **Field Guard**: In downstream deduplication confirmation, identical `estimated_value` is verified ($|\text{val}_x - \text{val}_y| == 0$) and closing date delta must be $\le 30$ days.
