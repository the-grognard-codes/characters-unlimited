"""Public workflow coverage for source-bound named skill pool milestones."""

from copy import deepcopy
import tempfile
import unittest

from characters_unlimited.advancement import learning_key
from characters_unlimited.application import CharacterApplication
from characters_unlimited.rules import RuleArchive
from tests.test_owned_class_profiles import owned_pack, archive_with


SOURCE = {'book': 'Synthetic source fixture', 'section': 'Named robot training awards'}
TRAINING = 'synthetic-elite-robot'


def fixture():
    pack = owned_pack()
    pack['skills'].append({'id': TRAINING, 'name': 'Synthetic Elite Robot Combat',
                           'kind': 'training', 'category': 'military',
                           'requires_specialty': True, 'description': 'Name the trained robot type.',
                           'source': SOURCE})
    profile = pack['class_profiles']['vagabond']
    profile['pools']['mos'] = {'count': 2, 'bonus': 0,
        'level_awards': [{'level': level, 'count': 1, 'source': SOURCE}
                         for level in (3, 6, 9, 12)]}
    profile['selection_rules']['mos'] = {'military': {'allow': [TRAINING], 'bonus': 0}}
    return pack


def choices(*names):
    return [{'skill_id': TRAINING, 'pool': 'mos', 'specialty': name} for name in names]


class NamedSkillPoolAwardTests(unittest.TestCase):
    def no_roll(self, sides):
        self.fail('Selection and portable replay must use retained dice')

    def test_ages_reselection_and_portable_reopen(self):
        archive = archive_with(fixture())
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides: 4, rule_archive=archive)
            hero = app.create(level=12)
            app.die = self.no_roll
            names = ('Samson', 'Explorer', 'Titan', 'Ogre', 'Behemoth', 'Glitter Boy')
            hero = app.select_skills(hero['id'], revision=hero['revision'], selections=choices(*names))
            self.assertEqual([hero['learning_levels'][learning_key('skill', TRAINING, name)]
                              for name in names], [1, 1, 3, 6, 9, 12])
            view = app.skill_view(hero['id'])
            self.assertEqual(view['remaining']['mos'], 0)
            self.assertEqual([row['learned_level'] for row in view['selected']], [1, 1, 3, 6, 9, 12])
            self.assertTrue(all('percentage' not in row for row in view['selected']))
            self.assertEqual(view['pool_catalog']['mos']['level_awards'][0]['source'], SOURCE)
            self.assertTrue(any('Mos choice award at level 3' in source and SOURCE['section'] in source
                                for source in view['sources']))

            hero = app.select_skills(hero['id'], revision=hero['revision'], selections=choices(*names[:2], *names[3:]))
            hero = app.select_skills(hero['id'], revision=hero['revision'],
                selections=choices(*names[:2], *names[3:], 'Replacement'))
            self.assertEqual(hero['learning_levels'][learning_key('skill', TRAINING, 'Replacement')], 3)
            hero = app.select_skills(hero['id'], revision=hero['revision'], selections=choices(*names))
            self.assertEqual(hero['learning_levels'][learning_key('skill', TRAINING, 'Titan')], 3)
            hero = app.select_skills(hero['id'], revision=hero['revision'],
                selections=choices(*names, 'Over budget'))
            self.assertEqual(hero['learning_levels'][learning_key('skill', TRAINING, 'Over budget')], 12)
            self.assertEqual(app.skill_view(hero['id'])['remaining']['mos'], -1)
            self.assertTrue(any('over the current level allowance' in note
                                for note in app.skill_view(hero['id'])['warnings']))
            imported = app.import_character(app.export_character(hero['id']))
            self.assertEqual(imported['learning_levels'], hero['learning_levels'])
            reopened = CharacterApplication(directory, die=self.no_roll, rule_archive=archive)
            self.assertEqual(reopened.get(hero['id']), hero)

    def test_advancement_and_undo_preserve_first_learning(self):
        archive = archive_with(fixture())
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides: 4, rule_archive=archive)
            hero = app.create(level=2)
            app.die = self.no_roll
            hero = app.select_skills(hero['id'], revision=hero['revision'], selections=choices('A', 'B'))
            self.assertEqual([hero['learning_levels'][learning_key('skill', TRAINING, name)]
                              for name in ('A', 'B')], [1, 1])
            app.die = lambda sides: 4
            hero = app.advance(hero['id'], revision=hero['revision'], method='level', value=3)
            app.die = self.no_roll
            hero = app.select_skills(hero['id'], revision=hero['revision'], selections=choices('A', 'B', 'C'))
            self.assertEqual(hero['learning_levels'][learning_key('skill', TRAINING, 'C')], 3)
            hero = app.undo_advancement(hero['id'], revision=hero['revision'])['character']
            self.assertEqual(hero['level'], 2)
            self.assertEqual(hero['learning_levels'][learning_key('skill', TRAINING, 'A')], 1)
            self.assertNotIn(learning_key('skill', TRAINING, 'C'), hero['learning_levels'])

    def test_inactive_bad_awards_reject_before_dice_or_writes(self):
        mutations = [
            lambda row: row.update(level=True),
            lambda row: row.update(level=1),
            lambda row: row.update(level=16),
            lambda row: row.update(count=True),
            lambda row: row.update(count=0),
            lambda row: row.update(source={}),
            lambda row: row.update(level=6),
        ]
        for mutate in mutations:
            with self.subTest(mutate=mutate), tempfile.TemporaryDirectory() as directory:
                pack = fixture()
                pack['class_profiles']['city-rat']['pools']['mos'] = deepcopy(
                    pack['class_profiles']['vagabond']['pools']['mos'])
                pack['class_profiles']['city-rat']['selection_rules']['mos'] = deepcopy(
                    pack['class_profiles']['vagabond']['selection_rules']['mos'])
                mutate(pack['class_profiles']['city-rat']['pools']['mos']['level_awards'][0])
                app = CharacterApplication(directory, die=self.no_roll, rule_archive=archive_with(pack))
                with self.assertRaisesRegex(ValueError, 'city-rat.*skills.*Named pool awards'):
                    app.create(character_class='vagabond')
                self.assertEqual(app.list(), [])

    def test_legacy_related_awards_stay_separate_and_conflicts_reject(self):
        pack = fixture()
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides: 4, rule_archive=archive_with(pack))
            hero = app.create(level=3)
            view = app.skill_view(hero['id'])
            self.assertEqual(view['remaining']['mos'], 3)
            self.assertEqual(view['remaining']['related'],
                pack['class_profiles']['vagabond']['pools']['related']['count'] + 1)
        pack = fixture()
        pack['class_profiles']['city-rat']['pools']['related']['level_awards'] = [
            {'level': 3, 'count': 1, 'source': SOURCE}]
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=self.no_roll, rule_archive=archive_with(pack))
            with self.assertRaisesRegex(ValueError, 'city-rat.*skills.*progression schedule'):
                app.create()
            self.assertEqual(app.list(), [])

    def test_explicit_early_age_is_retained_with_source_guidance(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides: 4, rule_archive=archive_with(fixture()))
            hero = app.create(level=3)
            app.die = self.no_roll
            hero = app.select_skills(hero['id'], revision=hero['revision'],
                selections=choices('A', 'B', 'C'), learned_level=1)
            self.assertEqual(hero['learning_levels'][learning_key('skill', TRAINING, 'C')], 1)
            self.assertTrue(any('recorded before their source award' in note
                                for note in app.skill_view(hero['id'])['warnings']))
