import unittest

from chemistry_mechanisms import mechanism_context, render_mechanism_panel


class ChemistryMechanismsTests(unittest.TestCase):
    class FakeStreamlit:
        def __init__(self):
            self.markdown_calls = []
            self.html_calls = []

        def markdown(self, value, **kwargs):
            self.markdown_calls.append((value, kwargs))

        def html(self, value):
            self.html_calls.append(value)

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

    def test_pt_zirconia_uses_composition_matched_bifunctional_drm_pathway(self):
        context = mechanism_context("reforma", ["Pt"], "", "ZrO₂")
        self.assertTrue(context["direct_match"])
        self.assertIn("carbonato", " ".join(context["steps"]))
        self.assertIn("perímetro Pt–ZrO₂", context["finding"])
        self.assertEqual(context["doi"], "https://doi.org/10.1006/jcat.1998.2022")

    def test_support_properties_create_qualified_hypotheses_not_confirmed_mechanism(self):
        props = {"basicidade": 0.95, "afinidade_co2": 0.88, "redox": 0.35, "vacancia_oxigenio": 0.28}
        context = mechanism_context("reforma", ["Co"], "La", "MgAlOx", support_properties=props)
        cards = " ".join(text for _, text in context["property_hypotheses"]["cards"])
        self.assertEqual(context["property_hypotheses"]["property_signal"], "basic")
        self.assertIn("proxies internos", cards)
        self.assertIn("não demonstra", cards)
        self.assertIn("etapa não atribuída", context["property_hypotheses"]["pathway"])
        self.assertFalse(context["direct_match"])

    def test_property_hypothesis_is_translated(self):
        props = {"basicidade": 0.90, "afinidade_co2": 0.85, "redox": 0.20, "vacancia_oxigenio": 0.18}
        context = mechanism_context("reforma", ["Co"], "La", "MgAl2O4", english=True, support_properties=props)
        cards = " ".join(text for _, text in context["property_hypotheses"]["cards"])
        self.assertIn("internal basicity/CO₂-affinity proxies", cards)
        self.assertIn("not demonstrate", cards)

    def test_alternative_supports_get_separate_property_hypotheses(self):
        profiles = [
            {"suporte": "MgAlOx", "basicidade": .95, "afinidade_co2": .88, "redox": .35, "vacancia_oxigenio": .28},
            {"suporte": "La2O3-Al2O3", "basicidade": .88, "afinidade_co2": .90, "redox": .45, "vacancia_oxigenio": .38},
            {"suporte": "MgAl2O4", "basicidade": .88, "afinidade_co2": .80, "redox": .28, "vacancia_oxigenio": .22},
        ]
        context = mechanism_context("reforma", ["Co"], "La",
                                   "MgAlOx, La2O3-Al2O3 ou espinelio MgAl2O4",
                                   support_property_profiles=profiles)
        support_card = context["property_hypotheses"]["cards"][1][1]
        path = context["property_hypotheses"]["pathway"]
        for name in ("MgAlOx", "La2O3-Al2O3", "MgAl2O4"):
            self.assertIn(name, support_card)
            self.assertIn(name, path)
        self.assertIn("Cenários por suporte", path)

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

    def test_support_recommendations_are_parsed_as_alternatives(self):
        context = mechanism_context("reforma", ["Co"], "La", "MgAlOx, La2O3-Al2O3 ou espinelio MgAl2O4")
        self.assertEqual(context["support_options"], ["MgAlOx", "La2O3-Al2O3", "espinelio MgAl2O4"])
        self.assertFalse(context["direct_match"])
        self.assertIn("alternativas de suporte", context["support_reading"])

    def test_ru_ceria_uses_composition_matched_operando_mechanism(self):
        context = mechanism_context("metanacao", ["Ru"], "", "CeO₂")
        self.assertTrue(context["direct_match"])
        self.assertIn("Ru–CO*", " ".join(context["steps"]))
        self.assertEqual(context["doi"], "https://doi.org/10.1021/acs.jpcc.1c07537")
        self.assertIn("corresponde ao suporte da referência", context["support_reading"])
        self.assertIn("ZrO₂, TiO₂ e In₂O₃", context["literature_notes"][0]["text"])

    def test_ru_support_review_is_not_treated_as_mechanism_for_other_support(self):
        context = mechanism_context("metanacao", ["Ru"], "", "ZrO₂")
        self.assertFalse(context["direct_match"])
        self.assertEqual(len(context["literature_notes"]), 1)
        self.assertIn("não suportes equivalentes", context["literature_notes"][0]["text"])
        self.assertIn("detalhada deste painel é para Ru/CeO₂", context["support_reading"])

    def test_nonmatching_composition_does_not_inherit_reference_pathway(self):
        fake_st = self.FakeStreamlit()
        render_mechanism_panel(fake_st, "reforma", "Co0.71La0.29", ["Co"], "La",
                               "MgAlOx, La2O3-Al2O3 ou espinelio MgAl2O4")
        panel = fake_st.html_calls[0]
        self.assertIn("Não há mecanismo correspondente à composição selecionada", panel)
        self.assertNotIn("CH₄ ativado", panel)
        self.assertNotIn("Chen et al.", panel)
        self.assertIn("ceo2", panel.lower())  # named only as the comparison reference
        self.assertIn("Co0.71La0.29", panel)
        self.assertIn("Analogia da literatura: Ni–Co/La₂O₃", panel)
        self.assertIn("10.1016/j.jcat.2016.03.018", panel)
        self.assertIn("Hipótese mecanística baseada nas propriedades", panel)
        self.assertIn("heurísticas normalizadas do suporte", panel)
        self.assertEqual(fake_st.markdown_calls, [])

    def test_render_uses_selected_reforming_metals_promoter_and_support(self):
        fake_st = self.FakeStreamlit()
        render_mechanism_panel(fake_st, "reforma", "NiPt", ["Pt", "Ni"], "K", "CeO₂", english=True)
        panel = fake_st.html_calls[0]
        self.assertIn("Pt was associated with CO₂ dissociation", panel)
        self.assertIn("K is selected but absent from the reference", panel)
        self.assertIn("Pt, Ni/CeO₂", panel)
        self.assertIn("composition differs", panel)
        self.assertIn("Property-based mechanistic hypothesis", panel)


if __name__ == "__main__":
    unittest.main()
