import unittest

from ltft_experimental import PI012_REFERENCE, kinetic_readiness, observed_totals


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


if __name__ == '__main__':
    unittest.main()
