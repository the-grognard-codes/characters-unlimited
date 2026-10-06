"""Fixed personal gear is a free, once-only class grant with unknown weights."""

from copy import deepcopy
from io import BytesIO
import tempfile
import unittest

from pypdf import PdfReader

from characters_unlimited.application import CharacterApplication, SaveConflict
from characters_unlimited.rules import RuleArchive


class StartingGearWorkflowTests(unittest.TestCase):
    def test_grant_preserves_funds_and_existing_items_without_inventing_prices_weights_or_effects(self):
        with tempfile.TemporaryDirectory() as directory:
            app=CharacterApplication(directory,die=lambda sides:4)
            character=app.create()
            character=app.set_equipment(character['id'],revision=0,inventory={'credits':500,'items':[]})
            character=app.purchase_equipment(character['id'],revision=1,item_id='wilks-320')
            original=deepcopy(character['equipment'])
            character=app.grant_starting_gear(character['id'],revision=2)
            self.assertEqual(character['equipment']['credits'],original['credits'])
            self.assertEqual(character['equipment']['items'][0],original['items'][0])
            self.assertEqual(len(character['starting_gear']['grants']),18)
            self.assertEqual(len(character['equipment']['items']),19)
            view=app.equipment_view(character['id'])
            gear=[item for item in view['items'] if item['category']=='gear']
            self.assertEqual(sum(item['quantity'] for item in gear),20)
            self.assertEqual(next(item['quantity'] for item in gear if item['name']=='Set of clothes'),2)
            self.assertTrue(all(item['cost_credits'] is None and item['weight_lbs'] is None for item in gear))
            self.assertEqual(view['carried_weight_lbs'],2)
            self.assertFalse(view['carried_weight_complete'])
            self.assertEqual(view['unknown_carried_weight_quantity'],20)
            self.assertEqual(view['attacks'],[])
            self.assertEqual(view['armor'],[])
            inventory=deepcopy(character['equipment'])
            for item in inventory['items'][1:]: item['equipped']=True
            inventory['items'][1]['quantity']=3
            inventory['items'][2]['location']='stored'
            character=app.set_equipment(character['id'],revision=3,inventory=inventory)
            view=app.equipment_view(character['id'])
            self.assertEqual(view['unknown_carried_weight_quantity'],20)
            self.assertEqual(view['attacks'],[])
            self.assertEqual(view['armor'],[])
            with self.assertRaises(ValueError): app.grant_starting_gear(character['id'],revision=character['revision'])
            fields=PdfReader(BytesIO(app.export_pdf(character['id']))).get_fields()
            assert fields is not None
            values=' '.join(str(field.get('/V','')) for field in fields.values())
            self.assertIn('Sleeping bag',values)
            self.assertIn('weight unspecified',values)
            self.assertIn('Known carried weight',values)
            self.assertNotIn('None lb',values)
            self.assertIn('Set of clothes x3; carried',str(fields['1_9']['/V']))
            self.assertIn('Baseball cap x1; stored',str(fields['2_9']['/V']))
            inventory=deepcopy(character['equipment']); inventory['items']=inventory['items'][:1]
            character=app.set_equipment(character['id'],revision=character['revision'],inventory=inventory)
            reopened=CharacterApplication(directory)
            self.assertEqual(reopened.get(character['id']),character)
            self.assertEqual(reopened.equipment_view(character['id'])['unknown_carried_weight_quantity'],0)
            self.assertEqual(reopened.duplicate(character['id'])['starting_gear'],character['starting_gear'])
            imported=reopened.import_character(reopened.export_character(character['id']))
            self.assertEqual(imported['equipment'],character['equipment'])
            self.assertEqual(imported['starting_gear'],character['starting_gear'])
            fields=PdfReader(BytesIO(reopened.export_pdf(character['id']))).get_fields()
            assert fields is not None
            values=' '.join(str(field.get('/V','')) for field in fields.values())
            values=' '.join(values.split())
            self.assertIn('Original personal starting gear grant',values)
            self.assertIn('Sleeping bag x1',values)
            self.assertIn('Set of clothes x2',values)
            with self.assertRaises(ValueError): reopened.grant_starting_gear(character['id'],revision=character['revision'])

    def test_old_pins_require_update_and_tampered_receipts_or_recorded_definition_changes_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            archive=RuleArchive.load()
            earlier=CharacterApplication(directory,die=lambda sides:4,rule_archive=RuleArchive(
                archive.definitions(),{**archive.active_versions(),'rifts-equipment':'1.1.0'}))
            character=earlier.create()
            character=earlier.generate_starting_funds(character['id'],revision=0)
            current=CharacterApplication(directory)
            with self.assertRaises(ValueError): current.grant_starting_gear(character['id'],revision=1)
            preview=current.preview_rule_upgrade(character['id'])
            self.assertTrue(any('Starting personal gear' in row['name'] for row in preview['equipment']))
            character=current.apply_rule_upgrade(character['id'],revision=1,token=preview['token'])['character']
            funds=deepcopy(character['starting_funds'])
            character=current.grant_starting_gear(character['id'],revision=character['revision'])
            self.assertEqual(character['starting_funds'],funds)
            for field,value in [('quantity',True),('item_id','unknown'),('possession_id','')]:
                bundle=current.export_character(character['id'])
                bundle['character']['starting_gear']['grants'][0][field]=value
                with self.assertRaises(ValueError): current.import_character(bundle)
                self.assertEqual(current.get(character['id']),character)
            bundle=current.export_character(character['id'])
            bundle['character']['starting_gear']['grants'][1]['possession_id']=bundle['character']['starting_gear']['grants'][0]['possession_id']
            with self.assertRaises(ValueError): current.import_character(bundle)
            bundle=current.export_character(character['id'])
            bundle['character']['starting_gear']['source']={}
            with self.assertRaises(ValueError): current.import_character(bundle)
            changed=archive.active('rifts-equipment'); changed['version']='99.0.0'
            changed['class_profiles']['vagabond']['starting_gear']['grants'][0]['quantity']=3
            newer=CharacterApplication(directory,rule_archive=RuleArchive([*archive.definitions(),changed],
                {**archive.active_versions(),'rifts-equipment':'99.0.0'}))
            with self.assertRaisesRegex(ValueError,'recorded starting gear'): newer.preview_rule_upgrade(character['id'])
            self.assertEqual(newer.get(character['id']),character)

    def test_stale_cross_game_unpriced_purchases_and_invalid_generic_state_preserve_saved_work(self):
        with tempfile.TemporaryDirectory() as directory:
            app=CharacterApplication(directory,die=lambda sides:4)
            character=app.create()
            edited=app.edit(character['id'],revision=0,notes='Keep this work')
            with self.assertRaises(SaveConflict): app.grant_starting_gear(character['id'],revision=0)
            self.assertEqual(app.get(character['id']),edited)
            hero=app.create(game='heroes-unlimited')
            with self.assertRaises(ValueError): app.grant_starting_gear(hero['id'],revision=0)
            character=app.grant_starting_gear(character['id'],revision=1)
            gear_id=character['equipment']['items'][0]['item_id']
            with self.assertRaises(ValueError): app.purchase_equipment(character['id'],revision=2,item_id=gear_id)
            inventory=deepcopy(character['equipment']); inventory['items'][0]['shots']=1
            with self.assertRaises(ValueError): app.set_equipment(character['id'],revision=2,inventory=inventory)
            self.assertEqual(app.get(character['id']),character)
            full=app.create()
            inventory={'credits':123,'items':[{'id':f'existing-{index}','item_id':'wilks-320',
                       'quantity':1,'location':'stored','equipped':False,'shots':20} for index in range(1000)]}
            full=app.set_equipment(full['id'],revision=0,inventory=inventory)
            with self.assertRaises(ValueError): app.grant_starting_gear(full['id'],revision=1)
            self.assertEqual(app.get(full['id']),full)


if __name__=='__main__':
    unittest.main()
