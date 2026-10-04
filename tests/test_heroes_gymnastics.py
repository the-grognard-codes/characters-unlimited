import tempfile,unittest
from copy import deepcopy
from characters_unlimited.application import CharacterApplication
class HeroesGymnasticsTests(unittest.TestCase):
 def test_gymnastics_combines_with_acrobatics_and_ordinary_skills_once(self):
  with tempfile.TemporaryDirectory() as directory:
   app=CharacterApplication(directory,die=lambda sides:4);c=app.create(game='heroes-unlimited')
   c=app.select_education(c['id'],revision=0,method='choose',education_id='high-school')
   c=app.set_attribute(c['id'],revision=c['revision'],attribute='IQ',mode='fixed',value=16)
   c=app.select_hero_secondary(c['id'],revision=c['revision'],selections=['prowl'])
   c=app.select_hero_programs(c['id'],revision=c['revision'],selections=[{'slot':0,'program':'physical-athletic','choices':{'physical':['acrobatics','gymnastics','climbing','hand-to-hand-basic']}}])
   view=app.hero_program_view(c['id']);skills={r['id']:r for r in view['skills']};gym=skills['gymnastics']
   self.assertEqual(view['warnings'],[])
   self.assertEqual((gym['primary_check_name'],gym['percentage'],gym['per_level']),('Sense of balance',57,3))
   self.assertEqual([(r['name'],r['percentage'],r['per_level']) for r in gym['additional_checks']],[('Work parallel bars & rings',67,3),('Climb rope',67,2),('Back flip',77,2)])
   self.assertEqual((skills['climbing']['percentage'],skills['climbing']['additional_checks'][0]['percentage'],skills['prowl']['percentage']),(67,57,37))
   self.assertEqual(tuple(c['attributes'][key]['value'] for key in ['PS','PP','PE']),(15,14,15))
   self.assertEqual(view['combat']['totals']['roll_with_impact']['value'],6)
   self.assertEqual(view['combat']['totals']['attacks']['value'],4)
   shared={r['name']:r for r in view['shared_abilities']['checks']}
   self.assertEqual({name:r['percentage'] for name,r in shared.items()},{'Sense of balance':67,'Walk tightrope or high wire':67,'Climb rope':77,'Back flip':77,'Work parallel bars & rings':67})
   self.assertEqual(shared['Sense of balance']['skill_id'],'acrobatics')
   self.assertEqual(shared['Back flip']['skill_id'],'gymnastics')
   self.assertEqual(shared['Back flip']['per_level'],2)
   self.assertEqual(len(shared['Climb rope']['origins']),2)
   c=app.generate_resources(c['id'],revision=c['revision'])
   self.assertEqual(app.resource_view(c['id'])['resources']['SDC']['value'],42)
   self.assertEqual(app.resource_view(c['id'])['resources']['HP']['value'],19)
   receipts=deepcopy(c['physical_acquisitions']);snapshot=deepcopy(c['resource_attribute_snapshot'])
   c=app.select_hero_programs(c['id'],revision=c['revision'],selections=[{'slot':0,'program':'physical-athletic','choices':{'physical':['acrobatics','climbing','hand-to-hand-basic']}}])
   skills={r['id']:r for r in app.hero_program_view(c['id'])['skills']}
   self.assertEqual((skills['climbing']['percentage'],skills['climbing']['additional_checks'][0]['percentage'],skills['prowl']['percentage']),(62,52,32))
   self.assertEqual(app.resource_view(c['id'])['resources']['SDC']['value'],34)
   self.assertEqual(app.resource_view(c['id'])['resources']['HP']['value'],19)
   c=app.select_hero_programs(c['id'],revision=c['revision'],selections=[{'slot':0,'program':'physical-athletic','choices':{'physical':['acrobatics','gymnastics','climbing','hand-to-hand-basic']}}])
   self.assertEqual(c['physical_acquisitions'],receipts);self.assertEqual(c['resource_attribute_snapshot'],snapshot)
   restored=app.import_character(app.export_character(c['id']))
   self.assertEqual(app.hero_program_view(restored['id'])['shared_abilities'],app.hero_program_view(c['id'])['shared_abilities'])

 def test_shared_fallbacks_use_best_check_without_granting_ordinary_skills(self):
  with tempfile.TemporaryDirectory() as directory:
   app=CharacterApplication(directory,die=lambda sides:4);c=app.create(game='heroes-unlimited')
   c=app.select_education(c['id'],revision=0,method='choose',education_id='high-school')
   c=app.select_hero_programs(c['id'],revision=c['revision'],selections=[{'slot':0,'program':'physical-athletic','choices':{'physical':['acrobatics','gymnastics']}}])
   view=app.hero_program_view(c['id']);checks={r['name']:r for r in view['shared_abilities']['checks']}
   self.assertEqual((checks['Base climb ability']['percentage'],checks['Base prowl ability']['percentage']),(45,35))
   self.assertEqual(checks['Base climb ability']['per_level'],0)
   self.assertEqual(checks['Base prowl ability']['per_level'],0)
   self.assertNotIn('climbing',[r['id'] for r in view['skills']]);self.assertNotIn('prowl',[r['id'] for r in view['skills']])
   self.assertNotIn('climbing',c['physical_acquisitions'])
   self.assertEqual(len(checks),7)

 def test_mixed_secondary_winner_has_no_borrowed_education_and_fixed_stats_win(self):
  with tempfile.TemporaryDirectory() as directory:
   app=CharacterApplication(directory,die=lambda sides:4);c=app.create(game='heroes-unlimited')
   c=app.select_education(c['id'],revision=0,method='choose',education_id='high-school')
   c=app.generate_resources(c['id'],revision=c['revision'])
   c=app.set_attribute(c['id'],revision=c['revision'],attribute='PS',mode='fixed',value=20)
   c=app.set_attribute(c['id'],revision=c['revision'],attribute='PE',mode='fixed',value=18)
   c=app.select_hero_programs(c['id'],revision=c['revision'],selections=[{'slot':0,'program':'physical-athletic','choices':{'physical':['acrobatics']}}])
   c=app.select_hero_secondary(c['id'],revision=c['revision'],selections=['gymnastics','gymnastics'])
   view=app.hero_program_view(c['id']);checks={r['name']:r for r in view['shared_abilities']['checks']}
   self.assertEqual(checks['Back flip']['percentage'],70)
   self.assertEqual(checks['Back flip']['contributions']['education'],0)
   self.assertTrue(checks['Back flip']['secondary_selected'])
   self.assertEqual(checks['Sense of balance']['percentage'],65)
   self.assertEqual((c['attributes']['PS']['value'],c['attributes']['PE']['value']),(20,18))
   self.assertEqual(app.resource_view(c['id'])['resources']['HP']['value'],16)
   self.assertEqual(view['combat']['totals']['attacks']['value'],3)
   self.assertEqual(view['combat']['parry_actions'],1)
   self.assertNotIn('gymnastics',view['secondary']['eligible_skill_ids'])
   self.assertTrue(any('Gymnastics is outside the eligible Secondary categories.' in r for r in view['warnings']))
   self.assertEqual(c['physical_acquisitions']['gymnastics']['rolls']['resource:SDC'],[4,4])

 def test_all_reviewed_physical_skills_combine_once_on_the_honor_system(self):
  with tempfile.TemporaryDirectory() as directory:
   app=CharacterApplication(directory,die=lambda sides:4);c=app.create(game='heroes-unlimited')
   c=app.select_education(c['id'],revision=0,method='choose',education_id='high-school')
   c=app.select_hero_secondary(c['id'],revision=c['revision'],selections=['body-building','running','athletics','boxing','acrobatics','gymnastics','hand-to-hand-martial-arts'])
   view=app.hero_program_view(c['id'])
   self.assertEqual(view['secondary']['used'],9)
   self.assertEqual(tuple(c['attributes'][key]['value'] for key in ['PS','PE','PP','SPD']),(20,16,14,32))
   for stat,value in [('attacks',5),('initiative',2),('damage',5),('parry',3),('dodge',3),('roll_with_impact',9),('pull_punch',3)]:self.assertEqual(view['combat']['totals'][stat]['value'],value)
   c=app.generate_resources(c['id'],revision=c['revision'])
   self.assertEqual(app.resource_view(c['id'])['resources']['SDC']['value'],76)

 def test_legacy_update_and_inactive_shared_definition_guard_reject_tampering(self):
  from characters_unlimited.rules import RuleArchive
  with tempfile.TemporaryDirectory() as directory:
   archive=RuleArchive.load();earlier=CharacterApplication(directory,die=lambda sides:4,rule_archive=RuleArchive(archive.definitions(),{**archive.active_versions(),'heroes-program-skills':'1.20.0'}))
   c=earlier.create(game='heroes-unlimited');c=earlier.select_education(c['id'],revision=0,method='choose',education_id='high-school')
   c=earlier.select_hero_secondary(c['id'],revision=c['revision'],selections=['acrobatics','climbing'])
   receipts=deepcopy(c['physical_acquisitions'])
   with self.assertRaises(ValueError):earlier.select_hero_secondary(c['id'],revision=c['revision'],selections=['gymnastics'])
   app=CharacterApplication(directory,die=lambda sides:4);preview=app.preview_rule_upgrade(c['id'])
   self.assertTrue(all(r['before']==r['after'] for r in preview['skills']));self.assertEqual(preview['combat'],[])
   c=app.apply_rule_upgrade(c['id'],revision=c['revision'],token=preview['token'])['character'];self.assertEqual(c['physical_acquisitions'],receipts)
   c=app.select_hero_secondary(c['id'],revision=c['revision'],selections=['acrobatics','gymnastics','climbing'])
   bad=app.export_character(c['id']);bad['character']['physical_acquisitions']['gymnastics']['rolls']['resource:SDC']=[7,4]
   with self.assertRaises(ValueError):app.import_character(bad)
   c=app.select_hero_secondary(c['id'],revision=c['revision'],selections=['acrobatics','climbing'])
   target=deepcopy(archive.active('heroes-program-skills'));target['version']='99.0.0'
   next(r for r in target['skills'] if r['id']=='gymnastics')['shared_check_skill_ids']=[]
   newer=CharacterApplication(directory,rule_archive=RuleArchive([*archive.definitions(),target],{**archive.active_versions(),'heroes-program-skills':'99.0.0'}))
   with self.assertRaises(ValueError):newer.preview_rule_upgrade(c['id'])
   self.assertEqual(app.get(c['id']),c)

 def test_outside_group_and_pending_repeat_cannot_add_shared_checks(self):
  with tempfile.TemporaryDirectory() as directory:
   app=CharacterApplication(directory,die=lambda sides:4);c=app.create(game='heroes-unlimited')
   c=app.select_education(c['id'],revision=0,method='choose',education_id='high-school')
   for selections in [[{'slot':0,'program':'computer','choices':{'repair-radio':['gymnastics']}}],
                      [{'slot':0,'program':'physical-athletic','choices':{'physical':['acrobatics']}},{'slot':1,'program':'physical-athletic','choices':{'physical':['gymnastics']}}]]:
    c=app.select_hero_programs(c['id'],revision=c['revision'],selections=selections)
    self.assertNotIn('gymnastics',c['physical_acquisitions'])
    self.assertEqual(app.hero_program_view(c['id'])['shared_abilities']['checks'],[])

 def test_pdf_outputs_duplicated_abilities_once_from_the_winning_source(self):
  from io import BytesIO
  from pypdf import PdfReader
  with tempfile.TemporaryDirectory() as directory:
   app=CharacterApplication(directory,die=lambda sides:4);c=app.create(game='heroes-unlimited')
   c=app.select_education(c['id'],revision=0,method='choose',education_id='high-school')
   c=app.select_hero_programs(c['id'],revision=c['revision'],selections=[{'slot':0,'program':'physical-athletic','choices':{'physical':['acrobatics','gymnastics','climbing','hand-to-hand-basic']}}])
   fields=PdfReader(BytesIO(app.export_pdf(c['id']))).get_fields();assert fields is not None
   self.assertEqual(fields['skills.acrobatics.name']['/V'],'Acrobatics: Sense of balance')
   self.assertNotIn('skills.gymnastics.name',fields)
   self.assertNotIn('skills.acrobatics.check2.name',fields)
   self.assertNotIn('skills.gymnastics.check1.name',fields)
   self.assertEqual(fields['skills.gymnastics.check2.percentage']['/V'],'75')
   self.assertEqual(fields['skills.gymnastics.check2.rate']['/V'],'2')
   names=[str(r.get('/V','')) for key,r in fields.items() if key.startswith('skills.') and key.endswith('.name')]
   for name in ['Sense of balance','Climb rope','Back flip','Base prowl ability']:self.assertEqual(sum(name in label for label in names),1)
   text=' '.join(' '.join(str(r.get('/V','')) for r in fields.values()).split())
   self.assertIn('use the best proficiency',text);self.assertIn('printed pp. 47, 56 / PDF pp. 48, 57',text)
   self.assertTrue(all(not r.get('/Ff',0)&1 for r in fields.values()))
if __name__=='__main__':unittest.main()
