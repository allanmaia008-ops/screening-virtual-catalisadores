import unittest

from fischer_tropsch_scope import FISCHER_TROPSCH_LTFT_SCOPE, validar_escopo_fischer_tropsch


class FischerTropschScopeTests(unittest.TestCase):
    def test_scope_is_valid_but_not_executable(self):
        self.assertTrue(validar_escopo_fischer_tropsch())
        self.assertEqual(FISCHER_TROPSCH_LTFT_SCOPE["status"], "definido_nao_executavel")

    def test_product_distribution_is_explicit(self):
        bands = FISCHER_TROPSCH_LTFT_SCOPE["produtos"]["faixas_a_reportar"]
        self.assertEqual(bands, ["CH4", "C2-C4", "C5-C11", "C12+", "C5+"])

    def test_cobalt_and_iron_are_separate_families(self):
        families = FISCHER_TROPSCH_LTFT_SCOPE["familias_ativas_iniciais"]
        self.assertNotEqual(families["cobalto"]["fase_ativa_referencia"], families["ferro"]["fase_ativa_referencia"])


if __name__ == "__main__":
    unittest.main()
