import unittest

from lpr.postprocess import (
    extract_plate_suffix,
    looks_like_plate,
    repair_plate_text,
    score_plate_text,
    supported_provinces,
)


class PostprocessTestCase(unittest.TestCase):
    def test_repair_keeps_standard_plate(self) -> None:
        self.assertEqual(repair_plate_text("粤B12345"), "粤B12345")

    def test_repair_normalizes_common_confusions(self) -> None:
        self.assertEqual(repair_plate_text("粤81234S"), "粤B12345")

    def test_fallback_plate_is_scored(self) -> None:
        self.assertTrue(looks_like_plate("AB12345"))
        self.assertGreater(score_plate_text("AB12345", 80), 0.5)

    def test_supports_all_32_province_level_prefixes(self) -> None:
        provinces = supported_provinces()
        self.assertEqual(len(provinces), 32)
        self.assertIn("京", provinces)
        self.assertIn("粤", provinces)
        self.assertIn("藏", provinces)
        self.assertIn("台", provinces)

    def test_normalizes_full_province_name(self) -> None:
        self.assertEqual(repair_plate_text("广东省B12345"), "粤B12345")
        self.assertEqual(repair_plate_text("台湾省A12345"), "台A12345")

    def test_extracts_suffix_from_symbol_noise(self) -> None:
        self.assertEqual(extract_plate_suffix("BA-|4237"), "A14237")


if __name__ == "__main__":
    unittest.main()
