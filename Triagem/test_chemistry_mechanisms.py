import unittest

from chemistry_mechanisms import mechanism_context


class ChemistryMechanismsTests(unittest.TestCase):
    def test_only_selected_reaction_has_a_pathway(self):
        self.assertEqual(mechanism_context("rwgs", ["Au"], "", "CeO₂")["label"][0], "RWGS")
        self.assertIsNone(mechanism_context("unsupported", ["Au"], "", "CeO2"))

    def test_direct_match_requires_metals_support_and_promoter_to_match(self):
        self.assertTrue(mechanism_context("metanacao", ["Ni"], "", "Y₂O₃")["direct_match"])
        self.assertFalse(mechanism_context("metanacao", ["Ni"], "K", "Y₂O₃")["direct_match"])
        self.assertFalse(mechanism_context("metanacao", ["Ni", "Co"], "", "Y₂O₃")["direct_match"])
        self.assertFalse(mechanism_context("metanacao", ["Ni"], "", "CeO2")["direct_match"])

    def test_reforming_reference_requires_bimetal_and_ceria(self):
        self.assertTrue(mechanism_context("reforma", ["Pt", "Ni"], "", "CeO₂")["direct_match"])
        self.assertFalse(mechanism_context("reforma", ["Ni"], "", "CeO₂")["direct_match"])


if __name__ == "__main__":
    unittest.main()
