from io import BytesIO
from pypdf import PdfReader
from typing import Any
from copy import deepcopy
import tempfile
import unittest
from characters_unlimited.application import CharacterApplication
from characters_unlimited.rules import RuleArchive
from tests.test_ability_parameters import archive_with, POWER, SOURCE


class NumericContributionTests(unittest.TestCase):
    def test_distinct_power_contributions_with_the_same_display_name_remain_explainable(self):
        pack = RuleArchive.load().active('heroes-super-abilities')
        for power in pack['powers']:
            if power['id'] in (POWER, 'extraordinary-mental-endurance'):
                power['name'] = 'Shared fixture label'
                power['source'] = {**SOURCE, 'printed_page': 1, 'pdf_page': 1}
        next(row for row in pack['powers'] if row['id'] == POWER)['saving_bonuses'] = {'horror-factor': 2}
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides: 4, rule_archive=archive_with(pack))
            hero = app.create(game='heroes-unlimited')
            hero = app.select_hero_powers(hero['id'], revision=hero['revision'], selections=[POWER, 'extraordinary-mental-endurance'])
            save = app.hero_powers_view(hero['id'])['saving_bonuses']['horror-factor']
            self.assertEqual(save['value'], 8)
            self.assertEqual(sum(save['contributions'].values()), save['value'])
            self.assertEqual(len(save['effect_contributions']), 2)
            fields = PdfReader(BytesIO(app.export_pdf(hero['id']))).get_fields()
            assert fields is not None
            evidence = ' '.join(str(row.get('/V', '')) for row in fields.values())
            self.assertIn('Shared fixture label (2)', evidence)
            self.assertIn('Synthetic ability fixture', evidence)
            app.die = lambda sides: self.fail('Reselection and reopening use retained dice')
            removed = app.select_hero_powers(hero['id'], revision=hero['revision'], selections=[])
            hero = app.select_hero_powers(hero['id'], revision=removed['revision'], selections=[POWER, 'extraordinary-mental-endurance'])
            self.assertEqual(app.hero_powers_view(hero['id'])['saving_bonuses']['horror-factor'], save)
            restored = app.import_character(app.export_character(hero['id']))
            self.assertEqual(app.hero_powers_view(restored['id'])['saving_bonuses']['horror-factor'], save)

    def test_unselected_bad_power_effects_reject_before_dice_or_save(self):
        from characters_unlimited.recorded_formulas import MAX_INTEGER
        for bonuses in [None, {'horror-factor': True}, {'horror-factor': MAX_INTEGER + 1}, {'unknown': 1}]:
            with self.subTest(bonuses=bonuses), tempfile.TemporaryDirectory() as directory:
                pack = RuleArchive.load().active('heroes-super-abilities')
                next(row for row in pack['powers'] if row['id'] == POWER)['saving_bonuses'] = bonuses
                calls = []
                def die(sides):
                    calls.append(sides)
                    return 4
                app = CharacterApplication(directory, die=die, rule_archive=archive_with(pack))
                hero = app.create(game='heroes-unlimited')
                calls.clear()
                with self.assertRaises(ValueError):
                    app.select_hero_powers(hero['id'], revision=hero['revision'], selections=['extraordinary-mental-endurance'])
                self.assertEqual(calls, [])
                self.assertEqual(app.get(hero['id']), hero)

    def test_unselected_owned_class_bonuses_preflight_before_initial_dice(self):
        from tests.test_owned_class_profiles import owned_pack
        for mutation in [{'saving': {'unknown': 1}}, {'perception': True}, {'source': {}}]:
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as directory:
                pack = owned_pack()
                pack['class_profiles']['city-rat']['class_bonuses'].update(mutation)
                app = CharacterApplication(directory, die=lambda sides: self.fail('Invalid class must preflight before dice'),
                                           rule_archive=archive_with(pack))
                with self.assertRaisesRegex(ValueError, 'city-rat.*class_bonuses'):
                    app.create(character_class='vagabond')
                self.assertEqual(app.list(), [])

    def test_class_bonus_totals_and_sources_survive_exact_portable_reopening(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides: 4)
            hero = app.create()
            combat = app.combat_view(hero['id'])
            perception = combat['class_bonuses']['perception']
            self.assertEqual(perception['value'], 4)
            self.assertEqual(perception['effect_contributions'][0]['id'], 'class:vagabond:perception')
            save = combat['saving_bonuses']['horror_factor']
            self.assertEqual(save['value'], sum(save['contributions'].values()))
            self.assertEqual(save['effect_contributions'][0]['source'], perception['effect_contributions'][0]['source'])
            restored = app.import_character(app.export_character(hero['id']))
            self.assertEqual(app.combat_view(restored['id'])['saving_bonuses'], combat['saving_bonuses'])

    def test_combined_overflow_rejects_power_selection_and_direct_attribute_edit(self):
        from characters_unlimited.recorded_formulas import MAX_INTEGER
        pack = RuleArchive.load().active('heroes-super-abilities')
        next(row for row in pack['powers'] if row['id'] == POWER)['saving_bonuses'] = {'psionics': MAX_INTEGER}
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides: 4, rule_archive=archive_with(pack))
            hero = app.create(game='heroes-unlimited')
            hero = app.select_hero_powers(hero['id'], revision=hero['revision'], selections=[POWER])
            self.assertEqual(app.hero_powers_view(hero['id'])['saving_bonuses']['psionics']['value'], MAX_INTEGER)
            with self.assertRaisesRegex(ValueError, 'exact integer range'):
                app.set_attribute(hero['id'], revision=hero['revision'], attribute='ME', mode='fixed', value=30)
            self.assertEqual(app.get(hero['id']), hero)
            with self.assertRaisesRegex(ValueError, 'exact integer range'):
                app.select_hero_powers(hero['id'], revision=hero['revision'], selections=[POWER, 'extraordinary-mental-endurance'])
            self.assertEqual(app.get(hero['id']), hero)
            faces = iter([6, 6, 5, 4])
            app.die = lambda sides: next(faces)
            with self.assertRaisesRegex(ValueError, 'exact integer range'):
                app.reroll(hero['id'], revision=hero['revision'], attribute='ME')
            self.assertEqual(app.get(hero['id']), hero)

    def test_common_numeric_boundary_preserves_unknowns_and_rejects_invalid_operations(self):
        from characters_unlimited.numeric_contributions import compile_numeric_contributions, apply_numeric_contributions
        from characters_unlimited.recorded_formulas import MAX_INTEGER
        row = {'id': 'spell-fixture', 'name': 'Fixture', 'operation': 'add', 'target': 'save', 'amount': 2, 'source': SOURCE}
        base: dict[str, Any] = {'value': None, 'contributions': {}, 'sources': []}
        result = apply_numeric_contributions(base, [row], 'save')
        self.assertIsNone(result['value'])
        self.assertEqual(result['contributions'], {'Fixture': 2})
        self.assertEqual(base, {'value': None, 'contributions': {}, 'sources': []})
        legacy = {**base, 'value': 10**400}
        self.assertEqual(apply_numeric_contributions(legacy, [], 'save'), legacy)
        invalids: list[dict[str, Any]] = [{'amount': True}, {'amount': MAX_INTEGER + 1}, {'operation': 'execute'}, {'target': 'missing'}, {'source': {}}]
        for mutation in invalids:
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                compile_numeric_contributions([{**row, **mutation}], {'save'})
        with self.assertRaises(ValueError):
            compile_numeric_contributions([row, deepcopy(row)], {'save'})
        with self.assertRaisesRegex(ValueError, 'exact integer range'):
            apply_numeric_contributions({**base, 'value': MAX_INTEGER}, [row], 'save')
