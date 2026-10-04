import tempfile,unittest
from copy import deepcopy
from characters_unlimited.application import CharacterApplication
class HeroesWrestlingTests(unittest.TestCase):
 def test_wrestling_combines_once_with_normal_program_boxing_and_training(self):
  with tempfile.TemporaryDirectory() as directory:
   app=CharacterApplication(directory,die=lambda sides:4)
   c=app.create(game='heroes-unlimited')
   c=app.select_education(c['id'],revision=0,method='choose',education_id='high-school')
   c=app.select_hero_programs(c['id'],revision=c['revision'],selections=[{'slot':0,'program':'physical-athletic','choices':{'physical':['wrestling','boxing','hand-to-hand-basic','swimming']}}])
   view=app.hero_program_view(c['id'])
   self.assertEqual(view['program_choices'][0]['groups'][0]['credited'],4)
   self.assertEqual(view['warnings'],[])
   self.assertEqual((c['attributes']['PS']['value'],c['attributes']['PE']['value']),(16,13))
   for stat,value in [('attacks',5),('damage',1),('parry',2),('dodge',2),('roll_with_impact',4)]:self.assertEqual(view['combat']['totals'][stat]['value'],value)
   self.assertEqual(c['physical_acquisitions']['wrestling'],{'rolls':{'resource:SDC':[4,4,4,4]}})
   self.assertEqual(c['attributes']['PP']['value'],12)
   self.assertNotIn('wrestling',[row['id'] for row in view['skills']])
   self.assertNotIn('climbing',[row['id'] for row in view['skills']])
   swimming=next(row for row in view['skills'] if row['id']=='swimming')
   self.assertEqual(swimming['percentage'],55)
   c=app.generate_resources(c['id'],revision=c['revision'])
   self.assertEqual(app.resource_view(c['id'])['resources']['SDC']['value'],58)
   self.assertEqual(app.resource_view(c['id'])['resources']['HP']['value'],17)
   receipts=deepcopy(c['physical_acquisitions']);snapshot=deepcopy(c['resource_attribute_snapshot'])
   c=app.select_hero_programs(c['id'],revision=c['revision'],selections=[{'slot':0,'program':'physical-athletic','choices':{'physical':['boxing','hand-to-hand-basic','swimming']}}])
   self.assertEqual(c['attributes']['PE']['value'],12)
   self.assertEqual(app.resource_view(c['id'])['resources']['SDC']['value'],42)
   self.assertEqual(app.resource_view(c['id'])['resources']['HP']['value'],17)
   c=app.select_hero_programs(c['id'],revision=c['revision'],selections=[{'slot':0,'program':'physical-athletic','choices':{'physical':['wrestling','boxing','hand-to-hand-basic','swimming']}}])
   self.assertEqual(c['physical_acquisitions'],receipts)
   self.assertEqual(c['resource_attribute_snapshot'],snapshot)
   restored=app.import_character(app.export_character(c['id']))
   self.assertEqual(app.hero_program_view(restored['id'])['physical'],app.hero_program_view(c['id'])['physical'])

 def test_untrained_fixed_attributes_and_secondary_honor_choice(self):
  with tempfile.TemporaryDirectory() as directory:
   app=CharacterApplication(directory,die=lambda sides:4);c=app.create(game='heroes-unlimited')
   c=app.select_education(c['id'],revision=0,method='choose',education_id='high-school')
   c=app.set_attribute(c['id'],revision=c['revision'],attribute='PS',mode='fixed',value=20)
   c=app.set_attribute(c['id'],revision=c['revision'],attribute='PE',mode='fixed',value=18)
   c=app.select_hero_secondary(c['id'],revision=c['revision'],selections=['wrestling','wrestling'])
   view=app.hero_program_view(c['id'])
   self.assertNotIn('wrestling',view['secondary']['eligible_skill_ids'])
   self.assertEqual((c['attributes']['PS']['value'],c['attributes']['PE']['value']),(20,18))
   self.assertEqual(view['combat']['training'],'No Hand to Hand')
   self.assertEqual(view['combat']['parry_actions'],1)
   for stat,value in [('attacks',3),('roll_with_impact',1),('parry',0),('dodge',0),('damage',5)]:self.assertEqual(view['combat']['totals'][stat]['value'],value)
   self.assertTrue(any('Wrestling is outside the eligible Secondary categories.' in row for row in view['warnings']))
   self.assertEqual(c['physical_acquisitions']['wrestling']['rolls']['resource:SDC'],[4,4,4,4])
   bad=app.export_character(c['id']);bad['character']['physical_acquisitions']['wrestling']['rolls']['resource:SDC']=[7,4,4,4]
   with self.assertRaises(ValueError):app.import_character(bad)
   self.assertEqual(app.get(c['id']),c)

 def test_earlier_pin_requires_upgrade_and_retained_inactive_definition_is_bound(self):
  from characters_unlimited.rules import RuleArchive
  with tempfile.TemporaryDirectory() as directory:
   archive=RuleArchive.load()
   earlier=CharacterApplication(directory,die=lambda sides:4,rule_archive=RuleArchive(archive.definitions(),{**archive.active_versions(),'heroes-program-skills':'1.18.0'}))
   c=earlier.create(game='heroes-unlimited');c=earlier.select_education(c['id'],revision=0,method='choose',education_id='high-school')
   c=earlier.select_hero_secondary(c['id'],revision=c['revision'],selections=['hand-to-hand-basic'])
   selections=[{'slot':0,'program':'physical-athletic','choices':{'physical':['wrestling']}}]
   with self.assertRaises(ValueError):earlier.select_hero_programs(c['id'],revision=c['revision'],selections=selections)
   app=CharacterApplication(directory,die=lambda sides:4);preview=app.preview_rule_upgrade(c['id'])
   self.assertEqual(preview['combat'],[])
   c=app.apply_rule_upgrade(c['id'],revision=c['revision'],token=preview['token'])['character']
   c=app.select_hero_programs(c['id'],revision=c['revision'],selections=selections)
   c=app.select_hero_programs(c['id'],revision=c['revision'],selections=[])
   target=deepcopy(archive.active('heroes-program-skills'));target['version']='99.0.0'
   next(row for row in target['skills'] if row['id']=='wrestling')['attributes']['PE']['bonus']=2
   newer=CharacterApplication(directory,rule_archive=RuleArchive([*archive.definitions(),target],{**archive.active_versions(),'heroes-program-skills':'99.0.0'}))
   with self.assertRaises(ValueError):newer.preview_rule_upgrade(c['id'])
   self.assertEqual(app.get(c['id']),c)

 def test_pending_repeat_does_not_acquire_wrestling(self):
  with tempfile.TemporaryDirectory() as directory:
   app=CharacterApplication(directory,die=lambda sides:4);c=app.create(game='heroes-unlimited')
   c=app.select_education(c['id'],revision=0,method='choose',education_id='high-school')
   c=app.select_hero_programs(c['id'],revision=c['revision'],selections=[{'slot':0,'program':'physical-athletic','choices':{'physical':['boxing']}},{'slot':1,'program':'physical-athletic','choices':{'physical':['wrestling']}}])
   self.assertNotIn('wrestling',c['physical_acquisitions'])
   self.assertEqual(c['attributes']['PE']['value'],12)
   group=app.hero_program_view(c['id'])['program_choices'][1]['groups'][0]
   self.assertFalse(group['credit_certified']);self.assertEqual(group['credited'],0)

 def test_editable_pdf_shows_wrestling_moves_source_and_combined_totals(self):
  from io import BytesIO
  from pypdf import PdfReader
  with tempfile.TemporaryDirectory() as directory:
   app=CharacterApplication(directory,die=lambda sides:4);c=app.create(game='heroes-unlimited')
   c=app.select_education(c['id'],revision=0,method='choose',education_id='high-school')
   c=app.select_hero_programs(c['id'],revision=c['revision'],selections=[{'slot':0,'program':'physical-athletic','choices':{'physical':['wrestling','boxing','hand-to-hand-basic','swimming']}}])
   c=app.generate_resources(c['id'],revision=c['revision'])
   fields=PdfReader(BytesIO(app.export_pdf(c['id']))).get_fields();assert fields is not None
   for name,value in [('ATTACKS','5'),('PS','16'),('PE','13'),('SDC','58'),('HP','17')]:self.assertEqual(fields[name]['/V'],value)
   text=' '.join(' '.join(str(row.get('/V','')) for row in fields.values()).split())
   for phrase in ['Body block/tackle does 1D4','loses one melee attack','Pin/incapacitate on a roll of 18, 19 or 20','Crush/squeeze does 1D4','printed pp. 56 / PDF pp. 57']:self.assertIn(phrase,text)
   self.assertNotIn('Wrestling is outside the eligible Secondary categories.',text)
   self.assertNotIn('skills.wrestling.percentage',fields)
   self.assertTrue(all(not row.get('/Ff',0)&1 for row in fields.values()))
if __name__=='__main__':unittest.main()
