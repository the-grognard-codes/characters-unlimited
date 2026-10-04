from copy import deepcopy
import tempfile
import unittest
from characters_unlimited.application import CharacterApplication
from characters_unlimited.rules import RuleArchive


FIELDS = ('name', 'path_name', 'source', 'pools', 'required', 'selection_rules',
          'combat', 'class_bonuses', 'resources', 'advancement', 'higher_advancement',
          'physical_grants', 'fixed_domestic_grants', 'path_guidance', 'skill_effects')


def owned_pack():
    pack = RuleArchive.load().active('rifts-domestic-skills')
    defaults = {'path_name': 'Human Vagabond', 'physical_grants': [],
                'fixed_domestic_grants': [], 'path_guidance': [], 'skill_effects': []}
    default_profile = {field: deepcopy(pack.get(field, defaults.get(field))) for field in FIELDS}
    other_profile = {**deepcopy(default_profile), **pack['class_profiles']['city-rat']}
    pack['class_profile_format'] = 'owned-v1'
    pack['class_profiles'] = {'vagabond': default_profile, 'city-rat': other_profile}
    return pack


def archive_with(pack):
    installed = RuleArchive.load()
    return RuleArchive([pack if row['id'] == pack['id'] and row['version'] == pack['version'] else row
                        for row in installed.definitions()], installed.active_versions())


class OwnedClassProfileTests(unittest.TestCase):
    def test_incomplete_unselected_profile_rejects_before_initial_dice(self):
        pack = owned_pack()
        del pack['class_profiles']['city-rat']['pools']
        with tempfile.TemporaryDirectory() as directory:
            calls = []
            def die(sides):
                calls.append(sides)
                return 4
            app = CharacterApplication(directory, die=die, rule_archive=archive_with(pack))
            with self.assertRaisesRegex(ValueError, 'city-rat.*pools'):
                app.create()
            self.assertEqual(calls, [])
            self.assertEqual(app.list(), [])

    def test_profiles_own_skills_resources_and_growth_despite_poisoned_root_mechanics(self):
        pack = owned_pack()
        source = {'book': 'Synthetic ownership fixture', 'section': 'Independent resource growth'}
        pack['class_profiles']['vagabond']['pools']['related']['count'] = 2
        pack['class_profiles']['vagabond']['pools']['secondary']['count'] = 1
        for identifier, gain in [('vagabond', 5), ('city-rat', 9)]:
            profile = pack['class_profiles'][identifier]
            profile['resources']['definitions'].append({'id': 'PPE', 'name': 'Synthetic P.P.E.', 'contributions': [
                {'id': 'initial', 'formula': {'count': 0, 'sides': 0, 'bonus': 10}, 'source': source}]})
            profile['advancement']['resource_gains'] = {'PPE': {
                'formula': {'count': 0, 'sides': 0, 'constant': gain}, 'source': source}}
        pack['pools']['related']['count'] = 99
        pack['physical_grants'] = ['not-a-real-skill']
        pack['resources'] = {}
        pack['advancement'] = {}
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides: 4, rule_archive=archive_with(pack))
            for identifier, count, pe, hp, ppe in [('vagabond', 2, 14, 22, 15), ('city-rat', 10, 13, 21, 19)]:
                with self.subTest(identifier=identifier):
                    hero = app.create(character_class=identifier)
                    self.assertEqual(app.skill_view(hero['id'])['remaining']['related'], count)
                    self.assertEqual(hero['attributes']['PE']['value'], pe)
                    hero = app.generate_resources(hero['id'], revision=hero['revision'])
                    hero = app.advance(hero['id'], revision=hero['revision'], method='level', value=2)
                    resources = app.resource_view(hero['id'])['resources']
                    self.assertEqual(resources['HP']['value'], hp)
                    self.assertEqual(resources['PPE']['value'], ppe)
                    bundle = app.export_character(hero['id'])
                    app.die = lambda sides: self.fail('Portable reopening must use retained rolls')
                    reopened = app.import_character(bundle)
                    self.assertEqual(app.resource_view(reopened['id'])['resources']['PPE']['value'], ppe)
                    app.die = lambda sides: 4

    def test_unknown_format_shape_or_profile_owner_rejects_before_generation(self):
        invalids = [('format', None), ('format', 'unknown'), ('default', None),
                    ('extra', None), ('kind', None), ('owner', None)]
        for kind, value in invalids:
            with self.subTest(kind=kind, value=value), tempfile.TemporaryDirectory() as directory:
                pack = owned_pack()
                profile = pack['class_profiles']['city-rat']
                if kind == 'format':
                    pack['class_profile_format'] = value
                elif kind == 'default':
                    del pack['class_profiles']['vagabond']
                elif kind == 'extra':
                    profile['callback'] = 'execute prose'
                elif kind == 'kind':
                    profile['resources'] = []
                else:
                    profile['advancement']['class_id'] = 'vagabond'
                app = CharacterApplication(directory, die=lambda sides: self.fail('Invalid profile must preflight'),
                                           rule_archive=archive_with(pack))
                with self.assertRaises(ValueError):
                    app.create()
                self.assertEqual(app.list(), [])
