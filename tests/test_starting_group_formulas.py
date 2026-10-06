"""Random supplementary grants remain original source-bound receipts."""

from copy import deepcopy
from io import BytesIO
import tempfile
import unittest
from pypdf import PdfReader
from characters_unlimited.application import CharacterApplication
from characters_unlimited.rules import RuleArchive
from characters_unlimited.equipment_profiles import EQUIPMENT_FIELDS


class StartingGroupFormulaTests(unittest.TestCase):
    def archive(self, mutate=None):
        archive = RuleArchive.load()
        pack = archive.active('rifts-equipment')
        pack['version'] = 'random-equipment-fixture'
        legacy = deepcopy(pack.get('class_profiles', {}))
        pack['class_profile_format'] = 'owned-v1'
        pack['default_class'] = 'vagabond'
        pack['class_profiles'] = {
            'vagabond': {field: deepcopy(pack.get(field, {})) for field in EQUIPMENT_FIELDS},
            'city-rat': {field: deepcopy(legacy['city-rat'].get(field, pack['source'] if field == 'source' else {}))
                         for field in EQUIPMENT_FIELDS},
        }
        group = pack['class_profiles']['city-rat']['starting_groups']['groups']['armor']
        group['additional_grants'] = {'urban-warrior': [
            {'item_id': 'city-rat-flashlight', 'quantity_formula': {'count': 1, 'sides': 4}}]}
        if mutate:
            mutate(group)
        return RuleArchive([*archive.definitions(), pack], {
            **archive.active_versions(), pack['id']: pack['version']})

    def test_once_only_random_grants_survive_removal_advancement_import_and_pdf(self):
        with tempfile.TemporaryDirectory() as directory:
            archive = self.archive()
            app = CharacterApplication(directory, die=lambda sides: 3, rule_archive=archive)
            hero = app.create(character_class='city-rat')
            calls = []
            def die(sides):
                calls.append(sides)
                return 4
            app.die = die
            hero = app.grant_starting_group(hero['id'], revision=hero['revision'],
                                             group_id='armor', selection='urban-warrior')
            self.assertEqual(calls, [4])
            receipt = deepcopy(hero['starting_equipment_groups'])
            extra = receipt['armor']['grants'][1]
            self.assertEqual(extra['rolls'], [4])
            self.assertEqual(extra['quantity'], 4)
            self.assertEqual(hero['equipment']['items'][1]['quantity'], 4)
            hero = app.set_equipment(hero['id'], revision=hero['revision'], inventory={'credits': 0, 'items': []})
            app.die = lambda sides: self.fail('Read, reopen, and repeat grant must not draw dice')
            self.assertEqual(app.equipment_view(hero['id'])['starting_groups']['groups'][0]['receipt'], receipt['armor'])
            with self.assertRaises(ValueError):
                app.grant_starting_group(hero['id'], revision=hero['revision'], group_id='armor', selection='urban-warrior')
            imported = app.import_character(app.export_character(hero['id']))
            self.assertEqual(imported['starting_equipment_groups'], receipt)
            reopened = CharacterApplication(directory, rule_archive=archive)
            self.assertEqual(reopened.get(hero['id'])['starting_equipment_groups'], receipt)
            fields = PdfReader(BytesIO(reopened.export_pdf(hero['id']))).get_fields()
            assert fields is not None
            values = ' '.join(str(field.get('/V', '')) for field in fields.values())
            self.assertIn('Recorded dice: 4', values)
            self.assertIn('Flashlight x4', values)
            bundle = app.export_character(hero['id'])
            for field, value in [('quantity', 3), ('rolls', [5]), ('rolls', [True]), ('possession_id', receipt['armor']['grants'][0]['possession_id'])]:
                invalid = deepcopy(bundle)
                invalid['character']['starting_equipment_groups']['armor']['grants'][1][field] = value
                with self.assertRaises(ValueError):
                    app.import_character(invalid)

    def test_invalid_unselected_supplementary_formulas_fail_before_generation(self):
        mutations = [
            lambda group: group['additional_grants'].update({'missing-option': []}),
            lambda group: group['additional_grants']['urban-warrior'][0].update(item_id='unknown-item'),
            lambda group: group['additional_grants']['urban-warrior'][0].update(quantity_formula={'count': 1, 'sides': 4, 'constant': -1}),
            lambda group: group['additional_grants']['urban-warrior'][0].update(quantity_formula={'count': True, 'sides': 4}),
            lambda group: group['additional_grants']['urban-warrior'][0].update(quantity_formula={'count': 1000, 'sides': 1000}),
            lambda group: group.update(condition={'name':'Missing original durability', 'formula':{'count':1,'sides':4,'multiplier':100}}),
        ]
        for mutate in mutations:
            with self.subTest(mutate=mutate), tempfile.TemporaryDirectory() as directory:
                app = CharacterApplication(directory, rule_archive=self.archive(mutate),
                                           die=lambda sides: self.fail('Invalid unselected equipment must fail before dice'))
                with self.assertRaises(ValueError):
                    app.create()

    def test_original_condition_is_retained_and_tampering_is_rejected(self):
        def condition(group):
            group['condition'] = {'name':'Missing original durability',
                                  'formula':{'count':1,'sides':4,'multiplier':10}}
        with tempfile.TemporaryDirectory() as directory:
            archive = self.archive(condition)
            app = CharacterApplication(directory, die=lambda sides: 3, rule_archive=archive)
            hero = app.create(character_class='city-rat')
            hero = app.grant_starting_group(hero['id'], revision=hero['revision'], group_id='armor', selection='plastic-man')
            receipt = hero['starting_equipment_groups']['armor']
            self.assertEqual(receipt['condition'], {'rolls':[3], 'value':30})
            app.die = lambda sides: self.fail('Original equipment condition must not reroll')
            hero = app.set_equipment(hero['id'], revision=hero['revision'], inventory={'credits':0, 'items':[]})
            bundle = app.export_character(hero['id'])
            self.assertEqual(app.import_character(bundle)['starting_equipment_groups']['armor'], receipt)
            invalid = deepcopy(bundle)
            invalid['character']['starting_equipment_groups']['armor']['condition']['value'] = 20
            with self.assertRaises(ValueError):
                app.import_character(invalid)
