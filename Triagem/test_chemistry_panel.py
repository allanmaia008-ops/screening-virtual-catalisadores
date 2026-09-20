import unittest

import numpy as np
import pandas as pd

from chemistry_panel import coke_resistance_score, kinetic_reference_line, sabatier_columns


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

    def test_sabatier_columns_accept_translated_volcano_headers(self):
        frame = pd.DataFrame(
            {
                "energia de adsorção do vulcão (eV)": [0.83],
                "score de vulcão": [0.94],
            }
        )
        self.assertEqual(
            sabatier_columns(frame),
            ("energia de adsorção do vulcão (eV)", "score de vulcão"),
        )

    def test_sabatier_columns_preserve_legacy_headers(self):
        frame = pd.DataFrame(
            {
                "energia de adsorção volcano (eV)": [0.83],
                "taxa relativa volcano": [0.94],
            }
        )
        self.assertEqual(
            sabatier_columns(frame),
            ("energia de adsorção volcano (eV)", "taxa relativa volcano"),
        )

    def test_kinetic_reference_line_returns_fit_and_correlation(self):
        reference = kinetic_reference_line(
            pd.Series([0.1, 0.2, 0.3, 0.4]),
            pd.Series([0.4, 0.5, 0.6, 0.7]),
        )
        self.assertIsNotNone(reference)
        x_line, y_line, correlation = reference
        self.assertEqual(len(x_line), 80)
        self.assertEqual(len(y_line), 80)
        self.assertAlmostEqual(correlation, 1.0)

    def test_kinetic_reference_line_rejects_constant_rate(self):
        reference = kinetic_reference_line(
            pd.Series([7.1e-8, 7.1e-8, 7.1e-8]),
            pd.Series([0.61, 0.65, 0.69]),
        )
        self.assertIsNone(reference)


if __name__ == "__main__":
    unittest.main()
