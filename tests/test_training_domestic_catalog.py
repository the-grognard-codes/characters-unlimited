import tempfile
import unittest
from copy import deepcopy
from io import BytesIO

from pypdf import PdfReader

from characters_unlimited.application import CharacterApplication
from characters_unlimited.rules import RuleArchive


def choices(*identifiers):
    return [{'skill_id': identifier, 'pool': 'related'} for identifier in identifiers]


def row(view, identifier):
    return next(item for item in [*view['selected'], *view['grants']] if item['id'] == identifier)


def candidate(change):
    installed = RuleArchive.load()
    pack = deepcopy(installed.active('rifts-domestic-skills'))
    pack['version'] = '9.99.0'
    change(pack)
    return RuleArchive(installed.definitions() + [pack], {**installed.active_versions(), pack['id']: pack['version']})


class TrainingDomesticCatalogTests(unittest.TestCase):
    def test_training_is_counted_source_visible_and_never_percentile_or_physical(self):
        with tempfile.TemporaryDirectory() as directory:
            draws = []
            def die(sides):
                draws.append(sides)
                return 4
            app = CharacterApplication(directory, die=die)
            hero = app.create()
            original = deepcopy(hero['attributes'])
            count = len(draws)
            before = app.skill_view(hero['id'])['remaining']['related']
            hero = app.select_skills(hero['id'], revision=0, selections=choices('hunting', 'sniper'))
            view = app.skill_view(hero['id'])
            self.assertEqual(view['remaining']['related'], before - 2)
            for identifier in ('hunting', 'sniper'):
                skill = row(view, identifier)
                self.assertEqual(skill['kind'], 'training')
                self.assertTrue(skill['source']['pages'])
                for field in ('percentage', 'base', 'per_level', 'effects', 'contributions'):
                    self.assertNotIn(field, skill)
            self.assertEqual(hero['attributes'], original)
            self.assertEqual(len(draws), count)
            self.assertNotIn('sniper', app.combat_view(hero['id'])['totals']['strike']['contributions'])

    def test_hunting_synergies_apply_once_and_cooking_is_contextual(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides: 4)
            hero = app.create()
            targets = ('prowl', 'track-trap-animals', 'skin-prepare-hides', 'imitate-voices')
            hero = app.select_skills(hero['id'], revision=0, selections=choices(*targets))
            before = app.skill_view(hero['id'])
            hero = app.select_skills(hero['id'], revision=hero['revision'], selections=choices(*targets, 'hunting', 'hunting'))
            after = app.skill_view(hero['id'])
            for identifier, bonus in zip(targets, (2, 5, 5, 4)):
                self.assertEqual(row(after, identifier)['percentage'], row(before, identifier)['percentage'] + bonus)
                self.assertEqual(row(after, identifier)['contributions']['Hunting'], bonus)
            cook = row(after, 'cook')
            self.assertEqual(cook['percentage'], row(before, 'cook')['percentage'])
            self.assertEqual(cook['additional_checks'][0]['percentage'], cook['percentage'] + 10)
            hero = app.select_skills(hero['id'], revision=hero['revision'], selections=choices(*targets))
            self.assertEqual(row(app.skill_view(hero['id']), 'cook')['additional_checks'], [])
            self.assertEqual(row(app.skill_view(hero['id']), 'prowl')['percentage'], row(before, 'prowl')['percentage'])

    def test_brewing_rates_repeat_bonus_and_distinct_medicine_synergies(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides: 4)
            hero = app.create(level=3)
            hero = app.select_skills(hero['id'], revision=0, selections=choices('brewing-basic', 'holistic-medicine'))
            before = app.skill_view(hero['id'])
            brew = row(before, 'brewing-basic')
            self.assertEqual((brew['percentage'], brew['additional_checks'][0]['percentage']), (35, 40))
            hero = app.select_skills(hero['id'], revision=hero['revision'], selections=choices('brewing-basic', 'brewing-basic', 'brewing-basic', 'brewing-medicinal', 'holistic-medicine'))
            after = app.skill_view(hero['id'])
            self.assertEqual((row(after, 'brewing-basic')['percentage'], row(after, 'brewing-basic')['additional_checks'][0]['percentage']), (45, 50))
            self.assertEqual(row(after, 'holistic-medicine')['percentage'], row(before, 'holistic-medicine')['percentage'] + 5)
            hero = app.set_attribute(hero['id'], revision=hero['revision'], attribute='IQ', mode='fixed', value=16)
            self.assertEqual(row(app.skill_view(hero['id']), 'brewing-basic')['percentage'], 47)

    def test_wardrobe_has_normal_growth_synergies_and_only_contextual_beauty(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides: 4)
            hero = app.create(level=3)
            targets = ('disguise', 'impersonation', 'performance', 'undercover-ops', 'seduction')
            hero = app.select_skills(hero['id'], revision=0, selections=choices(*targets))
            original = hero['attributes']['PB']['value']
            before = app.skill_view(hero['id'])
            hero = app.select_skills(hero['id'], revision=hero['revision'], selections=choices(*targets, 'wardrobe-grooming', 'wardrobe-grooming'))
            after = app.skill_view(hero['id'])
            self.assertEqual(row(after, 'wardrobe-grooming')['percentage'], 70)
            hero = app.advance(hero['id'], revision=hero['revision'], method='level', value=4)
            self.assertEqual(row(app.skill_view(hero['id']), 'wardrobe-grooming')['percentage'], 74)
            for identifier in targets:
                self.assertEqual(row(after, identifier)['percentage'], row(before, identifier)['percentage'] + 2)
            self.assertEqual(hero['attributes']['PB']['value'], original)

    def test_cooking_context_caps_after_normal_proficiency_and_undo_is_portable(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides: 4)
            hero = app.create(level=3)
            hero = app.select_skills(hero['id'], revision=0, selections=choices('hunting', 'cook'))
            hero = app.advance(hero['id'], revision=hero['revision'], method='level', value=15)
            cook = row(app.skill_view(hero['id']), 'cook')
            self.assertEqual((cook['percentage'], cook['additional_checks'][0]['percentage'], cook['additional_checks'][0]['uncapped_percentage']), (98, 98, 108))
            hero = app.undo_advancement(hero['id'], revision=hero['revision'])['character']
            imported = app.import_character(app.export_character(hero['id']))
            app = CharacterApplication(directory)
            self.assertEqual(app.skill_view(imported['id'])['selected'], app.skill_view(hero['id'])['selected'])

    def test_required_training_grants_and_choices_share_identity_with_optional_training(self):
        def change(pack):
            hunting = next(item for item in pack['skills'] if item['id'] == 'hunting')
            grant = {'id': 'required-hunting', 'name': 'Required Hunting', 'kind': 'training', 'catalog_skill_id': 'hunting', 'source': hunting['source']}
            owner = pack['class_profiles']['vagabond'] if pack.get('class_profile_format') == 'owned-v1' else pack
            owner['required']['grants'].append(grant)
            owner['required']['groups'].append({'id': 'training', 'name': 'Training', 'kind': 'select', 'count': 1, 'options': [grant]})
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides: 4, rule_archive=candidate(change))
            hero = app.create()
            hero = app.select_required_skills(hero['id'], revision=0, choices={'training':'required-hunting'})
            view = app.skill_view(hero['id'])
            self.assertEqual(view['required_remaining']['training'], 0)
            self.assertEqual(len([item for item in view['grants'] if item['id']=='hunting']), 1)
            self.assertNotIn('percentage', row(view, 'hunting'))
            self.assertEqual(row(view, 'cook')['additional_checks'][0]['percentage'], 60)
            hero = app.select_skills(hero['id'], revision=hero['revision'], selections=choices('hunting', 'prowl'))
            self.assertEqual(row(app.skill_view(hero['id']), 'prowl')['contributions']['Hunting'], 2)

    def test_invalid_training_and_context_declarations_fail_before_dice_for_every_owner(self):
        for field, value in [('base', 0), ('effects', {}), ('source', {}), ('prerequisites', [['unknown']]), ('requires_specialty', True)]:
            def change(pack):
                next(item for item in pack['skills'] if item['id'] == 'hunting')[field] = value
            with self.subTest(field=field), tempfile.TemporaryDirectory() as directory:
                draws = []
                def die(sides):
                    draws.append(sides)
                    return 4
                app = CharacterApplication(directory, die=die, rule_archive=candidate(change))
                with self.assertRaises(ValueError):
                    app.create(character_class='city-rat')
                self.assertEqual(draws, [])
        for change_check in ({'modifier': True}, {'context_of': 'unknown'}, {'maximum': -1}, {'requires_skill': 'unknown'}, {'base': 50}):
            def change(pack):
                next(item for item in pack['skills'] if item['id'] == 'cook')['additional_checks'][-1].update(change_check)
            with self.subTest(check=change_check), tempfile.TemporaryDirectory() as directory:
                draws = []
                def die(sides):
                    draws.append(sides)
                    return 4
                app = CharacterApplication(directory, die=die, rule_archive=candidate(change))
                with self.assertRaises(ValueError):
                    app.create(character_class='city-rat')
                self.assertEqual(draws, [])

    def test_old_pin_requires_explicit_upgrade_and_editable_pdf_retains_training_notes(self):
        installed = RuleArchive.load()
        old = RuleArchive(installed.definitions(), {**installed.active_versions(), 'rifts-domestic-skills': '2.22.0'})
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides: 4, rule_archive=old)
            hero = app.create()
            app = CharacterApplication(directory)
            self.assertEqual(len(app.skill_view(hero['id'])['catalog']), 202)
            with self.assertRaises(ValueError):
                app.select_skills(hero['id'], revision=0, selections=choices('hunting'))
            preview = app.preview_rule_upgrade(hero['id'])
            hero = app.apply_rule_upgrade(hero['id'], revision=0, token=preview['token'])['character']
            self.assertEqual(len(app.skill_view(hero['id'])['catalog']), 213)
            hero = app.select_skills(hero['id'], revision=hero['revision'], selections=choices('hunting', 'sniper', 'brewing-basic', 'wardrobe-grooming'))
            hero = app.generate_resources(hero['id'], revision=hero['revision'])
            fields = PdfReader(BytesIO(app.export_pdf(hero['id']))).get_fields() or {}
            text = '\n'.join(str(item.get('/V', '')) for item in fields.values())
            for expected in ('Hunting', 'Sniper', 'Cook game animals', 'Quality of brew', 'single-shot', 'dressed to impress'):
                self.assertIn(expected, text)
