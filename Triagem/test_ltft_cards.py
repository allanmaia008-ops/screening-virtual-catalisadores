import unittest
import pandas as pd
from ltft import generate_candidates, evaluate
from ltft_cards import recommendations_html, chemical


class CardsTests(unittest.TestCase):
    def test_cards_show_real_values_and_assets(self):
        rows = [evaluate(c) for c in generate_candidates(['Co','Fe'], 'K')[:2]]
        output = recommendations_html(pd.DataFrame(rows))
        self.assertEqual(output.count('<article class="ltft-card"'), 2)
        self.assertEqual(output.count('data:image/png;base64,'), 2)
        self.assertIn('Suporte da formulação', output)
        self.assertIn('não estrutura calculada', output)
        self.assertNotIn('Score de confiança:', output)

    def test_chemical_format_and_escape(self):
        self.assertEqual(chemical('Al2O3'), 'Al<sub>2</sub>O<sub>3</sub>')
        output = recommendations_html(pd.DataFrame([{'formula':'<script>alert(1)</script>'}]))
        self.assertNotIn('<script>', output)
        self.assertIn('Não calculado', output)


if __name__ == '__main__':
    unittest.main()
