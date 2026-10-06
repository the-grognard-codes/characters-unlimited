"""Fixed class training must reach the public equipped weapon projection."""
from copy import deepcopy
import tempfile
import unittest

from characters_unlimited.application import CharacterApplication


class FixedWeaponEquipmentTests(unittest.TestCase):
    def test_fixed_energy_rifle_enables_aimed_without_an_elective_choice(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides: 3)
            for class_id in ('coalition-grunt', 'coalition-technical-officer-communications'):
                with self.subTest(character_class=class_id):
                    hero = app.create(character_class=class_id)
                    hero = app.purchase_equipment(hero['id'], revision=hero['revision'], item_id='cs-c10')
                    inventory = deepcopy(hero['equipment'])
                    inventory['items'][0]['equipped'] = True
                    hero = app.set_equipment(hero['id'], revision=hero['revision'], inventory=inventory)
                    self.assertEqual(app.combat_view(hero['id'])['choices']['modern'], [])
                    view = app.equipment_view(hero['id'])
                    self.assertEqual(view['attacks'][0]['single']['value'], 0)
                    self.assertEqual(view['attacks'][0]['aimed']['value'], 2)
                    self.assertFalse(any('matching weapon proficiency is missing' in row for row in view['warnings']))
                    hero = app.set_attribute(hero['id'], revision=hero['revision'], attribute='PP', mode='fixed', value=5)
                    view = app.equipment_view(hero['id'])
                    self.assertIsNone(view['attacks'][0]['aimed']['value'])
                    self.assertIn('P.P. below 8', view['attacks'][0]['guidance'])
                    self.assertFalse(any('matching weapon proficiency is missing' in row for row in view['warnings']))
