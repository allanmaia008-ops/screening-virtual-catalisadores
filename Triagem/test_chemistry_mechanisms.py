import unittest

from chemistry_mechanisms import mechanism_context, render_mechanism_panel


class ChemistryMechanismsTests(unittest.TestCase):
    class FakeStreamlit:
        def __init__(self):
            self.markdown_calls = []

        def markdown(self, value, **kwargs):
            self.markdown_calls.append((value, kwargs))

    def test_only_selected_reaction_has_a_pathway(self):
        self.assertEqual(mechanism_context("rwgs", ["Au"], "", "CeO₂")["label"][0], "RWGS")
        self.assertIsNone(mechanism_context("unsupported", ["Au"], "", "CeO2"))

    def test_direct_match_requires_metals_support_and_promoter_to_match(self):
        self.assertTrue(mechanism_context("metanacao", ["Ni"], "", "Y₂O₃")["direct_match"])
        self.assertFalse(mechanism_context("metanacao", ["Ni"], "K", "Y₂O₃")["direct_match"])
        self.assertFalse(mechanism_context("metanacao", ["Ni", "Co"], "", "Y₂O₃")["direct_match"])
        self.assertTrue(mechanism_context("metanacao", ["Ni"], "", "CeO2")["direct_match"])

    def test_reforming_reference_requires_bimetal_and_ceria(self):
        self.assertTrue(mechanism_context("reforma", ["Pt", "Ni"], "", "CeO₂")["direct_match"])
        self.assertFalse(mechanism_context("reforma", ["Ni"], "", "CeO₂")["direct_match"])

    def test_methanation_pathway_changes_with_selected_support_system(self):
        y2o3 = mechanism_context("metanacao", ["Ni"], "", "Y₂O₃")
        ceria = mechanism_context("metanacao", ["Ni"], "", "CeO₂")
        self.assertIn("formiato superficial", y2o3["steps"][1])
        self.assertIn("CeO₂ vacancies", ceria["steps"][0])
        self.assertIn("C8CY02097C", ceria["doi"])

    def test_selected_promoter_is_explicitly_not_attributed_without_reference(self):
        context = mechanism_context("reforma", ["Ni"], "K", "CeO₂")
        self.assertIn("K foi selecionado", context["promoter_reading"])
        self.assertIn("Pt–Ni/CeO₂", context["risks"][-1][1])

    def test_render_uses_selected_reforming_metals_promoter_and_support(self):
        fake_st = self.FakeStreamlit()
        render_mechanism_panel(fake_st, "reforma", "NiPt", ["Pt", "Ni"], "K", "CeO₂", english=True)
        panel = fake_st.markdown_calls[0][0]
        self.assertIn("Pt was associated with CO₂ dissociation", panel)
        self.assertIn("K is selected but absent from the reference", panel)
        self.assertIn("Pt, Ni/CeO₂", panel)
        self.assertIn("composition differs", panel)


if __name__ == "__main__":
    unittest.main()
