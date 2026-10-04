"""Typed class effects use shared attribute semantics through public workflows."""
from copy import deepcopy
from io import BytesIO
from pypdf import PdfReader
import tempfile
import unittest
from characters_unlimited.application import CharacterApplication
from characters_unlimited.rules import RuleArchive

class SharedAttributeEffectTests(unittest.TestCase):
    def test_class_minimum_retains_rolls_and_higher_values_across_rerolls_and_portability(self):
        installed = RuleArchive.load()
        core = installed.active('rifts-core')
        selected = core['classes'][0]
        selected['attribute_bonuses'].pop('MA')
        selected['attribute_effects'] = {'MA': {
            'operation': 'minimum', 'formula': {'count': 1, 'sides': 6, 'constant': 24},
            'source': {'book': 'Synthetic framework fixture', 'section': 'Attribute minimum contract'}}}
        selected['attribute_effects']['ME'] = {
            'operation': 'add', 'formula': {'count': 0, 'sides': 0, 'constant': 5},
            'source': {'book': 'Synthetic framework fixture', 'section': 'Attribute addition contract'}}
        definitions = [core if (row['id'], row['version']) == (core['id'], core['version'])
                       else row for row in installed.definitions()]
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides: 4,
                rule_archive=RuleArchive(definitions, installed.active_versions()))
            character = app.create()
            self.assertEqual(character['attributes']['MA']['value'], 28)
            self.assertEqual(character['attributes']['ME']['value'], 17)
            modifier = deepcopy(character['attributes']['MA']['modifiers'][0])
            self.assertEqual(modifier['operation'], 'minimum')
            self.assertEqual(modifier['rolls'], [4])
            app.die = lambda sides: 6
            character = app.reroll(character['id'], revision=character['revision'], attribute='MA')
            self.assertEqual(character['attributes']['MA']['value'], 30)
            self.assertEqual(character['attributes']['MA']['modifiers'][0], modifier)
            character = app.set_attribute(character['id'], revision=character['revision'],
                attribute='MA', mode='fixed', value=40)
            self.assertEqual(character['attributes']['MA']['value'], 40)
            character = app.set_attribute(character['id'], revision=character['revision'], attribute='MA', mode='calculated')
            self.assertEqual(character['attributes']['MA']['value'], 30)
            app.die = lambda sides: 3
            character = app.reroll(character['id'], revision=character['revision'], attribute='MA')
            self.assertEqual(character['attributes']['MA']['value'], 28)
            bundle = app.export_character(character['id'])
            for operation in ('add', 'execute'):
                tampered = deepcopy(bundle)
                record = tampered['character']['attributes']['MA']
                record['modifiers'][0]['operation'] = operation
                record['value'] = 37
                with self.assertRaises(ValueError):
                    app.import_character(tampered)
            fields = PdfReader(BytesIO(app.export_pdf(character['id']))).get_fields()
            assert fields is not None
            self.assertEqual(fields['MA']['/V'], '28')
            restored = app.import_character(bundle)
            self.assertEqual(restored['attributes'], character['attributes'])
            self.assertEqual(restored['roll_history'], character['roll_history'])

    def test_invalid_typed_class_effects_reject_before_generation_dice(self):
        mutations = [
            lambda row: row.update(operation='execute'),
            lambda row: row.update(script='unreviewed expression'),
            lambda row: row['formula'].update(constant=True),
            lambda row: row.update(source=None),
            lambda row: row.update(source={}),
            lambda row: row.update(source={'book': ''}),
            lambda row: row.update(source={'book': 17}),
        ]
        for mutation in mutations:
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as directory:
                installed = RuleArchive.load()
                core = installed.active('rifts-core')
                selected = core['classes'][0]
                selected['attribute_bonuses'].pop('MA')
                effect = {'operation': 'minimum', 'formula': {'count': 1, 'sides': 6, 'constant': 24},
                          'source': {'book': 'Synthetic framework fixture'}}
                mutation(effect)
                selected['attribute_effects'] = {'MA': effect}
                definitions = [core if (row['id'], row['version']) == (core['id'], core['version'])
                               else row for row in installed.definitions()]
                app = CharacterApplication(directory, die=lambda sides: self.fail('Invalid rule rolled dice'),
                    rule_archive=RuleArchive(definitions, installed.active_versions()))
                with self.assertRaises(ValueError):
                    app.create()
                self.assertEqual(app.list(), [])

    def test_class_minimum_ignores_house_rules_and_preserves_starting_pe_snapshot(self):
        installed = RuleArchive.load()
        core = installed.active('rifts-core')
        selected = core['classes'][0]
        selected['attribute_bonuses'].pop('PE')
        selected['attribute_effects'] = {'PE': {
            'operation': 'minimum', 'formula': {'count': 1, 'sides': 4, 'constant': 24},
            'source': {'book': 'Synthetic framework fixture', 'section': 'Attribute minimum contract'}}}
        definitions = [core if (row['id'], row['version']) == (core['id'], core['version'])
                       else row for row in installed.definitions()]
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides: 1 if sides == 4 else 4,
                rule_archive=RuleArchive(definitions, installed.active_versions()))
            character = app.create(generation={'reroll_ones': True, 'extra_die': True})
            self.assertEqual(character['attributes']['PE']['value'], 25)
            self.assertEqual(character['attributes']['PE']['modifiers'][0]['rolls'], [1])
            character = app.generate_resources(character['id'], revision=character['revision'])
            self.assertEqual(app.resource_view(character['id'])['resources']['HP']['value'], 29)
            snapshot = deepcopy(character['resource_attribute_snapshot'])
            app.die = lambda sides: 6
            character = app.reroll(character['id'], revision=character['revision'], attribute='PE')
            self.assertEqual(character['attributes']['PE']['value'], 30)
            self.assertEqual(character['resource_attribute_snapshot'], snapshot)
            self.assertEqual(app.resource_view(character['id'])['resources']['HP']['value'], 29)
            restored = app.import_character(app.export_character(character['id']))
            self.assertEqual(restored['resource_attribute_snapshot'], snapshot)
