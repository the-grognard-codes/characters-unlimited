import sqlite3
from contextlib import closing
import tempfile
import unittest
from unittest.mock import patch

from characters_unlimited.application import CharacterApplication, SaveConflict
from characters_unlimited.rules import RuleArchive
from characters_unlimited.storage import CharacterStore


class SkillRuleUpgradeWorkflowTests(unittest.TestCase):
    def older_application(self, directory):
        archive = RuleArchive.load()
        active = archive.active_versions()
        active['rifts-domestic-skills'] = '1.0.0'
        return CharacterApplication(directory, die=lambda sides: 4,
            rule_archive=RuleArchive(archive.definitions(), active))

    def test_preview_is_read_only_and_applying_keeps_an_exact_pre_upgrade_backup(self):
        with tempfile.TemporaryDirectory() as directory:
            earlier = self.older_application(directory)
            character = earlier.create()
            character = earlier.set_attribute(character['id'], revision=0, attribute='IQ', mode='fixed', value=16)
            current = CharacterApplication(directory)
            self.assertEqual(current.skill_view(character['id'])['grants'][0]['percentage'], 50)
            preview = current.preview_rule_upgrade(character['id'])
            self.assertEqual(preview['changes'], [{'pack_id': 'rifts-domestic-skills', 'from': '1.0.0', 'to': '2.6.0'}])
            self.assertEqual(preview['skills'][0]['before'], 50)
            self.assertEqual(preview['skills'][0]['after'], 52)
            self.assertEqual(current.get(character['id']), character)
            result = current.apply_rule_upgrade(character['id'], revision=1, token=preview['token'])
            self.assertEqual(current.skill_view(character['id'])['grants'][0]['percentage'], 52)
            self.assertEqual(result['character']['attributes'], character['attributes'])
            with closing(sqlite3.connect(result['backup']['path'])) as backup:
                with current.store.connect() as live:
                    before = backup.execute('SELECT document FROM characters WHERE id=?', (character['id'],)).fetchone()[0]
                    after = live.execute('SELECT document FROM characters WHERE id=?', (character['id'],)).fetchone()[0]
                    self.assertNotEqual(before, after)
            with tempfile.TemporaryDirectory() as target:
                restored = CharacterStore(target)
                with closing(sqlite3.connect(result['backup']['path'])) as source:
                    with restored.connect() as destination:
                        source.backup(destination)
                self.assertEqual(restored.get(character['id']), character)
            with tempfile.TemporaryDirectory() as destination:
                imported = CharacterApplication(destination).import_character(current.export_character(character['id']))
                self.assertEqual(imported['additional_rule_packs']['rifts-domestic-skills'], '2.6.0')

    def test_stale_tampered_or_failed_upgrade_preserves_the_save(self):
        with tempfile.TemporaryDirectory() as directory:
            earlier = self.older_application(directory)
            character = earlier.create()
            current = CharacterApplication(directory)
            preview = current.preview_rule_upgrade(character['id'])
            with self.assertRaises(ValueError):
                current.apply_rule_upgrade(character['id'], revision=0, token='tampered')
            with patch.object(current.store, 'backup', side_effect=OSError('Interrupted backup')):
                with self.assertRaises(OSError):
                    current.apply_rule_upgrade(character['id'], revision=0, token=preview['token'])
            self.assertEqual(current.get(character['id']), character)
            changed = current.edit(character['id'], revision=0, notes='New work')
            with self.assertRaises(SaveConflict):
                current.apply_rule_upgrade(character['id'], revision=0, token=preview['token'])
            self.assertEqual(current.get(character['id']), changed)

    def test_interrupted_database_update_keeps_previous_rules(self):
        with tempfile.TemporaryDirectory() as directory:
            character = self.older_application(directory).create()
            current = CharacterApplication(directory)
            preview = current.preview_rule_upgrade(character['id'])
            with current.store.connect() as connection:
                connection.execute("CREATE TRIGGER interrupt_upgrade BEFORE UPDATE ON characters BEGIN SELECT RAISE(ABORT, 'Interrupted update'); END")
            with self.assertRaises(sqlite3.IntegrityError):
                current.apply_rule_upgrade(character['id'], revision=0, token=preview['token'])
            self.assertEqual(current.get(character['id']), character)

    def test_iq_bonus_uses_effective_attribute_and_applies_once_in_each_skill_pool(self):
        with tempfile.TemporaryDirectory() as directory:
            current = CharacterApplication(directory, die=lambda sides: 4)
            character = current.create()
            character = current.select_skills(character['id'], revision=0, selections=[
                {'skill_id': 'dance', 'pool': 'domestic'}, {'skill_id': 'fishing', 'pool': 'related'},
                {'skill_id': 'sewing', 'pool': 'secondary'}])
            for value, bonus in [(15, 0), (16, 2), (20, 6), (30, 16), (34, 16), (35, 18), (40, 20), (1000, 404)]:
                character = current.set_attribute(character['id'], revision=character['revision'], attribute='IQ', mode='fixed', value=value)
                view = current.skill_view(character['id'])
                self.assertEqual(view['grants'][0]['percentage'], min(98, 50 + bonus))
                self.assertEqual(view['grants'][0]['uncapped_percentage'], 50 + bonus)
                self.assertEqual([skill['percentage'] for skill in view['selected']], [min(98, base + bonus) for base in (45, 50, 40)])
                self.assertEqual([skill['uncapped_percentage'] for skill in view['selected']], [base + bonus for base in (45, 50, 40)])
                self.assertEqual(view['grants'][0]['contributions']['intelligence'], bonus)
            character = current.set_attribute(character['id'], revision=character['revision'], attribute='IQ', mode='adjustment', value=8)
            character = current.select_skills(character['id'], revision=character['revision'], selections=[{'skill_id': 'cook', 'pool': 'secondary'}])
            view = current.skill_view(character['id'])
            self.assertEqual(character['attributes']['IQ']['value'], 20)
            self.assertEqual(view['grants'][0]['percentage'], 66)
            self.assertEqual(view['selected'][0]['percentage'], 66)
