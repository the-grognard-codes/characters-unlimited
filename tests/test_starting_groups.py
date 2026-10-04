"""Independent starting equipment choices through the character interface."""

from copy import deepcopy
from io import BytesIO
import tempfile
import unittest
from pypdf import PdfReader
from characters_unlimited.application import CharacterApplication, SaveConflict
from characters_unlimited.rules import RuleArchive


class StartingGroupsTests(unittest.TestCase):
    def test_free_city_armor_group_preserves_money_gear_and_original_receipt_after_removal(self):
        with tempfile.TemporaryDirectory() as directory:
            app=CharacterApplication(directory,die=lambda sides:4)
            hero=app.create(character_class='city-rat')
            hero=app.generate_starting_funds(hero['id'],revision=hero['revision'])
            hero=app.grant_starting_gear(hero['id'],revision=hero['revision'])
            original=deepcopy(hero)
            app.die=lambda sides:self.fail('Starting armor must not roll dice')
            hero=app.grant_starting_group(hero['id'],revision=hero['revision'],group_id='armor',selection='urban-warrior')
            self.assertEqual(hero['equipment']['credits'],2400)
            self.assertEqual(hero['starting_funds'],original['starting_funds'])
            self.assertEqual(hero['starting_gear'],original['starting_gear'])
            self.assertEqual(len(hero['equipment']['items']),7)
            receipt=hero['starting_equipment_groups']['armor']
            self.assertEqual(receipt['selection'],'urban-warrior')
            self.assertEqual(receipt['source']['pages'],[89])
            self.assertEqual(len(receipt['grants']),1)
            view=app.equipment_view(hero['id'])
            self.assertEqual(view['carried_weight_lbs'],11)
            self.assertEqual(view['unknown_carried_weight_quantity'],7)
            self.assertEqual(view['armor'],[])
            group=view['starting_groups']['groups'][0]
            self.assertTrue(group['generated'])
            self.assertEqual(group['receipt'],receipt)
            with self.assertRaises(ValueError):
                app.grant_starting_group(hero['id'],revision=hero['revision'],group_id='armor',selection='huntsman')
            inventory=deepcopy(hero['equipment']);inventory['items']=inventory['items'][:6]
            hero=app.set_equipment(hero['id'],revision=hero['revision'],inventory=inventory)
            reopened=CharacterApplication(directory)
            self.assertEqual(reopened.get(hero['id']),hero)
            self.assertEqual(reopened.duplicate(hero['id'])['starting_equipment_groups'],hero['starting_equipment_groups'])
            imported=reopened.import_character(reopened.export_character(hero['id']))
            self.assertEqual(imported['starting_equipment_groups'],hero['starting_equipment_groups'])
            with self.assertRaises(ValueError):
                reopened.grant_starting_group(hero['id'],revision=hero['revision'],group_id='armor',selection='plastic-man')
            fields=PdfReader(BytesIO(reopened.export_pdf(hero['id']))).get_fields()
            assert fields is not None
            values=' '.join(str(field.get('/V','')) for field in fields.values())
            self.assertIn('Original starting armor',values)
            self.assertIn('Urban Warrior',values)

    def test_old_pins_and_added_groups_preserve_acquired_rules_and_progression(self):
        with tempfile.TemporaryDirectory() as directory:
            archive=RuleArchive.load()
            old=RuleArchive(archive.definitions(),{**archive.active_versions(),'rifts-equipment':'1.8.0'})
            previous=CharacterApplication(directory,die=lambda sides:4,rule_archive=old)
            hero=previous.create(character_class='city-rat')
            hero=previous.generate_resources(hero['id'],revision=hero['revision'])
            hero=previous.generate_starting_funds(hero['id'],revision=hero['revision'])
            current=CharacterApplication(directory,die=lambda sides:self.fail('Upgrade/grant must not roll dice'))
            self.assertFalse(current.equipment_view(hero['id'])['starting_groups']['supported'])
            with self.assertRaises(ValueError):
                current.grant_starting_group(hero['id'],revision=hero['revision'],group_id='armor',selection='urban-warrior')
            preview=current.preview_rule_upgrade(hero['id'])
            self.assertTrue(any('starting equipment group printed pp. 89 / PDF pp. 92' in source for source in preview['sources']))
            updated=current.apply_rule_upgrade(hero['id'],revision=hero['revision'],token=preview['token'])['character']
            self.assertEqual(updated['equipment'],hero['equipment'])
            self.assertEqual(updated['attributes'],hero['attributes'])
            updated=current.grant_starting_group(hero['id'],revision=updated['revision'],group_id='armor',selection='huntsman')
            current.die=lambda sides:4
            updated=current.advance(hero['id'],revision=updated['revision'],method='level',value=3)
            imported=current.import_character(current.export_character(hero['id']))
            self.assertEqual(imported['starting_equipment_groups'],updated['starting_equipment_groups'])
            restored=current.undo_advancement(hero['id'],revision=updated['revision'])['character']
            self.assertEqual(restored['starting_equipment_groups'],updated['starting_equipment_groups'])
            extension=archive.active('rifts-equipment');extension['version']='group-extension-fixture'
            groups=extension['class_profiles']['city-rat']['starting_groups']['groups']
            groups['personal']=dict(deepcopy(groups['armor']),name='Personal item',category='gear',options=['city-rat-flashlight'])
            extended_archive=RuleArchive([*archive.definitions(),extension],{**archive.active_versions(),'rifts-equipment':extension['version']})
            extended=CharacterApplication(directory,rule_archive=extended_archive)
            preview=extended.preview_rule_upgrade(hero['id'])
            result=extended.apply_rule_upgrade(hero['id'],revision=restored['revision'],token=preview['token'])['character']
            self.assertEqual(result['starting_equipment_groups'],restored['starting_equipment_groups'])
            self.assertFalse(extended.equipment_view(hero['id'])['starting_groups']['groups'][1]['generated'])
            extension['version']='group-change-fixture';groups['armor']['quantity']=2
            changed_archive=RuleArchive([*extended_archive.definitions(),extension],{**extended_archive.active_versions(),'rifts-equipment':extension['version']})
            changed=CharacterApplication(directory,rule_archive=changed_archive)
            with self.assertRaisesRegex(ValueError,'recorded starting equipment group rules'):
                changed.preview_rule_upgrade(hero['id'])
            self.assertEqual(changed.get(hero['id'])['equipment'],result['equipment'])

    def test_invalid_grants_and_import_receipts_are_rejected_without_save_changes(self):
        with tempfile.TemporaryDirectory() as directory:
            app=CharacterApplication(directory,die=lambda sides:4)
            hero=app.create(character_class='city-rat')
            for group,selection in [('unknown','urban-warrior'),('armor','wilks-320')]:
                with self.assertRaises(ValueError):
                    app.grant_starting_group(hero['id'],revision=hero['revision'],group_id=group,selection=selection)
                self.assertEqual(app.get(hero['id']),hero)
            with self.assertRaises(SaveConflict):
                app.grant_starting_group(hero['id'],revision=hero['revision']+1,group_id='armor',selection='urban-warrior')
            hero=app.grant_starting_gear(hero['id'],revision=hero['revision'])
            hero=app.grant_starting_group(hero['id'],revision=hero['revision'],group_id='armor',selection='plastic-man')
            bundle=app.export_character(hero['id'])
            original=deepcopy(bundle)
            for field,value in [('quantity',2),('possession_id','invalid')]:
                invalid=deepcopy(original)
                invalid['character']['starting_equipment_groups']['armor']['grants'][0][field]=value
                with self.assertRaises(ValueError):app.import_character(invalid)
            invalid=deepcopy(original)
            invalid['character']['starting_equipment_groups']['armor']['source']['pages']=[98]
            with self.assertRaises(ValueError):app.import_character(invalid)
            invalid=deepcopy(original)
            invalid['character']['starting_equipment_groups']['armor']['grants'][0]['possession_id']=hero['starting_gear']['grants'][0]['possession_id']
            with self.assertRaises(ValueError):app.import_character(invalid)
            self.assertEqual(app.get(hero['id']),hero)
            vag=app.create()
            with self.assertRaises(ValueError):
                app.grant_starting_group(vag['id'],revision=vag['revision'],group_id='armor',selection='urban-warrior')
