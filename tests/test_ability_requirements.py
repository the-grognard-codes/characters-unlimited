from copy import deepcopy
from io import BytesIO
import tempfile
import unittest
from pypdf import PdfReader
from characters_unlimited.application import CharacterApplication
from characters_unlimited.rules import RuleArchive
from tests.test_ability_parameters import archive_with, POWER, SOURCE

OTHER = 'extraordinary-mental-endurance'


def requirement_pack():
    pack = RuleArchive.load().active('heroes-super-abilities')
    power = next(row for row in pack['powers'] if row['id'] == POWER)
    power['requirements'] = [
        {'id': 'level', 'name': 'Experienced character', 'minimum_level': 3, 'source': SOURCE},
        {'id': 'mind', 'name': 'Mental endurance', 'attribute_minimum': {'attribute': 'ME', 'value': 10}, 'source': SOURCE},
        {'id': 'companion', 'name': 'Companion power', 'selected_options': {'catalog': 'powers',
            'selector': {'any_of': [{'ids': [OTHER]}]}, 'minimum': 1}, 'source': SOURCE}]
    return pack


class AbilityRequirementTests(unittest.TestCase):
    def test_unmet_requirements_retain_choices_and_effects_with_source_guidance(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides: 4, rule_archive=archive_with(requirement_pack()))
            hero = app.create(game='heroes-unlimited')
            hero = app.select_hero_powers(hero['id'], revision=hero['revision'], selections=[POWER])
            view = app.hero_powers_view(hero['id'])
            self.assertEqual(view['selections'], [POWER])
            self.assertEqual([row['satisfied'] for row in view['powers'][0]['requirements']], [False, True, False])
            self.assertEqual(len([warning for warning in view['warnings'] if 'requirement' in warning]), 2)
            self.assertEqual(hero['attributes']['MA']['value'], 28)
            fields = PdfReader(BytesIO(app.export_pdf(hero['id']))).get_fields()
            assert fields is not None
            text = ' '.join(' '.join(str(row.get('/V', '')) for row in fields.values()).split())
            self.assertIn('Experienced character', text)
            self.assertIn('Synthetic ability fixture', text)
            hero = app.generate_resources(hero['id'], revision=hero['revision'])
            hero = app.advance(hero['id'], revision=hero['revision'], method='level', value=3)
            hero = app.select_hero_powers(hero['id'], revision=hero['revision'], selections=[POWER, OTHER])
            view = app.hero_powers_view(hero['id'])
            self.assertTrue(all(row['satisfied'] for row in view['powers'][0]['requirements']))
            self.assertFalse(any('requirement' in warning for warning in view['warnings']))
            restored = app.import_character(app.export_character(hero['id']))
            self.assertEqual(app.hero_powers_view(restored['id'])['powers'][0]['requirements'], view['powers'][0]['requirements'])
            restored = app.select_hero_powers(restored['id'], revision=restored['revision'], selections=[])
            inactive = app.hero_powers_view(restored['id'])
            self.assertFalse(inactive['receipts'][0]['active'])
            self.assertFalse(any('requirement' in warning for warning in inactive['warnings']))
            self.assertFalse(inactive['receipts'][0]['requirements'][2]['satisfied'])
            fields = PdfReader(BytesIO(app.export_pdf(restored['id']))).get_fields()
            assert fields is not None
            text = ' '.join(' '.join(str(row.get('/V', '')) for row in fields.values()).split())
            self.assertIn('Retained inactive power', text)
            self.assertIn('Companion power', text)

    def test_unselected_bad_requirement_rejects_before_dice_or_save(self):
        invalids = [None,
            [{'id': 'bad', 'name': 'Bad', 'minimum_level': True, 'source': SOURCE}],
            [{'id': 'bad', 'name': 'Bad', 'minimum_level': 2, 'source': {}}],
            [{'id': 'bad', 'name': 'Bad', 'selected_options': {'catalog': 'powers', 'selector': {'any_of': [{'ids': ['missing']}]}, 'minimum': 1}, 'source': SOURCE}],
            [{'id': 'bad', 'name': 'Bad', 'attribute_minimum': {'attribute': 'missing', 'value': 10}, 'source': SOURCE}],
            [{'id': 'bad', 'name': 'Bad', 'minimum_level': 2, 'source': SOURCE, 'callback': 'evaluate'}]]
        for requirements in invalids:
            with self.subTest(requirements=requirements), tempfile.TemporaryDirectory() as directory:
                pack = requirement_pack()
                next(row for row in pack['powers'] if row['id'] == OTHER)['requirements'] = deepcopy(requirements)
                app = CharacterApplication(directory, die=lambda sides: 4, rule_archive=archive_with(pack))
                hero = app.create(game='heroes-unlimited')
                app.die = lambda sides: self.fail('Bad requirements must preflight')
                with self.assertRaises(ValueError):
                    app.select_hero_powers(hero['id'], revision=hero['revision'], selections=[POWER])
                self.assertEqual(app.get(hero['id']), hero)

    def test_requirement_status_recomputes_after_backtracking_under_the_exact_old_pin(self):
        old = requirement_pack()
        newer = deepcopy(old)
        newer['version'] = '1.3.1'
        next(row for row in newer['powers'] if row['id'] == POWER)['requirements'][0]['minimum_level'] = 1
        with tempfile.TemporaryDirectory() as first_directory, tempfile.TemporaryDirectory() as second_directory:
            first = CharacterApplication(first_directory, die=lambda sides: 4, rule_archive=archive_with(old))
            hero = first.create(game='heroes-unlimited')
            hero = first.select_hero_powers(hero['id'], revision=hero['revision'], selections=[POWER, OTHER])
            hero = first.generate_resources(hero['id'], revision=hero['revision'])
            hero = first.advance(hero['id'], revision=hero['revision'], method='level', value=3)
            installed = archive_with(old)
            active = installed.active_versions()
            active[old['id']] = newer['version']
            second = CharacterApplication(second_directory, die=lambda sides: self.fail('Import/backtracking must not roll'),
                rule_archive=RuleArchive([*installed.definitions(), newer], active))
            restored = second.import_character(first.export_character(hero['id']))
            while restored['level'] > 1:
                restored = second.undo_advancement(restored['id'], revision=restored['revision'])['character']
            view = second.hero_powers_view(restored['id'])
            self.assertFalse(view['powers'][0]['requirements'][0]['satisfied'])
            restored = second.select_hero_powers(restored['id'], revision=restored['revision'], selections=[POWER])
            view = second.hero_powers_view(restored['id'])
            self.assertFalse(view['powers'][0]['requirements'][2]['satisfied'])
            self.assertFalse(next(row for row in view['receipts'] if row['id'] == OTHER)['active'])
            self.assertEqual(restored['additional_rule_packs'][old['id']], old['version'])

    def test_shared_boundary_accepts_other_catalog_families_and_counts_distinct_options(self):
        from characters_unlimited.ability_requirements import compile_ability_requirements, project_ability_requirements
        for family in ('spells', 'psychic-abilities'):
            with self.subTest(family=family):
                definition = {'requirements': [{'id': 'known', 'name': 'Known abilities', 'source': SOURCE,
                    'selected_options': {'catalog': family, 'selector': {'any_of': [{'categories': ['basic']}]}, 'minimum': 2}}]}
                catalogs = {family: [{'id': 'first', 'category': 'basic'}, {'id': 'second', 'category': 'basic'}]}
                compiled = compile_ability_requirements(definition, catalogs, [])
                projected = project_ability_requirements(compiled, level=1, attributes={}, selections={family: ['first', 'first']})
                self.assertEqual(projected[0]['actual'], 1)
                self.assertFalse(projected[0]['satisfied'])
                projected = project_ability_requirements(compiled, level=1, attributes={}, selections={family: ['first', 'second']})
                self.assertTrue(projected[0]['satisfied'])
