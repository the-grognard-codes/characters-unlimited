import copy
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from characters_unlimited.application import CharacterApplication


class PortableCharacterWorkflowTests(unittest.TestCase):
    def test_untouched_character_exports_every_pack_used_by_its_projection(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides: 4)
            character = app.create()
            bundle = app.export_character(character['id'])
            self.assertEqual({pack['id'] for pack in bundle['rule_packs']}, {'rifts-core', 'rifts-domestic-skills'})

    def test_failed_backup_publication_preserves_the_previous_backup_and_save(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides: 4)
            character = app.create()
            previous = Path(app.backup()['path'])
            contents = previous.read_bytes()
            with patch('characters_unlimited.storage.os.replace', side_effect=OSError('Interrupted publication')):
                with self.assertRaises(OSError):
                    app.backup()
            self.assertEqual(previous.read_bytes(), contents)
            self.assertEqual(app.get(character['id']), character)
            self.assertEqual(list(previous.parent.glob('*.tmp')), [])

    def test_offline_export_import_preserves_values_history_and_exact_rules(self):
        with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
            origin = CharacterApplication(first, die=lambda sides: 4)
            character = origin.create(name='Road Scholar', notes='A portable story')
            character = origin.set_attribute(character['id'], revision=0, attribute='IQ', mode='fixed', value=20)
            character = origin.select_skills(character['id'], revision=1, selections=[{'skill_id':'dance', 'pool':'domestic'}])
            bundle = origin.export_character(character['id'])
            imported = CharacterApplication(second).import_character(bundle)
            self.assertNotEqual(imported['id'], character['id'])
            for field in ['name', 'notes', 'attributes', 'roll_history', 'rules', 'additional_rule_packs', 'skill_selections']:
                self.assertEqual(imported[field], character[field])
            self.assertEqual(imported['revision'], 0)
            self.assertEqual(len(bundle['rule_packs']), 2)

    def test_duplicate_is_independent_and_does_not_modify_original(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides: 4)
            original = app.create(name='Original')
            duplicate = app.duplicate(original['id'])
            app.edit(duplicate['id'], revision=0, notes='Different story')
            self.assertEqual(app.get(original['id']), original)
            self.assertEqual(len(app.list()), 2)

    def test_rejected_imports_leave_saved_characters_intact(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides: 4)
            character = app.create()
            bundle = app.export_character(character['id'])
            cases = [None, {}, {'format': 'unknown'}]
            modified = copy.deepcopy(bundle)
            modified['rule_packs'][0]['version'] = '999.0'
            cases.append(modified)
            for field, value in [('value', 999), ('base', 999), ('rolls', [9, 1, 2])]:
                modified = copy.deepcopy(bundle)
                modified['character']['attributes']['IQ'][field] = value
                cases.append(modified)
            modified = copy.deepcopy(bundle)
            modified['character']['attributes']['IQ']['explanation']['source']['book'] = 'Other Book'
            cases.append(modified)
            modified = copy.deepcopy(bundle)
            del modified['character']['attributes']['IQ']['bonus_rolls']
            cases.append(modified)
            modified = copy.deepcopy(bundle)
            modified['character']['attributes']['IQ']['rolls'] = 'bad'
            cases.append(modified)
            modified = copy.deepcopy(bundle)
            next(pack for pack in modified['rule_packs'] if pack['id'] == 'rifts-core')['races'][0]['attributes']['count'] = 100
            cases.append(modified)
            for value in cases:
                with self.assertRaises(ValueError):
                    app.import_character(value)
            self.assertEqual(app.list(), [character])

    def test_backup_is_a_consistent_database_that_can_reopen(self):
        with tempfile.TemporaryDirectory() as directory, tempfile.TemporaryDirectory() as restore:
            app = CharacterApplication(directory, die=lambda sides: 4)
            character = app.create(name='Backed up')
            backup = app.backup()
            Path(restore, 'characters.sqlite3').write_bytes(Path(backup['path']).read_bytes())
            self.assertEqual(CharacterApplication(restore).get(character['id']), character)
