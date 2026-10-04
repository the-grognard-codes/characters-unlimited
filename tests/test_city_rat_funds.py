"""City Rat starting funds through the public character workflow."""

import tempfile
import unittest
from io import BytesIO
from pypdf import PdfReader
from characters_unlimited.application import CharacterApplication
from characters_unlimited.rules import RuleArchive


class CityRatFundsTests(unittest.TestCase):
    def test_class_funds_draw_six_d6_and_three_d4_once_and_keep_item_value_separate(self):
        with tempfile.TemporaryDirectory() as directory:
            app=CharacterApplication(directory,die=lambda sides:4)
            hero=app.create(character_class='city-rat',generation={'reroll_ones':True,'extra_die':True})
            hero=app.set_equipment(hero['id'],revision=hero['revision'],inventory={'credits':500,'items':[]})
            calls=[]
            faces=iter([1,2,3,4,5,6,1,2,3])
            def die(sides):
                calls.append(sides)
                return next(faces)
            app.die=die
            self.assertTrue(app.equipment_view(hero['id'])['starting_funds']['supported'])
            hero=app.generate_starting_funds(hero['id'],revision=hero['revision'])
            self.assertEqual(calls,[6]*6+[4]*3)
            self.assertEqual(hero['starting_funds']['credits']['value'],2100)
            self.assertEqual(hero['starting_funds']['saleable_goods']['value'],6000)
            self.assertEqual(hero['equipment']['credits'],2600)
            self.assertEqual(hero['starting_funds']['credits']['source']['pages'],[89])
            with self.assertRaises(ValueError):
                app.generate_starting_funds(hero['id'],revision=hero['revision'])
            reopened=CharacterApplication(directory)
            imported=reopened.import_character(reopened.export_character(hero['id']))
            self.assertEqual(imported['starting_funds'],hero['starting_funds'])
            self.assertEqual(reopened.equipment_view(hero['id'])['starting_funds']['funds'],hero['starting_funds'])
            fields=PdfReader(BytesIO(reopened.export_pdf(hero['id']))).get_fields()
            assert fields is not None
            values=' '.join(str(field.get('/V','')) for field in fields.values())
            self.assertIn('Starting credits: 2100',values)
            self.assertIn('6000',values)
            self.assertIn('Starting Black Market item value remains recorded item value',values)
            self.assertNotIn('Starting saleable goods',values)
            self.assertIn('Current credits: 2600',values)

    def test_old_equipment_pin_requires_update_and_recorded_class_rules_cannot_change(self):
        with tempfile.TemporaryDirectory() as directory:
            archive=RuleArchive.load()
            old=RuleArchive(archive.definitions(),{**archive.active_versions(),'rifts-equipment':'1.5.0'})
            previous=CharacterApplication(directory,die=lambda sides:4,rule_archive=old)
            hero=previous.create(character_class='city-rat')
            hero=previous.set_equipment(hero['id'],revision=hero['revision'],inventory={'credits':500,'items':[]})
            current=CharacterApplication(directory,die=lambda sides:self.fail('Equipment update rolled dice'))
            self.assertFalse(current.equipment_view(hero['id'])['starting_funds']['supported'])
            with self.assertRaises(ValueError):
                current.generate_starting_funds(hero['id'],revision=hero['revision'])
            preview=current.preview_rule_upgrade(hero['id'])
            self.assertTrue(any('starting funds printed pp. 89 / PDF pp. 92' in source for source in preview['sources']))
            updated=current.apply_rule_upgrade(hero['id'],revision=hero['revision'],token=preview['token'])['character']
            self.assertEqual(updated['equipment'],hero['equipment'])
            self.assertEqual(updated['attributes'],hero['attributes'])
            current.die=lambda sides:4
            updated=current.generate_starting_funds(hero['id'],revision=updated['revision'])
            self.assertEqual(updated['equipment']['credits'],2900)
            updated=current.generate_resources(hero['id'],revision=updated['revision'])
            updated=current.advance(hero['id'],revision=updated['revision'],method='level',value=3)
            self.assertEqual(current.import_character(current.export_character(hero['id']))['starting_funds'],updated['starting_funds'])
            restored=current.undo_advancement(hero['id'],revision=updated['revision'])['character']
            self.assertEqual(restored['starting_funds'],updated['starting_funds'])
            correction=archive.active('rifts-equipment')
            correction['version']='funds-change-fixture'
            correction['class_profiles']['city-rat']['starting_funds']['definitions'][0]['count']=5
            changed=RuleArchive([*archive.definitions(),correction],
                {**archive.active_versions(),'rifts-equipment':correction['version']})
            revised=CharacterApplication(directory,rule_archive=changed)
            with self.assertRaisesRegex(ValueError,'recorded starting funds rules'):
                revised.preview_rule_upgrade(hero['id'])
            self.assertEqual(revised.get(hero['id'])['starting_funds'],updated['starting_funds'])
