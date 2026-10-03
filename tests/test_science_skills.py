import tempfile
import unittest

from characters_unlimited.application import CharacterApplication


class ScienceSkillWorkflowTests(unittest.TestCase):
    def test_navigation_uses_advanced_math_once_and_respects_pool_restrictions(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides: 4)
            character = app.create()
            choices = [
                {'skill_id': 'astronomy-navigation', 'pool': 'secondary'},
                {'skill_id': 'math-basic', 'pool': 'related'},
                {'skill_id': 'math-advanced', 'pool': 'related'},
                {'skill_id': 'math-advanced', 'pool': 'secondary'},
                {'skill_id': 'literacy-native', 'pool': 'related'},
            ]
            saved = app.select_skills(character['id'], revision=0, selections=choices)
            view = app.skill_view(saved['id'])
            self.assertEqual(view['selected'][0]['percentage'], 40)
            self.assertEqual(view['selected'][0]['contributions']['advanced_mathematics'], 10)
            self.assertFalse(any('missing prerequisite' in warning for warning in view['warnings']))
            choices[0]['pool'] = 'related'
            app.select_skills(saved['id'], revision=saved['revision'], selections=choices)
            view = app.skill_view(saved['id'])
            self.assertEqual(view['selected'][0]['percentage'], 40)
            self.assertTrue(any('Astronomy & Navigation: not available' in warning for warning in view['warnings']))

    def test_archaeology_has_two_checks_and_history_bonuses_apply_once(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides: 4)
            character = app.create()
            choices = [
                {'skill_id': 'archaeology', 'pool': 'related'},
                {'skill_id': 'anthropology', 'pool': 'secondary'},
                {'skill_id': 'archaeology', 'pool': 'secondary'},
                {'skill_id': 'history-pre', 'pool': 'related', 'specialty': 'North America'},
                {'skill_id': 'history-post', 'pool': 'secondary', 'specialty': 'Coalition'},
            ]
            app.select_skills(character['id'], revision=0, selections=choices)
            view = app.skill_view(character['id'])
            archaeology = view['selected'][0]
            self.assertEqual(archaeology['percentage'], 30)
            self.assertEqual(archaeology['additional_checks'][0]['percentage'], 20)
            self.assertEqual(view['selected'][3]['percentage'], 52)
            self.assertEqual(view['selected'][3]['additional_checks'][0]['percentage'], 44)
            self.assertEqual(view['selected'][4]['percentage'], 45)
            self.assertEqual(view['selected'][4]['additional_checks'][0]['percentage'], 40)
            self.assertTrue(any('Anthropology: not available' in warning for warning in view['warnings']))

    def test_ai_adds_once_to_computer_skills_and_chemistry_requires_its_training(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides: 4)
            character = app.create()
            choices = [
                {'skill_id': 'artificial-intelligence', 'pool': 'related'},
                {'skill_id': 'artificial-intelligence', 'pool': 'secondary'},
                {'skill_id': 'computer-operation', 'pool': 'related'},
                {'skill_id': 'computer-programming', 'pool': 'related'},
                {'skill_id': 'chemistry-analytical', 'pool': 'secondary'},
            ]
            saved = app.select_skills(character['id'], revision=0, selections=choices)
            view = app.skill_view(saved['id'])
            self.assertEqual(view['selected'][2]['percentage'], 50)
            self.assertEqual(view['selected'][3]['percentage'], 40)
            self.assertEqual(view['selected'][4]['percentage'], 25)
            self.assertTrue(any('missing prerequisite Chemistry' in warning for warning in view['warnings']))
            choices.extend([
                {'skill_id': 'chemistry', 'pool': 'related'},
                {'skill_id': 'math-basic', 'pool': 'related'},
                {'skill_id': 'math-advanced', 'pool': 'related'},
                {'skill_id': 'literacy-native', 'pool': 'related'},
            ])
            app.select_skills(saved['id'], revision=saved['revision'], selections=choices)
            self.assertFalse(any('missing prerequisite' in warning for warning in app.skill_view(saved['id'])['warnings']))

    def test_remaining_science_bases_are_source_bound_and_round_trip(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides: 4)
            character = app.create()
            choices = [
                {'skill_id': identifier, 'pool': 'secondary'}
                for identifier in ('astrophysics', 'biology', 'botany', 'chemistry-pharmaceutical', 'xenology')
            ]
            app.select_skills(character['id'], revision=0, selections=choices)
            view = app.skill_view(character['id'])
            self.assertEqual([row['percentage'] for row in view['selected']], [30, 30, 25, 30, 30])
            self.assertTrue(any('Basic' in warning and 'prerequisite' in warning for warning in view['warnings']))
            self.assertTrue(any('Advanced' in warning and 'prerequisite' in warning for warning in view['warnings']))
            self.assertEqual(view['remaining']['secondary'], 3)
            reopened = app.import_character(app.export_character(character['id']))
            self.assertEqual(app.skill_view(reopened['id'])['selected'], view['selected'])

    def test_new_science_catalog_requires_explicit_rule_update(self):
        from characters_unlimited.rules import RuleArchive

        with tempfile.TemporaryDirectory() as directory:
            archive = RuleArchive.load()
            active = archive.active_versions()
            active['rifts-domestic-skills'] = '1.6.0'
            earlier = CharacterApplication(directory, die=lambda sides: 4,
                                           rule_archive=RuleArchive(archive.definitions(), active))
            character = earlier.create()
            saved = earlier.select_skills(character['id'], revision=0, selections=[
                {'skill_id': 'computer-operation', 'pool': 'related'},
            ])
            app = CharacterApplication(directory)
            self.assertNotIn('astronomy-navigation', {row['id'] for row in app.skill_view(saved['id'])['catalog']})
            preview = app.preview_rule_upgrade(saved['id'])
            self.assertEqual(app.get(saved['id'])['attributes'], saved['attributes'])
            updated = app.apply_rule_upgrade(saved['id'], revision=saved['revision'], token=preview['token'])['character']
            self.assertIn('astronomy-navigation', {row['id'] for row in app.skill_view(updated['id'])['catalog']})
            self.assertEqual(app.skill_view(updated['id'])['selected'][0]['percentage'], 45)
            self.assertEqual(updated['skill_selections'], saved['skill_selections'])
