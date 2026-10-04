import tempfile,unittest
from characters_unlimited.application import CharacterApplication

class HeroesPhysicalSecondaryTests(unittest.TestCase):
    def test_outside_program_group_physical_choice_is_retained_without_an_acquisition(self):
        with tempfile.TemporaryDirectory() as directory:
            app=CharacterApplication(directory,die=lambda sides:4)
            hero=app.create(game='heroes-unlimited')
            hero=app.select_education(hero['id'],revision=0,method='choose',education_id='college-one')
            selection={'slot':0,'program':'computer','choices':{'repair-radio':['running']}}
            hero=app.select_hero_programs(hero['id'],revision=hero['revision'],selections=[selection])
            self.assertEqual(hero['hero_program_selections'],[selection])
            self.assertEqual(hero['physical_acquisitions'],{})
            self.assertEqual(hero['attributes']['PE']['value'],12)
            view=app.hero_program_view(hero['id'])
            self.assertEqual(view['physical_selections'],[])
            self.assertTrue(any('outside-group' in row for row in view['warnings']))
            restored=app.import_character(app.export_character(hero['id']))
            self.assertEqual(restored['physical_acquisitions'],{})

    def test_physical_secondaries_add_once_and_retain_dice_and_initial_hp_on_removal(self):
        with tempfile.TemporaryDirectory() as directory:
            draws=[]
            def die(sides):
                draws.append(sides)
                return 4
            app=CharacterApplication(directory,die=die)
            hero=app.create(game='heroes-unlimited')
            hero=app.select_education(hero['id'],revision=0,method='choose',education_id='high-school')
            initial_count=len(draws)
            choices=['body-building','running']
            hero=app.select_hero_secondary(hero['id'],revision=hero['revision'],selections=choices)
            self.assertEqual([hero['attributes'][name]['value'] for name in ['PS','PE','SPD']],[14,13,28])
            self.assertEqual(draws[initial_count:],[4,4,4,4,6])
            receipts=hero['physical_acquisitions']
            hero=app.generate_resources(hero['id'],revision=hero['revision'])
            view=app.resource_view(hero['id'])
            self.assertEqual([view['resources'][name]['value'] for name in ['HP','SDC','PPE']],[17,44,24])
            generated_count=len(draws)
            hero=app.select_hero_secondary(hero['id'],revision=hero['revision'],selections=[])
            self.assertEqual([hero['attributes'][name]['value'] for name in ['PS','PE','SPD']],[12,12,12])
            view=app.resource_view(hero['id'])
            self.assertEqual([view['resources'][name]['value'] for name in ['HP','SDC']],[17,30])
            hero=app.select_hero_secondary(hero['id'],revision=hero['revision'],selections=choices+choices)
            self.assertEqual(hero['physical_acquisitions'],receipts)
            self.assertEqual(len(draws),generated_count)
            self.assertEqual(hero['attributes']['PS']['value'],14)
            self.assertEqual(app.resource_view(hero['id'])['resources']['SDC']['value'],44)
            self.assertEqual(app.hero_program_view(hero['id'])['secondary']['used'],4)

    def test_retained_physical_dice_modifiers_and_hp_snapshot_survive_portable_reopening(self):
        with tempfile.TemporaryDirectory() as directory:
            app=CharacterApplication(directory,die=lambda sides:4)
            hero=app.create(game='heroes-unlimited')
            hero=app.select_education(hero['id'],revision=0,method='choose',education_id='high-school')
            hero=app.select_hero_secondary(hero['id'],revision=hero['revision'],selections=['running'])
            hero=app.generate_resources(hero['id'],revision=hero['revision'])
            hero=app.reroll(hero['id'],revision=hero['revision'],attribute='PE')
            hero=app.select_hero_secondary(hero['id'],revision=hero['revision'],selections=[])
            restored=app.import_character(app.export_character(hero['id']))
            self.assertEqual(restored['physical_acquisitions'],hero['physical_acquisitions'])
            self.assertEqual(restored['resource_attribute_snapshot'],hero['resource_attribute_snapshot'])
            self.assertEqual(restored['roll_history'],hero['roll_history'])
            self.assertEqual(app.resource_view(restored['id'])['resources']['HP']['value'],17)
            self.assertEqual(CharacterApplication(directory).get(hero['id']),hero)

    def test_editable_pdf_lists_physical_effects_dice_and_sources_without_percentages(self):
        from io import BytesIO
        from pypdf import PdfReader
        with tempfile.TemporaryDirectory() as directory:
            app=CharacterApplication(directory,die=lambda sides:4)
            hero=app.create(game='heroes-unlimited')
            hero=app.select_education(hero['id'],revision=0,method='choose',education_id='high-school')
            hero=app.select_hero_secondary(hero['id'],revision=hero['revision'],selections=['body-building','running'])
            hero=app.generate_resources(hero['id'],revision=hero['revision'])
            fields=PdfReader(BytesIO(app.export_pdf(hero['id']))).get_fields()
            assert fields is not None
            self.assertNotIn('skills.running.percentage',fields)
            self.assertEqual(fields['SDC']['/V'],'44')
            text='\n'.join(str(row.get('/V','')) for row in fields.values())
            self.assertIn('Physical: Body Building & Weight Lifting',text)
            self.assertIn('Physical: Running',text)
            self.assertIn('SPD +16 (dice [4, 4, 4, 4])',text)
            self.assertIn('printed pp. 56 / PDF pp. 57',text)

    def test_upgrade_rejects_changed_inactive_physical_definitions_without_reroll_or_migration(self):
        from copy import deepcopy
        from characters_unlimited.rules import RuleArchive
        with tempfile.TemporaryDirectory() as directory:
            app=CharacterApplication(directory,die=lambda sides:4)
            hero=app.create(game='heroes-unlimited')
            hero=app.select_education(hero['id'],revision=0,method='choose',education_id='high-school')
            hero=app.select_hero_secondary(hero['id'],revision=hero['revision'],selections=['running'])
            hero=app.select_hero_secondary(hero['id'],revision=hero['revision'],selections=[])
            archive=RuleArchive.load()
            for changed_field in ('attributes','name','guidance','prerequisites'):
                with self.subTest(changed_field=changed_field):
                    correction=deepcopy(archive.active('heroes-program-skills'))
                    correction['version']='99.0.0'
                    running=next(row for row in correction['skills'] if row['id']=='running')
                    if changed_field=='attributes':running['attributes']['PE']['bonus']=2
                    elif changed_field=='name':running['name']='Rewritten Running'
                    else:running[changed_field]=['changed']
                    newer=CharacterApplication(directory,rule_archive=RuleArchive([*archive.definitions(),correction],{**archive.active_versions(),'heroes-program-skills':'99.0.0'}))
                    with self.assertRaises(ValueError):newer.preview_rule_upgrade(hero['id'])
                    self.assertEqual(newer.get(hero['id']),hero)

    def test_manual_values_late_running_and_raw_house_rule_dice_preserve_initial_contributions(self):
        with tempfile.TemporaryDirectory() as directory:
            app=CharacterApplication(directory,die=lambda sides:4)
            hero=app.create(game='heroes-unlimited')
            hero=app.select_education(hero['id'],revision=0,method='choose',education_id='high-school')
            hero=app.reroll(hero['id'],revision=hero['revision'],generation={'reroll_ones':True,'extra_die':True})
            hero=app.set_attribute(hero['id'],revision=hero['revision'],attribute='PE',mode='fixed',value=16)
            hero=app.generate_resources(hero['id'],revision=hero['revision'])
            draws=[]
            def raw(sides):
                draws.append(sides)
                return 1
            app.die=raw
            hero=app.select_hero_secondary(hero['id'],revision=hero['revision'],selections=['running'])
            self.assertEqual(draws,[4,4,4,4,6])
            self.assertEqual(hero['attributes']['PE']['value'],16)
            self.assertEqual(hero['attributes']['SPD']['value'],16)
            self.assertEqual(app.resource_view(hero['id'])['resources']['HP']['value'],20)
            hero=app.set_attribute(hero['id'],revision=hero['revision'],attribute='PE',mode='calculated')
            self.assertEqual(hero['attributes']['PE']['value'],13)
            self.assertEqual(app.resource_view(hero['id'])['resources']['HP']['value'],20)
            hero=app.set_resource(hero['id'],revision=hero['revision'],resource='SDC',mode='fixed',value=80)
            self.assertEqual(app.resource_view(hero['id'])['resources']['SDC']['value'],80)
            hero=app.select_hero_secondary(hero['id'],revision=hero['revision'],selections=[])
            self.assertEqual(app.resource_view(hero['id'])['resources']['SDC']['value'],80)
            self.assertEqual(len(draws),5)

    def test_invalid_dice_stale_selections_and_forged_snapshot_or_history_leave_saved_work_intact(self):
        from copy import deepcopy
        from characters_unlimited.application import SaveConflict
        with tempfile.TemporaryDirectory() as directory:
            app=CharacterApplication(directory,die=lambda sides:4)
            hero=app.create(game='heroes-unlimited')
            hero=app.select_education(hero['id'],revision=0,method='choose',education_id='high-school')
            app.die=lambda sides:7
            with self.assertRaises(ValueError):app.select_hero_secondary(hero['id'],revision=hero['revision'],selections=['running'])
            self.assertEqual(app.get(hero['id']),hero)
            app.die=lambda sides:4
            hero=app.select_hero_secondary(hero['id'],revision=hero['revision'],selections=['running'])
            with self.assertRaises(SaveConflict):app.select_hero_secondary(hero['id'],revision=hero['revision']-1,selections=[])
            hero=app.generate_resources(hero['id'],revision=hero['revision'])
            hero=app.reroll(hero['id'],revision=hero['revision'],attribute='PE')
            bundle=app.export_character(hero['id'])
            for frame in ['resource_attribute_snapshot','history','receipt']:
                bad=deepcopy(bundle)
                if frame=='receipt':bad['character']['physical_acquisitions']['running']['rolls']['attribute:SPD'][0]=0
                elif frame=='history':bad['character']['roll_history'][-1]['attributes']['PE']['modifiers'][0]['source']['pages']=[999]
                else:bad['character'][frame]['PE']['modifiers'][0]['value']=2
                with self.assertRaises(ValueError):app.import_character(bad)
                self.assertEqual(app.get(hero['id']),hero)
            self.assertEqual(len(app.list()),1)

    def test_other_powers_and_program_changes_keep_physical_receipts_and_bonuses(self):
        with tempfile.TemporaryDirectory() as directory:
            app=CharacterApplication(directory,die=lambda sides:4)
            hero=app.create(game='heroes-unlimited')
            hero=app.select_education(hero['id'],revision=0,method='choose',education_id='college-one')
            hero=app.select_hero_secondary(hero['id'],revision=hero['revision'],selections=['running','body-building','palming'])
            receipts=hero['physical_acquisitions']
            hero=app.select_hero_powers(hero['id'],revision=hero['revision'],selections=['extraordinary-mental-affinity'])
            hero=app.select_hero_programs(hero['id'],revision=hero['revision'],selections=[{'slot':0,'program':'business'}])
            self.assertEqual(hero['physical_acquisitions'],receipts)
            self.assertEqual(hero['attributes']['PE']['value'],13)
            self.assertEqual(hero['attributes']['MA']['value'],28)
            view=app.hero_program_view(hero['id'])
            self.assertEqual(len(view['physical']['selected']),2)
            self.assertFalse(any(row['id']=='running' for row in view['skills']))
            self.assertEqual(next(row for row in view['skills'] if row['id']=='palming')['percentage'],30)

    def test_old_pins_require_update_before_physical_choices_and_compatible_receipts_survive(self):
        from copy import deepcopy
        from characters_unlimited.rules import RuleArchive
        with tempfile.TemporaryDirectory() as directory:
            archive=RuleArchive.load()
            old=CharacterApplication(directory,die=lambda sides:4,rule_archive=RuleArchive(archive.definitions(),{**archive.active_versions(),'heroes-program-skills':'1.10.0'}))
            hero=old.create(game='heroes-unlimited')
            hero=old.select_education(hero['id'],revision=0,method='choose',education_id='high-school')
            hero=old.select_hero_secondary(hero['id'],revision=hero['revision'],selections=['art'])
            app=CharacterApplication(directory,die=lambda sides:4)
            with self.assertRaises(ValueError):app.select_hero_secondary(hero['id'],revision=hero['revision'],selections=['running'])
            preview=app.preview_rule_upgrade(hero['id'])
            self.assertEqual(app.get(hero['id']),hero)
            hero=app.apply_rule_upgrade(hero['id'],revision=hero['revision'],token=preview['token'])['character']
            hero=app.select_hero_secondary(hero['id'],revision=hero['revision'],selections=['running'])
            receipts=hero['physical_acquisitions']
            correction=deepcopy(archive.active('heroes-program-skills'));correction['version']='99.0.0'
            newer=CharacterApplication(directory,die=lambda sides:0,rule_archive=RuleArchive([*archive.definitions(),correction],{**archive.active_versions(),'heroes-program-skills':'99.0.0'}))
            preview=newer.preview_rule_upgrade(hero['id'])
            hero=newer.apply_rule_upgrade(hero['id'],revision=hero['revision'],token=preview['token'])['character']
            self.assertEqual(hero['physical_acquisitions'],receipts)
            self.assertEqual(hero['attributes']['SPD']['value'],28)
            self.assertEqual(newer.import_character(newer.export_character(hero['id']))['physical_acquisitions'],receipts)

    def test_http_secondary_selection_returns_attribute_and_resource_effects_and_rejects_stale_changes(self):
        import json,threading
        from urllib.request import urlopen,Request
        from urllib.error import HTTPError
        from characters_unlimited.server import create_server
        with tempfile.TemporaryDirectory() as directory:
            app=CharacterApplication(directory,die=lambda sides:4)
            hero=app.create(game='heroes-unlimited')
            hero=app.select_education(hero['id'],revision=0,method='choose',education_id='high-school')
            server=create_server(app)
            worker=threading.Thread(target=server.serve_forever,daemon=True);worker.start()
            try:
                base=f'http://127.0.0.1:{server.server_port}'
                with urlopen(base+'/api/bootstrap',timeout=5) as response:token=json.load(response)['token']
                path=base+'/api/characters/'+hero['id']
                headers={'Content-Type':'application/json','X-Session-Token':token,'Origin':base}
                data=json.dumps({'revision':hero['revision'],'selections':['running','body-building']}).encode()
                with urlopen(Request(path+'/hero-secondary',data=data,headers=headers),timeout=5) as response:hero=json.load(response)
                self.assertEqual(hero['attributes']['PE']['value'],13)
                with urlopen(path+'/hero-programs',timeout=5) as response:view=json.load(response)
                self.assertEqual(len(view['physical']['selected']),2)
                with self.assertRaises(HTTPError) as stale:urlopen(Request(path+'/hero-secondary',data=data,headers=headers),timeout=5)
                self.assertEqual(stale.exception.code,409);stale.exception.close()
                data=json.dumps({'revision':hero['revision']}).encode()
                with urlopen(Request(path+'/resources',data=data,headers=headers),timeout=5) as response:hero=json.load(response)
                with urlopen(path+'/resources',timeout=5) as response:view=json.load(response)
                self.assertEqual(view['resources']['SDC']['value'],44)
                self.assertTrue(view['physical_supported'])
            finally:
                server.shutdown();server.server_close();worker.join(timeout=5)
