from copy import deepcopy
import tempfile
import unittest
from characters_unlimited.application import CharacterApplication
from tests.test_owned_class_profiles import owned_pack, archive_with


SOURCE = {'book': 'Synthetic composition fixture', 'section': 'Shared combat catalog'}


def catalog_pack():
    pack = owned_pack()
    shared_keys = {'hand_to_hand', 'ancient', 'modern', 'pp_bonuses', 'source', 'conditions_source'}
    common = {key: deepcopy(pack['combat'][key]) for key in shared_keys}
    pack['profile_catalogs'] = {'common-combat': {'field': 'combat', 'value': common, 'source': SOURCE}}
    for profile in pack['class_profiles'].values():
        choices = {key: value for key, value in profile['combat'].items() if key not in shared_keys}
        profile['combat'] = {'catalog_ref': 'common-combat', 'values': choices}
    return pack


class SharedProfileCatalogTests(unittest.TestCase):
    def test_distinct_owned_classes_reuse_one_catalog_and_reopen_exactly(self):
        pack = catalog_pack()
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides: 4, rule_archive=archive_with(pack))
            for identity, remaining in [('vagabond', {'ancient': 1, 'modern': 1}),
                                         ('city-rat', {'proficiencies': 1})]:
                with self.subTest(identity=identity):
                    hero = app.create(character_class=identity)
                    view = app.combat_view(hero['id'])
                    self.assertEqual(view['remaining'], remaining)
                    self.assertEqual(view['choices']['hand_to_hand'], 'basic')
                    hero = app.select_combat(hero['id'], revision=hero['revision'],
                                            choices={'hand_to_hand': 'expert', 'ancient': ['knife']})
                    view = app.combat_view(hero['id'])
                    self.assertEqual(view['choices']['hand_to_hand'], 'expert')
                    self.assertEqual(next(row for row in view['melee'] if row['id'] == 'knife')['strike']['value'], 0)
                    bundle = app.export_character(hero['id'])
                    app.die = lambda sides: self.fail('Reopening must retain acquired dice')
                    reopened = app.import_character(bundle)
                    self.assertEqual(app.combat_view(reopened['id'])['totals'], view['totals'])
                    app.die = lambda sides: 4

    def test_unselected_or_orphaned_reference_errors_reject_before_dice(self):
        for kind in ['missing', 'field', 'collision', 'shape', 'recursive', 'source', 'orphan']:
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as directory:
                pack = catalog_pack()
                reference = pack['class_profiles']['city-rat']['combat']
                catalog = pack['profile_catalogs']['common-combat']
                if kind == 'missing':
                    reference['catalog_ref'] = 'missing'
                elif kind == 'field':
                    catalog['field'] = 'resources'
                elif kind == 'collision':
                    reference['values']['ancient'] = []
                elif kind == 'shape':
                    reference['callback'] = 'execute prose'
                elif kind == 'recursive':
                    catalog['value']['catalog_ref'] = 'common-combat'
                elif kind == 'source':
                    catalog['source'] = {}
                else:
                    pack['profile_catalogs']['unused'] = {'field': 'combat', 'value': {}, 'source': {}}
                app = CharacterApplication(directory, die=lambda sides: self.fail('Invalid reference must preflight'),
                                           rule_archive=archive_with(pack))
                with self.assertRaises(ValueError):
                    app.create()
                self.assertEqual(app.list(), [])

    def test_advancement_references_validate_resolved_class_owners_and_resource_growth(self):
        pack = owned_pack()
        common = deepcopy(pack['class_profiles']['vagabond']['advancement'])
        del common['class_id']
        pack['profile_catalogs'] = {'shared-progression': {
            'field': 'advancement', 'value': common, 'source': SOURCE}}
        for identity, profile in pack['class_profiles'].items():
            profile['advancement'] = {'catalog_ref': 'shared-progression', 'values': {
                'class_id': identity, 'resource_gains': {'HP': {
                    'formula': {'count': 0, 'sides': 0, 'constant': 7}, 'source': SOURCE}}}}
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides: 4, rule_archive=archive_with(pack))
            for identity, expected in [('vagabond', 29), ('city-rat', 28)]:
                with self.subTest(identity=identity):
                    hero = app.create(character_class=identity)
                    hero = app.generate_resources(hero['id'], revision=hero['revision'])
                    hero = app.advance(hero['id'], revision=hero['revision'], method='level', value=2)
                    self.assertEqual(app.resource_view(hero['id'])['resources']['HP']['value'], expected)
                    reopened = app.import_character(app.export_character(hero['id']))
                    self.assertEqual(app.resource_view(reopened['id'])['resources']['HP']['value'], expected)
