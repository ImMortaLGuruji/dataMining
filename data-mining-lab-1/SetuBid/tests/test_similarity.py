"""Unit tests for text representation and exact similarity calculations."""

import unittest
from setubid.similarity.representation import extract_word_tokens, extract_char_ngrams, extract_char_ngrams_range
from setubid.similarity.exact import jaccard_similarity, compute_exact_notice_similarity, evaluate_field_compatibility


class TestSimilarity(unittest.TestCase):

    def test_extract_word_tokens(self):
        text = "Supply and Installation of 50 CCTV Cameras"
        tokens = extract_word_tokens(text)
        self.assertIn("supply", tokens)
        self.assertIn("installation", tokens)
        self.assertIn("cctv", tokens)
        self.assertIn("cameras", tokens)

    def test_extract_char_ngrams(self):
        text = "abcde"
        ngrams_3 = extract_char_ngrams(text, n=3)
        self.assertEqual(ngrams_3, {"abc", "bcd", "cde"})

    def test_extract_char_ngrams_range(self):
        text = "abcd"
        ngrams = extract_char_ngrams_range(text, min_n=2, max_n=3)
        expected = {"ab", "bc", "cd", "abc", "bcd"}
        self.assertEqual(ngrams, expected)

    def test_jaccard_similarity_edge_cases(self):
        # Identical
        s1 = {"a", "b", "c"}
        self.assertEqual(jaccard_similarity(s1, s1), 1.0)
        # Disjoint
        s2 = {"d", "e", "f"}
        self.assertEqual(jaccard_similarity(s1, s2), 0.0)
        # Overlapping: 1 intersection, 5 union -> 0.2
        s3 = {"c", "d", "e"}
        self.assertAlmostEqual(jaccard_similarity(s1, s3), 1.0 / 5.0)
        # Both empty
        self.assertEqual(jaccard_similarity(set(), set()), 1.0)

    def test_composite_similarity(self):
        b1 = {"road", "construction", "concrete"}
        b2 = {"road", "construction", "asphalt"}
        t1 = {"tender", "road"}
        t2 = {"tender", "road"}
        
        sim = compute_exact_notice_similarity(b1, b2, t1, t2, weight_body=0.7, weight_title=0.3)
        # Body jaccard: 2/4 = 0.5. Title jaccard: 1.0.
        # Composite: 0.7 * 0.5 + 0.3 * 1.0 = 0.35 + 0.30 = 0.65
        self.assertAlmostEqual(sim, 0.65)

    def test_field_compatibility(self):
        na = {"estimated_value": "45,00,000", "closing_date": "2024-05-15"}
        nb = {"estimated_value": "4500000", "closing_date": "2024-05-20"}
        compat = evaluate_field_compatibility(na, nb)
        self.assertTrue(compat["val_match"])
        self.assertEqual(compat["val_diff"], 0.0)
        self.assertEqual(compat["cls_delta_days"], 5)


if __name__ == "__main__":
    unittest.main()
