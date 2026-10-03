import tempfile
import unittest

from characters_unlimited.application import CharacterApplication


class NoncombatCategoryWorkflowTests(unittest.TestCase):
    def test_related_category_bonuses_and_barter_synergies_apply_once(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides:4)
            character = app.create()
            character = app.set_attribute(character['id'], revision=0, attribute='IQ', mode='fixed', value=16)
            ids = ['math-basic','math-advanced','literacy-native','basic-electronics','basic-mechanics','automotive-mechanics','first-aid']
            app.select_skills(character['id'], revision=1, selections=[{'skill_id':id,'pool':'related'} for id in ids])
            view = app.skill_view(character['id'])
            self.assertEqual({skill['id']:skill['percentage'] for skill in view['selected']}, {
                'math-basic':52,'math-advanced':52,'literacy-native':42,'basic-electronics':37,
                'basic-mechanics':37,'automotive-mechanics':32,'first-aid':52})
            barter = next(skill for skill in view['grants'] if skill['id']=='barter')
            self.assertEqual(barter['percentage'], 62)
            self.assertEqual(barter['contributions']['mathematics'],2)
            self.assertEqual(barter['contributions']['literacy'],2)
            self.assertEqual(view['remaining']['related'], -2)
            self.assertTrue(all(skill['quality']=='trained' for skill in view['selected']))

    def test_honor_system_retains_ineligible_pool_and_missing_prerequisite_without_invented_bonuses(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides:4)
            character = app.create()
            saved = app.select_skills(character['id'], revision=0, selections=[
                {'skill_id':'computer-repair','pool':'related'},
                {'skill_id':'math-advanced','pool':'domestic'},
                {'skill_id':'math-advanced','pool':'related'},
                {'skill_id':'math-advanced','pool':'related'}])
            view = app.skill_view(saved['id'])
            self.assertEqual([skill['percentage'] for skill in view['selected']], [30,45,50,50])
            self.assertTrue(any('Computer Repair' in warning and 'related' in warning for warning in view['warnings']))
            self.assertTrue(any('prerequisite' in warning and 'Mathematics: Basic' in warning for warning in view['warnings']))
            self.assertTrue(any('duplicate' in warning for warning in view['warnings']))
            self.assertEqual(len(saved['skill_selections']),4)

    def test_secondary_skills_and_language_specialties_survive_portable_reopening(self):
        with tempfile.TemporaryDirectory() as directory, tempfile.TemporaryDirectory() as other:
            app = CharacterApplication(directory, die=lambda sides:4)
            character = app.create()
            saved = app.select_skills(character['id'], revision=0, selections=[
                {'skill_id':'literacy-other','pool':'secondary','specialty':' Dragonese '},
                {'skill_id':'computer-repair','pool':'secondary'},
                {'skill_id':'first-aid','pool':'secondary'}])
            reopened = CharacterApplication(other)
            imported = reopened.import_character(app.export_character(saved['id']))
            self.assertEqual(imported['skill_selections'][0]['specialty'],'Dragonese')
            view = reopened.skill_view(imported['id'])
            self.assertEqual([skill['percentage'] for skill in view['selected']],[30,30,45])
            self.assertEqual(view['remaining']['secondary'],5)
            self.assertFalse(view['warnings'])

    def test_blank_other_literacy_does_not_grant_barter_synergy(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides:4)
            character = app.create()
            app.select_skills(character['id'], revision=0, selections=[
                {'skill_id':'literacy-other','pool':'secondary','specialty':' '}])
            view = app.skill_view(character['id'])
            barter = next(skill for skill in view['grants'] if skill['id']=='barter')
            self.assertEqual(barter['percentage'],56)
            self.assertNotIn('literacy',barter['contributions'])
            self.assertTrue(any('specialty' in warning for warning in view['warnings']))
