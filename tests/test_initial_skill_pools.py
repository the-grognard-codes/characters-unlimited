"""Public compatibility checks for source defaults on initial specialty choices."""
from copy import deepcopy
import tempfile
import unittest

from characters_unlimited.application import CharacterApplication
from characters_unlimited.advancement import learning_key
from characters_unlimited.rules import RuleArchive


class InitialSkillPoolTests(unittest.TestCase):
    def archive(self, bad_default=None, *, malformed=False):
        archive = RuleArchive.load()
        definition = archive.resolve('rifts-domestic-skills', '2.32.0')
        definition['version'] = 'initial-pool-fixture'
        profile = definition['class_profiles']['vagabond']
        profile['pools']['mos'] = {'count': 1, 'bonus': 0, 'default_learned_level': 1}
        profile['selection_rules']['mos'] = {'communications': {'allow': 'any', 'bonus': 10}}
        if malformed:
            definition['class_profiles']['city-rat']['pools']['related']['default_learned_level'] = bad_default
        active = archive.active_versions()
        active['rifts-domestic-skills'] = definition['version']
        return RuleArchive([*archive.definitions(), definition], active)

    def no_roll(self, sides):
        self.fail('Retained initial choices, import and reopen must not draw dice')

    def test_required_specialties_credit_distinct_completed_skills(self):
        archive = self.archive()
        pack = archive.resolve('rifts-domestic-skills', 'initial-pool-fixture')
        pack['version'] = 'initial-specialty-fixture'
        mos = pack['class_profiles']['vagabond']['pools']['mos']
        mos['count'] = 2
        mos['requirements'] = [{'id':'languages','name':'Initial languages','count':2,
            'counting':'distinct-specialties','selector':{'any_of':[{'ids':['language-other']}]},
            'source':{'book':'Source fixture','section':'Two initial language choices'}}]
        archive = RuleArchive([*archive.definitions(),pack],
            {**archive.active_versions(),'rifts-domestic-skills':'initial-specialty-fixture'})
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory,die=lambda sides:3,rule_archive=archive)
            hero = app.create()
            app.die = self.no_roll
            choices = [{'skill_id':'language-other','pool':'mos','specialty':''}]
            hero = app.select_skills(hero['id'],revision=hero['revision'],selections=choices)
            self.assertEqual(app.skill_view(hero['id'])['pool_requirements'][0]['remaining'],2)
            choices = [{'skill_id':'language-other','pool':'mos','specialty':name}
                       for name in ('Spanish',' spanish ','French')]
            hero = app.select_skills(hero['id'],revision=hero['revision'],selections=choices)
            requirement = app.skill_view(hero['id'])['pool_requirements'][0]
            self.assertEqual((requirement['credited'],requirement['remaining']),(2,0))
            self.assertEqual(len(hero['skill_selections']),3)
            imported = app.import_character(app.export_character(hero['id']))
            self.assertEqual(app.skill_view(imported['id'])['pool_requirements'],
                             app.skill_view(hero['id'])['pool_requirements'])

    def test_initial_specialty_defaults_to_one_and_exact_reopen_reselection_preserves_it(self):
        with tempfile.TemporaryDirectory() as directory:
            archive = self.archive()
            app = CharacterApplication(directory, die=lambda sides: 3, rule_archive=archive)
            hero = app.create(level=3)
            app.die = self.no_roll
            choices = [{'skill_id': 'language-other', 'pool': 'mos', 'specialty': 'Spanish'},
                       {'skill_id': 'basic-electronics', 'pool': 'related'}]
            hero = app.select_skills(hero['id'], revision=hero['revision'], selections=choices)
            rows = {row['id']: row for row in app.skill_view(hero['id'])['selected']}
            self.assertEqual(rows['language-other']['percentage'], 66)  # 50 + 10 + two 3% gains
            self.assertEqual(rows['basic-electronics']['percentage'], 35)  # 30 base + 5 class; no late growth
            self.assertEqual(hero['learning_levels'][learning_key('skill', 'basic-electronics')], 3)
            self.assertEqual(hero['learning_levels'][learning_key('skill', 'language-other', 'Spanish')], 1)
            self.assertEqual(app.skill_view(hero['id'])['remaining']['mos'], 0)
            self.assertEqual(app.skill_view(hero['id'])['pool_catalog']['mos']['default_learned_level'], 1)
            before = deepcopy(hero)
            hero = app.select_skills(hero['id'], revision=hero['revision'], selections=[])
            hero = app.select_skills(hero['id'], revision=hero['revision'], selections=choices, learned_level=3)
            self.assertEqual(hero['learning_levels'], before['learning_levels'])
            self.assertEqual(app.import_character(app.export_character(hero['id']))['learning_levels'], hero['learning_levels'])
            reopened = CharacterApplication(directory, die=self.no_roll, rule_archive=archive)
            self.assertEqual(reopened.get(hero['id']), hero)

    def test_explicit_player_age_and_preexisting_age_are_retained(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides: 3, rule_archive=self.archive())
            hero = app.create(level=3)
            app.die = self.no_roll
            hero = app.select_skills(hero['id'], revision=hero['revision'], learned_level=3,
                selections=[{'skill_id': 'language-other', 'pool': 'related', 'specialty': 'French'}])
            hero = app.select_skills(hero['id'], revision=hero['revision'],
                selections=[*hero['skill_selections'], {'skill_id': 'language-other', 'pool': 'mos', 'specialty': 'French'}])
            self.assertEqual(hero['learning_levels'][learning_key('skill', 'language-other', 'French')], 3)
            self.assertEqual([row['percentage'] for row in app.skill_view(hero['id'])['selected']], [50, 60])
            hero = app.select_skills(hero['id'], revision=hero['revision'], learned_level=3,
                selections=[{'skill_id': 'language-other', 'pool': 'mos', 'specialty': 'Spanish'}])
            self.assertEqual(hero['learning_levels'][learning_key('skill', 'language-other', 'Spanish')], 3)
            self.assertEqual(app.skill_view(hero['id'])['selected'][0]['percentage'], 60)

    def test_invalid_inactive_pool_default_rejects_before_dice(self):
        for value in (True, 0, 2, '1', None):
            with self.subTest(value=value), tempfile.TemporaryDirectory() as directory:
                app = CharacterApplication(directory, die=self.no_roll,
                    rule_archive=self.archive(value, malformed=True))
                with self.assertRaisesRegex(ValueError, 'Initial skill choice pools'):
                    app.create()
                self.assertEqual(app.list(), [])

    def test_invalid_inactive_choice_counting_rejects_before_dice(self):
        archive = self.archive()
        pack = archive.resolve('rifts-domestic-skills','initial-pool-fixture')
        pack['version'] = 'invalid-choice-policy-fixture'
        pack['class_profiles']['city-rat']['pools']['related']['requirements'] = [{
            'id':'extra-language','name':'Extra language','count':1,'counting':'entries',
            'selector':{'any_of':[{'ids':['language-other']}]},
            'source':{'book':'Source fixture','section':'Inactive choice policy'}}]
        archive = RuleArchive([*archive.definitions(),pack],
            {**archive.active_versions(),'rifts-domestic-skills':pack['version']})
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory,die=self.no_roll,rule_archive=archive)
            with self.assertRaisesRegex(ValueError,'supported choice counting'):
                app.create()
            self.assertEqual(app.list(),[])
