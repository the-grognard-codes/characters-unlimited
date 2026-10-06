from copy import deepcopy
from io import BytesIO
import tempfile
import unittest

from pypdf import PdfReader

from characters_unlimited.application import CharacterApplication
from characters_unlimited.rules import RuleArchive


class DescriptiveWeaponTests(unittest.TestCase):
    def archive(self, overrides=None):
        archive = RuleArchive.load()
        equipment = archive.active('rifts-equipment')
        equipment['version'] = '99.0.0'
        equipment['items'].append({
            'id': 'source-grenade', 'name': 'Source grenade', 'category': 'weapon',
            'weapon_kind': 'descriptive', 'damage': '2D6 M.D.',
            'range_feet': 120, 'range_meters': 36, 'weight_lbs': None,
            'cost_credits': 250, 'description': 'Blast radius 20 feet. Consume quantities manually.',
            'source': {'book': 'Rifts - Ultimate Edition', 'section': 'Hand grenades',
                       'pages': [260], 'pdf_pages': [263]},
        })
        equipment['items'][-1].update(overrides or {})
        return RuleArchive([*archive.definitions(), equipment],
                           {**archive.active_versions(), 'rifts-equipment': '99.0.0'})

    def test_inactive_invalid_descriptive_definitions_reject_before_dice(self):
        for changes in ({'description': ''}, {'range_feet': True}, {'range_meters': -1},
                        {'capacity': 10}, {'aimed_bonus': 3}, {'proficiency': 'energy-pistol'}):
            with self.subTest(changes=changes), tempfile.TemporaryDirectory() as directory:
                def no_roll(sides):
                    self.fail('Invalid unselected equipment must reject before generation')
                app = CharacterApplication(directory, die=no_roll, rule_archive=self.archive(changes))
                with self.assertRaises(ValueError):
                    app.create()
                self.assertEqual(app.list(), [])

    def test_quantities_reopen_and_export_without_shots_or_attack_bonuses(self):
        rules = self.archive()
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides: 3, rule_archive=rules)
            hero = app.create()
            hero = app.purchase_equipment(hero['id'], revision=0, item_id='source-grenade', quantity=2)
            inventory = deepcopy(hero['equipment'])
            inventory['items'][0]['equipped'] = True
            hero = app.set_equipment(hero['id'], revision=hero['revision'], inventory=inventory)
            view = app.equipment_view(hero['id'])
            self.assertEqual(view['items'][0]['quantity'], 2)
            self.assertIsNone(view['items'][0]['shots'])
            self.assertEqual(view['attacks'], [])
            self.assertEqual(view['melee_attacks'], [])
            broken = deepcopy(inventory)
            broken['items'][0]['shots'] = 1
            with self.assertRaises(ValueError):
                app.set_equipment(hero['id'], revision=hero['revision'], inventory=broken)
            bundle = app.export_character(hero['id'])
            bundle['character']['equipment'] = broken
            with self.assertRaises(ValueError):
                app.import_character(bundle)
            self.assertEqual(app.get(hero['id']), hero)
            reopened = CharacterApplication(directory, rule_archive=rules)
            self.assertEqual(reopened.equipment_view(hero['id']), view)
            imported = reopened.import_character(reopened.export_character(hero['id']))
            self.assertEqual(reopened.equipment_view(imported['id']), view)
            fields = PdfReader(BytesIO(app.export_pdf(hero['id']))).get_fields()
            assert fields is not None
            text = ' '.join(str(row.get('/V', '')) for row in fields.values())
            self.assertIn('Source grenade', text)
            self.assertIn('Blast radius 20 feet', text)
            self.assertNotIn('None/None', text)
