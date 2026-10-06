"""Automatic Physical grants remain tied to the character's pinned rules."""

import tempfile
import unittest
from copy import deepcopy

from characters_unlimited.application import CharacterApplication
from characters_unlimited.physical import acquire_physical, project_physical, validate_physical
from characters_unlimited.rules import RuleArchive


def granted_archive(grants=('running',)):
    archive = RuleArchive.load()
    pack = archive.active('rifts-domestic-skills')
    pack['version'] = 'physical-grant-fixture'
    pack['physical_grants'] = list(grants)
    if pack.get('class_profile_format') == 'owned-v1':
        pack['class_profiles']['vagabond']['physical_grants'] = list(grants)
    return RuleArchive([*archive.definitions(), pack],
                       {**archive.active_versions(), 'rifts-domestic-skills': pack['version']})


class AutomaticPhysicalTests(unittest.TestCase):
    def test_grant_is_acquired_on_create_and_survives_optional_running_and_reopen(self):
        with tempfile.TemporaryDirectory() as directory:
            calls = []

            def die(sides):
                calls.append(sides)
                return 2

            archive = granted_archive()
            app = CharacterApplication(directory, die=die, rule_archive=archive)
            hero = app.create(generation={'reroll_ones': True, 'extra_die': True})
            self.assertEqual(hero['physical_acquisitions']['running']['rolls'],
                             {'attribute:SPD': [2, 2, 2, 2], 'resource:SDC': [2]})
            self.assertEqual(hero['attributes']['PE']['value'], 9)
            self.assertEqual(hero['attributes']['SPD']['value'], 14)
            self.assertEqual(len([item for item in hero['attributes']['SPD']['modifiers']
                                  if item['id'] == 'physical:running']), 1)
            self.assertEqual(hero['roll_history'][0]['attributes']['SPD']['value'], 14)
            self.assertEqual(calls[-5:], [4, 4, 4, 4, 6])

            view = app.skill_view(hero['id'])
            self.assertEqual(len(view['physical']['selected']), 1)
            self.assertTrue(view['physical']['selected'][0]['grant'])
            self.assertEqual(len([item for item in view['grants'] if item['id'] == 'running']), 1)
            self.assertEqual(view['physical']['selected'][0]['effects']['attributes']['PE']['value'], 1)
            self.assertEqual(view['physical']['selected'][0]['effects']['attributes']['SPD']['value'], 8)
            self.assertEqual(view['physical']['resources'][0]['value'], 2)
            self.assertEqual(app.resource_view(hero['id'])['resources']['SDC']['contributions']['Physical: Running'], 2)

            before = len(calls)
            hero = app.select_skills(hero['id'], revision=hero['revision'],
                                     selections=[{'skill_id': 'running', 'pool': 'related'}])
            self.assertEqual(len(calls), before)
            self.assertEqual(hero['attributes']['SPD']['value'], 14)
            self.assertEqual(len(app.skill_view(hero['id'])['physical']['selected']), 1)
            hero = app.select_skills(hero['id'], revision=hero['revision'], selections=[])
            self.assertEqual(len(calls), before)
            self.assertEqual(hero['attributes']['SPD']['value'], 14)
            self.assertEqual(app.resource_view(hero['id'])['resources']['SDC']['contributions']['Physical: Running'], 2)
            bundle = app.export_character(hero['id'])
            self.assertEqual(app.import_character(bundle)['physical_acquisitions'], hero['physical_acquisitions'])
            missing = deepcopy(bundle)
            del missing['character']['physical_acquisitions']['running']
            with self.assertRaisesRegex(ValueError, 'Missing Physical skill acquisition'):
                app.import_character(missing)
            self.assertEqual(CharacterApplication(directory, rule_archive=archive).skill_view(hero['id']),
                             app.skill_view(hero['id']))

    def test_invalid_grant_and_missing_acquisition_fail_as_values_before_mutation(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides: 2, rule_archive=granted_archive(()))
            hero = app.create()
            pack = app.character_skill_pack(hero)
            for grants in ('running', [4], ['cook'], ['unknown']):
                with self.subTest(grants=grants):
                    bad_pack = {**pack, 'physical_grants': grants}
                    with self.assertRaises(ValueError):
                        acquire_physical(hero, [], bad_pack, lambda sides: 2)
                    self.assertNotIn('physical_acquisitions', app.get(hero['id']))
            bad_pack = {**pack, 'physical_grants': ['running']}
            with self.assertRaisesRegex(ValueError, 'Missing Physical skill acquisition'):
                validate_physical(hero, bad_pack)
            with self.assertRaisesRegex(ValueError, 'Missing Physical skill acquisition'):
                project_physical(hero, bad_pack)

            calls = []
            def die(sides):
                calls.append(sides)
                return 2
            duplicate_pack = {**pack, 'physical_grants': ['running', 'running']}
            changes = acquire_physical(hero, [{'skill_id': 'running', 'pool': 'related'}],
                                       duplicate_pack, die)
            granted = {**hero, **changes}
            validate_physical(granted, duplicate_pack)
            self.assertEqual(calls, [4, 4, 4, 4, 6])
            self.assertEqual(len(project_physical(granted, duplicate_pack)['selected']), 1)
            self.assertTrue(project_physical(granted, duplicate_pack)['selected'][0]['grant'])


if __name__ == '__main__':
    unittest.main()
