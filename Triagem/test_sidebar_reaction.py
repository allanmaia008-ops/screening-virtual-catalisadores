import unittest
from pathlib import Path


class SidebarReactionTests(unittest.TestCase):
    def test_reaction_selector_is_not_hidden_in_popover(self):
        source = Path(__file__).with_name("app.py").read_text(encoding="utf-8")
        self.assertNotIn('with st.popover("Reação"', source)
        self.assertIn('reacao = st.selectbox(', source)
        self.assertIn('key="config_reacao"', source)


if __name__ == "__main__":
    unittest.main()
