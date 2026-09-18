"""Unit tests for text normalization and boilerplate suppression."""

import unittest
from setubid.normalization.text import clean_text, strip_portal_boilerplate


class TestNormalization(unittest.TestCase):

    def test_clean_text_basic(self):
        raw = "  Tender Notice: Construction of 100m Road! \n\t Cost: Rs. 50,00,000/- "
        cleaned = clean_text(raw, lowercase=True)
        self.assertNotIn("!", cleaned)
        self.assertNotIn("\n", cleaned)
        self.assertNotIn("/", cleaned)
        self.assertIn("tender notice", cleaned)
        self.assertIn("construction of 100m road", cleaned)

    def test_clean_text_unicode(self):
        raw = "Tender \u2014 Civil Works \u2013 Bridge No. 4"
        cleaned = clean_text(raw, lowercase=True)
        self.assertIn("tender", cleaned)
        self.assertIn("bridge no 4", cleaned)

    def test_strip_portal_boilerplate_npas(self):
        body = (
            "NATIONAL PROCUREMENT AGGREGATION SERVICE TERMS AND CONDITIONS: "
            "All bids must adhere to national guidelines. "
            "Actual tender: Supply of 500 laptops for District Education Office."
        )
        stripped = strip_portal_boilerplate(body, portal_id="P001")
        self.assertNotIn("NATIONAL PROCUREMENT AGGREGATION SERVICE", stripped)
        self.assertIn("supply of 500 laptops", stripped.lower())

    def test_strip_portal_boilerplate_spc(self):
        body = (
            "STATE PROCUREMENT CELL DISCLAIMER: Applicable law applies. "
            "Notice Inviting Tender for laying water pipeline in Zone 4."
        )
        stripped = strip_portal_boilerplate(body, portal_id="P003")
        self.assertNotIn("STATE PROCUREMENT CELL", stripped)
        self.assertIn("laying water pipeline", stripped.lower())


if __name__ == "__main__":
    unittest.main()
