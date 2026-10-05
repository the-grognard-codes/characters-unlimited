from copy import deepcopy
from io import BytesIO
import tempfile
import unittest
from pypdf import PdfReader
from characters_unlimited.application import CharacterApplication
from characters_unlimited.rules import RuleArchive
from characters_unlimited.recorded_formulas import MAX_INTEGER
from tests.test_ability_parameters import archive_with, SOURCE

ABILITY = 'synthetic-sensory-ability'


def ability_pack(formulas=None):
    pack = RuleArchive.load().active('heroes-super-abilities')
    pack['powers'].append({'id': ABILITY, 'name': 'Synthetic sensory ability', 'category': 'minor',
        'source': SOURCE, 'guidance': ['Synthetic framework witness.'],
        'acquisition_formulas': {} if formulas is None else formulas,
        'parameters': [{'id': 'range', 'name': 'Range', 'quantity': {'base': 140, 'per_level': 0, 'unit': 'feet'}, 'source': SOURCE}],
        'saving_bonuses': {'psionics': 1}})
    return pack


class NonAttributeAbilityTests(unittest.TestCase):
    def test_nonrandom_ability_uses_retained_selection_without_attribute_changes(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides: 4, rule_archive=archive_with(ability_pack()))
            hero = app.create(game='heroes-unlimited')
            attributes = deepcopy(hero['attributes'])
            app.die = lambda sides: self.fail('Nonrandom ability selection does not roll')
            hero = app.select_hero_powers(hero['id'], revision=hero['revision'], selections=[ABILITY])
            self.assertEqual(hero['attributes'], attributes)
            view = app.hero_powers_view(hero['id'])
            receipt = view['receipts'][0]
            self.assertEqual(receipt['rolls'], {})
            self.assertIsNone(receipt['target'])
            self.assertEqual(receipt['parameters'][0]['value'], 140)
            self.assertEqual(view['saving_bonuses']['psionics']['value'], 1)
            removed = app.select_hero_powers(hero['id'], revision=hero['revision'], selections=[])
            self.assertEqual(app.hero_powers_view(hero['id'])['saving_bonuses']['psionics']['value'], 0)
            inactive = app.hero_powers_view(hero['id'])['receipts'][0]
            self.assertEqual(inactive['acquisition_id'], receipt['acquisition_id'])
            fields = PdfReader(BytesIO(app.export_pdf(hero['id']))).get_fields()
            assert fields is not None
            evidence = ' '.join(str(row.get('/V', '')) for row in fields.values())
            self.assertIn('Retained inactive power: Synthetic sensory ability', evidence)
            self.assertIn('Range: 140 feet', evidence)
            self.assertIn('Synthetic ability fixture', evidence)
            hero = app.select_hero_powers(hero['id'], revision=removed['revision'], selections=[ABILITY])
            self.assertEqual(app.hero_powers_view(hero['id'])['receipts'][0], receipt)
            restored = app.import_character(app.export_character(hero['id']))
            self.assertEqual(app.hero_powers_view(restored['id']), app.hero_powers_view(hero['id']))

    def test_non_attribute_random_groups_keep_raw_dice_without_house_generation_options(self):
        formulas = {'sense-strength': {'count': 2, 'sides': 6, 'constant': 3},
                    'fixed-reach': {'count': 0, 'sides': 0, 'constant': 10}}
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides: 4, rule_archive=archive_with(ability_pack(formulas)))
            hero = app.create(game='heroes-unlimited', generation={'reroll_ones': True, 'extra_die': True})
            attributes = deepcopy(hero['attributes'])
            calls = []
            def die(sides):
                calls.append(sides)
                return 1
            app.die = die
            hero = app.select_hero_powers(hero['id'], revision=hero['revision'], selections=[ABILITY])
            self.assertEqual(calls, [6, 6])
            self.assertEqual(hero['attributes'], attributes)
            receipt = app.hero_powers_view(hero['id'])['receipts'][0]
            self.assertEqual(receipt['rolls'], {'sense-strength': [1, 1], 'fixed-reach': []})
            self.assertIn('5', receipt['effect_summary'])
            forged = app.export_character(hero['id'])
            forged['character']['hero_powers']['acquisitions'][0]['rolls']['sense-strength'] = [0, 1]
            with self.assertRaises(ValueError):
                app.import_character(forged)

    def test_invalid_unselected_non_attribute_formulas_reject_before_dice_or_save(self):
        for formulas in [[], {'bad': {'count': True, 'sides': 6}},
                         {'bad': {'count': 1, 'sides': 6, 'constant': MAX_INTEGER}},
                         {'bad': {'count': 0, 'sides': 0, 'attribute': 'MA'}}]:
            with self.subTest(formulas=formulas), tempfile.TemporaryDirectory() as directory:
                pack = ability_pack()
                pack['powers'][-1]['acquisition_formulas'] = formulas
                app = CharacterApplication(directory, die=lambda sides: 4, rule_archive=archive_with(pack))
                hero = app.create(game='heroes-unlimited')
                app.die = lambda sides: self.fail('Malformed unselected declarations must preflight')
                with self.assertRaises(ValueError):
                    app.select_hero_powers(hero['id'], revision=hero['revision'], selections=['extraordinary-mental-affinity'])
                self.assertEqual(app.get(hero['id']), hero)

    def test_ambiguous_or_unsupported_unselected_ability_shapes_reject_before_dice(self):
        for mutation in [{'attribute_floor': {'attribute': 'MA', 'count': 1, 'sides': 6, 'constant': 24}},
                         {'guidance': 'not a list'}, {'source': {}}, {'callback': 'execute'},
                         {'acquisition_formulas': None}]:
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as directory:
                pack = ability_pack()
                pack['powers'][-1].update(mutation)
                app = CharacterApplication(directory, die=lambda sides: 4, rule_archive=archive_with(pack))
                hero = app.create(game='heroes-unlimited')
                app.die = lambda sides: self.fail('Invalid declarations must reject before new dice')
                with self.assertRaises(ValueError):
                    app.select_hero_powers(hero['id'], revision=hero['revision'], selections=['extraordinary-mental-affinity'])
                self.assertEqual(app.get(hero['id']), hero)
