import tempfile
import unittest
from copy import deepcopy
from io import BytesIO
from pypdf import PdfReader

from characters_unlimited.application import CharacterApplication, SaveConflict


class AmmunitionWorkflowTests(unittest.TestCase):
    def test_split_grouped_clips_preserves_ammunition_and_enables_one_reload(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides: 4)
            character = app.create()
            character = app.purchase_equipment(character['id'], revision=0, item_id='wilks-320')
            character = app.purchase_equipment(character['id'], revision=character['revision'],
                item_id='standard-e-clip', quantity=2, unit_cost=5000)
            original = deepcopy(character['equipment'])
            gun, clips = original['items']
            character = app.split_equipment(character['id'], revision=character['revision'], possession_id=clips['id'])
            self.assertEqual(character['equipment']['credits'], -21000)
            self.assertEqual([item['quantity'] for item in character['equipment']['items']], [1, 1, 1])
            self.assertEqual([item['shots'] for item in character['equipment']['items']], [20, 20, 20])
            self.assertEqual(character['equipment']['items'][1]['id'], clips['id'])
            self.assertNotEqual(character['equipment']['items'][2]['id'], clips['id'])
            character = app.reload_weapon(character['id'], revision=character['revision'],
                weapon_possession_id=gun['id'], clip_possession_id=clips['id'])
            with self.assertRaises(ValueError):
                app.split_equipment(character['id'], revision=character['revision'], possession_id=clips['id'])
            self.assertEqual(app.get(character['id']), character)

    def test_reload_exchanges_loaded_and_spare_clips_without_creating_ammunition(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides: 4)
            character = app.create()
            character = app.set_equipment(character['id'], revision=0,
                inventory={'credits': 20000, 'items': []})
            character = app.purchase_equipment(character['id'], revision=character['revision'], item_id='wilks-320')
            character = app.purchase_equipment(character['id'], revision=character['revision'],
                item_id='standard-e-clip', unit_cost=5500)
            inventory = deepcopy(character['equipment'])
            gun, clip = inventory['items']
            gun.update(shots=5, equipped=True)
            character = app.set_equipment(character['id'], revision=character['revision'], inventory=inventory)
            character = app.reload_weapon(character['id'], revision=character['revision'],
                weapon_possession_id=gun['id'], clip_possession_id=clip['id'])
            self.assertEqual(character['equipment']['credits'], 3500)
            self.assertEqual([item['shots'] for item in character['equipment']['items']], [20, 5])
            self.assertEqual([item['id'] for item in character['equipment']['items']], [gun['id'], clip['id']])
            self.assertEqual(len(app.equipment_view(character['id'])['attacks']), 1)
            imported = app.import_character(app.export_character(character['id']))
            self.assertEqual(imported['equipment'], character['equipment'])
            self.assertEqual(CharacterApplication(directory).get(character['id'])['equipment'], character['equipment'])
            fields = PdfReader(BytesIO(app.export_pdf(character['id']))).get_fields()
            assert fields is not None
            self.assertIn('5/20 shots', ' '.join(str(field.get('/V', '')) for field in fields.values()))

    def test_invalid_reload_and_clip_states_preserve_saved_inventory(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides: 4)
            character = app.create()
            for item_id, price in [('wilks-447', None), ('standard-e-clip', 5000), ('knife-small', 15)]:
                character = app.purchase_equipment(character['id'], revision=character['revision'], item_id=item_id, unit_cost=price)
            gun, clip, knife = character['equipment']['items']
            for weapon_id, clip_id in [(gun['id'], gun['id']), (knife['id'], clip['id']), (gun['id'], knife['id']), ('missing', clip['id'])]:
                with self.assertRaises(ValueError):
                    app.reload_weapon(character['id'], revision=character['revision'], weapon_possession_id=weapon_id, clip_possession_id=clip_id)
                self.assertEqual(app.get(character['id']), character)
            with self.assertRaises(SaveConflict):
                app.reload_weapon(character['id'], revision=0, weapon_possession_id=gun['id'], clip_possession_id=clip['id'])
            for key, value in [('shots', 21), ('shots', True), ('shots', None)]:
                inventory = deepcopy(character['equipment']); inventory['items'][1][key] = value
                with self.assertRaises(ValueError):
                    app.set_equipment(character['id'], revision=character['revision'], inventory=inventory)
                bundle = app.export_character(character['id']); bundle['character']['equipment'] = inventory
                with self.assertRaises(ValueError): app.import_character(bundle)
                self.assertEqual(app.get(character['id']), character)
            for key, state_value in [('location', 'stored'), ('quantity', 2)]:
                inventory = deepcopy(character['equipment'])
                inventory['items'][1].update(location='carried', quantity=1)
                inventory['items'][1][key] = state_value
                character = app.set_equipment(character['id'], revision=character['revision'], inventory=inventory)
                with self.assertRaises(ValueError):
                    app.reload_weapon(character['id'], revision=character['revision'], weapon_possession_id=gun['id'], clip_possession_id=clip['id'])
                self.assertEqual(app.get(character['id']), character)
