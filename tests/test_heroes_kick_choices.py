import tempfile,unittest
from characters_unlimited.application import CharacterApplication
class HeroesKickChoiceTests(unittest.TestCase):
 def test_basic_earned_choice_projects_once_and_survives_reselection(self):
  with tempfile.TemporaryDirectory() as directory:
   app=CharacterApplication(directory,die=lambda sides:4);c=app.create(game='heroes-unlimited',level=15)
   c=app.select_education(c['id'],revision=c['revision'],method='choose',education_id='high-school')
   c=app.select_hero_secondary(c['id'],revision=c['revision'],selections=['hand-to-hand-basic'],learned_level=1)
   c=app.select_hero_kicks(c['id'],revision=c['revision'],training_id='hand-to-hand-basic',selections=['karate-kick'])
   v=app.hero_program_view(c['id'])['combat'];k=v['kick_choices']
   self.assertEqual((k['count'],k['remaining'],k['selections']),(1,0,['karate-kick']))
   attacks={row['id']:row for row in v['unarmed']}
   self.assertEqual((attacks['karate-kick']['damage'],attacks['power-karate-kick']['damage'],attacks['power-karate-kick']['actions']),('2D4 + 4 S.D.C.','2 x 2D4 + 4 S.D.C.',2))
   self.assertNotIn('snap-kick',attacks)
   original=c['hero_kick_choices']
   c=app.select_hero_secondary(c['id'],revision=c['revision'],selections=[])
   self.assertNotIn('karate-kick',{row['id'] for row in app.hero_program_view(c['id'])['combat']['unarmed']})
   c=app.select_hero_secondary(c['id'],revision=c['revision'],selections=['hand-to-hand-basic'])
   self.assertEqual(c['hero_kick_choices'],original)
   self.assertIn('karate-kick',{row['id'] for row in app.hero_program_view(c['id'])['combat']['unarmed']})
   self.assertEqual(app.import_character(app.export_character(c['id']))['hero_kick_choices'],original)
 def test_all_styles_earn_their_own_choices_and_jump_action_costs(self):
  cases=[('hand-to-hand-expert',5,['roundhouse-kick','wheel-kick'],2),('hand-to-hand-martial-arts',3,['snap-kick','knee','crescent-kick','backward-sweep'],4),('hand-to-hand-assassin',9,['axe-kick','tripping'],2)]
  for style,level,choices,count in cases:
   with self.subTest(style=style),tempfile.TemporaryDirectory() as directory:
    app=CharacterApplication(directory,die=lambda sides:4);c=app.create(game='heroes-unlimited',level=level)
    c=app.select_education(c['id'],revision=c['revision'],method='choose',education_id='high-school')
    c=app.select_hero_secondary(c['id'],revision=c['revision'],selections=[style],learned_level=1)
    c=app.select_hero_kicks(c['id'],revision=c['revision'],training_id=style,selections=choices)
    v=app.hero_program_view(c['id'])['combat'];self.assertEqual((v['kick_choices']['count'],v['kick_choices']['remaining']),(count,0))
    attacks={row['id']:row for row in v['unarmed']};self.assertIn('karate-kick',attacks)
    self.assertNotIn('jump-kick',attacks);self.assertNotIn('power-backward-sweep',attacks)
    if style=='hand-to-hand-martial-arts':
     self.assertEqual(attacks['crescent-kick']['damage'],'2D4 + 2 S.D.C.')
     self.assertEqual(attacks['power-crescent-kick']['damage'],'2 x 2D4 + 2 S.D.C.')
     self.assertEqual(attacks['backward-sweep']['damage'],'No damage')
     c=app.advance(c['id'],revision=c['revision'],method='level',value=15)
     attacks={row['id']:row for row in app.hero_program_view(c['id'])['combat']['unarmed']}
     self.assertEqual((attacks['jump-kick']['damage'],attacks['jump-kick']['actions']),('6D6 + 4 S.D.C.','all'))
     self.assertEqual((attacks['flying-jump-kick']['damage'],attacks['flying-jump-kick']['actions']),('4D6 + 4 S.D.C.',2))
     self.assertNotIn('power-jump-kick',attacks);self.assertNotIn('power-flying-jump-kick',attacks)
    self.assertEqual(app.import_character(app.export_character(c['id']))['hero_kick_choices'],c['hero_kick_choices'])
 def test_late_training_retains_premature_choices_but_earns_moves_at_its_own_age(self):
  with tempfile.TemporaryDirectory() as directory:
   app=CharacterApplication(directory,die=lambda sides:4);c=app.create(game='heroes-unlimited',level=10)
   c=app.select_education(c['id'],revision=c['revision'],method='choose',education_id='high-school')
   c=app.select_hero_secondary(c['id'],revision=c['revision'],selections=['hand-to-hand-basic'])
   c=app.select_hero_kicks(c['id'],revision=c['revision'],training_id='hand-to-hand-basic',selections=['karate-kick','snap-kick','jump-kick'])
   v=app.hero_program_view(c['id'])['combat'];self.assertTrue(v['kick_choices']['warnings'])
   self.assertNotIn('karate-kick',{row['id'] for row in v['unarmed']})
   c=app.advance(c['id'],revision=c['revision'],method='level',value=12)
   v=app.hero_program_view(c['id'])['combat'];self.assertEqual((v['kick_choices']['age'],v['kick_choices']['remaining']),(3,-2))
   self.assertTrue({'karate-kick','snap-kick'}<={row['id'] for row in v['unarmed']});self.assertNotIn('jump-kick',{row['id'] for row in v['unarmed']})
   result=app.undo_advancement(c['id'],revision=c['revision']);c=result['character']
   self.assertEqual(c['hero_kick_choices'],result['recovery']['hero_kick_choices'])
   self.assertNotIn('karate-kick',{row['id'] for row in app.hero_program_view(c['id'])['combat']['unarmed']})
   self.assertEqual(app.import_character(app.export_character(c['id']))['hero_kick_choices'],c['hero_kick_choices'])
 def test_portable_choice_tampering_and_changed_rule_upgrade_are_atomic(self):
  from copy import deepcopy
  from characters_unlimited.rules import RuleArchive
  with tempfile.TemporaryDirectory() as directory:
   app=CharacterApplication(directory,die=lambda sides:4);c=app.create(game='heroes-unlimited',level=3)
   c=app.select_education(c['id'],revision=c['revision'],method='choose',education_id='high-school')
   c=app.select_hero_secondary(c['id'],revision=c['revision'],selections=['hand-to-hand-basic'],learned_level=1)
   c=app.select_hero_kicks(c['id'],revision=c['revision'],training_id='hand-to-hand-basic',selections=['karate-kick'])
   bundle=app.export_character(c['id']);count=len(app.list())
   for kind in ['pin','source','source-float','missing-record','unknown','duplicate','acquisition','game']:
    with self.subTest(kind=kind):
     b=deepcopy(bundle);record=b['character']['hero_kick_choices']['hand-to-hand-basic']
     if kind=='pin':b['character']['additional_rule_packs'].pop('heroes-combat-moves')
     elif kind=='source':record['source']={}
     elif kind=='source-float':record['source']['pages'][0]=67.0
     elif kind=='missing-record':b['character'].pop('hero_kick_choices')
     elif kind=='unknown':record['selections']=['unknown']
     elif kind=='duplicate':record['selections']=['karate-kick','karate-kick']
     elif kind=='acquisition':b['character']['hero_kick_choices']['hand-to-hand-expert']=record
     else:b['character']['game']='rifts'
     with self.assertRaises(ValueError):app.import_character(b)
   self.assertEqual((len(app.list()),app.get(c['id'])),(count,c))
   archive=RuleArchive.load();future=deepcopy(archive.active('heroes-combat-moves'));future['version']='99.0.0';future['kicks'][0]['dice']='8D6'
   newer=CharacterApplication(directory,rule_archive=RuleArchive([*archive.definitions(),future],{**archive.active_versions(),'heroes-combat-moves':'99.0.0'}))
   with self.assertRaisesRegex(ValueError,'recorded Heroes kick'):newer.preview_rule_upgrade(c['id'])
   self.assertEqual(newer.get(c['id']),c)
 def test_editable_pdf_keeps_kick_restrictions_choices_and_overflow(self):
  from io import BytesIO
  from pypdf import PdfReader
  with tempfile.TemporaryDirectory() as directory:
   app=CharacterApplication(directory,die=lambda sides:4);c=app.create(game='heroes-unlimited',level=15)
   c=app.select_education(c['id'],revision=c['revision'],method='choose',education_id='high-school')
   c=app.select_hero_secondary(c['id'],revision=c['revision'],selections=['hand-to-hand-martial-arts'],learned_level=1)
   c=app.select_hero_kicks(c['id'],revision=c['revision'],training_id='hand-to-hand-martial-arts',selections=['roundhouse-kick','wheel-kick','crescent-kick','backward-sweep'])
   fields=PdfReader(BytesIO(app.export_pdf(c['id']))).get_fields();assert fields is not None;values='\n'.join(str(row.get('/V','')) for row in fields.values())
   for text in ['Flying jump kick: 4D6 + 4 S.D.C.','Jump kick: 6D6 + 4 S.D.C.','Must be first attack','Only once per melee','Recorded kick choices','Backward sweep: No damage','general foot-strike table']:
    self.assertIn(text,values)
   self.assertEqual(fields['LEVEL']['/V'],'15')
 def test_http_choice_requires_session_and_current_revision(self):
  import json,threading
  from urllib.request import Request,urlopen
  from urllib.error import HTTPError
  from characters_unlimited.server import create_server
  with tempfile.TemporaryDirectory() as directory:
   app=CharacterApplication(directory,die=lambda sides:4);c=app.create(game='heroes-unlimited',level=3)
   c=app.select_education(c['id'],revision=c['revision'],method='choose',education_id='high-school')
   c=app.select_hero_secondary(c['id'],revision=c['revision'],selections=['hand-to-hand-basic'],learned_level=1)
   server=create_server(app);worker=threading.Thread(target=server.serve_forever,daemon=True);worker.start()
   try:
    base=f'http://127.0.0.1:{server.server_port}';path=base+'/api/characters/'+c['id']+'/hero-kicks'
    with urlopen(base+'/api/bootstrap',timeout=5) as response:token=json.load(response)['token']
    payload=json.dumps({'revision':c['revision'],'training_id':'hand-to-hand-basic','selections':['snap-kick']}).encode()
    with self.assertRaises(HTTPError) as denied:urlopen(Request(path,data=payload),timeout=5)
    self.assertEqual(denied.exception.code,403);denied.exception.close()
    headers={'Content-Type':'application/json','X-Session-Token':token,'Origin':base}
    with urlopen(Request(path,data=payload,headers=headers),timeout=5) as response:saved=json.load(response)
    with self.assertRaises(HTTPError) as stale:urlopen(Request(path,data=payload,headers=headers),timeout=5)
    self.assertEqual(stale.exception.code,409);stale.exception.close();self.assertEqual(app.get(c['id']),saved)
    with urlopen(base+'/api/characters/'+c['id']+'/hero-programs',timeout=5) as response:view=json.load(response)
    self.assertIn('snap-kick',{row['id'] for row in view['combat']['unarmed']})
   finally:server.shutdown();server.server_close();worker.join(timeout=5)
 def test_old_characters_keep_unarmed_projection_until_choices_are_saved(self):
  with tempfile.TemporaryDirectory() as directory:
   app=CharacterApplication(directory,die=lambda sides:4);c=app.create(game='heroes-unlimited',level=15)
   c=app.select_education(c['id'],revision=c['revision'],method='choose',education_id='high-school')
   c=app.select_hero_secondary(c['id'],revision=c['revision'],selections=['hand-to-hand-martial-arts'],learned_level=1)
   view=app.hero_program_view(c['id'])['combat'];self.assertFalse(view['kick_choices']['accepted'])
   self.assertEqual({row['id'] for row in view['unarmed']},{'punch','kick','power-punch','power-kick'})
   self.assertEqual(app.get(c['id']),c)
   c=app.select_hero_kicks(c['id'],revision=c['revision'],training_id='hand-to-hand-martial-arts',selections=[])
   self.assertIn('jump-kick',{row['id'] for row in app.hero_program_view(c['id'])['combat']['unarmed']})
