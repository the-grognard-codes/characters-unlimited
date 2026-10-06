"""Reviewed core armor through character equipment and editable sheets."""

from copy import deepcopy
from io import BytesIO
import tempfile
import unittest
from pypdf import PdfReader
from characters_unlimited.application import CharacterApplication
from characters_unlimited.rules import RuleArchive


class LightArmorTests(unittest.TestCase):
    def test_source_capacities_prices_protection_and_storage_remain_separate(self):
        with tempfile.TemporaryDirectory() as directory:
            app=CharacterApplication(directory,die=lambda sides:4)
            hero=app.create()
            hero=app.set_equipment(hero['id'],revision=hero['revision'],inventory={'credits':60000,'items':[]})
            for item_id in ('urban-warrior','huntsman'):
                hero=app.purchase_equipment(hero['id'],revision=hero['revision'],item_id=item_id)
            self.assertEqual(hero['equipment']['credits'],1000)
            inventory=deepcopy(hero['equipment'])
            for item in inventory['items']:item['equipped']=True
            hero=app.set_equipment(hero['id'],revision=hero['revision'],inventory=inventory)
            view=app.equipment_view(hero['id'])
            self.assertEqual(view['carried_weight_lbs'],27)
            self.assertEqual(len(view['armor']),2)
            urban,huntsman=view['armor']
            self.assertEqual(urban['locations'],{'main_body':50,'helmet':35,'left_arm':16,'right_arm':16,'left_leg':30,'right_leg':30})
            self.assertEqual(huntsman['locations'],{'main_body':45,'helmet':35,'left_arm':15,'right_arm':15,'left_leg':25,'right_leg':25})
            self.assertEqual((urban['movement_penalty'],huntsman['movement_penalty']),(-5,-10))
            self.assertTrue(urban['environmental']);self.assertFalse(huntsman['environmental'])
            self.assertTrue(any('Five-hour' in note for note in urban['protection_notes']))
            self.assertTrue(any('non-environmental' in note for note in huntsman['protection_notes']))
            self.assertTrue(any('Multiple' in warning for warning in view['warnings']))
            inventory['items'][1]['location']='stored'
            hero=app.set_equipment(hero['id'],revision=hero['revision'],inventory=inventory)
            view=app.equipment_view(hero['id'])
            self.assertEqual(view['carried_weight_lbs'],11)
            self.assertEqual(len(view['armor']),1)
            self.assertEqual(view['armor'][0]['locations']['main_body'],50)
            fields=PdfReader(BytesIO(app.export_pdf(hero['id']))).get_fields()
            assert fields is not None
            self.assertEqual(fields['ARMOR']['/V'],'Urban Warrior')
            self.assertEqual(fields['COST']['/V'],'35000')
            self.assertEqual(fields['WEIGHT 1']['/V'],'11 lb')
            self.assertEqual(fields['undefined_7']['/V'],'50')
            self.assertEqual(fields['page1.cell437']['/V'],'-5')
            values=' '.join(str(field.get('/V','')) for field in fields.values())
            self.assertIn('Environmental',values)
            self.assertIn('Five-hour',values)
            reopened=CharacterApplication(directory)
            self.assertEqual(reopened.equipment_view(hero['id'])['armor'],view['armor'])
            imported=reopened.import_character(reopened.export_character(hero['id']))
            self.assertEqual(reopened.equipment_view(imported['id'])['armor'],view['armor'])

    def test_reviewed_update_adds_protection_without_replacing_old_pins_or_inventory(self):
        with tempfile.TemporaryDirectory() as directory:
            archive=RuleArchive.load()
            old=RuleArchive(archive.definitions(),{**archive.active_versions(),'rifts-equipment':'1.7.0'})
            previous=CharacterApplication(directory,die=lambda sides:4,rule_archive=old)
            hero=previous.create()
            hero=previous.purchase_equipment(hero['id'],revision=hero['revision'],item_id='plastic-man')
            inventory=deepcopy(hero['equipment']);inventory['items'][0]['equipped']=True
            hero=previous.set_equipment(hero['id'],revision=hero['revision'],inventory=inventory)
            current=CharacterApplication(directory,die=lambda sides:self.fail('Rule update must not roll dice'))
            self.assertIsNone(current.equipment_view(hero['id'])['armor'][0]['environmental'])
            self.assertNotIn('urban-warrior',[item['id'] for item in current.equipment_view(hero['id'])['catalog']])
            preview=current.preview_rule_upgrade(hero['id'])
            self.assertTrue(any('environmental' in change['name'] for change in preview['equipment']))
            updated=current.apply_rule_upgrade(hero['id'],revision=hero['revision'],token=preview['token'])['character']
            self.assertEqual(updated['equipment'],hero['equipment'])
            self.assertEqual(updated['attributes'],hero['attributes'])
            self.assertTrue(current.equipment_view(hero['id'])['armor'][0]['environmental'])
            self.assertEqual(current.equipment_view(hero['id'])['armor'][0]['locations']['main_body'],35)
            self.assertIn('urban-warrior',[item['id'] for item in current.equipment_view(hero['id'])['catalog']])
            imported=current.import_character(current.export_character(hero['id']))
            self.assertEqual(imported['additional_rule_packs']['rifts-equipment'],'1.11.0')

    def test_huntsman_movement_penalty_does_not_assert_an_unreviewed_prowl_penalty(self):
        with tempfile.TemporaryDirectory() as directory:
            app=CharacterApplication(directory,die=lambda sides:4)
            hero=app.create()
            hero=app.purchase_equipment(hero['id'],revision=hero['revision'],item_id='huntsman')
            inventory=deepcopy(hero['equipment']);inventory['items'][0]['equipped']=True
            hero=app.set_equipment(hero['id'],revision=hero['revision'],inventory=inventory)
            self.assertEqual(app.equipment_view(hero['id'])['armor'][0]['movement_penalty'],-10)
            fields=PdfReader(BytesIO(app.export_pdf(hero['id']))).get_fields()
            assert fields is not None
            self.assertEqual(fields['page1.cell437'].get('/V',''),'')
            values=' '.join(str(field.get('/V','')) for field in fields.values())
            self.assertIn('Movement skill penalty -10%',values)
