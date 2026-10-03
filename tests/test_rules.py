import copy
import json
import tempfile
import unittest
from pathlib import Path

from characters_unlimited.application import CharacterApplication
from characters_unlimited.rules import RuleArchive


class AcceptedRuleWorkflowTests(unittest.TestCase):
    def test_changed_accepted_definition_is_rejected_before_application_opens(self):
        source = Path(__file__).resolve().parents[1] / 'characters_unlimited' / 'packs'
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in ('accepted.json', 'rifts-core.json', 'rifts-domestic-skills.json'):
                (root / name).write_bytes((source / name).read_bytes())
            modified = json.loads((root / 'rifts-core.json').read_text(encoding='utf-8'))
            modified['races'][0]['attributes']['count'] = 4
            (root / 'rifts-core.json').write_text(json.dumps(modified), encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'Accepted rule content changed'):
                RuleArchive.load(root)
            manifest = json.loads((root / 'accepted.json').read_text(encoding='utf-8'))
            manifest['definitions'][0]['filename'] = '../outside.json'
            (root / 'accepted.json').write_text(json.dumps(manifest), encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'inside the pack directory'):
                RuleArchive.load(root)

    def test_saved_projection_and_new_selections_use_the_pinned_accepted_version(self):
        installed = RuleArchive.load()
        old_skills = installed.resolve('rifts-domestic-skills', '1.0.0')
        old_skills['version'] = '0.9.0'
        old_skills['skills'][0]['base'] = 25
        archive = RuleArchive([*installed.definitions(), old_skills], installed.active_versions())
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides: 4, rule_archive=archive)
            character = app.create()
            character['additional_rule_packs']['rifts-domestic-skills'] = '0.9.0'
            app.store.put(character)
            self.assertEqual(app.skill_view(character['id'])['grants'][0]['percentage'], 40)
            selected = app.select_skills(character['id'], revision=0, selections=[{'skill_id': 'cook', 'pool': 'secondary'}])
            self.assertEqual(selected['additional_rule_packs']['rifts-domestic-skills'], '0.9.0')
            self.assertEqual(app.skill_view(character['id'])['grants'][0]['percentage'], 50)
            bundle = app.export_character(character['id'])
            self.assertEqual(next(pack for pack in bundle['rule_packs'] if pack['id'] == 'rifts-domestic-skills'), old_skills)
            with tempfile.TemporaryDirectory() as other:
                imported = CharacterApplication(other, rule_archive=archive).import_character(bundle)
                self.assertEqual(imported['additional_rule_packs'], selected['additional_rule_packs'])

    def test_archive_definitions_cannot_be_changed_through_caller_owned_objects(self):
        installed = RuleArchive.load()
        definitions = installed.definitions()
        archive = RuleArchive(definitions, installed.active_versions())
        definitions[0]['version'] = 'changed'
        returned = archive.resolve('rifts-core', '1.0.0')
        returned['races'].clear()
        self.assertEqual(len(archive.resolve('rifts-core', '1.0.0')['races']), 1)
        conflicting = copy.deepcopy(installed.definitions())
        changed = copy.deepcopy(conflicting[0])
        changed['edition'] = 'Changed edition'
        with self.assertRaises(ValueError):
            RuleArchive([*conflicting, changed], installed.active_versions())

    def test_unavailable_version_does_not_silently_substitute_current_rules(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides: 4)
            character = app.create()
            character['rules']['version'] = '999.0.0'
            app.store.put(character)
            with self.assertRaisesRegex(ValueError, 'Unsupported rule version'):
                app.skill_view(character['id'])
            self.assertEqual(app.store.get(character['id']), character)

    def test_rerolls_use_the_pinned_core_source_instead_of_the_active_source(self):
        installed = RuleArchive.load()
        old = installed.resolve('rifts-core', '1.0.0')
        old['version'] = '0.9.0'
        old['source']['section'] = 'Previously accepted attribute source'
        versions = installed.active_versions()
        versions['rifts-core'] = '0.9.0'
        earlier = RuleArchive([*installed.definitions(), old], versions)
        with tempfile.TemporaryDirectory() as directory:
            original = CharacterApplication(directory, die=lambda sides: 4, rule_archive=earlier).create()
            later = CharacterApplication(directory, die=lambda sides: 3,
                rule_archive=RuleArchive(earlier.definitions(), installed.active_versions()))
            rerolled = later.reroll(original['id'], revision=0, attribute='IQ')
            self.assertEqual(rerolled['rules'], original['rules'])
            self.assertEqual(rerolled['attributes']['IQ']['explanation']['source'], old['source'])
            self.assertEqual(next(pack for pack in later.export_character(original['id'])['rule_packs'] if pack['id'] == 'rifts-core'), old)
