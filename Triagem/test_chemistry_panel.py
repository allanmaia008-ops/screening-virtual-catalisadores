import unittest

import numpy as np
import pandas as pd

from chemistry_panel import coke_resistance_score


class ChemistryPanelTests(unittest.TestCase):
    def test_reads_portuguese_export(self):
        frame = pd.DataFrame({"fórmula": ["NiCo"], "score de resistência a coque": [0.585]})
        self.assertAlmostEqual(coke_resistance_score(frame), 0.585)

    def test_recovers_matching_formula_from_alternative_table(self):
        primary = pd.DataFrame({"fórmula": ["NiCo"], "score final": [0.8]})
        alternative = pd.DataFrame(
            {"Formula": ["FeCu", "NiCo"], "Coke resistance score": [0.35, 0.62]}
        )
        self.assertAlmostEqual(coke_resistance_score(primary, alternative), 0.62)

    def test_accepts_advanced_validation_label(self):
        primary = pd.DataFrame({"fórmula": ["NiCo"]})
        validation = pd.DataFrame(
            {"fórmula": ["NiCo"], "score anti coque avançado": [0.71]}
        )
        self.assertAlmostEqual(coke_resistance_score(primary, validation), 0.71)

    def test_normalizes_percentage_exports(self):
        frame = pd.DataFrame({"formula": ["NiCo"], "coke resistance": [58.5]})
        self.assertAlmostEqual(coke_resistance_score(frame), 0.585)

    def test_missing_value_is_not_replaced_by_zero(self):
        frame = pd.DataFrame({"formula": ["NiCo"], "score final": [0.8]})
        self.assertTrue(np.isnan(coke_resistance_score(frame)))


if __name__ == "__main__":
    unittest.main()
