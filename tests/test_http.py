import json
from io import BytesIO
import sqlite3
import tempfile
import threading
import unittest
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from pypdf import PdfReader

from characters_unlimited.application import CharacterApplication
from characters_unlimited.server import create_server
from characters_unlimited.rules import RuleArchive


class LocalBackupAdapterTests(unittest.TestCase):
    def test_physical_acquisition_endpoint_protects_and_projects_saved_bonuses(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory,die=lambda sides:4)
            hero = app.create()
            server = create_server(app)
            worker = threading.Thread(target=server.serve_forever,daemon=True)
            worker.start()
            try:
                base = f'http://127.0.0.1:{server.server_port}'
                with urlopen(base+'/api/bootstrap',timeout=5) as response:
                    token = json.load(response)['token']
                path = base+'/api/characters/'+hero['id']+'/skills'
                payload = json.dumps({'revision':0,'selections':[{'skill_id':'athletics','pool':'related'}]}).encode()
                headers = {'Content-Type':'application/json','X-Session-Token':token,'Origin':base}
                with self.assertRaises(HTTPError) as denied:
                    urlopen(Request(path,data=payload),timeout=5)
                self.assertEqual(denied.exception.code,403)
                denied.exception.close()
                with urlopen(Request(path,data=payload,headers=headers),timeout=5) as response:
                    saved = json.load(response)
                with urlopen(path,timeout=5) as response:
                    view = json.load(response)
                self.assertEqual(saved['attributes']['SPD']['value'],16)
                self.assertEqual(view['physical']['resources'][0]['value'],4)
                self.assertEqual(view['combat']['totals']['parry']['value'],1)
                with self.assertRaises(HTTPError) as stale:
                    urlopen(Request(path,data=payload,headers=headers),timeout=5)
                self.assertEqual(stale.exception.code,409)
                stale.exception.close()
                self.assertEqual(app.get(hero['id']),saved)
                advance_path = base+'/api/characters/'+hero['id']+'/advance'
                advance_payload = json.dumps({'revision':saved['revision'],'method':'level','value':2}).encode()
                with self.assertRaises(HTTPError) as denied_advance:
                    urlopen(Request(advance_path,data=advance_payload),timeout=5)
                self.assertEqual(denied_advance.exception.code,403)
                denied_advance.exception.close()
                # Starting resources have not yet been generated at this point.
                with self.assertRaises(HTTPError) as incomplete:
                    urlopen(Request(advance_path,data=advance_payload,headers=headers),timeout=5)
                self.assertEqual(incomplete.exception.code,400)
                incomplete.exception.close()
                resource_path = base+'/api/characters/'+hero['id']+'/resources'
                resource_payload = json.dumps({'revision':saved['revision']}).encode()
                with self.assertRaises(HTTPError) as denied_resource:
                    urlopen(Request(resource_path,data=resource_payload),timeout=5)
                self.assertEqual(denied_resource.exception.code,403)
                denied_resource.exception.close()
                with urlopen(Request(resource_path,data=resource_payload,headers=headers),timeout=5) as response:
                    saved = json.load(response)
                with urlopen(resource_path,timeout=5) as response:
                    resources = json.load(response)
                self.assertEqual(resources['resources']['HP']['value'],18)
                self.assertEqual(resources['resources']['SDC']['value'],42)
                with self.assertRaises(HTTPError) as stale_resource:
                    urlopen(Request(resource_path,data=resource_payload,headers=headers),timeout=5)
                self.assertEqual(stale_resource.exception.code,409)
                stale_resource.exception.close()
                self.assertEqual(app.get(hero['id']),saved)
                before = saved
                advance_payload = json.dumps({'revision':saved['revision'],'method':'level','value':2}).encode()
                with urlopen(Request(advance_path,data=advance_payload,headers=headers),timeout=5) as response:
                    advanced = json.load(response)
                self.assertEqual(advanced['level'],2)
                undo_path = base+'/api/characters/'+hero['id']+'/undo-advancement'
                undo_payload = json.dumps({'revision':advanced['revision']}).encode()
                with self.assertRaises(HTTPError) as denied_undo:
                    urlopen(Request(undo_path,data=undo_payload),timeout=5)
                self.assertEqual(denied_undo.exception.code,403)
                denied_undo.exception.close()
                with urlopen(Request(undo_path,data=undo_payload,headers=headers),timeout=5) as response:
                    undone = json.load(response)
                self.assertEqual(undone['character']['resources'],before['resources'])
                self.assertEqual(undone['character']['level'],1)
                self.assertEqual(app.get(undone['recovery']['id'])['level'],2)
            finally:
                server.shutdown(); server.server_close(); worker.join(timeout=5)

    def test_heroes_rule_preview_and_apply_use_protected_endpoints_and_exact_versions(self):
        with tempfile.TemporaryDirectory() as directory:
            archive = RuleArchive.load()
            legacy = RuleArchive(archive.definitions(), {**archive.active_versions(),'heroes-program-skills':'1.0.0'})
            earlier = CharacterApplication(directory, die=lambda sides:4, rule_archive=legacy)
            hero = earlier.create(game='heroes-unlimited')
            hero = earlier.select_education(hero['id'], revision=0, method='choose', education_id='high-school')
            hero = earlier.select_hero_programs(hero['id'], revision=hero['revision'], selections=[{'slot':0,'program':'business'}])
            current = CharacterApplication(directory)
            server = create_server(current)
            worker = threading.Thread(target=server.serve_forever, daemon=True)
            worker.start()
            try:
                base = f'http://127.0.0.1:{server.server_port}'
                with urlopen(base+'/api/bootstrap',timeout=5) as response:
                    token = json.load(response)['token']
                path = base+'/api/characters/'+hero['id']
                headers = {'Content-Type':'application/json','X-Session-Token':token,'Origin':base}
                with self.assertRaises(HTTPError) as denied:
                    urlopen(Request(path+'/rule-preview',data=b'{}'),timeout=5)
                self.assertEqual(denied.exception.code,403)
                denied.exception.close()
                with urlopen(Request(path+'/rule-preview',data=b'{}',headers=headers),timeout=5) as response:
                    preview = json.load(response)
                research = next(skill for skill in preview['skills'] if skill['name']=='Research')
                self.assertEqual((research['before'],research['after']),(55,50))
                self.assertEqual(current.get(hero['id']),hero)
                payload = json.dumps({'revision':hero['revision'],'token':preview['token']}).encode()
                with urlopen(Request(path+'/rule-upgrade',data=payload,headers=headers),timeout=5) as response:
                    result = json.load(response)
                self.assertEqual(result['character']['additional_rule_packs']['heroes-program-skills'],'1.9.0')
                with self.assertRaises(HTTPError) as conflict:
                    urlopen(Request(path+'/rule-upgrade',data=payload,headers=headers),timeout=5)
                self.assertEqual(conflict.exception.code,409)
                conflict.exception.close()
            finally:
                server.shutdown();server.server_close();worker.join(timeout=5)

    def test_heroes_program_endpoint_saves_and_reports_stale_choices(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides: 4)
            hero = app.create(game='heroes-unlimited')
            app.select_education(hero['id'], revision=0, method='choose', education_id='high-school')
            server = create_server(app)
            worker = threading.Thread(target=server.serve_forever, daemon=True)
            worker.start()
            try:
                base = f'http://127.0.0.1:{server.server_port}'
                with urlopen(base + '/api/bootstrap', timeout=5) as response:
                    token = json.load(response)['token']
                path = base + '/api/characters/' + hero['id'] + '/hero-programs'
                payload = json.dumps({'revision':1,'selections':[{'slot':0,'program':'business'}]}).encode()
                headers = {'Content-Type':'application/json','X-Session-Token':token,'Origin':base}
                with urlopen(Request(path, data=payload, headers=headers), timeout=5) as response:
                    saved = json.load(response)
                with urlopen(path, timeout=5) as response:
                    view = json.load(response)
                self.assertTrue(view['pinned'])
                self.assertEqual(next(item for item in view['skills'] if item['id'] == 'research')['percentage'], 50)
                with self.assertRaises(HTTPError) as conflict:
                    urlopen(Request(path, data=payload, headers=headers), timeout=5)
                self.assertEqual(conflict.exception.code, 409)
                conflict.exception.close()
                self.assertEqual(app.get(hero['id']), saved)
                payload = json.dumps({'revision':saved['revision'],'selections':[{'slot':0,'program':'medical-assistant'}]}).encode()
                with urlopen(Request(path,data=payload,headers=headers),timeout=5) as response:
                    saved = json.load(response)
                with urlopen(path,timeout=5) as response:
                    view = json.load(response)
                self.assertEqual(next(item for item in view['skills'] if item['id']=='paramedic')['percentage'],40)
                self.assertTrue(any('Medical Assistant is outside' in message for message in view['warnings']))
                self.assertEqual(saved['hero_program_selections'],[{'slot':0,'program':'medical-assistant'}])
                secondary_path = base+'/api/characters/'+hero['id']+'/hero-secondary'
                secondary_payload = json.dumps({'revision':saved['revision'],'selections':['research']}).encode()
                with self.assertRaises(HTTPError) as denied:
                    urlopen(Request(secondary_path,data=secondary_payload),timeout=5)
                self.assertEqual(denied.exception.code,403)
                denied.exception.close()
                with urlopen(Request(secondary_path,data=secondary_payload,headers=headers),timeout=5) as response:
                    saved = json.load(response)
                with urlopen(path,timeout=5) as response:
                    view = json.load(response)
                self.assertEqual(view['secondary']['remaining'],9)
                self.assertEqual(next(item for item in view['skills'] if item['id']=='research')['percentage'],50)
                with self.assertRaises(HTTPError) as stale:
                    urlopen(Request(secondary_path,data=secondary_payload,headers=headers),timeout=5)
                self.assertEqual(stale.exception.code,409)
                stale.exception.close()
                self.assertEqual(app.get(hero['id']),saved)
                computer_choices = [{'slot':0,'program':'computer','choices':{'repair-radio':['radio-basic']}}]
                payload = json.dumps({'revision':saved['revision'],'selections':computer_choices}).encode()
                with urlopen(Request(path,data=payload,headers=headers),timeout=5) as response:
                    saved = json.load(response)
                with urlopen(path,timeout=5) as response:
                    view = json.load(response)
                self.assertEqual(view['program_choices'][0]['groups'][0]['remaining'],0)
                self.assertEqual(next(item for item in view['skills'] if item['id']=='radio-basic')['percentage'],50)
                self.assertEqual(saved['hero_secondary_selections'],['research'])
                payload = json.dumps({'revision':saved['revision'],'selections':[
                    {'slot':0,'program':'communications','choices':{'communications':['optic-systems']}}]}).encode()
                with urlopen(Request(path,data=payload,headers=headers),timeout=5) as response:
                    saved = json.load(response)
                with urlopen(path,timeout=5) as response:
                    view = json.load(response)
                self.assertEqual(next(item for item in view['skills'] if item['id']=='tv-video')['percentage'],30)
                self.assertEqual(view['program_choices'][0]['groups'][0]['remaining'],0)
                self.assertEqual(saved['hero_secondary_selections'],['research'])
                payload = json.dumps({'revision':saved['revision'],'selections':['research','first-aid','holistic-medicine']}).encode()
                with urlopen(Request(secondary_path,data=payload,headers=headers),timeout=5) as response:
                    saved = json.load(response)
                with urlopen(path,timeout=5) as response:
                    view = json.load(response)
                self.assertEqual(view['secondary']['used'],4)
                self.assertEqual(view['secondary']['remaining'],6)
                self.assertEqual(next(item for item in view['skills'] if item['id']=='holistic-medicine')['percentage'],20)
                self.assertEqual(saved['hero_program_selections'][0]['program'],'communications')
            finally:
                server.shutdown(); server.server_close(); worker.join(timeout=5)

    def test_pdf_download_is_an_editable_document_and_preserves_saved_revision(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides: 4)
            character = app.create(name='Downloaded character')
            server = create_server(app)
            worker = threading.Thread(target=server.serve_forever, daemon=True)
            worker.start()
            try:
                with urlopen(f'http://127.0.0.1:{server.server_port}/api/characters/{character["id"]}/pdf', timeout=5) as response:
                    self.assertEqual(response.headers['Content-Type'], 'application/pdf')
                    reader = PdfReader(BytesIO(response.read()))
                    fields = reader.get_fields()
                    assert fields is not None
                    self.assertEqual(fields['NAME']['/V'], 'Downloaded character')
                self.assertEqual(app.get(character['id']), character)
            finally:
                server.shutdown()
                server.server_close()
                worker.join(timeout=3)

    def test_invalid_source_audit_returns_diagnostic_without_affecting_characters(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides: 4)
            character = app.create()
            server = create_server(app)
            worker = threading.Thread(target=server.serve_forever, daemon=True)
            worker.start()
            try:
                with patch.object(app, 'coverage', side_effect=ValueError('Source fingerprint changed')):
                    with self.assertRaises(HTTPError) as result:
                        urlopen(f'http://127.0.0.1:{server.server_port}/api/coverage', timeout=3)
                with result.exception as failure:
                    self.assertEqual(failure.code, 400)
                    self.assertIn('Source fingerprint changed', json.load(failure)['error'])
                self.assertEqual(app.get(character['id']), character)
            finally:
                server.shutdown()
                server.server_close()
                worker.join(timeout=3)

    def test_sqlite_backup_failure_returns_a_controlled_error_and_preserves_the_save(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides: 4)
            character = app.create()
            server = create_server(app)
            worker = threading.Thread(target=server.serve_forever, daemon=True)
            worker.start()
            try:
                address = f'http://127.0.0.1:{server.server_port}'
                with urlopen(address + '/api/bootstrap', timeout=3) as response:
                    token = json.load(response)['token']
                request = Request(address + '/api/backups', data=b'{}', headers={'X-Session-Token':token, 'Content-Type':'application/json'})
                with patch.object(app, 'backup', side_effect=sqlite3.OperationalError('Disk full')):
                    with self.assertRaises(HTTPError) as result:
                        urlopen(request, timeout=3)
                with result.exception as failure:
                    self.assertEqual(failure.code, 400)
                    self.assertIn('Existing saves and backups remain available', json.load(failure)['error'])
                self.assertEqual(app.get(character['id']), character)
            finally:
                server.shutdown()
                server.server_close()
                worker.join(timeout=3)
