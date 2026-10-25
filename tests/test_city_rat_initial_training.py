"""Source City Rat minimums use paid training without rewriting older pins."""

from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest

from characters_unlimited.application import CharacterApplication
from characters_unlimited.advancement import learning_key
from characters_unlimited.rules import RuleArchive


def candidate_archive():
    installed = RuleArchive.load()
    definitions = {(row['id'], row['version']): row for row in installed.definitions()}
    root = Path(__file__).resolve().parents[1] / 'characters_unlimited' / 'packs'
    for filename in ('rifts-core-1.19.0.json', 'rifts-domestic-skills-2.40.0.json'):
        pack = json.loads((root / filename).read_text(encoding='utf-8'))
        definitions[pack['id'], pack['version']] = pack
    return RuleArchive(list(definitions.values()), {**installed.active_versions(),
                       'rifts-core': '1.19.0', 'rifts-domestic-skills': '2.40.0'})


def choices(*identities, pool='related'):
    return [{'skill_id': identity, 'pool': pool, 'specialty': ''} for identity in identities]


class CityRatInitialTrainingTests(unittest.TestCase):
    def minimum(self, app, hero):
        return next(row for row in app.skill_view(hero['id'])['pool_requirements']
                    if row['id'] == 'initial-physical-rogue')

    def test_source_counts_percentages_and_resource_baseline_for_each_paid_style(self):
        for style, remaining in [('expert', 7), ('martial-arts', 6), ('assassin', 6)]:
            with self.subTest(style=style), tempfile.TemporaryDirectory() as directory:
                app = CharacterApplication(directory, die=lambda sides: 4, rule_archive=candidate_archive())
                hero = app.create(character_class='city-rat')
                self.assertEqual(self.minimum(app, hero)['remaining'], 3)
                hero = app.select_skills(hero['id'], revision=hero['revision'],
                                         selections=choices('climbing', 'prowl'))
                hero = app.select_combat(hero['id'], revision=hero['revision'],
                                         choices={'hand_to_hand': style})
                view = app.skill_view(hero['id'])
                self.assertEqual((self.minimum(app, hero)['credited'], self.minimum(app, hero)['remaining']), (3, 0))
                self.assertEqual(view['remaining'], {'related': remaining, 'secondary': 8})
                self.assertEqual({row['id']: row['percentage'] for row in view['selected']},
                                 {'climbing': 45, 'prowl': 40})
                self.assertEqual({key: hero['attributes'][key]['value'] for key in ('MA', 'PS', 'PE', 'SPD')},
                                 {'MA': 12, 'PS': 12, 'PE': 13, 'SPD': 33})
                hero = app.generate_resources(hero['id'], revision=hero['revision'])
                resources = app.resource_view(hero['id'])['resources']
                self.assertEqual((resources['HP']['value'], resources['SDC']['value']), (17, 32))
                self.assertNotIn('PPE', resources)

    def test_ineligible_and_secondary_selections_stay_visible_without_minimum_credit(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides: 4, rule_archive=candidate_archive())
            hero = app.create(character_class='city-rat')
            hero = app.select_combat(hero['id'], revision=hero['revision'], choices={'hand_to_hand': 'expert'})
            hero = app.select_skills(hero['id'], revision=hero['revision'], selections=[
                *choices('climbing', 'fencing'), *choices('prowl', pool='secondary')])
            row = self.minimum(app, hero)
            self.assertEqual((row['credited'], row['remaining']), (2, 1))
            self.assertEqual(len(hero['skill_selections']), 3)
            self.assertTrue(any('Fencing' in warning for warning in app.skill_view(hero['id'])['warnings']))

    def test_initial_choices_keep_learning_across_advancement_undo_and_reselection(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides: 4, rule_archive=candidate_archive())
            hero = app.create(character_class='city-rat')
            hero = app.select_skills(hero['id'], revision=hero['revision'], selections=choices('climbing', 'prowl'))
            hero = app.select_combat(hero['id'], revision=hero['revision'], choices={'hand_to_hand': 'expert'})
            hero = app.generate_resources(hero['id'], revision=hero['revision'])
            hero = app.advance(hero['id'], revision=hero['revision'], method='level', value=3)
            self.assertEqual(self.minimum(app, hero)['remaining'], 0)
            self.assertEqual(app.skill_view(hero['id'])['remaining'], {'related': 8, 'secondary': 9})
            hero = app.select_skills(hero['id'], revision=hero['revision'], selections=choices('climbing'))
            self.assertEqual(self.minimum(app, hero)['remaining'], 1)
            hero = app.select_skills(hero['id'], revision=hero['revision'], selections=choices('climbing', 'prowl'))
            self.assertEqual(hero['learning_levels'][learning_key('skill', 'prowl')], 1)
            self.assertEqual(self.minimum(app, hero)['remaining'], 0)
            hero = app.undo_advancement(hero['id'], revision=hero['revision'])['character']
            self.assertEqual(hero['level'], 2)
            self.assertEqual(self.minimum(app, hero)['remaining'], 0)

    def test_later_first_learning_does_not_fill_the_initial_minimum(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides: 4, rule_archive=candidate_archive())
            hero = app.create(character_class='city-rat')
            hero = app.select_skills(hero['id'], revision=hero['revision'], selections=choices('climbing'))
            hero = app.select_combat(hero['id'], revision=hero['revision'], choices={'hand_to_hand': 'expert'})
            hero = app.generate_resources(hero['id'], revision=hero['revision'])
            hero = app.advance(hero['id'], revision=hero['revision'], method='level', value=3)
            hero = app.select_skills(hero['id'], revision=hero['revision'],
                                     selections=choices('climbing', 'prowl'), learned_level=3)
            self.assertEqual(hero['learning_levels'][learning_key('skill', 'prowl')], 3)
            self.assertEqual((self.minimum(app, hero)['credited'], self.minimum(app, hero)['remaining']), (2, 1))

    def test_older_city_rat_human_and_dog_boy_pins_preserve_exact_public_outputs(self):
        installed = RuleArchive.load()
        old = RuleArchive(installed.definitions(), {**installed.active_versions(),
                          'rifts-core': '1.18.0', 'rifts-domestic-skills': '2.39.0'})
        archive = candidate_archive()
        methods = ('get', 'skill_view', 'resource_view', 'equipment_view', 'export_character')
        for race, identity in [('human', 'city-rat'), ('human', 'vagabond'),
                               ('dog-boy', 'dog-boy-coalition-disarm')]:
            with self.subTest(identity=identity), tempfile.TemporaryDirectory() as directory:
                app = CharacterApplication(directory, die=lambda sides: 4, rule_archive=old)
                hero = app.create(race=race, character_class=identity)
                hero = app.generate_resources(hero['id'], revision=hero['revision'])
                before = {method: deepcopy(getattr(app, method)(hero['id'])) for method in methods}
                def no_roll(sides):
                    self.fail('Historic pinned views cannot roll')
                reopened = CharacterApplication(directory, die=no_roll, rule_archive=archive)
                after = {method: getattr(reopened, method)(hero['id']) for method in methods}
                self.assertEqual(after, before)


if __name__ == '__main__':
    unittest.main()
