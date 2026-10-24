"""Permanent source-bound bonus dice through the public character workflow."""
from copy import deepcopy
import tempfile
import unittest
from typing import Any

from characters_unlimited.application import CharacterApplication
from characters_unlimited.portability import import_bundle
from characters_unlimited.recorded_formulas import MAX_INTEGER
from characters_unlimited.rules import RuleArchive
from tests.test_owned_class_profiles import owned_pack, archive_with


SOURCE = {'book': 'Synthetic retained bonus fixture', 'section': 'Permanent magic resistance'}
ROW = {'id': 'fixture:resistance', 'name': 'Retained resistance', 'target': 'saving:magic',
       'formula': {'count': 1, 'sides': 4}, 'source': SOURCE}


def rolled_pack():
    pack = owned_pack()
    pack['class_profiles']['vagabond']['class_bonuses']['rolled_bonuses'] = [deepcopy(ROW)]
    return pack


class RetainedNumericContributionTests(unittest.TestCase):
    def test_permanent_bonus_survives_edits_advancement_undo_and_exact_no_dice_replay(self):
        archive = archive_with(rolled_pack())
        with tempfile.TemporaryDirectory() as directory, tempfile.TemporaryDirectory() as copied:
            calls = []
            def die(sides):
                calls.append(sides)
                return 3
            app = CharacterApplication(directory, die=die, rule_archive=archive)
            hero = app.create()
            self.assertEqual(calls.count(4), 2)  # Existing class M.A. D4 plus permanent bonus D4.
            receipt = deepcopy(hero['numeric_acquisitions'])
            self.assertEqual(receipt, {'fixture:resistance': {'rolls': {'amount': [3]}}})
            save = app.combat_view(hero['id'])['saving_bonuses']['magic']
            self.assertEqual(save['effect_contributions'][-1]['amount'], 3)
            self.assertEqual(save['effect_contributions'][-1]['source'], SOURCE)
            self.assertTrue(any('Retained resistance: retained dice [3]; saving addition +3' in note
                                for note in app.combat_view(hero['id'])['saving_notes']))
            hero = app.generate_resources(hero['id'], revision=hero['revision'])
            hero = app.advance(hero['id'], revision=hero['revision'], method='level', value=3)
            app.die = lambda sides: self.fail('Replaying permanent dice must not roll')
            hero = app.undo_advancement(hero['id'], revision=hero['revision'])['character']
            hero = app.advance(hero['id'], revision=hero['revision'], method='level', value=3)
            hero = app.set_attribute(hero['id'], revision=hero['revision'], attribute='IQ', mode='fixed', value=18)
            self.assertEqual(hero['numeric_acquisitions'], receipt)
            reopened = CharacterApplication(directory, die=app.die, rule_archive=archive)
            self.assertEqual(reopened.get(hero['id']), hero)
            restored = CharacterApplication(copied, die=app.die, rule_archive=archive).import_character(app.export_character(hero['id']))
            self.assertEqual(restored['numeric_acquisitions'], receipt)
            self.assertEqual(reopened.combat_view(hero['id'])['saving_bonuses']['magic']['effect_contributions'][-1]['amount'], 3)

    def test_malformed_inactive_declarations_reject_before_initial_dice_and_save(self):
        mutations: list[dict[str, Any]] = [{'target': 'missing'}, {'formula': {'count': True, 'sides': 4}},
                     {'formula': {'count': 1, 'sides': 4, 'multiplier': MAX_INTEGER}},
                     {'source': {}}, {'id': 'class:city-rat:perception'},
                     {'target': 'perception'}, {'target': 'combat:attacks'}]
        for mutation in mutations:
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as directory:
                pack = owned_pack()
                pack['class_profiles']['city-rat']['class_bonuses']['rolled_bonuses'] = [{**deepcopy(ROW), **mutation}]
                app = CharacterApplication(directory, die=lambda sides: self.fail('Inactive rules must preflight'),
                                           rule_archive=archive_with(pack))
                with self.assertRaises(ValueError):
                    app.create()
                self.assertEqual(app.list(), [])

    def test_combined_current_and_later_additions_reject_before_any_dice(self):
        for later in (False, True):
            with self.subTest(later=later), tempfile.TemporaryDirectory() as directory:
                pack = owned_pack()
                bonuses = pack['class_profiles']['city-rat']['class_bonuses']
                bonuses['rolled_bonuses'] = [deepcopy(ROW)]
                if later:
                    bonuses['level_bonuses'] = [{'target':'saving:magic','levels':[15],'amount':MAX_INTEGER}]
                else:
                    bonuses['saving']['magic'] = MAX_INTEGER
                app = CharacterApplication(directory, die=lambda sides:self.fail('Combined bounds must preflight'),
                                           rule_archive=archive_with(pack))
                with self.assertRaisesRegex(ValueError, 'Combined class additions'):
                    app.create()
                self.assertEqual(app.list(), [])

    def test_missing_extra_altered_or_historically_changed_receipts_reject(self):
        archive = archive_with(rolled_pack())
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides: 3, rule_archive=archive)
            hero = app.create()
            hero = app.generate_resources(hero['id'], revision=hero['revision'])
            hero = app.advance(hero['id'], revision=hero['revision'], method='level', value=2)
            bundle = app.export_character(hero['id'])
            for kind in ('missing', 'extra', 'face', 'history'):
                with self.subTest(kind=kind):
                    damaged = deepcopy(bundle)
                    current = damaged['character']
                    if kind == 'missing':
                        del current['numeric_acquisitions']
                    elif kind == 'extra':
                        current['numeric_acquisitions']['unknown'] = {'rolls': {'amount': [3]}}
                    elif kind == 'face':
                        current['numeric_acquisitions']['fixture:resistance']['rolls']['amount'] = [5]
                    else:
                        current['advancement']['before']['numeric_acquisitions']['fixture:resistance']['rolls']['amount'] = [2]
                    with self.assertRaises(ValueError):
                        import_bundle(damaged, archive.definitions())

    def test_unchanged_legacy_profiles_keep_their_save_shape(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides: 3)
            hero = app.create()
            self.assertNotIn('numeric_acquisitions', hero)
            self.assertNotIn('numeric_acquisitions', app.import_character(app.export_character(hero['id'])))

    def test_rule_upgrade_rejects_reinterpretation_of_permanent_dice(self):
        from characters_unlimited.class_contributions import validate_class_numeric_upgrade
        pack = {'class_bonuses': {'rolled_bonuses': [deepcopy(ROW)]}}
        validate_class_numeric_upgrade(pack, deepcopy(pack))
        for change in ({'formula': {'count': 1, 'sides': 6}}, {'source': {**SOURCE, 'section': 'Changed'}}):
            target = deepcopy(pack)
            target['class_bonuses']['rolled_bonuses'][0].update(change)
            with self.assertRaisesRegex(ValueError, 'Receipt migration'):
                validate_class_numeric_upgrade(pack, target)
        with tempfile.TemporaryDirectory() as directory:
            old = rolled_pack()
            archive = archive_with(old)
            app = CharacterApplication(directory, die=lambda sides:3, rule_archive=archive)
            hero = app.create()
            new = deepcopy(old)
            new['version'] = '999.0.0'
            new['class_profiles']['vagabond']['class_bonuses']['rolled_bonuses'][0]['formula']['sides'] = 6
            app.rule_archive = RuleArchive([*archive.definitions(), new],
                                            {**archive.active_versions(), new['id']:new['version']})
            app.die = lambda sides:self.fail('Correction previews must never reroll')
            with self.assertRaisesRegex(ValueError, 'Receipt migration'):
                app.preview_rule_upgrade(hero['id'])
            self.assertEqual(app.get(hero['id']),hero)
