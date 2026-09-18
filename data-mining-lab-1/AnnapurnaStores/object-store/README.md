# Annapurna Stores — Object Store Layout

## 1. Overview
The raw data platform lands all supermarket daily sales files into a local S3-compatible **MinIO** object store under bucket `annapurna-raw`.

Source files are never modified in place, preserving raw lineage.

---

## 2. Storage Layouts

### Layout A — Partitioned Layout (Production)
```text
annapurna-raw/
└── raw/
    └── sales/
        ├── store=S01/
        │   ├── year=2024/
        │   │   ├── month=01/
        │   │   │   ├── SALES_S01_20240101.csv
        │   │   │   ├── SALES_S01_20240102.csv
        │   │   │   └── ...
        │   │   ├── month=02/
        │   │   └── ...
        ├── store=02/
        └── ...
```

### Layout B — Flat Layout (Benchmarking Comparison)
```text
annapurna-raw/
└── all-sales/
    ├── SALES_S01_20240101.csv
    ├── SALES_S01_20240102.csv
    ├── SALES_S02_20240101.csv
    └── ...
```

---

## 3. Partitioning Strategy & Pruning Rationale
In supermarket analytics, the most common operational queries filter by:
1. **Store** (`store=S01`)
2. **Year and Month** (`year=2024/month=03`)

By structuring high-cardinality filtering dimensions into the object key prefix hierarchy (`store=.../year=.../month=...`), analytical query engines (DuckDB, Spark, Presto) perform **prefix pruning**. Only the objects in the targeted sub-prefix are enumerated and fetched, eliminating unnecessary I/O across non-matching stores and months.
