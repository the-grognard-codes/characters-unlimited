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
                                        {'skill_id':'boxing','pool':'related'}]},token)
                endurance = request('/api/characters/'+identifier+'/skills')
                self.assertEqual(endurance['combat']['totals']['attacks']['value'],5)
                self.assertEqual(endurance['combat']['totals']['parry']['contributions']['Boxing'],2)
                self.assertEqual(endurance['combat']['totals']['parry']['contributions']['Athletics (General)'],1)
                self.assertEqual(len(character['physical_acquisitions']['boxing']['rolls']['resource:SDC']),3)
                running = next(skill for skill in endurance['selected'] if skill['id']=='running')
                self.assertEqual(running['activities'][0]['miles'],character['attributes']['PE']['value']*0.5)
                self.assertEqual(request('/api/characters/'+identifier+'/resources')['resources']['HP']['value'],resource_view['resources']['HP']['value'])
                character = request('/api/characters/'+identifier+'/equipment',
                    {'revision':character['revision'],'inventory':{'credits':50000,'items':[]}},token)
                for item_id in ('wilks-320','plastic-man'):
                    character = request('/api/characters/'+identifier+'/purchase-equipment',
                        {'revision':character['revision'],'item_id':item_id,'quantity':1},token)
                inventory = character['equipment']
                for item in inventory['items']: item['equipped']=True
                character = request('/api/characters/'+identifier+'/equipment',
                    {'revision':character['revision'],'inventory':inventory},token)
                character = request('/api/characters/'+identifier+'/combat',
                    {'revision':character['revision'],'choices':{'hand_to_hand':'basic','ancient':[],
                     'modern':['energy-pistol']}},token)
                gear = request('/api/characters/'+identifier+'/equipment')
                self.assertEqual(gear['inventory']['credits'],21000)
                self.assertEqual(gear['carried_weight_lbs'],15)
                self.assertEqual(gear['attacks'][0]['aimed']['contributions']['weapon_aimed_bonus'],2)
                self.assertEqual(gear['armor'][0]['locations']['main_body'],35)
                portable = request('/api/characters/' + identifier + '/export')
                imported = request('/api/import', {'bundle':portable}, token)
                self.assertNotEqual(imported['id'], identifier)
                self.assertEqual(imported['physical_acquisitions'],character['physical_acquisitions'])
                self.assertEqual(imported['resources'],character['resources'])
                self.assertEqual(imported['equipment'],character['equipment'])
                reader = PdfReader(BytesIO(request('/api/characters/' + identifier + '/pdf')))
                fields = reader.get_fields()
                assert fields is not None
                self.assertEqual(fields['NAME']['/V'], 'Packaged Rowan')
                self.assertEqual(fields['HIT POINTS']['/V'],str(resource_view['resources']['HP']['value']))
                self.assertTrue(reader.pages[0].get('/Annots'))
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
                hero_imported = request('/api/import', {'bundle':request('/api/characters/' + hero['id'] + '/export')}, token)
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
                self.assertEqual(result['character']['additional_rule_packs']['heroes-program-skills'],'1.6.0')
                self.assertEqual(result['character']['attributes'],legacy_imported['attributes'])
                self.assertEqual(result['character']['education'],legacy_imported['education'])
                self.assertEqual(request(legacy_path+'/hero-programs')['rules']['version'],'1.6.0')
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
                self.assertEqual(request('/api/characters/'+identifier)['physical_acquisitions'],character['physical_acquisitions'])
                self.assertEqual(request('/api/characters/'+identifier)['resources'],character['resources'])
                self.assertEqual(request('/api/characters/'+hero['id'])['hero_program_selections'],hero['hero_program_selections'])
                self.assertEqual(request('/api/characters/'+hero['id'])['hero_secondary_selections'],hero['hero_secondary_selections'])
                self.assertEqual(len(bootstrap['characters']), 5)
            finally:
                process.terminate(); process.wait(timeout=10)
