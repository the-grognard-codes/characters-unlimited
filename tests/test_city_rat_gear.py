"""City Rat fixed equipment through the public character workflow."""

from copy import deepcopy
from io import BytesIO
import tempfile
import unittest
from pypdf import PdfReader
from characters_unlimited.application import CharacterApplication
from characters_unlimited.rules import RuleArchive


class CityRatGearTests(unittest.TestCase):
    def test_free_fixed_gear_receipt_persists_after_inventory_edits_and_removal(self):
        with tempfile.TemporaryDirectory() as directory:
            app=CharacterApplication(directory,die=lambda sides:4)
            hero=app.create(character_class='city-rat')
            hero=app.generate_starting_funds(hero['id'],revision=hero['revision'])
            hero=app.generate_resources(hero['id'],revision=hero['revision'])
            original=deepcopy(hero)
            app.die=lambda sides:self.fail('Fixed gear must not roll dice')
            hero=app.grant_starting_gear(hero['id'],revision=hero['revision'])
            self.assertEqual(hero['starting_funds'],original['starting_funds'])
            self.assertEqual(hero['resources'],original['resources'])
            self.assertEqual(hero['equipment']['credits'],2400)
            self.assertEqual(len(hero['starting_gear']['grants']),6)
            view=app.equipment_view(hero['id'])
            self.assertEqual(sum(item['quantity'] for item in view['items']),7)
            self.assertEqual(view['unknown_carried_weight_quantity'],7)
            self.assertFalse(view['carried_weight_complete'])
            self.assertEqual(view['attacks'],[])
            self.assertEqual(view['armor'],[])
            self.assertEqual(next(item['quantity'] for item in view['items'] if item['item_id']=='city-rat-working-colors'),2)
            self.assertEqual(next(item['cost_credits'] for item in view['items'] if item['item_id']=='city-rat-rmk'),24000)
            self.assertEqual(hero['starting_gear']['source']['pages'],[89])
            with self.assertRaises(ValueError):
                app.grant_starting_gear(hero['id'],revision=hero['revision'])
            inventory=deepcopy(hero['equipment']);inventory['items']=[];inventory['credits']=123
            hero=app.set_equipment(hero['id'],revision=hero['revision'],inventory=inventory)
            reopened=CharacterApplication(directory)
            self.assertEqual(reopened.get(hero['id']),hero)
            self.assertEqual(reopened.duplicate(hero['id'])['starting_gear'],hero['starting_gear'])
            self.assertEqual(reopened.import_character(reopened.export_character(hero['id']))['starting_gear'],hero['starting_gear'])
            with self.assertRaises(ValueError):
                reopened.grant_starting_gear(hero['id'],revision=hero['revision'])
            fields=PdfReader(BytesIO(reopened.export_pdf(hero['id']))).get_fields()
            assert fields is not None
            values=' '.join(str(field.get('/V','')) for field in fields.values())
            self.assertIn('Working colors x2',values)
            self.assertIn('900-pound-test',values)
            self.assertIn('suturing',values)
            self.assertIn('90%',values)

    def test_old_pins_update_without_dice_and_recorded_gear_survives_progression(self):
        with tempfile.TemporaryDirectory() as directory:
            archive=RuleArchive.load()
            old=RuleArchive(archive.definitions(),{**archive.active_versions(),'rifts-equipment':'1.6.0'})
            previous=CharacterApplication(directory,die=lambda sides:4,rule_archive=old)
            hero=previous.create(character_class='city-rat')
            hero=previous.generate_resources(hero['id'],revision=hero['revision'])
            hero=previous.generate_starting_funds(hero['id'],revision=hero['revision'])
            current=CharacterApplication(directory,die=lambda sides:self.fail('Update or gear grant must not roll dice'))
            self.assertFalse(current.equipment_view(hero['id'])['starting_gear']['supported'])
            with self.assertRaises(ValueError):
                current.grant_starting_gear(hero['id'],revision=hero['revision'])
            preview=current.preview_rule_upgrade(hero['id'])
            self.assertTrue(any('starting personal gear printed pp. 89 / PDF pp. 92' in source for source in preview['sources']))
            updated=current.apply_rule_upgrade(hero['id'],revision=hero['revision'],token=preview['token'])['character']
            self.assertEqual(updated['starting_funds'],hero['starting_funds'])
            self.assertEqual(updated['resources'],hero['resources'])
            updated=current.grant_starting_gear(hero['id'],revision=updated['revision'])
            self.assertEqual(current.equipment_view(hero['id'])['starting_gear']['source']['pages'],[89])
            current.die=lambda sides:4
            updated=current.advance(hero['id'],revision=updated['revision'],method='level',value=3)
            imported=current.import_character(current.export_character(hero['id']))
            self.assertEqual(imported['starting_gear'],updated['starting_gear'])
            restored=current.undo_advancement(hero['id'],revision=updated['revision'])['character']
            self.assertEqual(restored['starting_gear'],updated['starting_gear'])
            self.assertEqual(restored['equipment'],updated['equipment'])
            correction=archive.active('rifts-equipment');correction['version']='gear-change-fixture'
            correction['class_profiles']['city-rat']['starting_gear']['grants'][0]['quantity']=3
            changed=RuleArchive([*archive.definitions(),correction],{**archive.active_versions(),'rifts-equipment':correction['version']})
            revised=CharacterApplication(directory,rule_archive=changed)
            with self.assertRaisesRegex(ValueError,'recorded starting gear rules'):
                revised.preview_rule_upgrade(hero['id'])
            self.assertEqual(revised.get(hero['id'])['starting_gear'],updated['starting_gear'])
