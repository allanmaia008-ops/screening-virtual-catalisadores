import unittest

from reaction_options import DEFAULT_PROMOTERS, promoter_options


class ReactionOptionsTests(unittest.TestCase):
    def test_other_reactions_keep_existing_options(self):
        self.assertEqual(promoter_options("metanacao"), list(DEFAULT_PROMOTERS))
        self.assertIn("Outro", promoter_options("rwgs"))


if __name__ == "__main__":
    unittest.main()
