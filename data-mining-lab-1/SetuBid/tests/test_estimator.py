"""Unit tests for MinHash signature estimator."""

import unittest
import numpy as np
from setubid.similarity.estimator import MinHashGenerator, estimate_jaccard


class TestEstimator(unittest.TestCase):

    def test_minhash_determinism(self):
        gen1 = MinHashGenerator(num_hashes=64, seed=42)
        gen2 = MinHashGenerator(num_hashes=64, seed=42)
        shingles = {"apple", "banana", "cherry", "date"}

        sig1 = gen1.compute_signature(shingles)
        sig2 = gen2.compute_signature(shingles)
        np.testing.assert_array_equal(sig1, sig2)

    def test_minhash_identical_sets(self):
        gen = MinHashGenerator(num_hashes=128, seed=42)
        shingles = {"highway", "resurfacing", "asphalt", "division_5"}
        sig1 = gen.compute_signature(shingles)
        sig2 = gen.compute_signature(shingles)

        est = estimate_jaccard(sig1, sig2)
        self.assertEqual(est, 1.0)

    def test_minhash_disjoint_sets(self):
        gen = MinHashGenerator(num_hashes=128, seed=42)
        s1 = {f"token_a_{i}" for i in range(100)}
        s2 = {f"token_b_{i}" for i in range(100)}
        sig1 = gen.compute_signature(s1)
        sig2 = gen.compute_signature(s2)

        est = estimate_jaccard(sig1, sig2)
        # Disjoint sets should have near-zero estimated similarity
        self.assertLessEqual(est, 0.05)


if __name__ == "__main__":
    unittest.main()
