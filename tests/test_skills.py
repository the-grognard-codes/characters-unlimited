import tempfile
import unittest

from characters_unlimited.application import CharacterApplication, SaveConflict


class DomesticSkillWorkflowTests(unittest.TestCase):
    def test_blank_instruments_are_retained_without_a_repeat_bonus(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides: 4)
            character = app.create()
            app.select_skills(character['id'], revision=0, selections=[{'skill_id': 'instrument', 'pool': 'secondary'}] * 2)
            view = app.skill_view(character['id'])
            self.assertEqual([s['percentage'] for s in view['selected']], [35, 35])
            self.assertTrue(view['warnings'])

    def test_instruments_are_distinct_specialties_and_repeats_use_best_bonus(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides: 4)
            character = app.create()
            app.select_skills(character['id'], revision=0, selections=[
                {'skill_id': 'instrument', 'pool': 'domestic', 'specialty': 'Guitar'},
                {'skill_id': 'instrument', 'pool': 'secondary', 'specialty': 'Violin'},
                {'skill_id': 'instrument', 'pool': 'secondary', 'specialty': ' guitar '},
                {'skill_id': 'cook', 'pool': 'secondary', 'specialty': 'Violin'},
            ])
            view = app.skill_view(character['id'])
            self.assertEqual([s['percentage'] for s in view['selected']], [60, 35, 60, 60])
            self.assertEqual(view['grants'][0]['percentage'], 60)
            self.assertEqual(view['selected'][3]['specialty'], '')

    def test_stale_selection_save_preserves_newer_choices(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides: 4)
            character = app.create()
            app.select_skills(character['id'], revision=0, selections=[{'skill_id': 'dance', 'pool': 'domestic'}])
            with self.assertRaises(SaveConflict):
                app.select_skills(character['id'], revision=0, selections=[])
            self.assertEqual(app.skill_view(character['id'])['selected'][0]['id'], 'dance')

    def test_domestic_choices_keep_pool_bonuses_and_persist(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides: 4)
            character = app.create()
            selected = app.select_skills(character['id'], revision=0, selections=[
                {'skill_id': 'dance', 'pool': 'domestic'},
                {'skill_id': 'fishing', 'pool': 'domestic'},
                {'skill_id': 'gardening', 'pool': 'related'},
                {'skill_id': 'sewing', 'pool': 'secondary'},
            ])
            skills = app.skill_view(selected['id'])
            self.assertEqual(skills['grants'][0]['percentage'], 50)
            self.assertEqual([s['percentage'] for s in skills['selected']], [45, 55, 46, 40])
            self.assertEqual(skills['remaining'], {'domestic': 0, 'related': 4, 'secondary': 7})
            self.assertEqual(CharacterApplication(directory).get(character['id'])['skill_selections'], selected['skill_selections'])

    def test_honor_system_retains_excess_and_duplicate_choices_with_guidance(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides: 4)
            character = app.create()
            app.select_skills(character['id'], revision=0, selections=[{'skill_id': 'dance', 'pool': 'domestic'}] * 3)
            view = app.skill_view(character['id'])
            self.assertEqual(len(view['selected']), 3)
            self.assertTrue(view['warnings'])
            self.assertEqual(view['selected'][0]['percentage'], 55)
            self.assertTrue(all(s['quality'] == 'professional' for s in view['selected']))

    def test_bad_skill_selection_cannot_replace_saved_choices(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides: 4)
            character = app.create()
            with self.assertRaises(ValueError):
                app.select_skills(character['id'], revision=0, selections=[{'skill_id': 'unknown', 'pool': 'domestic'}])
            self.assertEqual(app.get(character['id'])['revision'], 0)
