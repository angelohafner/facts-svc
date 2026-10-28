"""Checks for clean, renderer-independent SVC configuration validation."""

import json
import unittest

from facts_svc import Branch, BranchKind, SVCConfig, presets


class ModelTests(unittest.TestCase):
    def test_presets_have_unique_valid_branches(self):
        self.assertEqual(set(presets()), {"fc-tcr", "tsc-tcr", "hybrid", "multi-tsc", "tsr-fc", "tcr-only"})
        for config in presets().values():
            self.assertTrue(config.branches)
            self.assertEqual(SVCConfig.from_dict(json.loads(json.dumps(config.to_dict()))), config)

    def test_case_insensitive_branch_kind(self):
        branch = Branch.from_dict({"name": "TSC 1", "kind": "tsc"})
        self.assertIs(branch.kind, BranchKind.TSC)

    def test_bad_filter_order_is_rejected(self):
        for order in (None, 1, 3.5, True, -7):
            with self.subTest(order=order), self.assertRaises(ValueError):
                Branch("Harmonic filter", BranchKind.FILTER, harmonic_order=order)

    def test_illegal_order_for_non_filter_is_rejected(self):
        with self.assertRaises(ValueError):
            Branch("TCR", BranchKind.TCR, harmonic_order=5)

    def test_duplicate_branch_is_rejected(self):
        with self.assertRaises(ValueError):
            SVCConfig("Duplicate", (Branch("TCR", BranchKind.TCR),
                                    Branch("tcr", BranchKind.TSR)))

    def test_empty_config_is_rejected(self):
        with self.assertRaises(ValueError):
            SVCConfig("Empty", ())

    def test_unrecognized_component_is_rejected(self):
        with self.assertRaises(ValueError):
            Branch.from_dict({"name": "Other", "kind": "NOT_SUPPORTED"})


if __name__ == "__main__":
    unittest.main()
