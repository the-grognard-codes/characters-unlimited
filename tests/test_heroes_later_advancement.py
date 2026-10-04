import tempfile,unittest
from characters_unlimited.application import CharacterApplication
class HeroesLaterAdvancementTests(unittest.TestCase):
 def test_mutant_can_advance_through_fifteen_with_recorded_hp_and_training_age(self):
  with tempfile.TemporaryDirectory() as directory:
   app=CharacterApplication(directory,die=lambda sides:4);c=app.create(game='heroes-unlimited')
   c=app.select_education(c['id'],revision=0,method='choose',education_id='high-school')
   c=app.select_hero_secondary(c['id'],revision=c['revision'],selections=['hand-to-hand-basic','climbing'])
   c=app.generate_resources(c['id'],revision=c['revision'])
   c=app.advance(c['id'],revision=c['revision'],method='level',value=15)
   self.assertEqual((c['level'],c['experience']),(15,340501))
   self.assertEqual(app.resource_view(c['id'])['resources']['HP']['value'],72)
   self.assertEqual([r['level'] for r in c['later_advancements']],list(range(3,16)))
   v=app.hero_program_view(c['id']);t=v['combat']['totals']
   self.assertEqual({k:t[k]['value'] for k in ['attacks','parry','dodge','strike','initiative','damage','roll_with_impact','pull_punch','disarm']},
                    {'attacks':7,'parry':3,'dodge':3,'strike':2,'initiative':1,'damage':4,'roll_with_impact':4,'pull_punch':4,'disarm':1})
   self.assertEqual(v['secondary']['allowance'],20)
   self.assertEqual(next(s for s in v['skills'] if s['id']=='climbing')['percentage'],98)
   self.assertEqual(app.import_character(app.export_character(c['id']))['later_advancements'],c['later_advancements'])
 def test_endurance_keeps_one_power_die_at_every_attained_level(self):
  power='extraordinary-physical-endurance'
  for timing in ['before','inactive','after']:
   with self.subTest(timing=timing),tempfile.TemporaryDirectory() as directory:
    app=CharacterApplication(directory,die=lambda sides:4);c=app.create(game='heroes-unlimited')
    if timing!='after':c=app.select_hero_powers(c['id'],revision=c['revision'],selections=[power])
    c=app.generate_resources(c['id'],revision=c['revision'])
    if timing=='inactive':c=app.select_hero_powers(c['id'],revision=c['revision'],selections=[])
    c=app.advance(c['id'],revision=c['revision'],method='level',value=15)
    if timing=='inactive':
     self.assertEqual(app.resource_view(c['id'])['resources']['HP']['value'],81)
     c=app.select_hero_powers(c['id'],revision=c['revision'],selections=[power])
    if timing=='after':c=app.select_hero_powers(c['id'],revision=c['revision'],selections=[power])
    self.assertEqual(app.resource_view(c['id'])['resources']['HP']['value'],144 if timing=='after' else 153)
    gains=[c['advancement']['power_hp_rolls'],*(e['power_hp_rolls'] for e in c['later_advancements'])]
    self.assertEqual([next(iter(g.values()))['face'] for g in gains],[4]*14)
    c=app.select_hero_powers(c['id'],revision=c['revision'],selections=[])
    c=app.select_hero_powers(c['id'],revision=c['revision'],selections=[power]);self.assertEqual([c['advancement']['power_hp_rolls'],*(e['power_hp_rolls'] for e in c['later_advancements'])],gains)
    result=app.undo_advancement(c['id'],revision=c['revision']);c=result['character']
    self.assertEqual((c['level'],result['recovery']['level']),(14,15))
    self.assertEqual(app.resource_view(c['id'])['resources']['HP']['value'],68 if timing=='after' else (77 if timing=='inactive' else 145))
    app.die=lambda sides:(_ for _ in ()).throw(AssertionError('Replay must retain dice'))
    c=app.advance(c['id'],revision=c['revision'],method='level',value=15)
    self.assertEqual([e['hp_roll'] for e in c['later_advancements']],[4]*13)
    self.assertEqual(app.import_character(app.export_character(c['id']))['later_advancements'],c['later_advancements'])
 def test_starting_higher_level_all_profiles_and_later_training_learning_age(self):
  expected=[('hand-to-hand-expert',{'attacks':7,'parry':5,'dodge':5,'strike':2,'initiative':2,'damage':3,'roll_with_impact':2,'pull_punch':4,'disarm':2}),
            ('hand-to-hand-martial-arts',{'attacks':7,'parry':5,'dodge':5,'strike':2,'initiative':3,'damage':4,'roll_with_impact':3,'pull_punch':3,'disarm':4}),
            ('hand-to-hand-assassin',{'attacks':8,'parry':3,'dodge':3,'strike':6,'initiative':6,'damage':6,'roll_with_impact':5,'pull_punch':5,'disarm':4})]
  for style,totals in expected:
   with self.subTest(style=style),tempfile.TemporaryDirectory() as directory:
    app=CharacterApplication(directory,die=lambda sides:4);c=app.create(game='heroes-unlimited',level=15)
    c=app.select_education(c['id'],revision=c['revision'],method='choose',education_id='high-school')
    c=app.select_hero_secondary(c['id'],revision=c['revision'],selections=[style],learned_level=1)
    t=app.hero_program_view(c['id'])['combat']['totals'];self.assertEqual({key:t[key]['value'] for key in totals},totals)
    self.assertEqual(app.resource_view(c['id'])['resources']['HP']['value'],72)
    self.assertEqual(app.import_character(app.export_character(c['id']))['level'],15)
  with tempfile.TemporaryDirectory() as directory:
   app=CharacterApplication(directory,die=lambda sides:4);c=app.create(game='heroes-unlimited',level=10)
   self.assertEqual(app.hero_program_view(c['id'])['combat']['totals']['attacks']['value'],6)
   c=app.select_education(c['id'],revision=c['revision'],method='choose',education_id='high-school')
   c=app.select_hero_secondary(c['id'],revision=c['revision'],selections=['hand-to-hand-basic','prowl'])
   c=app.advance(c['id'],revision=c['revision'],method='level',value=15)
   v=app.hero_program_view(c['id']);t=v['combat']['totals']
   self.assertEqual((t['attacks']['value'],t['parry']['value'],t['strike']['value'],t['damage']['value']),(5,2,1,0))
   self.assertEqual(next(s for s in v['skills'] if s['id']=='prowl')['percentage'],50)
   self.assertEqual(c['learning_levels']['hand-to-hand-basic'],10)
 def test_later_xp_boundaries_and_invalid_requests_preserve_the_save(self):
  from characters_unlimited.storage import SaveConflict
  with tempfile.TemporaryDirectory() as directory:
   app=CharacterApplication(directory,die=lambda sides:4);c=app.create(game='heroes-unlimited');c=app.generate_resources(c['id'],revision=0)
   for level,xp in [(2,2051),(3,4101),(4,8251),(5,16501),(6,24601),(7,34701),(8,49801),(9,69901),(10,95001),(11,130101),(12,180201),(13,230301),(14,280401),(15,340501)]:
    old=c
    c=app.advance(c['id'],revision=c['revision'],method='xp',value=xp-1);self.assertEqual(c['level'],level-1)
    c=app.advance(c['id'],revision=c['revision'],method='xp',value=xp);self.assertEqual((c['level'],c['experience']),(level,xp))
    with self.assertRaises(SaveConflict):app.advance(c['id'],revision=old['revision'],method='xp',value=xp)
   c=app.advance(c['id'],revision=c['revision'],method='xp',value=400600)
   for method,value in [('xp',400601),('xp',-1),('xp',True),('level',16),('level',True),('level',14)]:
    with self.assertRaises(ValueError):app.advance(c['id'],revision=c['revision'],method=method,value=value)
   self.assertEqual(app.get(c['id']),c)
   self.assertEqual(app.hero_program_view(c['id'])['combat']['totals']['attacks']['value'],7)
 def test_portable_later_history_tampering_and_rule_updates_are_atomic(self):
  from copy import deepcopy
  from characters_unlimited.rules import RuleArchive
  with tempfile.TemporaryDirectory() as directory:
   app=CharacterApplication(directory,die=lambda sides:4);c=app.create(game='heroes-unlimited',level=15)
   c=app.select_hero_powers(c['id'],revision=c['revision'],selections=['extraordinary-physical-endurance'])
   bundle=app.export_character(c['id']);count=len(app.list());cases=[]
   for key,value in [('level',4),('hp_roll',7),('source',{}),('before',{}),('power_hp_rolls',{})]:
    b=deepcopy(bundle);b['character']['later_advancements'][0][key]=value;cases.append(b)
   b=deepcopy(bundle);b['character']['later_advancements'].pop(2);cases.append(b)
   b=deepcopy(bundle);b['character']['later_advancements'].reverse();cases.append(b)
   b=deepcopy(bundle);b['character']['additional_rule_packs'].pop('heroes-higher-advancement');cases.append(b)
   for identifier in ['heroes-program-skills','heroes-education','heroes-resources','heroes-super-abilities','heroes-advancement']:
    b=deepcopy(bundle);b['character']['additional_rule_packs'].pop(identifier);cases.append(b)
   b=deepcopy(bundle);b['character']['later_advancements'][0]['before']['additional_rule_packs'].pop('heroes-higher-advancement');cases.append(b)
   b=deepcopy(bundle);b['character']['later_advancements'][0]['before']['learning_levels']['pilot-automobile']=3;cases.append(b)
   for b in cases:
    with self.assertRaises(ValueError):app.import_character(b)
   self.assertEqual((len(app.list()),app.get(c['id'])),(count,c))
   self.assertEqual(app.preview_rule_upgrade(c['id'])['changes'],[])
   archive=RuleArchive.load();future=deepcopy(archive.active('heroes-higher-advancement'));future['version']='99.0.0';future['hp_die']=8
   newer=CharacterApplication(directory,rule_archive=RuleArchive([*archive.definitions(),future],{**archive.active_versions(),'heroes-higher-advancement':'99.0.0'}))
   with self.assertRaisesRegex(ValueError,'recorded Heroes later advancement'):newer.preview_rule_upgrade(c['id'])
   self.assertEqual(newer.get(c['id']),c)
 def test_later_pdf_and_power_receipts_project_actual_level_and_dice(self):
  from io import BytesIO
  from pypdf import PdfReader
  with tempfile.TemporaryDirectory() as directory:
   app=CharacterApplication(directory,die=lambda sides:4);c=app.create(game='heroes-unlimited')
   c=app.select_education(c['id'],revision=0,method='choose',education_id='high-school')
   c=app.select_hero_secondary(c['id'],revision=c['revision'],selections=['hand-to-hand-basic','climbing'])
   c=app.select_hero_powers(c['id'],revision=c['revision'],selections=['extraordinary-physical-endurance'])
   c=app.generate_resources(c['id'],revision=c['revision']);c=app.advance(c['id'],revision=c['revision'],method='level',value=15)
   powers=app.hero_powers_view(c['id']);self.assertIn('HP level 15 +4',powers['powers'][0]['effect_summary'])
   self.assertIn('through level 15',' '.join(powers['powers'][0]['guidance']))
   fields=PdfReader(BytesIO(app.export_pdf(c['id']))).get_fields();assert fields
   for name,value in [('LEVEL','15'),('HP','153'),('PARRY','3'),('DODGE','3'),('ATTACKS','7'),('SECONDARY_ALLOWANCE','2 / 20'),('skills.climbing.percentage','98')]:self.assertEqual(fields[name]['/V'],value)
   text=' '.join(str(row.get('/V','')) for row in fields.values());self.assertIn('HP level 15 +4',text);self.assertIn('Critical strike or knockout from behind.',text)
   self.assertIn('learned at level 1',text)
 def test_undo_each_level_restores_choices_and_replay_never_resamples(self):
  from copy import deepcopy
  with tempfile.TemporaryDirectory() as directory:
   app=CharacterApplication(directory,die=lambda sides:4);c=app.create(game='heroes-unlimited')
   c=app.select_education(c['id'],revision=0,method='choose',education_id='high-school')
   c=app.select_hero_secondary(c['id'],revision=c['revision'],selections=['hand-to-hand-basic','prowl'])
   c=app.generate_resources(c['id'],revision=c['revision']);initial=deepcopy(c)
   c=app.advance(c['id'],revision=c['revision'],method='level',value=15)
   c=app.select_hero_secondary(c['id'],revision=c['revision'],selections=['hand-to-hand-basic','prowl','climbing'])
   gains=deepcopy(c['later_advancements'])
   result=app.undo_advancement(c['id'],revision=c['revision']);c=result['character']
   self.assertNotIn('climbing',c['hero_secondary_selections']);self.assertIn('climbing',result['recovery']['hero_secondary_selections'])
   while c['level']>1:c=app.undo_advancement(c['id'],revision=c['revision'])['character']
   self.assertEqual((c['attributes'],c['resources'],c['hero_secondary_selections'],c['education']),
                    (initial['attributes'],initial['resources'],initial['hero_secondary_selections'],initial['education']))
   self.assertEqual(app.resource_view(c['id'])['resources']['HP']['value'],16)
   self.assertFalse(any(d['active'] for d in app.hero_program_view(c['id'])['advancement']['dice']))
   app.die=lambda sides:(_ for _ in ()).throw(AssertionError('Replay must retain dice'))
   c=app.advance(c['id'],revision=c['revision'],method='level',value=15)
   self.assertEqual([e['hp_roll'] for e in c['later_advancements']],[e['hp_roll'] for e in gains])
   self.assertEqual(app.resource_view(c['id'])['resources']['HP']['value'],72)
   self.assertNotIn('climbing',c['hero_secondary_selections'])
   self.assertEqual(app.import_character(app.export_character(c['id']))['later_advancements'],c['later_advancements'])
