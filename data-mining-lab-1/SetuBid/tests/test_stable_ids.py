"""Unit tests for stable opportunity identity persistence (Checkpoint 8).

Validates:
1. Restart stability across database connections
2. Repeated-run idempotency
3. New-copy duplicate arrival stability
4. New distinct notice arrival isolation
5. Deterministic cluster merge policy
"""

import os
import unittest
import duckdb
from setubid.deduplication.stable_ids import StableIdentityManager, generate_card_id
from setubid.deduplication.clustering import cluster_verified_pairs


class TestStableIdentities(unittest.TestCase):

    def setUp(self):
        self.test_db = "test_stable_ids.duckdb"
        if os.path.exists(self.test_db):
            os.remove(self.test_db)
        self.conn = duckdb.connect(self.test_db)
        # Create minimal schema
        self.conn.execute("""
            CREATE TABLE dedup_clusters (
                cluster_id VARCHAR PRIMARY KEY,
                stable_card_id VARCHAR NOT NULL UNIQUE,
                lead_notice_id VARCHAR NOT NULL
            );
            CREATE TABLE cluster_members (
                cluster_id VARCHAR,
                notice_id VARCHAR UNIQUE,
                portal_id VARCHAR,
                published_at DATE
            );
        """)

    def tearDown(self):
        self.conn.close()
        if os.path.exists(self.test_db):
            try:
                os.remove(self.test_db)
            except OSError:
                pass

    def test_repeated_run_idempotency(self):
        manager = StableIdentityManager(self.conn)
        raw_clusters = {
            "N10": ["N10", "N11"],
            "N20": ["N20", "N21", "N22"]
        }
        res1 = manager.assign_identities(raw_clusters)
        res2 = manager.assign_identities(raw_clusters)

        # All card IDs must remain exactly identical
        self.assertEqual(res1, res2)
        self.assertEqual(res1["N10"], res1["N11"])
        self.assertEqual(res1["N20"], res1["N21"])
        self.assertNotEqual(res1["N10"], res1["N20"])

    def test_restart_stability(self):
        manager1 = StableIdentityManager(self.conn)
        raw_clusters = {
            "N10": ["N10", "N11"],
            "N30": ["N30"]
        }
        card_map_1 = manager1.assign_identities(raw_clusters)

        # Close connection and open a fresh connection (simulating process restart)
        self.conn.close()
        fresh_conn = duckdb.connect(self.test_db)
        manager2 = StableIdentityManager(fresh_conn)

        self.assertEqual(manager2.get_card_id("N10"), card_map_1["N10"])
        self.assertEqual(manager2.get_card_id("N11"), card_map_1["N11"])
        self.assertEqual(manager2.get_card_id("N30"), card_map_1["N30"])
        fresh_conn.close()
        self.conn = duckdb.connect(self.test_db)

    def test_new_duplicate_copy_arrival(self):
        manager = StableIdentityManager(self.conn)
        initial_clusters = {
            "N10": ["N10", "N11"]
        }
        initial_map = manager.assign_identities(initial_clusters)
        original_card_id = initial_map["N10"]

        # A third duplicate copy N12 arrives and joins the cluster
        updated_clusters = {
            "N10": ["N10", "N11", "N12"]
        }
        updated_map = manager.assign_identities(updated_clusters)

        # Existing notices must NOT change their card ID
        self.assertEqual(updated_map["N10"], original_card_id)
        self.assertEqual(updated_map["N11"], original_card_id)
        # New copy must inherit the existing card ID
        self.assertEqual(updated_map["N12"], original_card_id)

    def test_new_unrelated_notice_arrival(self):
        manager = StableIdentityManager(self.conn)
        c1 = {"N10": ["N10", "N11"]}
        m1 = manager.assign_identities(c1)
        card_10 = m1["N10"]

        # An unrelated notice N99 arrives as a new cluster
        c2 = {
            "N10": ["N10", "N11"],
            "N99": ["N99"]
        }
        m2 = manager.assign_identities(c2)

        # Existing cluster card ID is preserved
        self.assertEqual(m2["N10"], card_10)
        self.assertEqual(m2["N11"], card_10)
        # New notice gets a distinct card ID
        self.assertIn("N99", m2)
        self.assertNotEqual(m2["N99"], card_10)

    def test_deterministic_cluster_merge_policy(self):
        manager = StableIdentityManager(self.conn)
        # Two previously separate clusters
        initial = {
            "N10": ["N10"],
            "N20": ["N20"]
        }
        map_init = manager.assign_identities(initial)
        card_a = map_init["N10"]
        card_b = map_init["N20"]
        self.assertNotEqual(card_a, card_b)

        # Now they merge because a new bridging notice N15 is discovered
        merged = {
            "N10": ["N10", "N15", "N20"]
        }
        map_merged = manager.assign_identities(merged)

        # The winning card ID must be the lexicographical minimum of the existing card IDs
        winning_card = min(card_a, card_b)
        self.assertEqual(map_merged["N10"], winning_card)
        self.assertEqual(map_merged["N15"], winning_card)
        self.assertEqual(map_merged["N20"], winning_card)


if __name__ == "__main__":
    unittest.main()
