"""Acquisition formula contracts through player-facing workflows."""

from copy import deepcopy
import tempfile
import unittest

from characters_unlimited.application import CharacterApplication
from characters_unlimited.rules import RuleArchive


class RecordedFormulaFrameworkTests(unittest.TestCase):
    def power_archive(self, change):
        installed = RuleArchive.load()
        target = installed.active('heroes-super-abilities')
        change(target['powers'][0]['attribute_floor'])
        definitions = [target if (row['id'], row['version']) == (target['id'], target['version'])
                       else row for row in installed.definitions()]
        return RuleArchive(definitions, installed.active_versions())

    def test_unsupported_power_formula_data_cannot_change_a_saved_character(self):
        mutations = [
            lambda row: row.update(constant=True),
            lambda row: row.update(constant=24.5),
            lambda row: row.update(count=True),
            lambda row: row.update(count=1001),
            lambda row: row.update(sides=0),
            lambda row: row.update(multiplier=False),
            lambda row: row.update(multiplier=0),
            lambda row: row.update(constant=9_007_199_254_740_991),
            lambda row: row.update(script='arbitrary prose is not an operation'),
        ]
        for mutation in mutations:
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as directory:
                app = CharacterApplication(directory, die=lambda sides: 4,
                                           rule_archive=self.power_archive(mutation))
                hero = app.create(game='heroes-unlimited')
                before = deepcopy(app.get(hero['id']))
                with self.assertRaises(ValueError):
                    app.select_hero_powers(hero['id'], revision=hero['revision'],
                                           selections=['extraordinary-mental-affinity'])
                self.assertEqual(app.get(hero['id']), before)
                self.assertEqual(len(app.list()), 1)

    def test_imported_class_formula_uses_same_multiplier_and_replay_contract(self):
        installed = RuleArchive.load()
        core = installed.active('rifts-core')
        core['classes'][0]['attribute_bonuses']['MA'] = {
            'count': 1, 'sides': 4, 'constant': 3, 'multiplier': 2}
        definitions = [core if (row['id'], row['version']) == (core['id'], core['version'])
                       else row for row in installed.definitions()]
        archive = RuleArchive(definitions, installed.active_versions())
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides: 4, rule_archive=archive)
            character = app.create(generation={'reroll_ones': True, 'extra_die': True})
            self.assertEqual(character['attributes']['MA']['base'], 12)
            self.assertEqual(character['attributes']['MA']['modifiers'][0]['value'], 14)
            self.assertEqual(character['attributes']['MA']['value'], 26)
            app.die = lambda sides: 3
            character = app.reroll(character['id'], revision=0, attribute='MA')
            self.assertEqual(character['attributes']['MA']['value'], 23)
            self.assertEqual(character['attributes']['MA']['modifiers'][0]['rolls'], [4])
            reopened = app.import_character(app.export_character(character['id']))
            self.assertEqual(reopened['attributes'], character['attributes'])
            altered = app.export_character(character['id'])
            altered['character']['attributes']['MA']['modifiers'][0]['value'] = 7
            altered['character']['attributes']['MA']['value'] = 16
            with self.assertRaises(ValueError):
                app.import_character(altered)
            self.assertEqual(len(app.list()), 2)

    def test_imported_physical_formula_retains_multiplied_bonus_without_rerolls(self):
        installed = RuleArchive.load()
        skills = installed.active('heroes-program-skills')
        running = next(row for row in skills['skills'] if row['id'] == 'running')
        running['attributes']['SPD'] = {'count': 4, 'sides': 4, 'bonus': 3, 'multiplier': 2}
        definitions = [skills if (row['id'], row['version']) == (skills['id'], skills['version'])
                       else row for row in installed.definitions()]
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides: 4,
                                       rule_archive=RuleArchive(definitions, installed.active_versions()))
            hero = app.create(game='heroes-unlimited')
            hero = app.select_education(hero['id'], revision=0, method='choose', education_id='high-school')
            hero = app.select_hero_secondary(hero['id'], revision=hero['revision'], selections=['running'])
            self.assertEqual(hero['attributes']['SPD']['value'], 50)
            receipts = deepcopy(hero['physical_acquisitions'])
            hero = app.select_hero_secondary(hero['id'], revision=hero['revision'], selections=[])
            self.assertEqual(hero['attributes']['SPD']['value'], 12)
            app.die = lambda sides: self.fail('Retained acquisition must not roll again')
            hero = app.select_hero_secondary(hero['id'], revision=hero['revision'], selections=['running'])
            self.assertEqual(hero['attributes']['SPD']['value'], 50)
            self.assertEqual(hero['physical_acquisitions'], receipts)
            reopened = app.import_character(app.export_character(hero['id']))
            self.assertEqual(reopened['attributes'], hero['attributes'])
            self.assertEqual(reopened['physical_acquisitions'], receipts)

    def test_invalid_fixed_resource_formula_is_rejected_before_skill_save(self):
        installed = RuleArchive.load()
        skills = installed.active('heroes-program-skills')
        running = next(row for row in skills['skills'] if row['id'] == 'running')
        running['resources']['SDC'] = {
            'count': 0, 'sides': 0, 'bonus': 9_007_199_254_740_991, 'multiplier': 2}
        definitions = [skills if (row['id'], row['version']) == (skills['id'], skills['version'])
                       else row for row in installed.definitions()]
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides: 4,
                                       rule_archive=RuleArchive(definitions, installed.active_versions()))
            hero = app.create(game='heroes-unlimited')
            hero = app.select_education(hero['id'], revision=0, method='choose', education_id='high-school')
            before = deepcopy(app.get(hero['id']))
            with self.assertRaises(ValueError):
                app.select_hero_secondary(hero['id'], revision=hero['revision'], selections=['running'])
            self.assertEqual(app.get(hero['id']), before)
