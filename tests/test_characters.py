import tempfile
import unittest

from characters_unlimited.application import CharacterApplication, SaveConflict


class CharacterWorkflowTests(unittest.TestCase):
    def test_house_rules_apply_before_drop_lowest_and_not_to_exceptional_dice(self):
        with tempfile.TemporaryDirectory() as directory:
            sequence = iter([6, 6, 1, 6, 5, 1])
            app = CharacterApplication(directory, die=lambda sides: next(sequence, 4))
            character = app.create(generation={"reroll_ones": True, "extra_die": True})
            iq = character["attributes"]["IQ"]
            self.assertEqual(iq["value"], 19)
            self.assertEqual(iq["kept"], [6, 6, 6])
            self.assertEqual(iq["discarded"], [5])
            self.assertEqual(iq["bonus_rolls"], [1])
            self.assertEqual(iq["rerolls"], [{"index": 2, "rolls": [1, 6]}])

    def test_rerolls_preserve_history_and_manual_fixed_or_additive_values(self):
        with tempfile.TemporaryDirectory() as directory:
            result = [4]
            app = CharacterApplication(directory, die=lambda sides: result[0])
            character = app.create()
            fixed = app.set_attribute(character["id"], revision=0, attribute="IQ", mode="fixed", value=20)
            result[0] = 3
            rerolled = app.reroll(character["id"], revision=fixed["revision"], attribute="IQ")
            self.assertEqual(rerolled["attributes"]["IQ"]["base"], 9)
            self.assertEqual(rerolled["attributes"]["IQ"]["value"], 20)
            self.assertEqual(rerolled["attributes"]["ME"]["value"], 12)
            self.assertEqual(rerolled["roll_history"][0]["attributes"]["IQ"]["base"], 12)
            adjusted = app.set_attribute(character["id"], revision=rerolled["revision"], attribute="IQ", mode="adjustment", value=2)
            result[0] = 5
            latest = app.reroll(character["id"], revision=adjusted["revision"], attribute="IQ")
            self.assertEqual(latest["attributes"]["IQ"]["value"], 17)
            self.assertEqual(len(app.get(character["id"])["roll_history"]), 3)

    def test_ones_repeat_until_non_one_and_all_attempts_are_retained(self):
        with tempfile.TemporaryDirectory() as directory:
            sequence = iter([1, 1, 2])
            app = CharacterApplication(directory, die=lambda sides: next(sequence, 4))
            character = app.create(generation={"reroll_ones": True})
            self.assertEqual(character["attributes"]["IQ"]["value"], 10)
            self.assertEqual(character["attributes"]["IQ"]["rerolls"], [{"index": 0, "rolls": [1, 1, 2]}])

    def test_stale_reroll_cannot_change_attributes_or_add_phantom_history(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides: 4)
            character = app.create()
            app.edit(character["id"], revision=0, notes="Newer saved notes")
            with self.assertRaises(SaveConflict):
                app.reroll(character["id"], revision=0, attribute="IQ")
            saved = app.get(character["id"])
            self.assertEqual(saved["notes"], "Newer saved notes")
            self.assertEqual(len(saved["roll_history"]), 1)

    def test_a_nonterminating_die_does_not_save_a_partial_character(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides: 1)
            with self.assertRaises(ValueError):
                app.create(generation={"reroll_ones": True})
            self.assertEqual(app.list(), [])

    def test_player_can_generate_and_reopen_a_rifts_character(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides: 4)
            character = app.create(name="Rowan", race="human", character_class="vagabond")
            self.assertEqual(character["attributes"]["IQ"]["value"], 12)
            self.assertEqual(character["attributes"]["SPD"]["value"], 12)
            reopened = CharacterApplication(directory).get(character["id"])
            self.assertEqual(reopened["name"], "Rowan")
            self.assertEqual(reopened["attributes"]["IQ"]["rolls"], [4, 4, 4])
            self.assertEqual(reopened["rules"]["version"], "1.6.0")
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
            app = CharacterApplication(directory, die=lambda sides: sides)
            character = app.create()
            self.assertEqual(character["attributes"]["IQ"]["value"], 30)
            self.assertEqual(character["attributes"]["IQ"]["bonus_rolls"], [6, 6])


if __name__ == "__main__":
    unittest.main()
