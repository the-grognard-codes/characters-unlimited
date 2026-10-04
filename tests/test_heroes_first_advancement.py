import tempfile,unittest
from characters_unlimited.application import CharacterApplication
class HeroesFirstAdvancementTests(unittest.TestCase):
 def test_first_advance_grows_each_check_with_recorded_hp(self):
  with tempfile.TemporaryDirectory() as directory:
   app=CharacterApplication(directory,die=lambda sides:4);c=app.create(game='heroes-unlimited')
   c=app.select_education(c['id'],revision=0,method='choose',education_id='high-school')
   c=app.select_hero_secondary(c['id'],revision=c['revision'],selections=['acrobatics','gymnastics','climbing','hand-to-hand-basic'])
   c=app.generate_resources(c['id'],revision=c['revision'])
   c=app.advance(c['id'],revision=c['revision'],method='xp',value=2051)
   self.assertEqual((c['level'],c['experience']),(2,2051))
   v=app.hero_program_view(c['id']);skills={s['id']:s for s in v['skills']}
   self.assertEqual(skills['climbing']['percentage'],65)
   self.assertEqual(skills['climbing']['additional_checks'][0]['percentage'],55)
   self.assertEqual([s['percentage'] for s in skills['acrobatics']['additional_checks']],[63,72,55,30])
   self.assertEqual({s['name']:s['percentage'] for s in v['shared_abilities']['checks']}['Back flip'],72)
   self.assertEqual(v['combat']['totals']['parry']['value'],2)
   self.assertEqual(app.resource_view(c['id'])['resources']['HP']['value'],23)

 def test_xp_boundaries_new_character_and_training_levels(self):
  from copy import deepcopy
  from characters_unlimited.storage import SaveConflict
  from characters_unlimited.rules import RuleArchive
  archive=RuleArchive.load()
  first_only=RuleArchive([p for p in archive.definitions() if p['id']!='heroes-higher-advancement'],
                        {k:v for k,v in archive.active_versions().items() if k!='heroes-higher-advancement'})
  for training,stat,value in [('hand-to-hand-basic','parry',2),('hand-to-hand-expert','parry',3),('hand-to-hand-martial-arts','disarm',2),('hand-to-hand-assassin','attacks',5),(None,'attacks',4)]:
   with self.subTest(training=training),tempfile.TemporaryDirectory() as directory:
    app=CharacterApplication(directory,die=lambda sides:4,rule_archive=first_only);c=app.create(game='heroes-unlimited')
    c=app.select_education(c['id'],revision=0,method='choose',education_id='high-school')
    if training:c=app.select_hero_secondary(c['id'],revision=c['revision'],selections=[training])
    c=app.generate_resources(c['id'],revision=c['revision']);prior=deepcopy(c)
    c=app.advance(c['id'],revision=c['revision'],method='xp',value=2050)
    self.assertEqual(c['level'],1);self.assertNotIn('advancement',c)
    with self.assertRaises(SaveConflict):app.advance(c['id'],revision=prior['revision'],method='level',value=2)
    c=app.advance(c['id'],revision=c['revision'],method='level',value=2)
    self.assertEqual((c['level'],c['experience']),(2,2051))
    combat=app.hero_program_view(c['id'])['combat'];self.assertEqual(combat['totals'][stat]['value'],value)
    self.assertEqual(combat['parry_actions'],0 if training else 1)
    self.assertEqual(combat['level'],2)
    for row in app.hero_program_view(c['id'])['physical']['selected']:
     self.assertNotIn('level 1 only',' '.join(row.get('guidance',[])))
    self.assertNotIn('and Heroes advancement remain unfinished',' '.join(app.resource_view(c['id'])['guidance']))
    c=app.advance(c['id'],revision=c['revision'],method='xp',value=4100)
    self.assertEqual(c['advancement']['xp'],4100)
    for method,bad in [('xp',4101),('xp',True),('level',3),('level',1)]:
     with self.assertRaises(ValueError):app.advance(c['id'],revision=c['revision'],method=method,value=bad)
    self.assertEqual(app.get(c['id']),c)
    restored=app.import_character(app.export_character(c['id']));self.assertEqual(restored['advancement'],c['advancement'])
  with tempfile.TemporaryDirectory() as directory:
   app=CharacterApplication(directory,die=lambda sides:4);c=app.create(game='heroes-unlimited',level=2)
   self.assertEqual(app.resource_view(c['id'])['resources']['HP']['value'],20)
   self.assertEqual(app.hero_program_view(c['id'])['combat']['totals']['attacks']['value'],4)
   restored=app.import_character(app.export_character(c['id']));self.assertEqual(restored['level'],2)
   undone=app.undo_advancement(c['id'],revision=c['revision'])['character'];self.assertEqual(undone['level'],1)

 def test_learning_age_removal_and_independent_fallback_rates(self):
  with tempfile.TemporaryDirectory() as directory:
   app=CharacterApplication(directory,die=lambda sides:4);c=app.create(game='heroes-unlimited')
   c=app.select_education(c['id'],revision=0,method='choose',education_id='high-school')
   c=app.select_hero_secondary(c['id'],revision=c['revision'],selections=['acrobatics','gymnastics'])
   c=app.generate_resources(c['id'],revision=c['revision']);c=app.advance(c['id'],revision=c['revision'],method='level',value=2)
   checks={r['name']:r for r in app.hero_program_view(c['id'])['shared_abilities']['checks']}
   self.assertEqual((checks['Base climb ability']['percentage'],checks['Base prowl ability']['percentage']),(40,30))
   c=app.select_hero_secondary(c['id'],revision=c['revision'],selections=['acrobatics','gymnastics','climbing','hand-to-hand-expert'])
   v=app.hero_program_view(c['id']);climb=next(r for r in v['skills'] if r['id']=='climbing')
   self.assertEqual(climb['percentage'],60);self.assertEqual(c['learning_levels']['climbing'],2)
   self.assertEqual(v['combat']['totals']['parry']['value'],0)
   c=app.select_hero_secondary(c['id'],revision=c['revision'],selections=['gymnastics'])
   c=app.select_hero_secondary(c['id'],revision=c['revision'],selections=['acrobatics','gymnastics','climbing','hand-to-hand-expert'],learned_level=1)
   self.assertEqual(c['learning_levels']['climbing'],2);self.assertEqual(c['learning_levels']['acrobatics'],1)
   c=app.select_hero_secondary(c['id'],revision=c['revision'],selections=['acrobatics','gymnastics','climbing','hand-to-hand-expert','prowl','hand-to-hand-basic'],learned_level=1)
   c=app.select_hero_training(c['id'],revision=c['revision'],training_id='hand-to-hand-basic')
   self.assertEqual(app.hero_program_view(c['id'])['combat']['totals']['parry']['value'],2)
   self.assertEqual(next(r for r in app.hero_program_view(c['id'])['skills'] if r['id']=='prowl')['percentage'],40)
   for bad in [True,3,0]:
    with self.assertRaises(ValueError):app.select_hero_secondary(c['id'],revision=c['revision'],selections=[],learned_level=bad)

 def test_endurance_power_inactive_late_acquisition_and_undo_replay_retained_dice(self):
  from copy import deepcopy
  power='extraordinary-physical-endurance'
  for timing in ['before','inactive','after']:
   with self.subTest(timing=timing),tempfile.TemporaryDirectory() as directory:
    app=CharacterApplication(directory,die=lambda sides:4);c=app.create(game='heroes-unlimited')
    if timing!='after':c=app.select_hero_powers(c['id'],revision=c['revision'],selections=[power])
    c=app.generate_resources(c['id'],revision=c['revision'])
    if timing=='inactive':c=app.select_hero_powers(c['id'],revision=c['revision'],selections=[])
    before=deepcopy(c);c=app.advance(c['id'],revision=c['revision'],method='level',value=2)
    if timing=='after':c=app.select_hero_powers(c['id'],revision=c['revision'],selections=[power])
    expected=49 if timing!='after' else 40
    if timing=='inactive':
     self.assertEqual(app.resource_view(c['id'])['resources']['HP']['value'],29)
     c=app.select_hero_powers(c['id'],revision=c['revision'],selections=[power])
    self.assertEqual(app.resource_view(c['id'])['resources']['HP']['value'],expected)
    pv=app.hero_powers_view(c['id']);self.assertNotIn('level 1 only',' '.join(next(r for r in pv['catalog'] if r['id']==power)['guidance']))
    self.assertIn('HP level 2 +4',pv['powers'][0]['effect_summary'])
    rolls=deepcopy(c['hero_powers']);gains=deepcopy(c['advancement']['power_hp_rolls']);snapshot=deepcopy(c['resource_attribute_snapshot'])
    c=app.select_hero_powers(c['id'],revision=c['revision'],selections=[])
    dice=app.hero_program_view(c['id'])['advancement']['dice']
    self.assertTrue(dice[0]['active']);self.assertFalse(dice[1]['active'])
    c=app.select_hero_powers(c['id'],revision=c['revision'],selections=[power])
    self.assertTrue(app.hero_program_view(c['id'])['advancement']['dice'][1]['active'])
    self.assertEqual(c['hero_powers']['acquisitions'],rolls['acquisitions']);self.assertEqual(c['advancement']['power_hp_rolls'],gains)
    self.assertEqual(c['resource_attribute_snapshot'],snapshot)
    restored=app.import_character(app.export_character(c['id']));self.assertEqual(restored['advancement'],c['advancement'])
    result=app.undo_advancement(c['id'],revision=c['revision']);c=result['character']
    self.assertEqual(c['level'],1);self.assertEqual(result['recovery']['level'],2)
    for key in ['attributes','resources','resource_attribute_snapshot']:
     self.assertEqual(c[key],before[key])
    app.die=lambda sides:(_ for _ in ()).throw(AssertionError('replay must not roll'))
    c=app.advance(c['id'],revision=c['revision'],method='level',value=2)
    self.assertEqual(c['advancement']['hp_roll'],4);self.assertEqual(c['advancement']['power_hp_rolls'],gains)
    if timing=='after':self.assertFalse(app.hero_program_view(c['id'])['advancement']['dice'][1]['active'])
    if timing!='after':
     c=app.select_hero_powers(c['id'],revision=c['revision'],selections=[power])
     self.assertEqual(app.resource_view(c['id'])['resources']['HP']['value'],49)

 def test_portable_rejects_missing_invalid_records_before_save(self):
  from copy import deepcopy
  with tempfile.TemporaryDirectory() as directory:
   app=CharacterApplication(directory,die=lambda sides:4);c=app.create(game='heroes-unlimited')
   c=app.select_hero_powers(c['id'],revision=0,selections=['extraordinary-physical-endurance'])
   c=app.generate_resources(c['id'],revision=c['revision']);c=app.advance(c['id'],revision=c['revision'],method='level',value=2)
   bundle=app.export_character(c['id']);cache_id=next(iter(c['advancement']['power_hp_rolls']));count=len(app.list())
   cases=[]
   for key,value in [('hp_roll',7),('active',False),('xp',2050),('source',{}),('before',{})]:
    b=deepcopy(bundle);b['character']['advancement'][key]=value;cases.append(b)
   for key,value in [('face',5),('source',{}),('power','extraordinary-mental-endurance')]:
    b=deepcopy(bundle);b['character']['advancement']['power_hp_rolls'][cache_id][key]=value;cases.append(b)
   b=deepcopy(bundle);b['character']['learning_levels'].pop('pilot-automobile');cases.append(b)
   b=deepcopy(bundle);b['character']['learning_levels']['pilot-automobile']=2;cases.append(b)
   b=deepcopy(bundle);b['character']['advancement']['power_hp_rolls']={};cases.append(b)
   b=deepcopy(bundle);b['character']['additional_rule_packs'].pop('heroes-advancement');cases.append(b)
   for b in cases:
    with self.assertRaises(ValueError):app.import_character(b)
   self.assertEqual(len(app.list()),count);self.assertEqual(app.get(c['id']),c)
   from characters_unlimited.rules import RuleArchive
   archive=RuleArchive.load();future=deepcopy(archive.active('heroes-advancement'));future['version']='99.0.0';future['hp_die']=8
   newer=CharacterApplication(directory,rule_archive=RuleArchive([*archive.definitions(),future],{**archive.active_versions(),'heroes-advancement':'99.0.0'}))
   with self.assertRaises(ValueError):newer.preview_rule_upgrade(c['id'])
   self.assertEqual(newer.get(c['id']),c)

 def test_editable_pdf_projects_level_hp_growth_and_training(self):
  from io import BytesIO
  from pypdf import PdfReader
  with tempfile.TemporaryDirectory() as directory:
   app=CharacterApplication(directory,die=lambda sides:4);c=app.create(game='heroes-unlimited')
   c=app.select_education(c['id'],revision=0,method='choose',education_id='high-school')
   c=app.select_hero_programs(c['id'],revision=c['revision'],selections=[{'slot':0,'program':'physical-athletic','choices':{'physical':['acrobatics','gymnastics','climbing','hand-to-hand-basic']}}])
   c=app.generate_resources(c['id'],revision=c['revision']);c=app.advance(c['id'],revision=c['revision'],method='level',value=2)
   fields=PdfReader(BytesIO(app.export_pdf(c['id']))).get_fields()
   assert fields is not None
   for name,value in [('LEVEL','2'),('HP','23'),('PARRY','2'),('DODGE','2'),('skills.acrobatics.percentage','67'),('skills.acrobatics.check1.percentage','77'),('skills.gymnastics.check2.percentage','77')]:self.assertEqual(fields[name]['/V'],value)
   text=' '.join(str(r.get('/V','')) for r in fields.values());self.assertIn('learned at level 1',text);self.assertIn('2,051 XP',text)


 def test_fixed_resource_and_percentage_cap_preserve_underlying_gains(self):
  with tempfile.TemporaryDirectory() as directory:
   app=CharacterApplication(directory,die=lambda sides:4);c=app.create(game='heroes-unlimited')
   with self.assertRaises(ValueError):app.advance(c['id'],revision=0,method='level',value=2)
   c=app.select_education(c['id'],revision=0,method='choose',education_id='doctorate')
   c=app.set_attribute(c['id'],revision=c['revision'],attribute='IQ',mode='fixed',value=30)
   c=app.select_hero_programs(c['id'],revision=c['revision'],selections=[{'slot':0,'program':'physical-athletic','choices':{'physical':['acrobatics','gymnastics','climbing','hand-to-hand-basic']}}])
   c=app.generate_resources(c['id'],revision=c['revision'])
   c=app.set_resource(c['id'],revision=c['revision'],resource='HP',mode='fixed',value=100)
   c=app.advance(c['id'],revision=c['revision'],method='level',value=2)
   hp=app.resource_view(c['id'])['resources']['HP'];self.assertEqual((hp['value'],hp['calculated_value']),(100,23))
   checks=app.hero_program_view(c['id'])['shared_abilities']['checks'];self.assertTrue(all(r['percentage']==98 for r in checks if r['name'] not in ['Base prowl ability','Base climb ability']))
   c=app.set_resource(c['id'],revision=c['revision'],resource='HP',mode='adjustment',value=7)
   self.assertEqual(app.resource_view(c['id'])['resources']['HP']['value'],30)

 def test_http_advancement_token_stale_revision_and_projection(self):
  import json,threading
  from urllib.request import urlopen,Request
  from urllib.error import HTTPError
  from characters_unlimited.server import create_server
  with tempfile.TemporaryDirectory() as directory:
   app=CharacterApplication(directory,die=lambda sides:4);c=app.create(game='heroes-unlimited');c=app.generate_resources(c['id'],revision=0)
   server=create_server(app);worker=threading.Thread(target=server.serve_forever,daemon=True);worker.start()
   try:
    base=f'http://127.0.0.1:{server.server_port}'
    with urlopen(base+'/api/bootstrap',timeout=5) as response:token=json.load(response)['token']
    path=base+'/api/characters/'+c['id'];data=json.dumps({'revision':c['revision'],'method':'xp','value':2051}).encode()
    with self.assertRaises(HTTPError) as denied:urlopen(Request(path+'/advance',data=data,headers={'Content-Type':'application/json'}),timeout=5)
    self.assertEqual(denied.exception.code,403);denied.exception.close()
    headers={'Content-Type':'application/json','X-Session-Token':token,'Origin':base}
    with urlopen(Request(path+'/advance',data=data,headers=headers),timeout=5) as response:c=json.load(response)
    with self.assertRaises(HTTPError) as stale:urlopen(Request(path+'/advance',data=data,headers=headers),timeout=5)
    self.assertEqual(stale.exception.code,409);stale.exception.close();self.assertEqual(app.get(c['id']),c)
    with urlopen(path+'/hero-programs',timeout=5) as response:view=json.load(response)
    self.assertEqual(view['advancement']['level'],2);self.assertEqual(view['advancement']['dice'][0]['face'],4)
    self.assertEqual(view['combat']['totals']['attacks']['value'],4)
   finally:server.shutdown();server.server_close();worker.join(timeout=5)
