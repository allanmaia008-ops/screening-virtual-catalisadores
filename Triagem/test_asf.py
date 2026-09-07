import math
import unittest
from asf import distribution, band_fraction, tail_fraction, aviation_screen


class ASFTests(unittest.TestCase):
    def test_conservation_all_bases_and_tails(self):
        for a in (0, .1, .8, .95, .999999):
            for basis in ("carbon", "molar", "paraffin_mass"):
                result = distribution(a, 30, basis)
                self.assertAlmostEqual(sum(result['exclusive_groups'].values()), 1)
                self.assertAlmostEqual(sum(r['fraction'] for r in result['rows'])+result['tail_fraction'], 1)
                self.assertAlmostEqual(result['C5plus_subtotal'], result['exclusive_groups']['C5-C11']+result['exclusive_groups']['C12+'])

    def test_analytical_values(self):
        self.assertAlmostEqual(band_fraction(.8, 1, 1), .04)
        self.assertAlmostEqual(tail_fraction(.8, 5), .73728)
        self.assertAlmostEqual(band_fraction(.8, 1, 1, 'molar'), .2)
        self.assertEqual(tail_fraction(0, 2), 0)

    def test_mass_is_exact_for_paraffins(self):
        a = .8
        values = [(1-a)*a**(n-1)*(12.011*n+1.008*(2*n+2)) for n in range(1, 500)]
        expected = sum(values[4:11])/sum(values)
        self.assertAlmostEqual(band_fraction(a, 5, 11, 'paraffin_mass'), expected)

    def test_invalid_input(self):
        for a in (-.1, 1, 1.1, math.nan, math.inf, True, '0.8'):
            with self.assertRaises(ValueError): distribution(a)
        for n in (0, -1, 1.5, True):
            with self.assertRaises(ValueError): tail_fraction(.8, n)
        with self.assertRaises(ValueError): band_fraction(.8, 5, 4)
        with self.assertRaises(ValueError): distribution(.8, basis='unknown')

    def test_aviation_partition_is_not_saf_yield(self):
        result = aviation_screen(.9)
        self.assertAlmostEqual(sum(result[k] for k in ('lighter_fraction','direct_cut_fraction','heavy_feed_fraction')), 1)
        self.assertIsNone(result['upgraded_jet_yield'])


if __name__ == '__main__': unittest.main()
