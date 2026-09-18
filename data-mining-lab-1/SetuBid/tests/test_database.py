"""Unit tests for database persistence and index structures."""

import os
import unittest
import duckdb


class TestDatabasePersistence(unittest.TestCase):

    def setUp(self):
        self.db_path = "test_db_persistence.duckdb"
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        self.conn = duckdb.connect(self.db_path)

    def tearDown(self):
        self.conn.close()
        if os.path.exists(self.db_path):
            try:
                os.remove(self.db_path)
            except OSError:
                pass

    def test_schema_and_index_creation(self):
        schema_file = os.path.join(os.path.dirname(__file__), "..", "sql", "schema.sql")
        indexes_file = os.path.join(os.path.dirname(__file__), "..", "sql", "indexes.sql")

        with open(schema_file, "r") as f:
            self.conn.execute(f.read())
        with open(indexes_file, "r") as f:
            self.conn.execute(f.read())

        # Insert dummy notice and signature
        self.conn.execute("""
            INSERT INTO notices (notice_id, portal_id, published_at, title, body, estimated_value, closing_date)
            VALUES ('N001', 'P001', '2024-01-01', 'Test Tender', 'Road construction', 1000000.0, '2024-02-01')
        """)
        self.conn.execute("""
            INSERT INTO retrieval_signatures (notice_id, band_idx, bucket_key)
            VALUES ('N001', 0, 9876543210123)
        """)

        cnt = self.conn.execute("SELECT count(*) FROM retrieval_signatures WHERE band_idx = 0 AND bucket_key = 9876543210123").fetchone()[0]
        self.assertEqual(cnt, 1)

        # Test index probe
        res = self.conn.execute("""
            SELECT notice_id FROM retrieval_signatures WHERE band_idx = 0 AND bucket_key = 9876543210123
        """).fetchone()[0]
        self.assertEqual(res, "N001")


if __name__ == "__main__":
    unittest.main()
