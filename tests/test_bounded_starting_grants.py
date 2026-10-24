"""Public witnesses for chosen funds and retained base-quantity dice."""

from copy import deepcopy
import tempfile
import unittest
from typing import Any

from characters_unlimited.application import CharacterApplication, SaveConflict
from characters_unlimited.rules import RuleArchive


class BoundedStartingGrantTests(unittest.TestCase):
    def archive(self, mutate=None):
        archive = RuleArchive.load()
        pack = archive.active('rifts-equipment')
        pack['version'] = 'bounded-starting-fixture'
        profile = pack['class_profiles']['city-rat']
        profile['starting_funds'] = {
            'character_class': 'city-rat', 'guidance': ['Synthetic contract witness.'],
            'definitions': [{'id': 'credits', 'name': 'Chosen starting credits',
                             'count': 0, 'sides': 0, 'multiplier': 2,
                             'choice': {'name': 'Monthly amount', 'minimum': 200, 'maximum': 300},
                             'source': deepcopy(profile['source'])}]}
        group = profile['starting_groups']['groups']['knife']
        group.pop('quantity')
        group['quantity_formula'] = {'count': 1, 'sides': 6}
        if mutate:
            mutate(profile)
        return RuleArchive([*archive.definitions(), pack],
                           {**archive.active_versions(), pack['id']: pack['version']})

    def test_bounded_choice_grants_two_units_without_dice_and_preserves_original_receipt(self):
        for monthly, starting in ((200, 400), (250, 500), (300, 600)):
            with self.subTest(monthly=monthly), tempfile.TemporaryDirectory() as directory:
                archive = self.archive()
                app = CharacterApplication(directory, rule_archive=archive, die=lambda sides: 3)
                hero = app.create(character_class='city-rat')
                app.die = lambda sides: self.fail('Chosen funds and reads must not draw dice')
                hero = app.generate_starting_funds(hero['id'], revision=hero['revision'], choices={'credits': monthly})
                receipt = deepcopy(hero['starting_funds'])
                self.assertEqual(receipt['credits']['choice'], monthly)
                self.assertEqual(receipt['credits']['rolls'], [])
                self.assertEqual(receipt['credits']['value'], starting)
                self.assertEqual(hero['equipment']['credits'], starting)
                hero = app.set_equipment(hero['id'], revision=hero['revision'], inventory={'credits': -25, 'items': []})
                with self.assertRaises(ValueError):
                    app.generate_starting_funds(hero['id'], revision=hero['revision'], choices={'credits': monthly})
                reopened = CharacterApplication(directory, rule_archive=archive, die=app.die)
                self.assertEqual(reopened.get(hero['id']), hero)
                self.assertEqual(reopened.equipment_view(hero['id'])['starting_funds']['funds'], receipt)
                imported = reopened.import_character(reopened.export_character(hero['id']))
                self.assertEqual(imported['starting_funds'], receipt)
                self.assertEqual(imported['equipment']['credits'], -25)

    def test_base_quantity_draws_once_and_survives_inventory_removal_and_portable_replay(self):
        with tempfile.TemporaryDirectory() as directory:
            archive = self.archive()
            app = CharacterApplication(directory, rule_archive=archive, die=lambda sides: 3)
            hero = app.create(character_class='city-rat')
            calls = []
            def die(sides):
                calls.append(sides)
                return 6
            app.die = die
            hero = app.grant_starting_group(hero['id'], revision=hero['revision'], group_id='knife', selection='knife-large')
            self.assertEqual(calls, [6])
            receipt = deepcopy(hero['starting_equipment_groups'])
            self.assertEqual(receipt['knife']['grants'][0]['rolls'], [6])
            self.assertEqual(receipt['knife']['grants'][0]['quantity'], 6)
            self.assertEqual(len(hero['equipment']['items']), 1)
            self.assertEqual(hero['equipment']['items'][0]['quantity'], 6)
            hero = app.set_equipment(hero['id'], revision=hero['revision'], inventory={'credits': 0, 'items': []})
            app.die = lambda sides: self.fail('Retained quantities must not draw again')
            with self.assertRaises(ValueError):
                app.grant_starting_group(hero['id'], revision=hero['revision'], group_id='knife', selection='knife-large')
            self.assertEqual(app.equipment_view(hero['id'])['starting_groups']['groups'][1]['receipt'], receipt['knife'])
            self.assertEqual(app.import_character(app.export_character(hero['id']))['starting_equipment_groups'], receipt)
            self.assertEqual(CharacterApplication(directory, rule_archive=archive).get(hero['id']), hero)

    def test_invalid_choices_and_stale_revisions_fail_without_dice_or_save_changes(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, rule_archive=self.archive(), die=lambda sides: 3)
            hero = app.create(character_class='city-rat')
            app.die = lambda sides: self.fail('Invalid choices must fail before dice')
            invalid_choices: list[Any] = [None, {}, [], {'credits': True}, {'credits': 250.5}, {'credits': 199},
                                         {'credits': 301}, {'credits': '250'}, {'credits': 250, 'extra': 1}]
            for choices in invalid_choices:
                with self.subTest(choices=choices), self.assertRaises(ValueError):
                    app.generate_starting_funds(hero['id'], revision=hero['revision'], choices=choices)
                self.assertEqual(app.get(hero['id']), hero)
            with self.assertRaises(SaveConflict):
                app.generate_starting_funds(hero['id'], revision=hero['revision'] + 1, choices={'credits': 250})
            self.assertEqual(app.get(hero['id']), hero)

    def test_malformed_inactive_definitions_fail_before_creation_dice(self):
        mutations = [
            lambda p: p['starting_funds']['definitions'][0]['choice'].update(minimum=True),
            lambda p: p['starting_funds']['definitions'][0]['choice'].update(maximum=199),
            lambda p: p['starting_funds']['definitions'][0]['choice'].update(maximum=9_007_199_254_740_991),
            lambda p: p['starting_funds']['definitions'][0].update(count=1, sides=6),
            lambda p: p['starting_funds']['definitions'][0].update(constant=1),
            lambda p: p['starting_groups']['groups']['knife'].update(quantity=1),
            lambda p: p['starting_groups']['groups']['knife'].update(quantity_formula={'count': True, 'sides': 6}),
            lambda p: p['starting_groups']['groups']['knife'].update(quantity_formula={'count': 1, 'sides': 6, 'constant': -1}),
            lambda p: p['starting_groups']['groups']['knife'].update(quantity_formula={'count': 1000, 'sides': 6}),
        ]
        for mutate in mutations:
            with self.subTest(mutate=mutate), tempfile.TemporaryDirectory() as directory:
                app = CharacterApplication(directory, rule_archive=self.archive(mutate),
                                           die=lambda sides: self.fail('Inactive rules must compile before dice'))
                with self.assertRaises(ValueError):
                    app.create()

    def test_tampered_receipts_and_reinterpreting_updates_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            archive = self.archive()
            app = CharacterApplication(directory, rule_archive=archive, die=lambda sides: 3)
            hero = app.create(character_class='city-rat')
            hero = app.generate_starting_funds(hero['id'], revision=hero['revision'], choices={'credits': 250})
            hero = app.grant_starting_group(hero['id'], revision=hero['revision'], group_id='knife', selection='knife-large')
            bundle = app.export_character(hero['id'])
            mutations = [
                lambda c: c['starting_funds']['credits'].update(choice=249),
                lambda c: c['starting_funds']['credits'].update(choice=True),
                lambda c: c['starting_funds']['credits'].update(source={}),
                lambda c: c['starting_equipment_groups']['knife']['grants'][0].update(quantity=2),
                lambda c: c['starting_equipment_groups']['knife']['grants'][0].update(rolls=[7]),
                lambda c: c['starting_equipment_groups']['knife']['grants'][0].update(rolls=[True]),
            ]
            for mutate in mutations:
                invalid = deepcopy(bundle)
                mutate(invalid['character'])
                with self.assertRaises(ValueError):
                    app.import_character(invalid)
                self.assertEqual(app.get(hero['id']), hero)
            for field in ('starting_funds', 'starting_groups'):
                changed = archive.active('rifts-equipment')
                changed['version'] = 'changed-bounded-fixture'
                profile = changed['class_profiles']['city-rat']
                if field == 'starting_funds':
                    profile[field]['definitions'][0]['choice']['maximum'] = 350
                else:
                    profile[field]['groups']['knife']['quantity_formula']['sides'] = 5
                newer = CharacterApplication(directory, rule_archive=RuleArchive([*archive.definitions(), changed],
                    {**archive.active_versions(), changed['id']: changed['version']}))
                with self.assertRaisesRegex(ValueError, 'recorded starting'):
                    newer.preview_rule_upgrade(hero['id'])
                self.assertEqual(newer.get(hero['id']), hero)
