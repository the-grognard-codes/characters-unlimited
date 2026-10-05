from copy import deepcopy
import tempfile
import unittest
from characters_unlimited.application import CharacterApplication
from tests.test_owned_class_profiles import owned_pack, archive_with


def recording_die(calls: list[int]):
    def die(sides):
        calls.append(sides)
        return 4
    return die


class ClassMechanicalPreflightTests(unittest.TestCase):
    def test_unselected_owned_resource_formula_rejects_before_initial_attributes(self):
        pack = owned_pack()
        profile = pack['class_profiles']['city-rat']
        profile['resources']['definitions'][0]['contributions'][1]['formula']['count'] = True
        with tempfile.TemporaryDirectory() as directory:
            calls: list[int] = []
            app = CharacterApplication(directory, die=recording_die(calls), rule_archive=archive_with(pack))
            with self.assertRaisesRegex(ValueError, 'city-rat.*resources'):
                app.create(character_class='vagabond')
            self.assertEqual(calls, [])
            self.assertEqual(app.list(), [])

    def test_unselected_nested_components_and_shared_catalogs_preflight_before_dice(self):
        source = {'book': 'Synthetic preflight fixture', 'section': 'Owned mechanical components'}
        from characters_unlimited.recorded_formulas import MAX_INTEGER
        cases = [
            ('resources', lambda profile: profile['resources']['definitions'].append(deepcopy(profile['resources']['definitions'][0]))),
            ('resources', lambda profile: profile['resources']['definitions'][0]['contributions'][0].update(source={})),
            ('skills', lambda profile: profile['pools']['related'].update(count=True)),
            ('skills', lambda profile: profile['selection_rules']['related']['medical'].update(costs={'missing': 2})),
            ('skills', lambda profile: profile.update(fixed_domestic_grants=[{'id': 'missing', 'bonus': 5}])),
            ('skills', lambda profile: profile.update(skill_effects=[{'id': 'bad', 'name': 'Bad', 'operation': 'add', 'amount': 1,
                'selector': {'any_of': [{'ids': ['missing']}]}, 'source': source}])),
            ('skills', lambda profile: profile['selection_rules']['related']['medical'].update(callback='execute')),
            ('physical', lambda profile: profile.update(physical_grants=['missing'])),
            ('advancement', lambda profile: profile['advancement'].update(resource_gains={'missing': {
                'formula': {'count': 0, 'sides': 0, 'constant': 1}, 'source': source}})),
            ('higher_advancement', lambda profile: profile['higher_advancement'].update(hp_die=True)),
            ('higher_advancement', lambda profile: profile['higher_advancement']['xp_ranges'][1].__setitem__(0, 999)),
            ('advancement', lambda profile: profile['advancement'].update(resource_gains={'HP': {
                'formula': {'count': 1, 'sides': 6, 'constant': MAX_INTEGER - 1}, 'source': source}}))]
        for field, mutate in cases:
            with self.subTest(field=field), tempfile.TemporaryDirectory() as directory:
                pack = owned_pack()
                mutate(pack['class_profiles']['city-rat'])
                calls: list[int] = []
                app = CharacterApplication(directory, die=recording_die(calls), rule_archive=archive_with(pack))
                with self.assertRaisesRegex(ValueError, 'city-rat.*' + field):
                    app.create(character_class='vagabond')
                self.assertEqual(calls, [])
                self.assertEqual(app.list(), [])

    def test_resolved_shared_resource_catalog_validates_for_every_owner(self):
        pack = owned_pack()
        resources = deepcopy(pack['class_profiles']['vagabond']['resources'])
        resources['definitions'][0]['contributions'][1]['formula']['count'] = True
        pack['profile_catalogs'] = {'resources': {'field': 'resources', 'value': resources,
            'source': {'book': 'Synthetic shared fixture', 'section': 'Shared resource catalog'}}}
        pack['class_profiles']['city-rat']['resources'] = {'catalog_ref': 'resources', 'values': {}}
        with tempfile.TemporaryDirectory() as directory:
            calls: list[int] = []
            app = CharacterApplication(directory, die=recording_die(calls), rule_archive=archive_with(pack))
            with self.assertRaisesRegex(ValueError, 'city-rat.*resources'):
                app.create(character_class='vagabond')
            self.assertEqual(calls, [])
            self.assertEqual(app.list(), [])
