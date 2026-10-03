"""Source-grounded one-time Vagabond funds through the character seam."""

from io import BytesIO
import tempfile
import threading
import json
import unittest
from urllib.request import Request, urlopen
from urllib.error import HTTPError

from pypdf import PdfReader

from characters_unlimited.application import CharacterApplication, SaveConflict
from characters_unlimited.rules import RuleArchive
from characters_unlimited.server import create_server


class StartingFundsWorkflowTests(unittest.TestCase):
    def test_http_generation_is_protected_revision_checked_and_cannot_repeat(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory,die=lambda sides:1)
            character = app.create()
            server = create_server(app)
            worker = threading.Thread(target=server.serve_forever,daemon=True); worker.start()
            try:
                base = f'http://127.0.0.1:{server.server_port}'
                with urlopen(base+'/api/bootstrap',timeout=5) as response: token = json.load(response)['token']
                path = base+'/api/characters/'+character['id']+'/starting-funds'
                payload = json.dumps({'revision':0}).encode()
                for headers in ({},{'X-Session-Token':token,'Origin':'https://elsewhere.invalid'}):
                    with self.assertRaises(HTTPError) as rejected:
                        urlopen(Request(path,data=payload,headers=headers),timeout=5)
                    self.assertEqual(rejected.exception.code,403); rejected.exception.close()
                headers = {'X-Session-Token':token,'Origin':base,'Content-Type':'application/json'}
                with urlopen(Request(path,data=payload,headers=headers),timeout=5) as response: saved=json.load(response)
                self.assertEqual(saved['equipment']['credits'],200)
                for revision,code in ((0,409),(saved['revision'],400)):
                    with self.assertRaises(HTTPError) as rejected:
                        urlopen(Request(path,data=json.dumps({'revision':revision}).encode(),headers=headers),timeout=5)
                    self.assertEqual(rejected.exception.code,code); rejected.exception.close()
                self.assertEqual(app.get(character['id']),saved)
            finally:
                server.shutdown(); worker.join(timeout=2); server.server_close()

    def test_once_only_credits_and_goods_ignore_house_options_and_survive_purchase_portability_and_pdf(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory,die=lambda sides:4)
            character = app.create(generation={'reroll_ones':True,'extra_die':True})
            self.assertFalse(app.equipment_view(character['id'])['starting_funds']['generated'])
            self.assertNotIn('starting_funds',app.get(character['id']))
            character = app.set_equipment(character['id'],revision=0,inventory={'credits':500,'items':[]})
            faces = iter([1,2,3,4])
            app.die = lambda sides:next(faces)
            character = app.generate_starting_funds(character['id'],revision=1)
            self.assertEqual(character['starting_funds']['credits']['rolls'],[1,2])
            self.assertEqual(character['starting_funds']['credits']['value'],300)
            self.assertEqual(character['starting_funds']['saleable_goods']['rolls'],[3,4])
            self.assertEqual(character['starting_funds']['saleable_goods']['value'],700)
            self.assertEqual(character['equipment']['credits'],800)
            self.assertEqual(character['starting_funds']['credits']['source']['pages'],[98])
            self.assertIsNone(next(faces,None))
            with self.assertRaises(ValueError):
                app.generate_starting_funds(character['id'],revision=character['revision'])
            character = app.purchase_equipment(character['id'],revision=character['revision'],item_id='wilks-320')
            self.assertEqual(character['equipment']['credits'],-10200)
            view = app.equipment_view(character['id'])
            self.assertEqual(view['starting_funds']['funds'],character['starting_funds'])
            reopened = CharacterApplication(directory)
            self.assertEqual(reopened.get(character['id']),character)
            duplicate = reopened.duplicate(character['id'])
            imported = reopened.import_character(reopened.export_character(character['id']))
            for copy in (duplicate,imported):
                self.assertEqual(copy['starting_funds'],character['starting_funds'])
                self.assertEqual(copy['equipment'],character['equipment'])
            fields = PdfReader(BytesIO(reopened.export_pdf(character['id']))).get_fields()
            assert fields is not None
            values = ' '.join(str(field.get('/V','')) for field in fields.values())
            self.assertIn('Starting credits: 300',values)
            self.assertIn('saleable goods',values)
            self.assertIn('700',values)
            self.assertIn('Current credits: -10200',values)

    def test_old_pins_need_explicit_update_before_generation_and_recorded_rules_cannot_be_reinterpreted(self):
        with tempfile.TemporaryDirectory() as directory:
            archive = RuleArchive.load()
            earlier = CharacterApplication(directory,die=lambda sides:4,rule_archive=RuleArchive(
                archive.definitions(),{**archive.active_versions(),'rifts-equipment':'1.0.0'}))
            character = earlier.create()
            character = earlier.set_equipment(character['id'],revision=0,inventory={'credits':10,'items':[]})
            current = CharacterApplication(directory,die=lambda sides:1)
            self.assertFalse(current.equipment_view(character['id'])['starting_funds']['supported'])
            with self.assertRaises(ValueError): current.generate_starting_funds(character['id'],revision=1)
            preview = current.preview_rule_upgrade(character['id'])
            self.assertTrue(any('Starting funds' in row['name'] for row in preview['equipment']))
            character = current.apply_rule_upgrade(character['id'],revision=1,token=preview['token'])['character']
            character = current.generate_starting_funds(character['id'],revision=character['revision'])
            self.assertEqual(character['equipment']['credits'],210)
            changed = archive.active('rifts-equipment'); changed['version']='99.0.0'
            changed['starting_funds']['definitions'][0]['multiplier']=200
            newer = CharacterApplication(directory,rule_archive=RuleArchive([*archive.definitions(),changed],
                {**archive.active_versions(),'rifts-equipment':'99.0.0'}))
            with self.assertRaisesRegex(ValueError,'recorded starting'):
                newer.preview_rule_upgrade(character['id'])
            self.assertEqual(newer.get(character['id']),character)

    def test_invalid_rolls_overflow_stale_cross_game_and_tampered_imports_leave_save_intact(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory,die=lambda sides:4)
            character = app.create()
            character = app.set_equipment(character['id'],revision=0,
                inventory={'credits':9_007_199_254_740_991,'items':[]})
            with self.assertRaises(ValueError): app.generate_starting_funds(character['id'],revision=1)
            self.assertEqual(app.get(character['id']),character)
            character = app.set_equipment(character['id'],revision=1,inventory={'credits':0,'items':[]})
            for invalid in (True,0,7):
                app.die = lambda sides,value=invalid:value
                with self.assertRaises(ValueError): app.generate_starting_funds(character['id'],revision=2)
                self.assertEqual(app.get(character['id']),character)
            with self.assertRaises(SaveConflict): app.generate_starting_funds(character['id'],revision=1)
            app.die = lambda sides:2
            hero = app.create(game='heroes-unlimited')
            with self.assertRaises(ValueError): app.generate_starting_funds(hero['id'],revision=0)
            character = app.generate_starting_funds(character['id'],revision=2)
            for field,value in [('rolls',[True,2]),('value',1),('source',{}),('rolls',[2])]:
                bundle = app.export_character(character['id'])
                bundle['character']['starting_funds']['credits'][field]=value
                with self.assertRaises(ValueError): app.import_character(bundle)
                self.assertEqual(app.get(character['id']),character)
            bundle = app.export_character(character['id'])
            del bundle['character']['additional_rule_packs']['rifts-equipment']
            with self.assertRaises(ValueError): app.import_character(bundle)


if __name__ == '__main__':
    unittest.main()
