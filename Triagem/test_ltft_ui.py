import tempfile
import unittest

from streamlit.testing.v1 import AppTest


class InterfaceTest(unittest.TestCase):
    def test_controls_and_results(self):
        with tempfile.TemporaryDirectory() as output:
            script = (
                'from ltft_ui import render\n'
                'import streamlit as st\n'
                'execute = st.button("Executar")\n'
                f'render(["Co"], None, {output!r}, execute, True)\n'
            )
            app = AppTest.from_string(script).run(timeout=120)
            self.assertFalse(app.exception)
            self.assertEqual(len(app.slider), 3)
            app.button[0].click().run(timeout=120)
            self.assertFalse(app.exception)
            self.assertFalse(app.error)
            # Four funnel metrics plus four experimental-comparison indicators.
            self.assertEqual(len(app.metric), 8)
            self.assertTrue(any('ltft-card' in item.value and 'Fração C₅₊' in item.value for item in app.markdown))
            self.assertTrue(any('ft-podium' in item.value and 'ft-medal' in item.value for item in app.markdown))
            table = next(item.value for item in app.markdown if '<table class="ft-table">' in item.value)
            self.assertEqual(table.count('<tr>'), 11)
            next(b for b in app.button if b.label == 'Calcular quantidades').click().run(timeout=120)
            self.assertFalse(app.exception)
            self.assertFalse(app.error)
            self.assertTrue(any('Suporte seco:' in item.value for item in app.success))
            self.assertTrue(any('Modelo cinético ainda bloqueado' in item.value for item in app.warning))
            selector = next(s for s in app.selectbox if s.label == 'Candidato para análise de α e suporte')
            selector.select_index(1).run(timeout=120)
            self.assertFalse(app.exception)
            next(s for s in app.selectbox if s.label == 'Parâmetro').select('Promotor').run(timeout=120)
            self.assertFalse(app.exception)
            app.slider[0].set_value(230).run(timeout=120)
            self.assertFalse(app.exception)
            self.assertEqual(len(app.metric), 0)


if __name__ == '__main__':
    unittest.main()
