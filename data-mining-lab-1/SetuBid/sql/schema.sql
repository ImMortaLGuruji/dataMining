-- SetuBid Relational Schema (DuckDB / PostgreSQL compatible)

CREATE TABLE IF NOT EXISTS notices (
    notice_id VARCHAR PRIMARY KEY,
    portal_id VARCHAR NOT NULL,
    published_at DATE NOT NULL,
    title VARCHAR NOT NULL,
    body VARCHAR NOT NULL,
    estimated_value DOUBLE,
    closing_date DATE
);

CREATE TABLE IF NOT EXISTS retrieval_signatures (
    notice_id VARCHAR NOT NULL,
    band_idx INTEGER NOT NULL,
    bucket_key UBIGINT NOT NULL,
    PRIMARY KEY (notice_id, band_idx)
);

CREATE TABLE IF NOT EXISTS dedup_clusters (
    cluster_id VARCHAR PRIMARY KEY,
    stable_card_id VARCHAR NOT NULL UNIQUE,
    lead_notice_id VARCHAR NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS cluster_members (
    cluster_id VARCHAR NOT NULL REFERENCES dedup_clusters(cluster_id),
    notice_id VARCHAR NOT NULL UNIQUE REFERENCES notices(notice_id),
    portal_id VARCHAR NOT NULL,
    published_at DATE NOT NULL,
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (cluster_id, notice_id)
);
