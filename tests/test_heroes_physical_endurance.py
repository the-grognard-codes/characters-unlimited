import tempfile,unittest
from copy import deepcopy
from characters_unlimited.application import CharacterApplication

POWER='extraordinary-physical-endurance'
class HeroesPhysicalEnduranceTests(unittest.TestCase):
    def test_http_power_selection_is_token_and_revision_checked_and_projects_resource_receipts(self):
        import json,threading
        from urllib.request import urlopen,Request
        from urllib.error import HTTPError
        from characters_unlimited.server import create_server
        with tempfile.TemporaryDirectory() as directory:
            app=CharacterApplication(directory,die=lambda sides:4)
            c=app.create(game='heroes-unlimited')
            server=create_server(app)
            worker=threading.Thread(target=server.serve_forever,daemon=True);worker.start()
            try:
                base=f'http://127.0.0.1:{server.server_port}'
                with urlopen(base+'/api/bootstrap',timeout=5) as response:token=json.load(response)['token']
                path=base+'/api/characters/'+c['id']
                headers={'Content-Type':'application/json','X-Session-Token':token,'Origin':base}
                data=json.dumps({'revision':0,'selections':[POWER]}).encode()
                with self.assertRaises(HTTPError) as denied:urlopen(Request(path+'/hero-powers',data=data,headers={'Content-Type':'application/json'}),timeout=5)
                self.assertEqual(denied.exception.code,403);denied.exception.close()
                with urlopen(Request(path+'/hero-powers',data=data,headers=headers),timeout=5) as response:c=json.load(response)
                self.assertEqual(c['attributes']['PE']['value'],21)
                with self.assertRaises(HTTPError) as stale:urlopen(Request(path+'/hero-powers',data=data,headers=headers),timeout=5)
                self.assertEqual(stale.exception.code,409);stale.exception.close()
                data=json.dumps({'revision':c['revision']}).encode()
                with urlopen(Request(path+'/resources',data=data,headers=headers),timeout=5) as response:c=json.load(response)
                with urlopen(path+'/resources',timeout=5) as response:view=json.load(response)
                self.assertEqual([view['resources'][n]['value'] for n in ['HP','SDC']],[41,190])
            finally:
                server.shutdown();server.server_close();worker.join(timeout=5)

    def test_late_acquisition_raw_ones_manual_totals_and_other_powers_keep_starting_hp(self):
        with tempfile.TemporaryDirectory() as directory:
            app=CharacterApplication(directory,die=lambda sides:4)
            c=app.create(game='heroes-unlimited')
            c=app.reroll(c['id'],revision=0,generation={'reroll_ones':True,'extra_die':True})
            c=app.generate_resources(c['id'],revision=c['revision'])
            self.assertEqual(app.resource_view(c['id'])['resources']['HP']['value'],16)
            app.die=lambda sides:1
            c=app.select_hero_powers(c['id'],revision=c['revision'],selections=[POWER,'extraordinary-mental-affinity','extraordinary-physical-beauty'])
            self.assertEqual(c['attributes']['PE']['value'],18)
            self.assertEqual(c['attributes']['MA']['value'],25)
            self.assertEqual(c['attributes']['PB']['value'],22)
            view=app.resource_view(c['id'])
            self.assertEqual([view['resources'][n]['value'] for n in ['HP','SDC']],[20,70])
            c=app.set_resource(c['id'],revision=c['revision'],resource='HP',mode='adjustment',value=5)
            c=app.set_resource(c['id'],revision=c['revision'],resource='SDC',mode='fixed',value=80)
            c=app.set_attribute(c['id'],revision=c['revision'],attribute='PE',mode='fixed',value=30)
            app.die=lambda sides:4
            c=app.reroll(c['id'],revision=c['revision'],attribute='PE')
            c=app.select_hero_powers(c['id'],revision=c['revision'],selections=['extraordinary-mental-affinity','extraordinary-physical-beauty'])
            view=app.resource_view(c['id'])
            self.assertEqual([view['resources'][n]['value'] for n in ['HP','SDC']],[21,80])
            restored=app.import_character(app.export_character(c['id']))
            self.assertEqual(restored['roll_history'],c['roll_history'])
            self.assertEqual(restored['resource_attribute_snapshot'],c['resource_attribute_snapshot'])

    def test_invalid_group_dice_sources_modifiers_and_snapshots_reject_without_save_loss(self):
        from characters_unlimited.storage import SaveConflict
        with tempfile.TemporaryDirectory() as directory:
            app=CharacterApplication(directory,die=lambda sides:4)
            c=app.create(game='heroes-unlimited')
            for face in (0,7,True,2.5):
                app.die=lambda sides:face
                with self.assertRaises(ValueError):app.select_hero_powers(c['id'],revision=0,selections=[POWER])
                self.assertEqual(app.get(c['id']),c)
            app.die=lambda sides:4
            c=app.select_hero_powers(c['id'],revision=0,selections=[POWER])
            c=app.generate_resources(c['id'],revision=c['revision'])
            c=app.reroll(c['id'],revision=c['revision'],attribute='PE')
            with self.assertRaises(SaveConflict):app.select_hero_powers(c['id'],revision=0,selections=[])
            bundle=app.export_character(c['id'])
            for issue in ('group','die','level','source','current','history','snapshot'):
                with self.subTest(issue=issue):
                    bad=deepcopy(bundle);hero=bad['character'];receipt=hero['hero_powers']['acquisitions'][0]
                    if issue=='group':receipt['rolls'].pop('SDC')
                    elif issue=='die':receipt['rolls']['SDC'][0]=5
                    elif issue=='level':receipt['rolls']['HP-levels'].append(4)
                    elif issue=='source':receipt['source']['printed_page']=1
                    else:
                        attrs=hero['attributes'] if issue=='current' else hero['roll_history'][-1]['attributes'] if issue=='history' else hero['resource_attribute_snapshot']
                        attrs['PE']['modifiers'][0]['value']=10
                        attrs['PE']['value']+=1
                    with self.assertRaises(ValueError):app.import_character(bad)
                    self.assertEqual(app.get(c['id']),c)

    def test_old_power_pins_require_explicit_update_and_inactive_definitions_stay_immutable(self):
        from characters_unlimited.rules import RuleArchive
        with tempfile.TemporaryDirectory() as directory:
            archive=RuleArchive.load()
            legacy=RuleArchive(archive.definitions(),{**archive.active_versions(),'heroes-super-abilities':'1.2.0'})
            earlier=CharacterApplication(directory,die=lambda sides:4,rule_archive=legacy)
            c=earlier.create(game='heroes-unlimited')
            c=earlier.select_hero_powers(c['id'],revision=0,selections=['extraordinary-mental-affinity'])
            receipt=deepcopy(c['hero_powers']['acquisitions'])
            app=CharacterApplication(directory,die=lambda sides:4)
            with self.assertRaises(ValueError):app.select_hero_powers(c['id'],revision=c['revision'],selections=[POWER])
            preview=app.preview_rule_upgrade(c['id'])
            c=app.apply_rule_upgrade(c['id'],revision=c['revision'],token=preview['token'])['character']
            self.assertEqual(c['hero_powers']['acquisitions'],receipt)
            c=app.select_hero_powers(c['id'],revision=c['revision'],selections=['extraordinary-mental-affinity',POWER])
            c=app.select_hero_powers(c['id'],revision=c['revision'],selections=[])
            corrected=deepcopy(archive.active('heroes-super-abilities'));corrected['version']='99.0.0'
            next(row for row in corrected['powers'] if row['id']==POWER)['hp_per_level']['sides']=6
            incompatible=CharacterApplication(directory,rule_archive=RuleArchive([*archive.definitions(),corrected],{**archive.active_versions(),'heroes-super-abilities':'99.0.0'}))
            with self.assertRaisesRegex(ValueError,'acquired power'):incompatible.preview_rule_upgrade(c['id'])
            self.assertEqual(app.get(c['id']),c)

    def test_editable_pdf_has_additive_power_receipts_saving_units_and_blank_ungenerated_resources(self):
        from io import BytesIO
        from pypdf import PdfReader
        with tempfile.TemporaryDirectory() as directory:
            app=CharacterApplication(directory,die=lambda sides:4)
            c=app.create(game='heroes-unlimited')
            c=app.select_hero_powers(c['id'],revision=0,selections=[POWER])
            fields=PdfReader(BytesIO(app.export_pdf(c['id']))).get_fields()
            assert fields is not None
            self.assertEqual(fields['HP']['/V'],'')
            self.assertEqual(fields['SAVE_MAGIC']['/V'],'+3')
            self.assertEqual(fields['SAVE_POISON']['/V'],'+3')
            self.assertEqual(fields['SAVE_COMA']['/V'],'+12%')
            text='\n'.join(str(row.get('/V','')) for row in fields.values())
            self.assertIn('HP level 1 +4 (dice [4])',text)
            self.assertIn('Fatigue 1/10 normal',text)
            self.assertNotIn('recorded target None',text)
            c=app.generate_resources(c['id'],revision=c['revision'])
            fields=PdfReader(BytesIO(app.export_pdf(c['id']))).get_fields()
            assert fields is not None
            self.assertEqual(fields['HP']['/V'],'41')
            self.assertEqual(fields['SDC']['/V'],'190')

    def test_ordinary_pe_saves_and_fatigue_use_effective_attributes_without_direct_power_bonuses(self):
        with tempfile.TemporaryDirectory() as directory:
            app=CharacterApplication(directory,die=lambda sides:4)
            c=app.create(game='heroes-unlimited')
            c=app.select_hero_powers(c['id'],revision=0,selections=[POWER])
            view=app.hero_powers_view(c['id'])
            self.assertEqual(view['saving_bonuses']['poison']['value'],3)
            self.assertEqual(view['saving_bonuses']['magic']['value'],3)
            self.assertEqual(view['saving_bonuses']['coma-death']['value'],12)
            self.assertEqual(view['saving_bonuses']['coma-death']['unit'],'percentage-points')
            self.assertEqual(view['saving_bonuses']['poison']['contributions'],{'P.E.':3})
            self.assertEqual(view['fatigue_rate'],{'numerator':1,'denominator':10})
            for score,poison,coma in [(15,0,0),(30,8,30),(31,8,31),(60,8,60),(0,None,None)]:
                c=app.set_attribute(c['id'],revision=c['revision'],attribute='PE',mode='fixed',value=score)
                view=app.hero_powers_view(c['id'])
                self.assertEqual(view['saving_bonuses']['poison']['value'],poison)
                self.assertEqual(view['saving_bonuses']['coma-death']['value'],coma)
            c=app.select_hero_powers(c['id'],revision=c['revision'],selections=[])
            self.assertEqual(app.hero_powers_view(c['id'])['fatigue_rate'],{'numerator':1,'denominator':1})

    def test_additive_endurance_resource_dice_include_level_one_and_reselection_never_rerolls(self):
        with tempfile.TemporaryDirectory() as directory:
            draws=[]
            def die(sides):draws.append(sides);return 4
            app=CharacterApplication(directory,die=die)
            c=app.create(game='heroes-unlimited')
            c=app.select_education(c['id'],revision=0,method='choose',education_id='high-school')
            c=app.select_hero_secondary(c['id'],revision=c['revision'],selections=['body-building','running'])
            start=len(draws)
            c=app.select_hero_powers(c['id'],revision=c['revision'],selections=[POWER])
            self.assertEqual(c['attributes']['PE']['value'],22)
            self.assertCountEqual(draws[start:],[6,4,4,4,4,6,6,6,4])
            receipt=deepcopy(c['hero_powers'])
            c=app.generate_resources(c['id'],revision=c['revision'])
            view=app.resource_view(c['id'])
            self.assertEqual([view['resources'][n]['value'] for n in ['HP','SDC','PPE']],[42,204,24])
            count=len(draws)
            c=app.select_hero_powers(c['id'],revision=c['revision'],selections=[])
            self.assertEqual(c['attributes']['PE']['value'],13)
            view=app.resource_view(c['id'])
            self.assertEqual([view['resources'][n]['value'] for n in ['HP','SDC']],[26,44])
            c=app.select_hero_powers(c['id'],revision=c['revision'],selections=[POWER])
            self.assertEqual(len(draws),count)
            self.assertEqual(c['hero_powers']['acquisitions'],receipt['acquisitions'])
            self.assertEqual(app.resource_view(c['id'])['resources']['HP']['value'],42)
            restored=app.import_character(app.export_character(c['id']))
            self.assertEqual(restored['hero_powers'],c['hero_powers'])
            self.assertEqual(app.resource_view(restored['id'])['resources']['HP']['value'],42)
            self.assertEqual(CharacterApplication(directory).get(c['id']),c)
