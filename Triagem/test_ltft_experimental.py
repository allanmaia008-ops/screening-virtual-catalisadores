import unittest

from ltft_experimental import (BEZERRA_2010_REFERENCE, PI012_REFERENCE,
    compare_candidates_with_mello, kinetic_readiness, mello_selectivity_table, observed_totals,
    thesis_evidence_readiness)
import pandas as pd


class ExperimentalAnchorTests(unittest.TestCase):
    def test_reported_totals_at_48_hours(self):
        table = observed_totals(48)
        self.assertEqual(table['Massa no período (g)'].round(2).tolist(), [14.4, 14.4, 9.6])

    def test_reported_totals_at_full_duration(self):
        table = observed_totals(PI012_REFERENCE['reported_operation_h'])
        self.assertAlmostEqual(table['Massa no período (g)'].sum(), 153.6)

    def test_extrapolation_is_rejected(self):
        with self.assertRaises(ValueError):
            observed_totals(192.01)
        with self.assertRaises(ValueError):
            observed_totals(-1)

    def test_kinetics_remain_blocked(self):
        readiness = kinetic_readiness()
        self.assertFalse(readiness['ready'])
        self.assertIsNone(readiness['CO_conversion_pct'])
        self.assertIsNone(readiness['physical_productivity'])
        self.assertIsNone(readiness['WGS_extent'])
        self.assertIn('CO_conversion_pct', readiness['missing_fields'])
        self.assertIn('carbon_balance_pct', readiness['missing_fields'])

    def test_mello_hydrocarbon_selectivities_close(self):
        table = mello_selectivity_table()
        self.assertTrue((table['fechamento_HC_pct'].round(10) == 100.0).all())

    def test_mello_tiox_values_are_transcribed(self):
        row = mello_selectivity_table().set_index('Catalisador').loc['CoRu/TiOx@AO']
        self.assertEqual(row['C13plus_pct'], 40.5)
        self.assertEqual(row['CTY_mol_CO_gCo_h'], 0.23)
        self.assertEqual(row['CO2_pct'], 0.5)

    def test_theses_improve_anchor_but_not_calibration(self):
        gate = thesis_evidence_readiness()
        self.assertTrue(gate['experimental_anchor_ready'])
        self.assertFalse(gate['kinetic_calibration_ready'])
        self.assertIsNone(BEZERRA_2010_REFERENCE['cobalt_k'])
        self.assertNotEqual(mello_selectivity_table()['CO2_pct'].max(), 0.0)

    def test_candidate_comparison_preserves_non_equivalence(self):
        candidates = pd.DataFrame([
            {'candidate_id':'a', 'formula':'Co1.00', 'family':'Co', 'support':'Al2O3', 'promoter':'Ru', 'metal_loading_wt_pct':20, 'promoter_loading_wt_pct':1, 'temperature_C':220, 'pressure_bar':20, 'H2_CO':2},
            {'candidate_id':'b', 'formula':'Co1.00', 'family':'Co', 'support':'TiO2', 'promoter':'Ru', 'metal_loading_wt_pct':20, 'promoter_loading_wt_pct':1, 'temperature_C':225, 'pressure_bar':20, 'H2_CO':2},
            {'candidate_id':'c', 'formula':'Fe1.00', 'family':'Fe', 'support':'C', 'promoter':'K', 'metal_loading_wt_pct':15, 'promoter_loading_wt_pct':2, 'temperature_C':220, 'pressure_bar':20, 'H2_CO':2},
        ])
        result = compare_candidates_with_mello(candidates).set_index('candidate_id')
        self.assertEqual(result.loc['a', 'reference_catalyst'], 'CoRu/AO')
        self.assertEqual(result.loc['b', 'support_match'], 'analogo_nao_equivalente')
        self.assertEqual(result.loc['c', 'applicability'], 'fora_do_domínio_experimental')
        self.assertIn('não são previsão', result.loc['a', 'interpretation'])


if __name__ == '__main__':
    unittest.main()
