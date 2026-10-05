from copy import deepcopy
import tempfile
import unittest
from typing import Any
from characters_unlimited.application import CharacterApplication
from characters_unlimited.rules import RuleArchive
from tests.test_ability_parameters import archive_with, POWER


class RetainedAcquisitionTests(unittest.TestCase):
    def test_unselected_malformed_power_formula_preflights_before_any_dice(self):
        pack = RuleArchive.load().active('heroes-super-abilities')
        other = next(row for row in pack['powers'] if row['id'] == 'extraordinary-mental-endurance')
        other['attribute_floor']['count'] = True
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides: 4, rule_archive=archive_with(pack))
            hero = app.create(game='heroes-unlimited')
            app.die = lambda sides: self.fail('Every declaration must validate before acquisition dice')
            with self.assertRaises(ValueError):
                app.select_hero_powers(hero['id'], revision=hero['revision'], selections=[POWER])
            self.assertEqual(app.get(hero['id']), hero)

    def test_common_acquisition_boundary_retains_raw_dice_and_supports_nonrandom_abilities(self):
        from characters_unlimited.retained_acquisitions import acquire_selected, validate_cached_acquisitions
        catalog = {'physical-option': {'bonus': {'count': 2, 'sides': 6, 'constant': 3}},
                   'psychic-option': {}, 'spell-option': {'capacity': {'count': 0, 'sides': 0, 'constant': 7}}}
        faces = iter([1, 5])
        acquired = acquire_selected(catalog, {}, ['physical-option', 'psychic-option', 'spell-option'], lambda sides: next(faces))
        self.assertEqual(acquired['physical-option']['rolls']['bonus'], [1, 5])
        self.assertEqual(acquired['psychic-option'], {'rolls': {}})
        self.assertEqual(acquired['spell-option'], {'rolls': {'capacity': []}})
        original = deepcopy(acquired)
        inactive = acquire_selected(catalog, acquired, [], lambda sides: self.fail('Removal must not roll'))
        reselected = acquire_selected(catalog, inactive, list(catalog), lambda sides: self.fail('Reselection must not roll'))
        self.assertEqual(reselected, original)
        reselected['physical-option']['rolls']['bonus'][0] = 2
        self.assertEqual(acquired, original)
        validate_cached_acquisitions(catalog, original)
        constants_omitted = acquire_selected(catalog, {}, ['spell-option'], lambda sides: self.fail('Constants must not roll'), record_constants=False)
        self.assertEqual(constants_omitted['spell-option'], {'rolls': {}})

    def test_bad_inactive_receipts_and_unselected_formula_bounds_preflight_before_dice(self):
        from characters_unlimited.retained_acquisitions import acquire_selected
        from characters_unlimited.recorded_formulas import MAX_INTEGER
        catalog = {'first': {'gain': {'count': 1, 'sides': 6}}, 'second': {'gain': {'count': 1, 'sides': 6}}}
        bad_caches: list[dict[str, Any]] = [{'second': {'rolls': {'gain': [7]}}}, {'second': {'rolls': {'wrong': [1]}}},
                      {'missing': {'rolls': {}}}, {'second': {'rolls': {'gain': [True]}}}]
        for cache in bad_caches:
            with self.subTest(cache=cache), self.assertRaises(ValueError):
                acquire_selected(catalog, cache, ['first'], lambda sides: self.fail('All retained receipts must preflight'))
        invalid = deepcopy(catalog)
        invalid['second']['gain']['constant'] = MAX_INTEGER - 1
        with self.assertRaises(ValueError):
            acquire_selected(invalid, {}, ['first'], lambda sides: self.fail('Possible overflow must preflight'))
        with self.assertRaises(ValueError):
            acquire_selected(catalog, {}, ['first', 'first'], lambda sides: self.fail('Duplicates must preflight'))
        with self.assertRaises(ValueError):
            acquire_selected(catalog, {}, ['missing'], lambda sides: self.fail('Missing identities must preflight'))

    def test_power_receipt_source_preflights_before_acquiring_another_power(self):
        from characters_unlimited.heroes_powers import select_powers
        pack = RuleArchive.load().active('heroes-super-abilities')
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides: 4)
            hero = app.create(game='heroes-unlimited')
            hero = app.select_hero_powers(hero['id'], revision=hero['revision'], selections=[POWER])
            original = deepcopy(hero)
            forged = deepcopy(hero)
            forged['hero_powers']['acquisitions'][0]['source']['book'] = 'Forged source'
            with self.assertRaises(ValueError):
                select_powers(forged, [POWER, 'extraordinary-mental-endurance'], pack,
                    lambda sides: self.fail('Forged source must reject before another acquisition'))
            self.assertEqual(app.get(hero['id']), original)
