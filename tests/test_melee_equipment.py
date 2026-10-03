import tempfile
import unittest
from copy import deepcopy
from io import BytesIO
from pypdf import PdfReader

from characters_unlimited.application import CharacterApplication
from characters_unlimited.rules import RuleArchive


class MeleeEquipmentWorkflowTests(unittest.TestCase):
    def test_old_combat_pin_explains_missing_strength_rules(self):
        with tempfile.TemporaryDirectory() as directory:
            archive = RuleArchive.load()
            app = CharacterApplication(directory, die=lambda sides: 4, rule_archive=RuleArchive(
                archive.definitions(), {**archive.active_versions(), 'rifts-domestic-skills': '1.0.0'}))
            character = app.create()
            character = app.purchase_equipment(character['id'], revision=0,
                item_id='knife-small', unit_cost=15)
            inventory = deepcopy(character['equipment'])
            inventory['items'][0]['equipped'] = True
            app.set_equipment(character['id'], revision=character['revision'], inventory=inventory)
            knife = app.equipment_view(character['id'])['melee_attacks'][0]
            self.assertEqual(knife['damage'], 'Pending strength damage rules')
            self.assertIn('review a rule update', knife['guidance'])

    def test_knife_corrections_preview_active_totals_before_atomic_apply(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides: 4)
            character = app.create()
            character = app.purchase_equipment(character['id'], revision=0,
                item_id='knife-large', unit_cost=30)
            character = app.select_combat(character['id'], revision=character['revision'],
                choices={'ancient': ['knife']})
            inventory = deepcopy(character['equipment'])
            inventory['items'][0]['equipped'] = True
            character = app.set_equipment(character['id'], revision=character['revision'], inventory=inventory)
            archive = RuleArchive.load()
            newer = archive.active('rifts-equipment')
            newer['version'] = '99.0.0'
            knife = next(item for item in newer['items'] if item['id'] == 'knife-large')
            knife.update(damage='2D6 S.D.C.', proficiency='sword')
            current = CharacterApplication(directory, rule_archive=RuleArchive(
                [*archive.definitions(), newer],
                {**archive.active_versions(), 'rifts-equipment': '99.0.0'}))
            preview = current.preview_rule_upgrade(character['id'])
            changes = {row['name']: (row['before'], row['after']) for row in preview['equipment']}
            self.assertEqual(changes['Large Knife (melee 1): damage'], ('1D6 S.D.C.', '2D6 S.D.C.'))
            self.assertEqual(changes['Large Knife (melee 1): parry total'], (1, 0))
            self.assertEqual(current.get(character['id']), character)
            saved = current.apply_rule_upgrade(character['id'], revision=character['revision'], token=preview['token'])['character']
            self.assertEqual(saved['equipment'], character['equipment'])
            self.assertEqual(current.equipment_view(character['id'])['melee_attacks'][0]['damage'], '2D6 S.D.C.')

    def test_knife_purchase_and_equipped_damage_use_normal_strength_once(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides: 4)
            character = app.create()
            character = app.set_equipment(character['id'], revision=0,
                inventory={'credits': 500, 'items': []})
            character = app.purchase_equipment(character['id'], revision=character['revision'],
                item_id='knife-large', quantity=2, unit_cost=30)
            self.assertEqual(character['equipment']['credits'], 440)
            self.assertIsNone(character['equipment']['items'][0]['shots'])
            character = app.set_attribute(character['id'], revision=character['revision'],
                attribute='PS', mode='fixed', value=20)
            character = app.set_attribute(character['id'], revision=character['revision'],
                attribute='PP', mode='fixed', value=20)
            character = app.select_combat(character['id'], revision=character['revision'],
                choices={'hand_to_hand': 'assassin', 'ancient': ['knife'], 'modern': []})
            inventory = deepcopy(character['equipment'])
            inventory['items'][0]['equipped'] = True
            character = app.set_equipment(character['id'], revision=character['revision'], inventory=inventory)
            view = app.equipment_view(character['id'])
            knife = view['melee_attacks'][0]
            self.assertEqual((knife['strike']['value'], knife['parry']['value']), (5, 4))
            self.assertEqual(knife['damage'], '1D6 + 5 S.D.C.')
            self.assertEqual(view['attacks'], [])
            self.assertFalse(view['carried_weight_complete'])
            self.assertEqual(view['unknown_carried_weight_quantity'], 2)
            self.assertEqual(CharacterApplication(directory).equipment_view(character['id']), view)
            imported = app.import_character(app.export_character(character['id']))
            self.assertEqual(app.equipment_view(imported['id']), view)
            fields = PdfReader(BytesIO(app.export_pdf(character['id']))).get_fields()
            assert fields is not None
            values = ' '.join(str(field.get('/V', '')) for field in fields.values())
            self.assertIn('1D6 + 5 S.D.C.', values)
            self.assertIn('Melee', values)

    def test_range_prices_and_melee_ammunition_reject_without_losing_saved_work(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides: 4)
            character = app.create()
            for price in (None, True, 14, 76, 15.5):
                with self.assertRaises(ValueError):
                    app.purchase_equipment(character['id'], revision=0,
                        item_id='knife-small', unit_cost=price)
                self.assertEqual(app.get(character['id']), character)
            character = app.purchase_equipment(character['id'], revision=0,
                item_id='knife-small', unit_cost=75)
            self.assertEqual(character['equipment']['credits'], -75)
            inventory = deepcopy(character['equipment'])
            inventory['items'][0].update(equipped=True, shots=1)
            with self.assertRaises(ValueError):
                app.set_equipment(character['id'], revision=character['revision'], inventory=inventory)
            self.assertEqual(app.get(character['id']), character)
            inventory['items'][0]['shots'] = None
            character = app.set_equipment(character['id'], revision=character['revision'], inventory=inventory)
            self.assertEqual(app.equipment_view(character['id'])['melee_attacks'][0]['damage'], '1D4 S.D.C.')
            character = app.set_attribute(character['id'], revision=character['revision'],
                attribute='PP', mode='fixed', value=7)
            self.assertIsNone(app.equipment_view(character['id'])['melee_attacks'][0]['strike']['value'])
            character = app.set_attribute(character['id'], revision=character['revision'],
                attribute='PS', mode='fixed', value=2)
            self.assertIn('Pending', app.equipment_view(character['id'])['melee_attacks'][0]['damage'])
            inventory = deepcopy(character['equipment'])
            inventory['items'][0]['location'] = 'stored'
            character = app.set_equipment(character['id'], revision=character['revision'], inventory=inventory)
            self.assertEqual(app.equipment_view(character['id'])['melee_attacks'], [])
