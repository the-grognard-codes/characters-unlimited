import json
import threading
from urllib.request import Request,urlopen
from urllib.error import HTTPError
from characters_unlimited.server import create_server
from io import BytesIO
from pypdf import PdfReader
from copy import deepcopy
from characters_unlimited.storage import SaveConflict
import tempfile,unittest
from characters_unlimited.application import CharacterApplication

class HeroesStartingResourceTests(unittest.TestCase):
    def test_initial_hit_points_record_effective_endurance_and_mutant_sdc(self):
        with tempfile.TemporaryDirectory() as directory:
            app=CharacterApplication(directory,die=lambda sides:4)
            hero=app.create(game='heroes-unlimited')
            hero=app.set_attribute(hero['id'],revision=0,attribute='PE',mode='fixed',value=16)
            hero=app.generate_resources(hero['id'],revision=hero['revision'])
            view=app.resource_view(hero['id'])
            self.assertEqual(view['resources']['HP']['value'],20)
            self.assertEqual(view['resources']['SDC']['value'],30)
            self.assertEqual(hero['resource_attribute_snapshot']['PE']['value'],16)
            self.assertEqual(hero['resources']['HP']['contributions'][1]['rolls'],[4])
            hero=app.set_attribute(hero['id'],revision=hero['revision'],attribute='PE',mode='fixed',value=25)
            self.assertEqual(app.resource_view(hero['id'])['resources']['HP']['value'],20)
            with self.assertRaises(ValueError):app.generate_resources(hero['id'],revision=hero['revision'])
            self.assertEqual(app.get(hero['id']),hero)

    def test_potential_psychic_energy_uses_six_raw_dice_without_attribute_options(self):
        with tempfile.TemporaryDirectory() as directory:
            app=CharacterApplication(directory,die=lambda sides:4)
            hero=app.create(game='heroes-unlimited',generation={'reroll_ones':True,'extra_die':True})
            calls=[]
            def die(sides):
                calls.append(sides)
                return 1
            app.die=die
            hero=app.generate_resources(hero['id'],revision=0)
            view=app.resource_view(hero['id'])
            self.assertEqual(view['resources']['PPE']['value'],6)
            self.assertEqual(calls,[6,6,6,6,6,6,6])
            self.assertEqual(hero['resources']['PPE']['contributions'][0]['rolls'],[1,1,1,1,1,1])
            self.assertEqual(view['resources']['HP']['value'],13)

    def test_generated_resources_reopen_portably_and_manual_totals_preserve_dice(self):
        with tempfile.TemporaryDirectory() as directory:
            app=CharacterApplication(directory,die=lambda sides:4)
            hero=app.create(game='heroes-unlimited')
            hero=app.generate_resources(hero['id'],revision=0)
            recorded=deepcopy(hero['resources']['HP']['contributions'])
            hero=app.set_resource(hero['id'],revision=hero['revision'],resource='HP',mode='adjustment',value=5)
            self.assertEqual(app.resource_view(hero['id'])['resources']['HP']['value'],21)
            hero=app.set_resource(hero['id'],revision=hero['revision'],resource='HP',mode='fixed',value=50)
            self.assertEqual(app.resource_view(hero['id'])['resources']['HP']['value'],50)
            self.assertEqual(hero['resources']['HP']['contributions'],recorded)
            imported=app.import_character(app.export_character(hero['id']))
            self.assertEqual(imported['resources'],hero['resources'])
            self.assertEqual(imported['resource_attribute_snapshot'],hero['resource_attribute_snapshot'])
            self.assertEqual(CharacterApplication(directory).resource_view(hero['id']),app.resource_view(hero['id']))
            hero=app.set_resource(hero['id'],revision=hero['revision'],resource='HP',mode='calculated')
            self.assertEqual(app.resource_view(hero['id'])['resources']['HP']['value'],16)

    def test_editable_sheet_uses_generated_resource_values_and_retained_sources(self):
        with tempfile.TemporaryDirectory() as directory:
            app=CharacterApplication(directory,die=lambda sides:4)
            hero=app.create(game='heroes-unlimited')
            hero=app.generate_resources(hero['id'],revision=0)
            fields=PdfReader(BytesIO(app.export_pdf(hero['id']))).get_fields()
            assert fields is not None
            self.assertEqual(fields['HP']['/V'],'16')
            self.assertEqual(fields['SDC']['/V'],'30')
            self.assertEqual(fields['PPE']['/V'],'24')
            text='\n'.join(str(row.get('/V','')) for row in fields.values())
            self.assertIn('Starting resources',text)
            self.assertIn('heroes-resources 1.0.0',text)

    def test_bad_dice_stale_requests_and_tampered_imports_preserve_saved_character(self):
        with tempfile.TemporaryDirectory() as directory:
            app=CharacterApplication(directory,die=lambda sides:4)
            hero=app.create(game='heroes-unlimited')
            app.die=lambda sides:0
            with self.assertRaises(ValueError):app.generate_resources(hero['id'],revision=0)
            self.assertEqual(app.get(hero['id']),hero)
            app.die=lambda sides:4
            hero=app.generate_resources(hero['id'],revision=0)
            with self.assertRaises(SaveConflict):app.generate_resources(hero['id'],revision=0)
            with self.assertRaises(SaveConflict):app.set_resource(hero['id'],revision=0,resource='HP',mode='fixed',value=100)
            bundle=app.export_character(hero['id'])
            for mutation in ['pin','dice','source','snapshot-power','invalid-snapshot']:
                bad=deepcopy(bundle)
                character=bad['character']
                if mutation=='pin':character['additional_rule_packs'].pop('heroes-resources')
                elif mutation=='dice':character['resources']['PPE']['contributions'][0]['rolls'][0]=0
                elif mutation=='source':character['resources']['SDC']['contributions'][0]['source']['pages']=[999]
                elif mutation=='invalid-snapshot':character['resource_attribute_snapshot']=['invalid']
                else:
                    snapshot=character['resource_attribute_snapshot']['PE']
                    snapshot['modifiers']=[{'id':'power-floor:forged','value':20,'rolls':[1],'source':deepcopy(snapshot['explanation']['source'])}]
                    snapshot['value']=20
                    character['resources']['HP']['contributions'][0]['value']=20
                with self.assertRaises(ValueError):app.import_character(bad)
            self.assertEqual(app.get(hero['id']),hero)
            self.assertEqual(len(app.list()),1)

    def test_local_http_adapter_generates_projects_and_edits_heroes_resources(self):
        with tempfile.TemporaryDirectory() as directory:
            app=CharacterApplication(directory,die=lambda sides:4)
            hero=app.create(game='heroes-unlimited')
            server=create_server(app)
            worker=threading.Thread(target=server.serve_forever,daemon=True);worker.start()
            try:
                base=f'http://127.0.0.1:{server.server_port}'
                with urlopen(base+'/api/bootstrap',timeout=5) as response:token=json.load(response)['token']
                path=base+'/api/characters/'+hero['id']
                headers={'Content-Type':'application/json','X-Session-Token':token,'Origin':base}
                with urlopen(Request(path+'/resources',data=b'{"revision":0}',headers=headers),timeout=5) as response:hero=json.load(response)
                with urlopen(path+'/resources',timeout=5) as response:view=json.load(response)
                self.assertEqual(view['resources']['HP']['value'],16)
                self.assertEqual(view['resources']['SDC']['value'],30)
                self.assertEqual(view['resources']['PPE']['value'],24)
                with self.assertRaises(HTTPError) as stale:urlopen(Request(path+'/resources',data=b'{"revision":0}',headers=headers),timeout=5)
                self.assertEqual(stale.exception.code,409);stale.exception.close()
                data=json.dumps({'revision':hero['revision'],'resource':'SDC','mode':'fixed','value':80}).encode()
                with urlopen(Request(path+'/resource',data=data,headers=headers),timeout=5) as response:hero=json.load(response)
                self.assertEqual(app.resource_view(hero['id'])['resources']['SDC']['value'],80)
            finally:
                server.shutdown();server.server_close();worker.join(timeout=5)
