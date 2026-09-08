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
            self.assertEqual(len(app.metric), 4)
            self.assertTrue(any('ltft-card' in item.value and 'Fração C₅₊' in item.value for item in app.markdown))
            app.slider[0].set_value(230).run(timeout=120)
            self.assertFalse(app.exception)
            self.assertEqual(len(app.metric), 0)


if __name__ == '__main__':
    unittest.main()
