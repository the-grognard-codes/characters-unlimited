from copy import deepcopy
from io import BytesIO
import tempfile
import unittest
from pypdf import PdfReader
from characters_unlimited.application import CharacterApplication
from characters_unlimited.rules import RuleArchive
from characters_unlimited.recorded_formulas import MAX_INTEGER

SOURCE = {'book': 'Synthetic ability fixture', 'section': 'Shared ability parameters'}
POWER = 'extraordinary-mental-affinity'


def archive_with(pack):
    installed = RuleArchive.load()
    return RuleArchive([pack if row['id'] == pack['id'] and row['version'] == pack['version'] else row
                        for row in installed.definitions()], installed.active_versions())


def parameter_pack():
    pack = RuleArchive.load().active('heroes-super-abilities')
    power = next(row for row in pack['powers'] if row['id'] == POWER)
    power['parameters'] = [
        {'id': 'range', 'name': 'Range', 'quantity': {'base': 140, 'per_level': 0, 'unit': 'feet'}, 'source': SOURCE},
        {'id': 'duration', 'name': 'Duration', 'quantity': {'base': 0, 'per_level': 2, 'unit': 'minutes'}, 'source': SOURCE},
        {'id': 'cost', 'name': 'Energy cost', 'quantity': {'base': 2, 'per_level': 0, 'unit': 'P.P.E.'}, 'source': SOURCE},
        {'id': 'save', 'name': 'Saving throw', 'text': 'None; synthetic condition', 'source': SOURCE}]
    return pack


class AbilityParameterTests(unittest.TestCase):
    def test_source_bound_quantities_scale_with_level_and_survive_exact_reopening(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides: 4, rule_archive=archive_with(parameter_pack()))
            hero = app.create(game='heroes-unlimited')
            hero = app.select_hero_powers(hero['id'], revision=hero['revision'], selections=[POWER])
            parameters = app.hero_powers_view(hero['id'])['powers'][0]['parameters']
            self.assertEqual(next(row for row in parameters if row['id'] == 'duration')['value'], 2)
            self.assertEqual(next(row for row in parameters if row['id'] == 'save')['text'], 'Saving throw: None; synthetic condition')
            hero = app.generate_resources(hero['id'], revision=hero['revision'])
            hero = app.advance(hero['id'], revision=hero['revision'], method='level', value=3)
            parameters = app.hero_powers_view(hero['id'])['powers'][0]['parameters']
            self.assertEqual(next(row for row in parameters if row['id'] == 'duration')['value'], 6)
            self.assertEqual(next(row for row in parameters if row['id'] == 'cost')['value'], 2)
            self.assertEqual(app.resource_view(hero['id'])['resources']['PPE']['value'], 24)
            restored = app.import_character(app.export_character(hero['id']))
            self.assertEqual(app.hero_powers_view(restored['id'])['powers'][0]['parameters'], parameters)
            fields = PdfReader(BytesIO(app.export_pdf(hero['id']))).get_fields()
            assert fields is not None
            evidence = ' '.join(' '.join(str(row.get('/V', '')) for row in fields.values()).split())
            self.assertIn('Duration: 6 minutes', evidence)
            self.assertIn('Synthetic ability fixture', evidence)
            self.assertIn('Shared ability parameters', evidence)

    def test_invalid_unselected_parameters_reject_before_power_dice_or_save(self):
        invalids = [None,
            [{'id': 'bad', 'name': 'Bad', 'text': 'Literal', 'source': {}}],
            [{'id': 'bad', 'name': 'Bad', 'quantity': {'base': True, 'per_level': 0, 'unit': 'feet'}, 'source': SOURCE}],
            [{'id': 'bad', 'name': 'Bad', 'quantity': {'base': MAX_INTEGER, 'per_level': 1, 'unit': 'feet'}, 'source': SOURCE}],
            [{'id': 'bad', 'name': 'Bad', 'text': 'Literal', 'source': SOURCE, 'callback': 'execute prose'}]]
        for parameters in invalids:
            with self.subTest(parameters=parameters), tempfile.TemporaryDirectory() as directory:
                pack = parameter_pack()
                other = next(row for row in pack['powers'] if row['id'] != POWER)
                other['parameters'] = parameters
                app = CharacterApplication(directory, die=lambda sides: 4, rule_archive=archive_with(pack))
                hero = app.create(game='heroes-unlimited')
                app.die = lambda sides: self.fail('Invalid unselected parameters must preflight')
                with self.assertRaises(ValueError):
                    app.select_hero_powers(hero['id'], revision=hero['revision'], selections=[POWER])
                self.assertEqual(app.get(hero['id']), hero)

    def test_origin_one_and_inactive_power_parameters_use_current_level_without_reroll(self):
        pack = parameter_pack()
        power = next(row for row in pack['powers'] if row['id'] == POWER)
        power['parameters'][1]['quantity'] = {'base': 5, 'per_level': 3, 'level_origin': 1, 'unit': 'minutes'}
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides: 4, rule_archive=archive_with(pack))
            hero = app.create(game='heroes-unlimited')
            hero = app.select_hero_powers(hero['id'], revision=hero['revision'], selections=[POWER])
            self.assertEqual(app.hero_powers_view(hero['id'])['powers'][0]['parameters'][1]['value'], 5)
            hero = app.generate_resources(hero['id'], revision=hero['revision'])
            hero = app.advance(hero['id'], revision=hero['revision'], method='level', value=3)
            hero = app.select_hero_powers(hero['id'], revision=hero['revision'], selections=[])
            receipt = app.hero_powers_view(hero['id'])['receipts'][0]
            self.assertFalse(receipt['active'])
            self.assertEqual(receipt['parameters'][1]['value'], 11)
            fields = PdfReader(BytesIO(app.export_pdf(hero['id']))).get_fields()
            assert fields is not None
            evidence = ' '.join(' '.join(str(row.get('/V', '')) for row in fields.values()).split())
            self.assertIn('Duration: 11 minutes', evidence)
            app.die = lambda sides: self.fail('Reselection must retain power dice')
            hero = app.select_hero_powers(hero['id'], revision=hero['revision'], selections=[POWER])
            self.assertEqual(app.hero_powers_view(hero['id'])['powers'][0]['parameters'][1]['value'], 11)

    def test_portable_parameters_use_the_exact_old_pin_with_a_newer_active_catalog(self):
        old = parameter_pack()
        newer = deepcopy(old)
        newer['version'] = '1.3.1'
        next(row for row in newer['powers'] if row['id'] == POWER)['parameters'][1]['quantity']['per_level'] = 3
        with tempfile.TemporaryDirectory() as first_directory, tempfile.TemporaryDirectory() as next_directory:
            first = CharacterApplication(first_directory, die=lambda sides: 4, rule_archive=archive_with(old))
            hero = first.create(game='heroes-unlimited')
            hero = first.select_hero_powers(hero['id'], revision=hero['revision'], selections=[POWER])
            hero = first.generate_resources(hero['id'], revision=hero['revision'])
            hero = first.advance(hero['id'], revision=hero['revision'], method='level', value=3)
            installed = archive_with(old)
            active = installed.active_versions()
            active[old['id']] = newer['version']
            next_app = CharacterApplication(next_directory, die=lambda sides: self.fail('Import must not roll'),
                                            rule_archive=RuleArchive([*installed.definitions(), newer], active))
            restored = next_app.import_character(first.export_character(hero['id']))
            self.assertEqual(next_app.hero_powers_view(restored['id'])['powers'][0]['parameters'][1]['value'], 6)
            self.assertEqual(restored['additional_rule_packs'][old['id']], old['version'])
