import unittest

from wetext import Normalizer, normalize


class NBestTest(unittest.TestCase):
    def test_matches_official_chinese_itn_order(self):
        normalizer = Normalizer(lang="zh", operator="itn")
        self.assertEqual(normalizer.normalize("一点零二", nbest=3), ["1.02", "1.0二", "一点零二"])

    def test_matches_official_english_tn_tie_order(self):
        normalizer = Normalizer(lang="en", operator="tn")
        self.assertEqual(
            normalizer.normalize("4x6", nbest=3),
            ["four by six", "four times six", "four x six"],
        )

    def test_function_api_and_validation(self):
        self.assertEqual(normalize("一点零二", lang="zh", operator="itn", nbest=2), ["1.02", "1.0二"])
        with self.assertRaises(ValueError):
            normalize("test", nbest=0)
        with self.assertRaises(ValueError):
            normalize("test", nbest=True)

    def test_candidates_expose_costs_in_nbest_order(self):
        candidates = Normalizer(lang="en", operator="tn").normalize_candidates("4x6", nbest=3)
        self.assertEqual(
            [candidate.text for candidate in candidates],
            ["four by six", "four times six", "four x six"],
        )
        self.assertLessEqual(candidates[0].cost, candidates[1].cost)
        self.assertLess(candidates[1].cost, candidates[2].cost)
        self.assertEqual(
            set(candidates[0].as_dict()),
            {"text", "cost", "tagger_cost", "verbalizer_cost", "tagger_rank", "verbalizer_rank"},
        )


class MappingTest(unittest.TestCase):
    def test_chinese_money_mapping(self):
        result = Normalizer(lang="zh", operator="itn").normalize_with_mapping("价格是十三点五元")
        self.assertEqual(result.output_text, "价格是¥13.5")
        self.assertEqual(len(result.mappings), 1)
        mapping = result.mappings[0]
        self.assertEqual(mapping.token_type, "money")
        self.assertEqual((mapping.input_start, mapping.input_end, mapping.input_text), (3, 8, "十三点五元"))
        self.assertEqual((mapping.output_start, mapping.output_end, mapping.output_text), (3, 8, "¥13.5"))

    def test_nbest_mapping_matches_outputs(self):
        results = Normalizer(lang="zh", operator="itn").normalize_with_mapping("一点零二", nbest=3)
        self.assertEqual([result.output_text for result in results], ["1.02", "1.0二", "一点零二"])

    def test_identity_and_unicode_postprocessing(self):
        result = Normalizer(
            lang="zh",
            operator="tn",
            traditional_to_simple=True,
        ).normalize_with_mapping("這是2026年", include_identity=True)
        self.assertEqual(result.output_text, "这是二零二六年")
        self.assertEqual(
            result.mappings[0].as_dict(),
            {
                "kind": "replace",
                "token_type": "char",
                "input": {"start": 0, "end": 1, "text": "這"},
                "output": {"start": 0, "end": 1, "text": "这"},
            },
        )

    def test_mapping_dict_shape(self):
        result = Normalizer(lang="en", operator="tn").normalize_with_mapping("I paid $12.50.")
        payload = result.as_dict()
        self.assertEqual(payload["input"], "I paid $12.50.")
        self.assertEqual(payload["output"], "I paid twelve point five dollars.")
        self.assertEqual(payload["mappings"][0]["token_type"], "money")

    def test_fix_contractions_is_incompatible_with_mapping(self):
        normalizer = Normalizer(lang="en", operator="tn", fix_contractions=True)
        with self.assertRaisesRegex(ValueError, "incompatible"):
            normalizer.normalize_with_mapping("plain text")


if __name__ == "__main__":
    unittest.main()
