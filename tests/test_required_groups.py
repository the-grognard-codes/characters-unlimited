import tempfile
import unittest
from copy import deepcopy

from characters_unlimited.application import CharacterApplication
from characters_unlimited.rules import RuleArchive


class RequiredGroupWorkflowTests(unittest.TestCase):
    def test_group_choices_survive_advancement_portable_copy_and_undo(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides:4)
            hero = app.create()
            hero = app.select_required_skills(hero['id'], revision=0, choices={
                'native_language':'English','other_languages':['Elven','Goblin'],
                'pilot':'motorcycle','repair':'general-repair'})
            hero = app.generate_resources(hero['id'], revision=hero['revision'])
            before = hero
            hero = app.advance(hero['id'], revision=hero['revision'], method='level', value=2)
            view = app.skill_view(hero['id'])
            self.assertEqual(next(item for item in view['grants'] if item['id']=='motorcycle')['percentage'],76)
            copy = app.import_character(app.export_character(hero['id']))
            self.assertEqual(copy['learning_levels'],hero['learning_levels'])
            hero = app.undo_advancement(hero['id'], revision=hero['revision'])['character']
            self.assertEqual(hero['required_skill_choices'],before['required_skill_choices'])
            self.assertEqual(next(item for item in app.skill_view(hero['id'])['grants'] if item['id']=='motorcycle')['percentage'],72)

    def group_application(self, directory):
        archive = RuleArchive.load()
        pack = archive.resolve('rifts-domestic-skills','2.7.0')
        legacy = deepcopy(pack['required'])
        pack['version'] = 'groups-fixture'
        pack['required'] = {'format':2, 'grants':legacy['grants'], 'groups':[
            {'id':'native_language','name':'Native language','kind':'text','count':1},
            {'id':'other_languages','name':'Other languages','kind':'text-list','count':2,
             'skill':legacy['other_languages']['skill'],'different_from':['native_language']},
            {'id':'vehicles','name':'Vehicle skills','kind':'select','count':2,
             'options':legacy['pilot']['options']}]}
        pack['required']['grants'][0]['specialty_from'] = 'native_language'
        return CharacterApplication(directory, die=lambda sides:4,
            rule_archive=RuleArchive([*archive.definitions(),pack],
                {**archive.active_versions(), pack['id']:pack['version']}))

    def test_multiple_choice_groups_retain_excess_without_duplicate_bonuses(self):
        with tempfile.TemporaryDirectory() as directory:
            app = self.group_application(directory)
            hero = app.create()
            hero = app.select_required_skills(hero['id'], revision=0, choices={
                'native_language':'English', 'other_languages':[' english ', 'Elven', 'ELVEN', 'Goblin', 'Dwarven'],
                'vehicles':['automobile','motorcycle','automobile']})
            view = app.skill_view(hero['id'])
            self.assertEqual(view['required_remaining'], {'native_language':0,'other_languages':-1,'vehicles':0})
            self.assertEqual(len([item for item in view['grants'] if item['id']=='automobile']),1)
            self.assertEqual(next(item for item in view['grants'] if item['id']=='automobile')['percentage'],70)
            self.assertEqual(next(item for item in view['grants'] if item['id']=='native-language')['specialty'],'English')
            self.assertTrue(any('duplicate' in warning.lower() for warning in view['warnings']))
            self.assertEqual(app.import_character(app.export_character(hero['id']))['required_skill_choices'],hero['required_skill_choices'])
            saved = app.get(hero['id'])
            with self.assertRaises(ValueError):
                app.select_required_skills(hero['id'], revision=saved['revision'], choices={'vehicles':['unknown']})
            self.assertEqual(app.get(hero['id']),saved)

    def test_legacy_pinned_choices_expose_the_same_group_interface(self):
        with tempfile.TemporaryDirectory() as directory:
            archive = RuleArchive.load()
            app = CharacterApplication(directory, die=lambda sides:4,
                rule_archive=RuleArchive(archive.definitions(),{**archive.active_versions(),'rifts-domestic-skills':'2.7.0'}))
            hero = app.create()
            hero = app.select_required_skills(hero['id'], revision=0, choices={
                'native_language':'English','other_languages':['Elven','Goblin'],
                'pilot':'motorcycle','repair':'general-repair'})
            view = app.skill_view(hero['id'])
            self.assertEqual([group['id'] for group in view['required_catalog']['groups']],
                ['native_language','other_languages','pilot','repair'])
            self.assertTrue(all(value==0 for value in view['required_remaining'].values()))
            self.assertEqual(next(item for item in view['grants'] if item['id']=='motorcycle')['percentage'],72)
            current = CharacterApplication(directory, die=lambda sides:self.fail('Required-rule update rerolled dice'))
            preview = current.preview_rule_upgrade(hero['id'])
            self.assertTrue(all(item['before']==item['after'] for item in preview['skills']))
            upgraded = current.apply_rule_upgrade(hero['id'], revision=hero['revision'], token=preview['token'])['character']
            self.assertEqual(upgraded['required_skill_choices'], hero['required_skill_choices'])
            self.assertEqual(upgraded['attributes'], hero['attributes'])
            self.assertEqual(current.skill_view(hero['id'])['required_remaining'],view['required_remaining'])
