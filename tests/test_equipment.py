import tempfile
import unittest
import json
import threading
from copy import deepcopy
from io import BytesIO

from pypdf import PdfReader
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from unittest.mock import patch

from characters_unlimited.application import CharacterApplication, SaveConflict
from characters_unlimited.rules import RuleArchive
from characters_unlimited.server import create_server


class EquipmentWorkflowTests(unittest.TestCase):
    def test_pdf_exports_one_character_snapshot_during_a_concurrent_inventory_edit(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory,die=lambda sides:4)
            character = app.create(name='Before concurrent edit')
            character = app.set_equipment(character['id'],revision=0,inventory={'credits':50000,'items':[]})
            original_get = app.get
            changed = False
            def read_then_edit(identifier):
                nonlocal changed
                snapshot = original_get(identifier)
                if not changed:
                    changed = True
                    other = CharacterApplication(directory)
                    edited = other.set_equipment(identifier,revision=snapshot['revision'],inventory={'credits':1234,'items':[]})
                    other.edit(identifier,revision=edited['revision'],name='After concurrent edit')
                return snapshot
            with patch.object(app,'get',side_effect=read_then_edit):
                reader = PdfReader(BytesIO(app.export_pdf(character['id'])))
            fields = reader.get_fields(); assert fields is not None
            values = ' '.join(str(field.get('/V','')) for field in fields.values())
            self.assertEqual(fields['NAME']['/V'],'Before concurrent edit')
            self.assertIn('Current credits: 50000',values)
            self.assertNotIn('Current credits: 1234',values)
            self.assertEqual(app.get(character['id'])['equipment']['credits'],1234)

    def test_equipment_http_actions_require_local_token_and_saved_revision(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory,die=lambda sides:4)
            character = app.create()
            server = create_server(app)
            worker = threading.Thread(target=server.serve_forever,daemon=True); worker.start()
            try:
                base = f'http://127.0.0.1:{server.server_port}'
                with urlopen(base+'/api/bootstrap',timeout=5) as response: token = json.load(response)['token']
                path = base+'/api/characters/'+character['id']
                payload = json.dumps({'revision':0,'item_id':'wilks-320','quantity':1}).encode()
                for headers in ({},{'X-Session-Token':token,'Origin':'https://elsewhere.invalid'}):
                    with self.assertRaises(HTTPError) as rejected:
                        urlopen(Request(path+'/purchase-equipment',data=payload,headers=headers),timeout=5)
                    self.assertEqual(rejected.exception.code,403); rejected.exception.close()
                headers = {'X-Session-Token':token,'Content-Type':'application/json','Origin':base}
                with urlopen(Request(path+'/purchase-equipment',data=payload,headers=headers),timeout=5) as response:
                    saved = json.load(response)
                with urlopen(path+'/equipment',timeout=5) as response: view = json.load(response)
                self.assertEqual(view['inventory']['credits'],-11000)
                self.assertEqual(len(view['items']),1)
                with self.assertRaises(HTTPError) as rejected:
                    urlopen(Request(path+'/purchase-equipment',data=payload,headers=headers),timeout=5)
                self.assertEqual(rejected.exception.code,409); rejected.exception.close()
                invalid = json.dumps({'revision':saved['revision'],'inventory':{'credits':0,'items':[{}]}}).encode()
                with self.assertRaises(HTTPError) as rejected:
                    urlopen(Request(path+'/equipment',data=invalid,headers=headers),timeout=5)
                self.assertEqual(rejected.exception.code,400); rejected.exception.close()
                self.assertEqual(app.get(character['id']),saved)
            finally:
                server.shutdown(); worker.join(timeout=2); server.server_close()

    def test_purchase_equip_store_and_export_reviewed_rifts_equipment(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory,die=lambda sides:4)
            character = app.create()
            self.assertNotIn('rifts-equipment',character['additional_rule_packs'])
            character = app.set_equipment(character['id'],revision=0,inventory={'credits':50000,'items':[]})
            self.assertEqual(character['additional_rule_packs']['rifts-equipment'],'1.5.0')
            for item_id,quantity in [('wilks-320',2),('wilks-447',1),('plastic-man',1)]:
                character = app.purchase_equipment(character['id'],revision=character['revision'],item_id=item_id,quantity=quantity)
            self.assertEqual(character['equipment']['credits'],-8000)
            view = app.equipment_view(character['id'])
            self.assertEqual(view['carried_weight_lbs'],22)
            self.assertTrue(any('credit' in warning.lower() for warning in view['warnings']))
            self.assertEqual(view['attacks'],[])
            inventory = deepcopy(character['equipment'])
            for item in inventory['items']:
                item['equipped']=True
            character = app.set_equipment(character['id'],revision=character['revision'],inventory=inventory)
            view = app.equipment_view(character['id'])
            self.assertEqual(view['attacks'][0]['aimed']['value'],None)
            character = app.select_combat(character['id'],revision=character['revision'],choices={
                'hand_to_hand':'basic','ancient':[],'modern':['energy-pistol','energy-rifle']})
            view = app.equipment_view(character['id'])
            pistol,rifle = view['attacks']
            self.assertEqual(pistol['single']['value'],1)
            self.assertEqual(pistol['aimed']['value'],5)
            self.assertEqual(pistol['aimed']['actions'],2)
            self.assertEqual(rifle['single']['value'],0)
            self.assertEqual(rifle['aimed']['value'],3)
            self.assertEqual(pistol['damage'],'1D6 M.D.')
            self.assertEqual(rifle['damage'],'3D6 M.D.')
            self.assertNotIn('burst',pistol)
            character = app.set_attribute(character['id'],revision=character['revision'],attribute='PS',mode='fixed',value=50)
            character = app.set_attribute(character['id'],revision=character['revision'],attribute='PP',mode='fixed',value=30)
            boosted = app.equipment_view(character['id'])['attacks'][0]
            self.assertEqual(boosted['aimed']['value'],5)
            self.assertEqual(boosted['damage'],'1D6 M.D.')
            character = app.set_attribute(character['id'],revision=character['revision'],attribute='PP',mode='fixed',value=7)
            self.assertEqual(app.equipment_view(character['id'])['attacks'][0]['single']['value'],None)
            character = app.set_attribute(character['id'],revision=character['revision'],attribute='PP',mode='fixed',value=12)
            armor = view['armor'][0]
            self.assertEqual(armor['locations']['main_body'],35)
            self.assertEqual(armor['locations']['helmet'],30)
            inventory = deepcopy(character['equipment'])
            inventory['items'][0]['shots']=3
            inventory['items'][1]['location']='stored'
            character = app.set_equipment(character['id'],revision=character['revision'],inventory=inventory)
            view = app.equipment_view(character['id'])
            self.assertEqual(len(view['attacks']),1)
            self.assertEqual(view['carried_weight_lbs'],17)
            bundle = app.export_character(character['id'])
            imported = app.import_character(bundle)
            self.assertEqual(imported['equipment'],character['equipment'])
            self.assertEqual(CharacterApplication(directory).equipment_view(character['id']),view)
            reader = PdfReader(BytesIO(app.export_pdf(character['id'])))
            fields = reader.get_fields()
            assert fields is not None
            values = ' '.join(str(field.get('/V','')) for field in fields.values())
            self.assertIn("Wilk's 320",values)
            self.assertIn('Plastic-Man',values)
            self.assertIn('-8000',values)
            inventory['items']=[]
            character = app.set_equipment(character['id'],revision=character['revision'],inventory=inventory)
            self.assertEqual(character['equipment']['credits'],-8000)
            self.assertEqual(app.equipment_view(character['id'])['carried_weight_lbs'],0)

    def test_inventory_boundaries_exact_pins_and_rejected_writes_preserve_saved_work(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory,die=lambda sides:4)
            character = app.create()
            character = app.purchase_equipment(character['id'],revision=0,item_id='wilks-320')
            for quantity in (True,0,1001):
                with self.assertRaises(ValueError):
                    app.purchase_equipment(character['id'],revision=character['revision'],item_id='wilks-320',quantity=quantity)
                self.assertEqual(app.get(character['id']),character)
            invalid = []
            for key,value in [('quantity',0),('shots',21),('shots',True),('location','elsewhere'),('equipped',1),('item_id','unknown')]:
                record = deepcopy(character['equipment']); record['items'][0][key]=value; invalid.append(record)
            record = deepcopy(character['equipment']); record['items'].append(deepcopy(record['items'][0])); invalid.append(record)
            for credits in (True,10**400):
                record = deepcopy(character['equipment']); record['credits']=credits; invalid.append(record)
            for inventory in invalid:
                with self.assertRaises(ValueError):
                    app.set_equipment(character['id'],revision=character['revision'],inventory=inventory)
                bundle = app.export_character(character['id']); bundle['character']['equipment']=inventory
                with self.assertRaises(ValueError): app.import_character(bundle)
                self.assertEqual(app.get(character['id']),character)
            with self.assertRaises(SaveConflict):
                app.purchase_equipment(character['id'],revision=0,item_id='plastic-man')
            self.assertEqual(app.get(character['id']),character)
            bundle = app.export_character(character['id'])
            del bundle['character']['additional_rule_packs']['rifts-equipment']
            with self.assertRaises(ValueError): app.import_character(bundle)
            bundle = app.export_character(character['id'])
            next(pack for pack in bundle['rule_packs'] if pack['id']=='rifts-equipment')['items'][0]['cost_credits']=1
            with self.assertRaises(ValueError): app.import_character(bundle)
            archive = RuleArchive.load()
            newer = deepcopy(archive.resolve('rifts-equipment','1.0.0')); newer['version']='99.0.0'
            newer['items'][0]['aimed_bonus']=99
            current = CharacterApplication(directory,rule_archive=RuleArchive([*archive.definitions(),newer],
                {**archive.active_versions(),'rifts-equipment':'99.0.0'}))
            self.assertEqual(current.equipment_view(character['id'])['catalog'][0]['aimed_bonus'],2)
            inventory = deepcopy(character['equipment']); inventory['items'][0].update(equipped=True,shots=0)
            character = app.set_equipment(character['id'],revision=character['revision'],inventory=inventory)
            self.assertEqual(app.equipment_view(character['id'])['attacks'][0]['single']['value'],None)
            self.assertTrue(any('shots' in warning for warning in app.equipment_view(character['id'])['warnings']))
            inventory = deepcopy(character['equipment']); inventory['credits']=-9_007_199_254_740_991
            character = app.set_equipment(character['id'],revision=character['revision'],inventory=inventory)
            with self.assertRaises(ValueError):
                app.purchase_equipment(character['id'],revision=character['revision'],item_id='wilks-320')
            self.assertEqual(app.get(character['id']),character)
            hero = app.create(game='heroes-unlimited')
            with self.assertRaises(ValueError):
                app.purchase_equipment(hero['id'],revision=0,item_id='wilks-320')
            self.assertEqual(app.get(hero['id']),hero)
