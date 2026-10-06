"""Explicit equipment corrections through the public character workflow."""

from copy import deepcopy
from contextlib import closing
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

from characters_unlimited.application import CharacterApplication, SaveConflict
from characters_unlimited.rules import RuleArchive


class EquipmentUpgradeTests(unittest.TestCase):
    def newer_application(self, directory, change=None):
        archive = RuleArchive.load()
        equipment = archive.active('rifts-equipment')
        equipment['version'] = '99.0.0'
        equipment['items'][0].update(weight_lbs=3, aimed_bonus=4, cost_credits=12000)
        equipment['items'][2]['locations']['main_body'] = 40
        if change:
            change(equipment)
        return CharacterApplication(directory, rule_archive=RuleArchive(
            [*archive.definitions(), equipment],
            {**archive.active_versions(), 'rifts-equipment': '99.0.0'}))

    def character_with_equipment(self, directory):
        app = CharacterApplication(directory, die=lambda sides:4)
        character = app.create()
        for item_id in ('wilks-320', 'plastic-man'):
            character = app.purchase_equipment(character['id'], revision=character['revision'], item_id=item_id)
        inventory = deepcopy(character['equipment'])
        inventory['items'][0].update(equipped=True, shots=3, quantity=2)
        inventory['items'][1]['equipped'] = True
        character = app.set_equipment(character['id'], revision=character['revision'], inventory=inventory)
        character = app.select_combat(character['id'], revision=character['revision'],
            choices={'hand_to_hand':'basic', 'ancient':[], 'modern':['energy-pistol']})
        return app, character

    def test_preview_then_apply_preserves_possessions_and_changes_only_reviewed_pins(self):
        with tempfile.TemporaryDirectory() as directory:
            _, character = self.character_with_equipment(directory)
            current = self.newer_application(directory)
            before = current.equipment_view(character['id'])
            self.assertEqual(before['carried_weight_lbs'],17)
            self.assertEqual(before['attacks'][0]['aimed']['value'],5)
            preview = current.preview_rule_upgrade(character['id'])
            self.assertEqual(preview['changes'],[{'pack_id':'rifts-equipment','from':'1.11.0','to':'99.0.0'}])
            changes = {row['name']:(row['before'],row['after']) for row in preview['equipment']}
            self.assertEqual(changes['Carried weight (lb)'],(17,19))
            self.assertTrue(any('aimed' in name and values == (5,7) for name,values in changes.items()))
            self.assertTrue(any('locations' in name for name in changes))
            self.assertEqual(current.get(character['id']),character)
            result = current.apply_rule_upgrade(character['id'], revision=character['revision'], token=preview['token'])
            updated = result['character']
            self.assertEqual(updated['equipment'],character['equipment'])
            self.assertEqual(updated['attributes'],character['attributes'])
            self.assertEqual(updated['additional_rule_packs']['rifts-equipment'],'99.0.0')
            self.assertEqual(current.equipment_view(character['id'])['attacks'][0]['aimed']['value'],7)
            self.assertEqual(self.newer_application(directory).equipment_view(character['id'])['carried_weight_lbs'],19)
            imported = current.import_character(current.export_character(character['id']))
            self.assertEqual(imported['equipment'],character['equipment'])
            self.assertTrue(result['backup']['path'])
            with closing(sqlite3.connect(result['backup']['path'])) as backup:
                import json
                saved = json.loads(backup.execute('SELECT document FROM characters WHERE id=?',
                                                (character['id'],)).fetchone()[0])
            self.assertEqual(saved,character)

    def test_skill_and_equipment_updates_apply_atomically_after_an_interrupted_attempt(self):
        with tempfile.TemporaryDirectory() as directory:
            archive = RuleArchive.load()
            earlier = CharacterApplication(directory,die=lambda sides:4,rule_archive=RuleArchive(
                archive.definitions(),{**archive.active_versions(),'rifts-domestic-skills':'2.2.0'}))
            character = earlier.create()
            character = earlier.purchase_equipment(character['id'],revision=0,item_id='wilks-320')
            current = self.newer_application(directory)
            preview = current.preview_rule_upgrade(character['id'])
            self.assertEqual([row['pack_id'] for row in preview['changes']],
                             ['rifts-domestic-skills','rifts-equipment'])
            with current.store.connect() as connection:
                connection.execute("CREATE TRIGGER interrupt_upgrade BEFORE UPDATE ON characters BEGIN SELECT RAISE(ABORT, 'Interrupted update'); END")
            with self.assertRaises(sqlite3.IntegrityError):
                current.apply_rule_upgrade(character['id'],revision=1,token=preview['token'])
            self.assertEqual(current.get(character['id']),character)
            with current.store.connect() as connection:
                connection.execute('DROP TRIGGER interrupt_upgrade')
            result = current.apply_rule_upgrade(character['id'],revision=1,token=preview['token'])
            self.assertEqual(result['character']['additional_rule_packs'],
                             {'rifts-domestic-skills':'2.24.0','rifts-equipment':'99.0.0'})
            self.assertEqual(result['character']['equipment'],character['equipment'])

    def test_incompatible_missing_items_or_capacity_do_not_modify_saved_inventory(self):
        with tempfile.TemporaryDirectory() as directory:
            _, character = self.character_with_equipment(directory)
            for change in (lambda pack:pack['items'].pop(0),
                           lambda pack:pack['items'][0].update(capacity=2)):
                current = self.newer_application(directory,change)
                with self.assertRaises(ValueError):
                    current.preview_rule_upgrade(character['id'])
                self.assertEqual(current.get(character['id']),character)

    def test_tampered_stale_changed_target_or_failed_backup_keeps_both_pins(self):
        with tempfile.TemporaryDirectory() as directory:
            _, character = self.character_with_equipment(directory)
            current = self.newer_application(directory)
            preview = current.preview_rule_upgrade(character['id'])
            with self.assertRaises(ValueError):
                current.apply_rule_upgrade(character['id'],revision=character['revision'],token='tampered')
            changed_target = self.newer_application(directory,lambda pack:pack['items'][0].update(aimed_bonus=6))
            with self.assertRaises(ValueError):
                changed_target.apply_rule_upgrade(character['id'],revision=character['revision'],token=preview['token'])
            with patch.object(current.store,'backup',side_effect=OSError('Interrupted backup')):
                with self.assertRaises(OSError):
                    current.apply_rule_upgrade(character['id'],revision=character['revision'],token=preview['token'])
            self.assertEqual(current.get(character['id']),character)
            edited = current.edit(character['id'],revision=character['revision'],notes='New work')
            with self.assertRaises(SaveConflict):
                current.apply_rule_upgrade(character['id'],revision=character['revision'],token=preview['token'])
            self.assertEqual(current.get(character['id']),edited)

    def test_no_equipment_pin_is_added_to_an_older_character_by_preview_or_skill_upgrade(self):
        with tempfile.TemporaryDirectory() as directory:
            archive = RuleArchive.load()
            app = CharacterApplication(directory,die=lambda sides:4,rule_archive=RuleArchive(
                archive.definitions(),{**archive.active_versions(),'rifts-domestic-skills':'1.0.0'}))
            character = app.create()
            current = self.newer_application(directory)
            preview = current.preview_rule_upgrade(character['id'])
            self.assertEqual(preview['equipment'],[])
            result = current.apply_rule_upgrade(character['id'],revision=0,token=preview['token'])
            self.assertNotIn('rifts-equipment',result['character']['additional_rule_packs'])


if __name__ == '__main__':
    unittest.main()
