"""Unit tests for LSH retrieval indexing."""

import unittest
import numpy as np
from setubid.retrieval.index import LSHIndex


class TestRetrieval(unittest.TestCase):

    def test_lsh_insertion_and_retrieval(self):
        lsh = LSHIndex(num_bands=4, rows_per_band=4)
        sig1 = np.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16], dtype=np.int64)
        # Identical signature
        sig2 = np.copy(sig1)
        # Different signature
        sig3 = np.array([100 + i for i in range(16)], dtype=np.int64)

        lsh.insert("N1", sig1)
        lsh.insert("N2", sig2)
        lsh.insert("N3", sig3)

        cand_n1 = lsh.query_candidates("N1")
        self.assertIn("N2", cand_n1)
        self.assertNotIn("N3", cand_n1)
        self.assertNotIn("N1", cand_n1)  # self excluded

    def test_candidate_cap(self):
        lsh = LSHIndex(num_bands=2, rows_per_band=2)
        sig = np.array([1, 2, 3, 4], dtype=np.int64)
        for i in range(50):
            lsh.insert(f"N{i}", sig)

        cand = lsh.query_candidates("N0", candidate_cap=10)
        self.assertLessEqual(len(cand), 10)

    def test_theoretical_probability(self):
        lsh = LSHIndex(num_bands=32, rows_per_band=8)
        # At s=0, P=0. At s=1, P=1.
        self.assertAlmostEqual(lsh.theoretical_collision_prob(0.0), 0.0)
        self.assertAlmostEqual(lsh.theoretical_collision_prob(1.0), 1.0)
        # At s=0.65, P should be around 0.50
        p_mid = lsh.theoretical_collision_prob(0.65)
        self.assertGreater(p_mid, 0.40)
        self.assertLess(p_mid, 0.65)


if __name__ == "__main__":
    unittest.main()
