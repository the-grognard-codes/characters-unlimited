import tempfile
import unittest

from characters_unlimited.application import CharacterApplication, SaveConflict


class CharacterWorkflowTests(unittest.TestCase):
    def test_player_can_generate_and_reopen_a_rifts_character(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides: 4)
            character = app.create(name="Rowan", race="human", character_class="vagabond")
            self.assertEqual(character["attributes"]["IQ"]["value"], 12)
            self.assertEqual(character["attributes"]["SPD"]["value"], 12)
            reopened = CharacterApplication(directory).get(character["id"])
            self.assertEqual(reopened["name"], "Rowan")
            self.assertEqual(reopened["attributes"]["IQ"]["rolls"], [4, 4, 4])
            self.assertEqual(reopened["rules"]["version"], "1.0.0")
            self.assertIn("Skills are not yet complete", reopened["completion"])

    def test_stale_save_preserves_the_newer_character(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides: 4)
            original = app.create(name="Rowan")
            app.edit(original["id"], name="Rowan the Wanderer", revision=original["revision"])
            with self.assertRaises(SaveConflict):
                app.edit(original["id"], notes="Unsaved second-tab notes", revision=original["revision"])
            self.assertEqual(app.get(original["id"])["name"], "Rowan the Wanderer")

    def test_save_without_a_revision_cannot_overwrite_a_character(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides: 4)
            original = app.create(name="Rowan")
            with self.assertRaises(ValueError):
                app.edit(original["id"], name="Stale name", revision=None)
            self.assertEqual(app.get(original["id"])["name"], "Rowan")

    def test_rifts_second_exceptional_die_is_terminal(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides: 6)
            character = app.create()
            self.assertEqual(character["attributes"]["IQ"]["value"], 30)
            self.assertEqual(character["attributes"]["IQ"]["bonus_rolls"], [6, 6])


if __name__ == "__main__":
    unittest.main()
