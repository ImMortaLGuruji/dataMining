-- SetuBid Relational Indexes

-- Core secondary index for sublinear LSH candidate bucket lookup
CREATE INDEX IF NOT EXISTS idx_retrieval_band_bucket 
ON retrieval_signatures (band_idx, bucket_key);

-- Secondary index on notice_id for fast signature retrieval
CREATE INDEX IF NOT EXISTS idx_retrieval_notice_id 
ON retrieval_signatures (notice_id);

-- Cluster lookup indexes
CREATE INDEX IF NOT EXISTS idx_cluster_card_id 
ON dedup_clusters (stable_card_id);

CREATE INDEX IF NOT EXISTS idx_members_notice 
ON cluster_members (notice_id);
