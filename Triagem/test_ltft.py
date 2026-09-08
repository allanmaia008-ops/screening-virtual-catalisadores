import tempfile
import unittest
import pandas as pd
from ltft import generate_candidates, evaluate, run


class LTFTTests(unittest.TestCase):
    def test_profiles_and_product_balance(self):
        from asf import distribution
        for metals in (['Co'], ['Fe'], ['Co','Fe']):
            candidate = generate_candidates(metals)[0]
            result = evaluate(candidate)
            self.assertIsNone(result['WGS_extent'])
            self.assertIn('WGS', result['wgs_status'])
            self.assertIn('activation', result)
        for alpha in (0, .5, .85, .98, .999999):
            result = distribution(alpha)
            groups = result['exclusive_groups']
            self.assertEqual(list(groups), ['CH4','C2-C4','C5-C11','C12-C20','C21+'])
            self.assertAlmostEqual(sum(groups.values()), 1)
            self.assertAlmostEqual(sum(groups[k] for k in ('C5-C11','C12-C20','C21+')), result['C5plus_subtotal'])
    def test_generation_identity_and_mass(self):
        for metals, promoter in ((['Co'], ''), (['Fe'], 'K'), (['Co','Fe'], 'Mn')):
            rows = generate_candidates(metals, promoter)
            self.assertEqual(len(rows), len({r['candidate_id'] for r in rows}))
            self.assertEqual(rows, generate_candidates(metals, promoter))
            for row in rows:
                self.assertAlmostEqual(sum(row['fractions'].values()), 1)
                self.assertEqual(set(row['fractions']), set(metals))
                self.assertEqual(row['metal_loading_wt_pct']+row['promoter_loading_wt_pct']+row['support_wt_pct'], 100)

    def test_prior_trends_and_invalid_conditions(self):
        candidate = generate_candidates(['Co'])[0]
        self.assertGreater(evaluate(candidate, 200)['alpha'], evaluate(candidate,250)['alpha'])
        self.assertGreater(evaluate(candidate, ratio=1.5)['alpha'], evaluate(candidate,ratio=2.2)['alpha'])
        self.assertEqual(evaluate(candidate, alpha_override=.9)['alpha'], .9)
        self.assertIsNone(evaluate(candidate)['CO_conversion_pct'])
        with self.assertRaises(ValueError): evaluate(candidate, temperature=500)
        with self.assertRaises(ValueError): generate_candidates(['Ni'])

    def test_families_are_distinct(self):
        self.assertIn('Co0', evaluate(generate_candidates(['Co'])[0])['phase_hypothesis'])
        self.assertIn('Carbetos', evaluate(generate_candidates(['Fe'])[0])['phase_hypothesis'])

    def test_complete_execution_real_descriptors_and_exports(self):
        with tempfile.TemporaryDirectory() as folder:
            result = run(['Co','Fe'], 'K', folder)
            counts = result['metadata']['counts']
            self.assertEqual([counts[k] for k in ('gerados','selecionados_100','refinados_10','prioritarios_2')], [1000,100,10,2])
            self.assertGreater(len(result['tables']['descritores_magpie'].columns), 100)
            top = result['tables']['refinados_10']
            self.assertTrue(top['score_LTFT'].between(0,1).all())
            self.assertTrue(top['alpha'].between(0,1).all())
            from pathlib import Path
            workbook = next(Path(folder).glob('*.xlsx'))
            self.assertEqual(len(pd.read_excel(workbook, sheet_name='refinados_10')), 10)
            groups = pd.read_excel(workbook, sheet_name='grupos_produtos')
            self.assertEqual(len(groups), 50)
            self.assertTrue((groups.groupby('candidate_id').carbon_pct.sum().round(8) == 100).all())
            self.assertIn('sem conversão ou produtividade calibradas', next(Path(folder).glob('*.html')).read_text(encoding='utf-8'))
            self.assertTrue(next(Path(folder).glob('*_resumo.json')).is_file())


if __name__ == '__main__': unittest.main()
