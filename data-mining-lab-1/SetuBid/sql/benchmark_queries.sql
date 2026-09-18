-- SetuBid Database Access Path Benchmark Queries

-- Query 1: Production Candidate Lookup using (band_idx, bucket_key) Index
-- Parametrized for a notice's 32 band keys via temp table or unnest
EXPLAIN ANALYZE
SELECT DISTINCT r.notice_id
FROM retrieval_signatures r
JOIN query_bands q 
  ON r.band_idx = q.band_idx 
 AND r.bucket_key = q.bucket_key
WHERE r.notice_id != 'TARGET_NOTICE_ID';

-- Query 2: Forced Sequential Scan Alternative (Disabling Index or Scanning Unindexed Table)
EXPLAIN ANALYZE
SELECT DISTINCT r.notice_id
FROM retrieval_signatures_unindexed r
JOIN query_bands q 
  ON r.band_idx = q.band_idx 
 AND r.bucket_key = q.bucket_key
WHERE r.notice_id != 'TARGET_NOTICE_ID';
