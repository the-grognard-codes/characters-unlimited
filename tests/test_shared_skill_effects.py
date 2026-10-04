from copy import deepcopy
from io import BytesIO
import tempfile
import unittest
from pypdf import PdfReader
from characters_unlimited.application import CharacterApplication
from characters_unlimited.rules import RuleArchive


def archive_with(pack):
    installed = RuleArchive.load()
    return RuleArchive([
        pack if (row['id'], row['version']) == (pack['id'], pack['version']) else row
        for row in installed.definitions()
    ], installed.active_versions())


def effect(selector):
    return {'id': 'fixture-bonus', 'name': 'Shared fixture bonus', 'operation': 'add',
            'amount': 7, 'selector': selector,
            'source': {'book': 'Synthetic fixture', 'section': 'Skill effects'}}


class SharedSkillEffectTests(unittest.TestCase):
    def test_rifts_class_effect_applies_once_to_granted_and_selected_skills(self):
        pack = RuleArchive.load().active('rifts-domestic-skills')
        rule = effect({'any_of': [{'ids': ['cook']}, {'categories': ['domestic']}]})
        pack['skill_effects'] = [rule]
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides: 4, rule_archive=archive_with(pack))
            hero = app.create()
            baseline_app = CharacterApplication(directory + '/baseline', die=lambda sides: 4)
            baseline = baseline_app.create()
            before = next(row for row in baseline_app.skill_view(baseline['id'])['grants'] if row['id'] == 'cook')
            after = next(row for row in app.skill_view(hero['id'])['grants'] if row['id'] == 'cook')
            self.assertEqual(after['percentage'], before['percentage'] + 7)
            self.assertEqual(after['effect_contributions'][0]['source'], rule['source'])
            hero = app.select_skills(hero['id'], revision=hero['revision'],
                                     selections=[{'skill_id': 'cook', 'pool': 'secondary'}])
            view = app.skill_view(hero['id'])
            row = next(row for row in view['selected'] if row['skill_id'] == 'cook')
            self.assertEqual(row['contributions']['Effect: Shared fixture bonus'], 7)
            self.assertEqual(app.import_character(app.export_character(hero['id']))['skill_selections'], hero['skill_selections'])
            fields = PdfReader(BytesIO(app.export_pdf(hero['id']))).get_fields()
            self.assertIsNotNone(fields)
            assert fields is not None
            self.assertEqual(fields['page1.cell100']['/V'], '67')
            self.assertEqual(fields['page1.cell102']['/V'], '67')

    def test_heroes_selected_power_effect_targets_acquired_skill_without_granting_it(self):
        pack = RuleArchive.load().active('heroes-super-abilities')
        power = next(row for row in pack['powers'] if row['id'] == 'extraordinary-mental-affinity')
        rule = effect({'any_of': [{'ids': ['mathematics-basic']}]})
        power['skill_effects'] = [rule]
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides: 4, rule_archive=archive_with(pack))
            hero = app.create(game='heroes-unlimited')
            before = next(row for row in app.hero_program_view(hero['id'])['skills'] if row['id'] == 'mathematics-basic')
            hero = app.select_hero_powers(hero['id'], revision=hero['revision'], selections=[power['id']])
            after = next(row for row in app.hero_program_view(hero['id'])['skills'] if row['id'] == 'mathematics-basic')
            self.assertEqual(after['percentage'], before['percentage'] + 7)
            self.assertEqual(after['effect_contributions'][0]['source'], rule['source'])
            hero = app.select_hero_powers(hero['id'], revision=hero['revision'], selections=[])
            self.assertEqual(next(row for row in app.hero_program_view(hero['id'])['skills'] if row['id'] == 'mathematics-basic')['percentage'], before['percentage'])
            restored = app.import_character(app.export_character(hero['id']))
            self.assertEqual(restored['hero_powers'], hero['hero_powers'])

    def test_required_and_scholastic_effects_share_additional_check_and_cap_rules(self):
        installed = RuleArchive.load()
        rifts = installed.active('rifts-domestic-skills')
        rifts['skill_effects'] = [{**effect({'any_of': [{'ids': ['native-language']}]}), 'amount': 20}]
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides: 4, rule_archive=archive_with(rifts))
            hero = app.create()
            native = next(row for row in app.skill_view(hero['id'])['grants'] if row['id'] == 'native-language')
            self.assertEqual(native['contributions']['Effect: Shared fixture bonus'], 20)
            self.assertEqual(native['percentage'], 98)
        pack = installed.active('heroes-program-skills')
        pack['skill_effects'] = [effect({'any_of': [{'ids': ['pick-pockets']}]})]
        second = deepcopy(pack['skill_effects'][0])
        second['id'] = 'second-fixture'
        second['amount'] = 2
        pack['skill_effects'].append(second)
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides: 4, rule_archive=archive_with(pack))
            hero = app.create(game='heroes-unlimited')
            hero = app.select_education(hero['id'], revision=hero['revision'], method='choose', education_id='high-school')
            hero = app.select_hero_secondary(hero['id'], revision=hero['revision'], selections=['pick-pockets', 'seduction'])
            row = next(row for row in app.hero_program_view(hero['id'])['skills'] if row['id'] == 'pick-pockets')
            self.assertEqual(row['contributions']['Effect: Shared fixture bonus'], 9)
            self.assertEqual(row['percentage'], 34)
            self.assertEqual(row['additional_checks'][0]['percentage'], 39)
            self.assertEqual(len(row['effect_contributions']), 2)
            self.assertNotIn('palming', [row['id'] for row in app.hero_program_view(hero['id'])['skills']])

    def test_malformed_effects_reject_before_generation_or_new_power_dice(self):
        installed = RuleArchive.load()
        base = effect({'any_of': [{'ids': ['cook']}]})
        changes: tuple[dict, ...] = ({'operation': 'multiply'}, {'amount': True}, {'source': {}},
                       {'selector': {'any_of': [{'ids': ['missing-fixture']}]}}, {'unexpected': 1})
        for change in changes:
            with self.subTest(change=change), tempfile.TemporaryDirectory() as directory:
                pack = installed.active('rifts-domestic-skills')
                pack['skill_effects'] = [{**base, **change}]
                draws = []
                def die(sides):
                    draws.append(sides)
                    return 4
                app = CharacterApplication(directory, die=die,
                                           rule_archive=archive_with(pack))
                with self.assertRaises(ValueError):
                    app.create()
                self.assertEqual(draws, [])
        pack = installed.active('heroes-super-abilities')
        pack['powers'][-1]['skill_effects'] = [effect({'any_of': [{'ids': ['missing-fixture']}]})]
        with tempfile.TemporaryDirectory() as directory:
            draws = []
            def die(sides):
                draws.append(sides)
                return 4
            app = CharacterApplication(directory, die=die,
                                       rule_archive=archive_with(pack))
            hero = app.create(game='heroes-unlimited')
            draws.clear()
            with self.assertRaises(ValueError):
                app.select_hero_powers(hero['id'], revision=hero['revision'], selections=['extraordinary-mental-affinity'])
            self.assertEqual(draws, [])
            self.assertEqual(app.get(hero['id']), hero)

    def test_nondefault_class_does_not_inherit_default_class_skill_effects(self):
        pack = RuleArchive.load().active('rifts-domestic-skills')
        pack['skill_effects'] = [effect({'any_of': [{'ids': ['cook']}]})]
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides: 4, rule_archive=archive_with(pack))
            hero = app.create(character_class='city-rat')
            hero = app.select_skills(hero['id'], revision=hero['revision'],
                                     selections=[{'skill_id': 'cook', 'pool': 'secondary'}])
            row = next(row for row in app.skill_view(hero['id'])['selected'] if row['skill_id'] == 'cook')
            self.assertNotIn('Effect: Shared fixture bonus', row['contributions'])
            self.assertNotIn('effect_contributions', row)

    def test_skill_totals_outside_exact_integer_range_reject_before_save(self):
        from characters_unlimited.recorded_formulas import MAX_INTEGER
        pack = RuleArchive.load().active('rifts-domestic-skills')
        pack['skill_effects'] = [{**effect({'any_of': [{'ids': ['cook']}]}), 'amount': MAX_INTEGER}]
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides: 4, rule_archive=archive_with(pack))
            with self.assertRaises(ValueError):
                app.create()

    def test_power_effect_dependencies_remain_pinned_before_education(self):
        installed = RuleArchive.load()
        pack = installed.active('heroes-super-abilities')
        power = next(row for row in pack['powers'] if row['id'] == 'extraordinary-mental-affinity')
        power['skill_effects'] = [effect({'any_of': [{'ids': ['mathematics-basic']}]})]
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides: 4, rule_archive=archive_with(pack))
            hero = app.create(game='heroes-unlimited')
            hero = app.select_hero_powers(hero['id'], revision=hero['revision'], selections=[power['id']])
            self.assertEqual(hero['additional_rule_packs']['heroes-program-skills'], installed.active('heroes-program-skills')['version'])
            bundle = app.export_character(hero['id'])
            changed = installed.active('heroes-program-skills')
            changed['version'] = '99.0.0'
            next(row for row in changed['skills'] if row['id'] == 'mathematics-basic')['base'] = 1
            active = {**app.rule_archive.active_versions(), changed['id']: changed['version']}
            newer = RuleArchive([*app.rule_archive.definitions(), changed], active)
            other = CharacterApplication(directory + '/other', rule_archive=newer)
            restored = other.import_character(bundle)
            row = next(row for row in other.hero_program_view(restored['id'])['skills'] if row['id'] == 'mathematics-basic')
            self.assertEqual(row['percentage'], 52)
            bad = deepcopy(bundle)
            del bad['character']['additional_rule_packs']['heroes-program-skills']
            with self.assertRaises(ValueError):
                app.import_character(bad)

    def test_contextual_effect_overflow_rejects_selection_atomically(self):
        from characters_unlimited.recorded_formulas import MAX_INTEGER
        pack = RuleArchive.load().active('heroes-program-skills')
        pack['skill_effects'] = [effect({'any_of': [{'ids': ['pick-pockets']}]})]
        target = next(row for row in pack['skills'] if row['id'] == 'pick-pockets')
        target['additional_checks'] = [{'name': 'Synthetic contextual check', 'context_of': 'primary',
                                        'modifier': MAX_INTEGER, 'requires_skill': 'seduction'}]
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides: 4, rule_archive=archive_with(pack))
            hero = app.create(game='heroes-unlimited')
            hero = app.select_education(hero['id'], revision=hero['revision'], method='choose', education_id='high-school')
            with self.assertRaises(ValueError):
                app.select_hero_secondary(hero['id'], revision=hero['revision'], selections=['pick-pockets', 'seduction'])
            self.assertEqual(app.get(hero['id']), hero)
