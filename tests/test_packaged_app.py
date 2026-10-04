import os
from pathlib import Path
import socket
import subprocess
import tempfile
import time
import unittest
from urllib.error import URLError
from urllib.request import Request, urlopen
import json
from io import BytesIO
from copy import deepcopy
from pypdf import PdfReader
from characters_unlimited.application import CharacterApplication
from characters_unlimited.rules import RuleArchive


@unittest.skipUnless(os.getenv('CHARACTERS_UNLIMITED_EXE'), 'Frozen executable checked by the packaging workflow')
class PackagedApplicationTests(unittest.TestCase):
    def test_frozen_app_works_without_developer_tools_and_reopens_saved_characters(self):
        executable = Path(os.environ['CHARACTERS_UNLIMITED_EXE']).resolve()
        self.assertTrue(executable.is_file(), 'Build the Windows package first')
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            environment = dict(os.environ)
            environment['PATH'] = str(Path(os.environ['SystemRoot']) / 'System32')
            with socket.socket() as probe:
                probe.bind(('127.0.0.1', 0))
                port = probe.getsockname()[1]
            url = f'http://127.0.0.1:{port}'
            def request(path, value=None, token=None):
                body = None if value is None else json.dumps(value).encode()
                headers = {'Content-Type':'application/json'}
                if token is not None:
                    headers['X-Session-Token'] = token
                with urlopen(Request(url + path, data=body, headers=headers), timeout=15) as response:
                    payload = response.read()
                    return payload if response.headers.get_content_type() == 'application/pdf' else json.loads(payload)
            def launch(gui=False):
                startup = subprocess.STARTUPINFO()
                startup.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startup.wShowWindow = subprocess.SW_HIDE
                process = subprocess.Popen([str(executable), '--no-browser' if gui else '--headless',
                                            '--port', str(port), '--data-dir', str(root / 'saves')],
                                           cwd=root, env=environment, startupinfo=startup)
                try:
                    deadline = time.monotonic() + 30
                    while time.monotonic() < deadline:
                        if process.poll() is not None:
                            self.fail(f'Packaged app exited with {process.returncode}')
                        try:
                            return process, request('/api/bootstrap')
                        except URLError:
                            time.sleep(.1)
                    self.fail('Packaged app did not start within 30 seconds')
                except BaseException:
                    process.terminate(); process.wait(timeout=10)
                    raise
            process, bootstrap = launch()
            try:
                with urlopen(url, timeout=15) as page:
                    self.assertIn(b'Export editable PDF', page.read())
                token = bootstrap['token']
                character = request('/api/characters', {'name':'Packaged Rowan'}, token)
                identifier = character['id']
                character = request('/api/characters/'+identifier+'/required-skills',
                    {'revision':character['revision'],'choices':{'native_language':'American',
                     'other_languages':['Spanish','Dragonese'],'pilot':'automobile','repair':'general-repair'}},token)
                required = request('/api/characters/'+identifier+'/skills')
                self.assertEqual(required['required_remaining'],
                                 {'native_language':0,'other_languages':0,'pilot':0,'repair':0})
                self.assertEqual(len(required['required_catalog']['groups']),4)
                self.assertEqual(len(character['attributes']), 8)
                self.assertEqual(request('/api/characters/' + identifier)['name'], 'Packaged Rowan')
                before_physical = character['attributes']
                character = request('/api/characters/'+identifier+'/skills',
                                    {'revision':character['revision'],'selections':[
                                        {'skill_id':'athletics','pool':'related'},
                                        {'skill_id':'body-building','pool':'related'}]},token)
                physical_view = request('/api/characters/'+identifier+'/skills')
                self.assertEqual(character['attributes']['PS']['value'],before_physical['PS']['value']+3)
                speed_roll = character['physical_acquisitions']['athletics']['rolls']['attribute:SPD'][0]
                self.assertTrue(1<=speed_roll<=6)
                self.assertEqual(character['attributes']['SPD']['value'],before_physical['SPD']['value']+speed_roll)
                self.assertEqual(physical_view['remaining']['related'],3)
                character = request('/api/characters/'+identifier+'/resources',{'revision':character['revision']},token)
                resource_view = request('/api/characters/'+identifier+'/resources')
                hp_roll = character['resources']['HP']['contributions'][1]['rolls'][0]
                self.assertEqual(resource_view['resources']['HP']['value'],before_physical['PE']['value']+hp_roll)
                sdc_base = sum(item['value'] for item in character['resources']['SDC']['contributions'])
                sdc_roll = character['physical_acquisitions']['athletics']['rolls']['resource:SDC'][0]
                self.assertEqual(resource_view['resources']['SDC']['value'],sdc_base+sdc_roll+10)
                coverage = request('/api/coverage')
                self.assertIn('books', coverage)
                self.assertEqual(coverage['summary']['canonical_options'],718)
                self.assertEqual(coverage['summary']['unassigned_options'],0)
                self.assertEqual(coverage['summary']['mechanically_reviewed'],0)
                self.assertTrue(coverage['content_tickets'])
                character = request('/api/characters/'+identifier+'/skills',
                                    {'revision':character['revision'],'selections':[
                                        {'skill_id':'athletics','pool':'related'},
                                        {'skill_id':'body-building','pool':'related'},
                                        {'skill_id':'physical-labor','pool':'related'},
                                        {'skill_id':'running','pool':'related'},
                                        {'skill_id':'boxing','pool':'related'},
                                        {'skill_id':'swimming','pool':'secondary'}]},token)
                endurance = request('/api/characters/'+identifier+'/skills')
                self.assertEqual(endurance['combat']['totals']['attacks']['value'],5)
                self.assertEqual(endurance['combat']['totals']['parry']['contributions']['Boxing'],2)
                self.assertEqual(endurance['combat']['totals']['parry']['contributions']['Athletics (General)'],1)
                self.assertEqual(len(character['physical_acquisitions']['boxing']['rolls']['resource:SDC']),3)
                running = next(skill for skill in endurance['selected'] if skill['id']=='running')
                self.assertEqual(running['activities'][0]['miles'],character['attributes']['PE']['value']*0.5)
                swimming = next(skill for skill in endurance['selected'] if skill['id']=='swimming')
                self.assertEqual(swimming['per_level'],5)
                self.assertEqual(swimming['contributions']['base'],50)
                self.assertEqual(swimming['activities'][0]['yards_per_melee'],character['attributes']['PS']['value']*3)
                self.assertEqual(swimming['activities'][0]['minutes'],character['attributes']['PE']['value'])
                self.assertEqual(character['physical_acquisitions']['swimming']['rolls'],{})
                self.assertEqual(request('/api/characters/'+identifier+'/resources')['resources']['HP']['value'],resource_view['resources']['HP']['value'])
                character = request('/api/characters/'+identifier+'/equipment',
                    {'revision':character['revision'],'inventory':{'credits':50000,'items':[]}},token)
                character = request('/api/characters/'+identifier+'/starting-funds',
                    {'revision':character['revision']},token)
                starting_credit_value = sum(character['starting_funds']['credits']['rolls'])*100
                self.assertEqual(character['equipment']['credits'],50000+starting_credit_value)
                self.assertEqual(len(character['starting_funds']['saleable_goods']['rolls']),2)
                character = request('/api/characters/'+identifier+'/starting-gear',
                    {'revision':character['revision']},token)
                self.assertEqual(len(character['starting_gear']['grants']),18)
                character = request('/api/characters/'+identifier+'/starting-choices',
                    {'revision':character['revision'],'choices':{'armor':'plastic-man','gun':'wilks-320',
                     'knife':'knife-large','transport':'vagabond-junker-car'}},token)
                self.assertEqual(len(character['starting_choices']['grants']),5)
                for item_id in ('wilks-320','plastic-man'):
                    character = request('/api/characters/'+identifier+'/purchase-equipment',
                        {'revision':character['revision'],'item_id':item_id,'quantity':1},token)
                character = request('/api/characters/'+identifier+'/purchase-equipment',
                    {'revision':character['revision'],'item_id':'knife-large','unit_cost':30},token)
                character = request('/api/characters/'+identifier+'/purchase-equipment',
                    {'revision':character['revision'],'item_id':'standard-e-clip','quantity':2,'unit_cost':5000},token)
                character = request('/api/characters/'+identifier+'/split-equipment',
                    {'revision':character['revision'],'possession_id':character['equipment']['items'][-1]['id']},token)
                inventory = character['equipment']
                for item in inventory['items']: item['equipped']=True
                gun = next(item for item in inventory['items'] if item['item_id']=='wilks-320')
                clip = inventory['items'][-1]
                gun['shots'] = 3
                character = request('/api/characters/'+identifier+'/equipment',
                    {'revision':character['revision'],'inventory':inventory},token)
                character = request('/api/characters/'+identifier+'/reload-weapon',
                    {'revision':character['revision'],'weapon_possession_id':gun['id'],'clip_possession_id':clip['id']},token)
                character = request('/api/characters/'+identifier+'/combat',
                    {'revision':character['revision'],'choices':{'hand_to_hand':'basic','ancient':['knife'],
                     'modern':['energy-pistol']}},token)
                gear = request('/api/characters/'+identifier+'/equipment')
                self.assertEqual(gear['inventory']['credits'],10970+starting_credit_value)
                self.assertEqual(gear['carried_weight_lbs'],30)
                self.assertEqual(gear['unknown_carried_weight_quantity'],25)
                self.assertFalse(gear['carried_weight_complete'])
                self.assertEqual(gear['attacks'][0]['aimed']['contributions']['weapon_aimed_bonus'],2)
                self.assertEqual(gear['armor'][0]['locations']['main_body'],35)
                self.assertEqual(gear['melee_attacks'][0]['base_damage'],'1D6 S.D.C.')
                self.assertEqual(character['equipment']['items'][-1]['shots'],3)
                self.assertEqual(gear['attacks'][0]['shots'],20)
                portable = request('/api/characters/' + identifier + '/export')
                imported = request('/api/import', {'bundle':portable}, token)
                self.assertNotEqual(imported['id'], identifier)
                self.assertEqual(imported['physical_acquisitions'],character['physical_acquisitions'])
                self.assertEqual(imported['resources'],character['resources'])
                self.assertEqual(imported['equipment'],character['equipment'])
                self.assertEqual(imported['starting_funds'],character['starting_funds'])
                self.assertEqual(imported['starting_gear'],character['starting_gear'])
                self.assertEqual(imported['starting_choices'],character['starting_choices'])
                reader = PdfReader(BytesIO(request('/api/characters/' + identifier + '/pdf')))
                fields = reader.get_fields()
                assert fields is not None
                self.assertEqual(fields['NAME']['/V'], 'Packaged Rowan')
                self.assertEqual(fields['HIT POINTS']['/V'],str(resource_view['resources']['HP']['value']))
                self.assertTrue(reader.pages[0].get('/Annots'))
                pre_level = character
                character = request('/api/characters/'+identifier+'/advance',
                    {'revision':character['revision'],'method':'xp','value':1876},token)
                self.assertEqual(character['level'],2)
                advancement_die = character['advancement']['hp_roll']
                self.assertTrue(1<=advancement_die<=6)
                self.assertEqual(request('/api/characters/'+identifier+'/resources')['resources']['HP']['value'],
                                 resource_view['resources']['HP']['value']+advancement_die)
                self.assertEqual(request('/api/characters/'+identifier+'/skills')['combat']['totals']['parry']['contributions']['hand_to_hand'],2)
                portable_level = request('/api/characters/'+identifier+'/export')
                level_copy = request('/api/import',{'bundle':portable_level},token)
                self.assertEqual(level_copy['advancement'],character['advancement'])
                restored = request('/api/characters/'+identifier+'/undo-advancement',
                    {'revision':character['revision']},token)
                character = restored['character']
                self.assertEqual(character['equipment'],pre_level['equipment'])
                self.assertEqual(character['physical_acquisitions'],pre_level['physical_acquisitions'])
                self.assertEqual(request('/api/characters/'+restored['recovery']['id'])['level'],2)
                character = request('/api/characters/'+identifier+'/advance',
                    {'revision':character['revision'],'method':'level','value':2},token)
                self.assertEqual(character['advancement']['hp_roll'],advancement_die)
                character = request('/api/characters/'+identifier+'/advance',
                    {'revision':character['revision'],'method':'level','value':15},token)
                self.assertEqual(character['level'],15)
                combat = request('/api/characters/'+identifier+'/skills')['combat']
                self.assertEqual(combat['conditions']['critical']['natural_min'],19)
                self.assertIn('knee', [move['id'] for move in combat['unarmed']])
                fields = PdfReader(BytesIO(request('/api/characters/'+identifier+'/pdf'))).get_fields()
                assert fields is not None
                self.assertEqual(fields['CRITICAL STRIKE']['/V'], 'Natural 19–')
                self.assertIn('BODY FLIP THROW', fields)
                later_dice = [event['hp_roll'] for event in character['later_advancements']]
                self.assertEqual(len(later_dice),13)
                self.assertTrue(all(1 <= face <= 6 for face in later_dice))
                self.assertEqual(request('/api/characters/'+identifier+'/resources')['resources']['HP']['value'],
                                 resource_view['resources']['HP']['value']+advancement_die+sum(later_dice))
                restored = request('/api/characters/'+identifier+'/undo-advancement',
                    {'revision':character['revision']},token)
                character = restored['character']
                self.assertEqual(character['level'],14)
                character = request('/api/characters/'+identifier+'/advance',
                    {'revision':character['revision'],'method':'level','value':15},token)
                self.assertEqual([event['hp_roll'] for event in character['later_advancements']],later_dice)
                with urlopen(url + '/education.js', timeout=15) as script:
                    self.assertIn(b'loadEducation', script.read())
                with urlopen(url + '/resources.js',timeout=15) as script:
                    self.assertIn(b'renderResources',script.read())
                hero = request('/api/characters', {'name':'Packaged Beacon','game':'heroes-unlimited'}, token)
                hero = request('/api/characters/' + hero['id'] + '/education',
                               {'revision':0,'method':'choose','education_id':'military-specialist'}, token)
                education = request('/api/characters/' + hero['id'] + '/education')
                self.assertEqual(education['outcome']['secondary_count'], 5)
                hero = request('/api/characters/' + hero['id'] + '/hero-programs',
                               {'revision':hero['revision'],'selections':[{'slot':4,'program':'business'}]}, token)
                programs = request('/api/characters/' + hero['id'] + '/hero-programs')
                self.assertEqual(next(item for item in programs['skills'] if item['id'] == 'research')['contributions']['education'], 10)
                hero_pdf = PdfReader(BytesIO(request('/api/characters/'+hero['id']+'/pdf')))
                hero_fields = hero_pdf.get_fields()
                assert hero_fields is not None
                self.assertEqual(hero_fields['NAME']['/V'], 'Packaged Beacon')
                self.assertEqual(hero_fields['EDUCATION']['/V'], 'Military Specialist')
                self.assertEqual(hero_fields['HP'].get('/V', ''), '')
                self.assertTrue(all('HEROES UNLIMITED' in page.extract_text() for page in hero_pdf.pages))
                hero = request('/api/characters/'+hero['id']+'/hero-programs',
                               {'revision':hero['revision'],'selections':[{'slot':4,'program':'medical-assistant'}]},token)
                programs = request('/api/characters/'+hero['id']+'/hero-programs')
                paramedic = next(item for item in programs['skills'] if item['id']=='paramedic')
                self.assertEqual(paramedic['contributions']['education'],10)
                self.assertEqual(paramedic['contributions']['base'],40)
                self.assertEqual(paramedic['per_level'],5)
                hero = request('/api/characters/'+hero['id']+'/hero-secondary',
                               {'revision':hero['revision'],'selections':['research']},token)
                programs = request('/api/characters/'+hero['id']+'/hero-programs')
                self.assertEqual(programs['secondary']['remaining'],4)
                self.assertEqual(next(item for item in programs['skills'] if item['id']=='research')['contributions']['education'],0)
                computer_choices = [{'slot':4,'program':'computer','choices':{'repair-radio':['radio-basic']}}]
                hero = request('/api/characters/'+hero['id']+'/hero-programs',
                               {'revision':hero['revision'],'selections':computer_choices},token)
                programs = request('/api/characters/'+hero['id']+'/hero-programs')
                self.assertEqual(programs['program_choices'][0]['groups'][0]['remaining'],0)
                self.assertEqual(next(item for item in programs['skills'] if item['id']=='radio-basic')['contributions']['base'],45)
                self.assertEqual(next(item for item in programs['skills'] if item['id']=='radio-basic')['contributions']['education'],10)
                hero = request('/api/characters/'+hero['id']+'/hero-programs',
                               {'revision':hero['revision'],'selections':[
                                   {'slot':4,'program':'communications','choices':{'communications':['optic-systems']}}]},token)
                programs = request('/api/characters/'+hero['id']+'/hero-programs')
                video = next(item for item in programs['skills'] if item['id']=='tv-video')
                self.assertEqual(video['contributions']['education'],10)
                self.assertEqual(video['contributions']['Optic Systems'],5)
                self.assertEqual(video['per_level'],4)
                self.assertEqual(programs['program_choices'][0]['groups'][0]['remaining'],0)
                hero = request('/api/characters/'+hero['id']+'/hero-secondary',
                               {'revision':hero['revision'],'selections':['research','first-aid','holistic-medicine']},token)
                programs = request('/api/characters/'+hero['id']+'/hero-programs')
                self.assertEqual((programs['secondary']['used'],programs['secondary']['remaining']),(4,1))
                self.assertEqual(programs['secondary']['selection_costs']['holistic-medicine'],2)
                holistic = next(item for item in programs['skills'] if item['id']=='holistic-medicine')
                self.assertEqual(holistic['contributions']['base'],20)
                self.assertEqual(holistic['contributions']['education'],0)
                hero = request('/api/characters/'+hero['id']+'/power-budget',
                               {'revision':hero['revision'],'method':'choose','outcome_id':'continuous-mutation'},token)
                power_budget = request('/api/characters/'+hero['id']+'/power-budget')
                self.assertEqual(power_budget['budgets'], [{'name':'Major super ability OR Super psionic power','count':1}])
                hero = request('/api/characters/'+hero['id']+'/hero-powers',
                               {'revision':hero['revision'],'selections':['extraordinary-mental-affinity']},token)
                hero_powers = request('/api/characters/'+hero['id']+'/hero-powers')
                self.assertTrue(25 <= hero_powers['powers'][0]['target'] <= 30)
                self.assertEqual(hero_powers['powers'][0]['rolls'],hero['hero_powers']['acquisitions'][0]['rolls'])
                self.assertGreaterEqual(hero['attributes']['MA']['value'],hero_powers['powers'][0]['target'])
                hero = request('/api/characters/'+hero['id']+'/hero-powers',
                               {'revision':hero['revision'],'selections':['extraordinary-mental-affinity','extraordinary-mental-endurance']},token)
                hero_powers = request('/api/characters/'+hero['id']+'/hero-powers')
                endurance = next(row for row in hero_powers['powers'] if row['id']=='extraordinary-mental-endurance')
                self.assertTrue(23 <= endurance['target'] <= 29)
                self.assertEqual(len(endurance['rolls']),2)
                self.assertEqual(hero_powers['saving_bonuses']['psionics']['target'],12)
                hero = request('/api/characters/'+hero['id']+'/hero-powers',
                               {'revision':hero['revision'],'selections':['extraordinary-mental-affinity','extraordinary-mental-endurance','extraordinary-physical-beauty']},token)
                hero_powers = request('/api/characters/'+hero['id']+'/hero-powers')
                beauty = next(row for row in hero_powers['powers'] if row['id']=='extraordinary-physical-beauty')
                self.assertTrue(22 <= beauty['target'] <= 28)
                self.assertEqual(len(beauty['rolls']),2)
                self.assertTrue(60 <= hero_powers['charm_impress'] <= 92)
                hero = request('/api/characters/'+hero['id']+'/hero-secondary',
                               {'revision':hero['revision'],'selections':['cardsharp','palming','concealment','pick-locks','prowl','streetwise','seduction','ventriloquism','art','photography','general-repair-maintenance','body-building','running','athletics','climbing','swimming','scuba','hand-to-hand-basic','hand-to-hand-expert','hand-to-hand-martial-arts','hand-to-hand-assassin']},token)
                hero = request('/api/characters/'+hero['id']+'/hero-training',{'revision':hero['revision'],'training_id':'hand-to-hand-martial-arts'},token)
                hero_combat = request('/api/characters/'+hero['id']+'/hero-programs')['combat']
                self.assertEqual(hero_combat['training'],'Hand to Hand: Martial Arts')
                self.assertEqual(hero_combat['totals']['attacks']['value'],4)
                self.assertEqual(hero_combat['parry_actions'],0)
                self.assertEqual(hero_combat['totals']['parry']['contributions']['Athletics (general)'],1)
                self.assertEqual(hero_combat['totals']['roll_with_impact']['contributions']['Athletics (general)'],1)
                rogue = {row['id']:row for row in request('/api/characters/'+hero['id']+'/hero-programs')['skills']}
                self.assertEqual(rogue['cardsharp']['contributions']['Palming'],4)
                self.assertEqual(rogue['cardsharp']['contributions']['Extraordinary Mental Affinity'],10)
                self.assertEqual(rogue['concealment']['contributions']['Extraordinary Mental Affinity'],10)
                self.assertNotIn('Extraordinary Physical Beauty',rogue['cardsharp']['contributions'])
                self.assertEqual(rogue['pick-locks']['per_level'],5)
                self.assertEqual(rogue['ventriloquism']['contributions']['Extraordinary Mental Affinity'],10)
                self.assertEqual(rogue['general-repair-maintenance']['additional_checks'][0]['percentage'],rogue['general-repair-maintenance']['percentage']/2)
                hero = request('/api/characters/'+hero['id']+'/resources',{'revision':hero['revision']},token)
                hero_resources = request('/api/characters/'+hero['id']+'/resources')
                self.assertTrue(43 <= hero_resources['resources']['SDC']['value'] <= 54)
                self.assertEqual(hero_resources['resources']['SDC']['contributions']['Physical: Body Building & Weight Lifting'],10)
                self.assertTrue(6 <= hero_resources['resources']['PPE']['value'] <= 36)
                self.assertTrue(hero['attributes']['PE']['value']+1 <= hero_resources['resources']['HP']['value'] <= hero['attributes']['PE']['value']+6)
                starting_hp = hero_resources['resources']['HP']['value']
                starting_sdc = hero_resources['resources']['SDC']['value']
                initial_snapshot = hero['resource_attribute_snapshot']
                hero = request('/api/characters/'+hero['id']+'/hero-powers',
                               {'revision':hero['revision'],'selections':['extraordinary-mental-affinity','extraordinary-mental-endurance','extraordinary-physical-beauty','extraordinary-physical-endurance']},token)
                hero_powers = request('/api/characters/'+hero['id']+'/hero-powers')
                physical_endurance = next(row for row in hero_powers['powers'] if row['id']=='extraordinary-physical-endurance')
                self.assertEqual(len(physical_endurance['rolls']['HP-levels']),1)
                self.assertEqual(len(physical_endurance['rolls']['SDC']),4)
                self.assertEqual(hero['resource_attribute_snapshot'],initial_snapshot)
                self.assertEqual(hero_powers['fatigue_rate'],{'numerator':1,'denominator':10})
                activity = next(row for row in request('/api/characters/'+hero['id']+'/hero-programs')['physical']['selected'] if row['id']=='swimming')['activities'][0]
                self.assertEqual(activity['yards_per_melee'],hero['attributes']['PS']['value']*3)
                self.assertEqual(activity['ordinary_minutes'],hero['attributes']['PE']['value'])
                self.assertEqual(activity['minutes'],hero['attributes']['PE']['value']*10)
                self.assertEqual(activity['fatigue_sources'][0]['printed_page'],232)
                underwater = next(row for row in request('/api/characters/'+hero['id']+'/hero-programs')['physical']['selected'] if row['id']=='scuba')['activities'][0]
                self.assertEqual(underwater['id'],'underwater-swimming')
                self.assertEqual(underwater['yards_per_melee'],hero['attributes']['PS']['value']*2)
                self.assertEqual(underwater['minutes'],hero['attributes']['PE']['value']*10)
                hero_resources = request('/api/characters/'+hero['id']+'/resources')
                self.assertTrue(starting_hp+4 <= hero_resources['resources']['HP']['value'] <= starting_hp+22)
                self.assertTrue(starting_sdc+40 <= hero_resources['resources']['SDC']['value'] <= starting_sdc+160)
                resource_pdf = PdfReader(BytesIO(request('/api/characters/'+hero['id']+'/pdf'))).get_fields()
                assert resource_pdf is not None
                self.assertIn('skills.climbing.check0.percentage',resource_pdf)
                self.assertIn('skills.swimming.percentage',resource_pdf)
                scuba_line = f"S.C.U.B.A. (Advanced Swimming): {rogue['scuba']['percentage']}% (+5% per level)"
                self.assertTrue('skills.scuba.percentage' in resource_pdf or
                                any(row.get('/V') == scuba_line for row in resource_pdf.values()))
                self.assertEqual(resource_pdf['COMBAT_SKILL']['/V'],'Hand to Hand: Martial Arts')
                self.assertEqual(resource_pdf['ATTACKS']['/V'],'4')
                self.assertEqual(resource_pdf['HP']['/V'],str(hero_resources['resources']['HP']['value']))
                self.assertEqual(resource_pdf['SDC']['/V'],str(hero_resources['resources']['SDC']['value']))
                self.assertEqual(resource_pdf['PPE']['/V'],str(hero_resources['resources']['PPE']['value']))
                hero_imported = request('/api/import', {'bundle':request('/api/characters/' + hero['id'] + '/export')}, token)
                self.assertEqual(hero_imported['resources'],hero['resources'])
                self.assertEqual(hero_imported['physical_acquisitions'],hero['physical_acquisitions'])
                self.assertEqual(hero_imported['hero_combat_training'],hero['hero_combat_training'])
                self.assertEqual(hero_imported['resource_attribute_snapshot'],hero['resource_attribute_snapshot'])
                self.assertEqual(hero_imported['power_budget'], hero['power_budget'])
                self.assertEqual(hero_imported['hero_powers'], hero['hero_powers'])
                self.assertEqual(hero_imported['education'], hero['education'])
                self.assertEqual(hero_imported['hero_program_selections'], hero['hero_program_selections'])
                self.assertEqual(hero_imported['hero_secondary_selections'],hero['hero_secondary_selections'])
                archive = RuleArchive.load()
                legacy = RuleArchive(archive.definitions(), {**archive.active_versions(),'heroes-program-skills':'1.0.0'})
                earlier = CharacterApplication(root/'legacy-fixture',die=lambda sides:4,rule_archive=legacy)
                old_hero = earlier.create(game='heroes-unlimited')
                old_hero = earlier.select_education(old_hero['id'],revision=0,method='choose',education_id='high-school')
                old_hero = earlier.set_attribute(old_hero['id'],revision=old_hero['revision'],attribute='IQ',mode='fixed',value=16)
                old_hero = earlier.select_hero_programs(old_hero['id'],revision=old_hero['revision'],selections=[{'slot':0,'program':'business'}])
                legacy_imported = request('/api/import',{'bundle':earlier.export_character(old_hero['id'])},token)
                legacy_path = '/api/characters/'+legacy_imported['id']
                preview = request(legacy_path+'/rule-preview',{},token)
                research = next(skill for skill in preview['skills'] if skill['name']=='Research')
                self.assertEqual((research['before'],research['after']),(57,52))
                result = request(legacy_path+'/rule-upgrade',{'revision':legacy_imported['revision'],'token':preview['token']},token)
                self.assertEqual(result['character']['additional_rule_packs']['heroes-program-skills'],'1.16.0')
                self.assertEqual(result['character']['attributes'],legacy_imported['attributes'])
                self.assertEqual(result['character']['education'],legacy_imported['education'])
                self.assertEqual(request(legacy_path+'/hero-programs')['rules']['version'],'1.16.0')

                city = request('/api/characters',
                               {'name':'Packaged City Rat','race':'human','character_class':'city-rat'}, token)
                city_path = '/api/characters/' + city['id']
                self.assertEqual(city['character_class'], 'city-rat')
                running_rolls = city['physical_acquisitions']['running']['rolls']
                self.assertEqual(len(running_rolls['attribute:SPD']), 4)
                self.assertTrue(all(1 <= face <= 4 for face in running_rolls['attribute:SPD']))
                self.assertEqual(len(running_rolls['resource:SDC']), 1)
                self.assertTrue(1 <= running_rolls['resource:SDC'][0] <= 6)
                city_view = request(city_path+'/skills')
                self.assertEqual(city_view['remaining'], {'related':10,'secondary':8})
                self.assertEqual(city_view['combat']['class_bonuses']['perception']['value'], 3)
                self.assertEqual(len([item for item in city_view['grants'] if item['id']=='running']), 1)
                self.assertTrue(next(item for item in city_view['physical']['selected']
                                     if item['id']=='running')['grant'])
                city = request(city_path+'/required-skills',
                               {'revision':city['revision'], 'choices':{
                                   'native_language':'English','other_languages':['French'],
                                   'vehicle':'hovercycle'}}, token)
                city = request(city_path+'/combat',
                               {'revision':city['revision'], 'choices':{
                                   'hand_to_hand':'basic','ancient':['knife']}}, token)
                city_view = request(city_path+'/skills')
                self.assertTrue(all(remaining == 0 for remaining in city_view['required_remaining'].values()))
                self.assertEqual(city_view['combat']['remaining'], {'proficiencies':0})
                self.assertTrue(any(item['id']=='hovercycle' for item in city_view['grants']))
                city = request(city_path+'/skills', {'revision':city['revision'],
                    'selections':[{'skill_id':'paramedic','pool':'related'}]}, token)
                weighted = request(city_path+'/skills')
                self.assertEqual(weighted['remaining']['related'],8)
                self.assertEqual(weighted['selected'][0]['selection_cost'],2)
                city_view = weighted
                city = request(city_path+'/resources', {'revision':city['revision']}, token)
                city_resources = request(city_path+'/resources')['resources']
                hp = {item['id']:item for item in city['resources']['HP']['contributions']}
                self.assertEqual(hp['starting-pe']['value'], city['attributes']['PE']['value'])
                self.assertEqual(city_resources['HP']['value'],
                                 hp['starting-pe']['value'] + hp['level-one']['value'])
                sdc = {item['id']:item for item in city['resources']['SDC']['contributions']}
                self.assertEqual(len(sdc['city-rat']['rolls']), 2)
                self.assertTrue(all(1 <= face <= 4 for face in sdc['city-rat']['rolls']))
                self.assertEqual(city_resources['SDC']['value'],
                                 sum(item['value'] for item in sdc.values())
                                 + running_rolls['resource:SDC'][0])
                city = request(city_path+'/starting-funds', {'revision':city['revision']}, token)
                self.assertEqual(len(city['starting_funds']['credits']['rolls']),6)
                self.assertEqual(len(city['starting_funds']['saleable_goods']['rolls']),3)
                self.assertTrue(all(1 <= face <= 4 for face in city['starting_funds']['saleable_goods']['rolls']))
                self.assertEqual(city['equipment']['credits'],city['starting_funds']['credits']['value'])
                self.assertEqual(city['starting_funds']['credits']['source']['pages'],[89])
                city = request(city_path+'/starting-gear', {'revision':city['revision']}, token)
                self.assertEqual(len(city['starting_gear']['grants']),6)
                self.assertEqual(request(city_path+'/equipment')['unknown_carried_weight_quantity'],7)
                city = request(city_path+'/starting-group',
                               {'revision':city['revision'],'group_id':'armor','selection':'urban-warrior'}, token)
                self.assertEqual(city['starting_equipment_groups']['armor']['selection'],'urban-warrior')
                self.assertEqual(city['equipment']['credits'],city['starting_funds']['credits']['value'])
                city_inventory = deepcopy(city['equipment'])
                city_inventory['items'][-1]['equipped'] = True
                city = request(city_path+'/equipment',
                               {'revision':city['revision'],'inventory':city_inventory}, token)
                city_armor = request(city_path+'/equipment')['armor'][0]
                self.assertEqual(city_armor['locations']['main_body'],50)
                self.assertTrue(city_armor['environmental'])

                city = request(city_path+'/starting-group',
                               {'revision':city['revision'],'group_id':'knife','selection':'knife-large'}, token)
                self.assertEqual(city['equipment']['credits'],city['starting_funds']['credits']['value'])
                self.assertEqual(city['starting_equipment_groups']['knife']['selection'],'knife-large')
                city_inventory = deepcopy(city['equipment'])
                city_inventory['items'][-1]['equipped'] = True
                city = request(city_path+'/equipment',
                               {'revision':city['revision'],'inventory':city_inventory}, token)
                self.assertIn('1D6',request(city_path+'/equipment')['melee_attacks'][0]['damage'])

                self.assertNotIn('power-kick',[move['id'] for move in request(city_path+'/skills')['combat']['unarmed']])
                city = request(city_path+'/combat',
                               {'revision':city['revision'],'choices':{'hand_to_hand':'expert','ancient':['knife']}}, token)
                city_view = request(city_path+'/skills')
                city_moves = {move['id']:move for move in city_view['combat']['unarmed']}
                self.assertEqual(city_moves['power-kick']['actions'],2)
                self.assertNotIn('power-karate-kick',city_moves)

                city_portable = request(city_path+'/export')
                city_imported = request('/api/import', {'bundle':city_portable}, token)
                self.assertEqual(city_imported['character_class'], 'city-rat')
                self.assertEqual(city_imported['physical_acquisitions'], city['physical_acquisitions'])
                self.assertEqual(city_imported['resources'], city['resources'])
                self.assertEqual(city_imported['starting_funds'], city['starting_funds'])
                self.assertEqual(city_imported['starting_gear'], city['starting_gear'])
                self.assertEqual(city_imported['starting_equipment_groups'], city['starting_equipment_groups'])
                city_fields = PdfReader(BytesIO(request(city_path+'/pdf'))).get_fields()
                assert city_fields is not None
                self.assertEqual(city_fields['NAME']['/V'], 'Packaged City Rat')
                self.assertEqual(city_fields['OCC']['/V'], 'City Rat')
                self.assertEqual(city_fields['ARMOR']['/V'], 'Urban Warrior')
                self.assertEqual(city_fields['HIT POINTS']['/V'], str(city_resources['HP']['value']))
                self.assertIn('Original starting knife',' '.join(str(field.get('/V','')) for field in city_fields.values()))
                self.assertIn('Power kick:',' '.join(str(field.get('/V','')) for field in city_fields.values()))
            finally:
                process.terminate(); process.wait(timeout=10)
            with socket.socket() as occupied:
                occupied.bind(('127.0.0.1', 0))
                occupied.listen()
                failed = subprocess.Popen([str(executable), '--headless', '--port',
                                           str(occupied.getsockname()[1]), '--data-dir', str(root / 'saves')],
                                          cwd=root, env=environment)
                try:
                    self.assertEqual(failed.wait(timeout=15), 1)
                    self.assertIn('Traceback', (root / 'saves' / 'startup-error.log').read_text())
                finally:
                    if failed.poll() is None:
                        failed.terminate(); failed.wait(timeout=10)
            process, bootstrap = launch(gui=True)
            try:
                self.assertEqual(request('/api/characters/' + identifier)['name'], 'Packaged Rowan')
            finally:
                process.terminate(); process.wait(timeout=10)
            process, bootstrap = launch()
            try:
                self.assertEqual(request('/api/characters/' + identifier)['name'], 'Packaged Rowan')
                self.assertEqual(request('/api/characters/' + hero['id'])['education'], hero['education'])
                self.assertEqual(request('/api/characters/'+hero['id']+'/power-budget'),power_budget)
                self.assertEqual(request('/api/characters/'+hero['id']+'/hero-powers'),hero_powers)
                self.assertEqual(request('/api/characters/'+identifier)['physical_acquisitions'],character['physical_acquisitions'])
                self.assertEqual(request('/api/characters/'+identifier)['resources'],character['resources'])
                self.assertEqual(request('/api/characters/'+identifier)['starting_funds'],character['starting_funds'])
                self.assertEqual(request('/api/characters/'+identifier)['starting_gear'],character['starting_gear'])
                self.assertEqual(request('/api/characters/'+identifier)['starting_choices'],character['starting_choices'])
                self.assertEqual(request('/api/characters/'+identifier)['equipment'],character['equipment'])
                self.assertEqual(request('/api/characters/'+hero['id'])['hero_program_selections'],hero['hero_program_selections'])
                self.assertEqual(request('/api/characters/'+hero['id'])['hero_secondary_selections'],hero['hero_secondary_selections'])
                self.assertEqual(request('/api/characters/'+hero['id']+'/hero-programs')['combat'],hero_combat)
                self.assertEqual(len(bootstrap['characters']), 10)
                self.assertEqual(request(city_path)['physical_acquisitions'], city['physical_acquisitions'])
                self.assertEqual(request(city_path)['resources'], city['resources'])
                self.assertEqual(request(city_path)['starting_funds'], city['starting_funds'])
                self.assertEqual(request(city_path)['starting_gear'], city['starting_gear'])
                self.assertEqual(request(city_path)['starting_equipment_groups'], city['starting_equipment_groups'])
                self.assertEqual(request('/api/characters/'+city_imported['id'])['character_class'], 'city-rat')
                reopened_city = request(city_path+'/skills')
                self.assertEqual(reopened_city['remaining'], city_view['remaining'])
                self.assertEqual(reopened_city['combat']['remaining'], {'proficiencies':0})
                self.assertEqual(len([item for item in reopened_city['grants'] if item['id']=='running']), 1)
                self.assertEqual(request('/api/characters/'+identifier)['level'],15)
                self.assertEqual(request('/api/characters/'+identifier)['advancement']['hp_roll'],advancement_die)
                self.assertEqual([event['hp_roll'] for event in request('/api/characters/'+identifier)['later_advancements']],later_dice)
            finally:
                process.terminate(); process.wait(timeout=10)
