import unittest,tempfile
from characters_unlimited.application import CharacterApplication
class HeroesPhysicalProgramTests(unittest.TestCase):
 def test_physical_program_grants_boxing_and_four_weighted_choices(self):
  with tempfile.TemporaryDirectory() as directory:
   app=CharacterApplication(directory,die=lambda sides:4)
   c=app.create(game='heroes-unlimited')
   c=app.select_education(c['id'],revision=0,method='choose',education_id='high-school')
   c=app.select_hero_programs(c['id'],revision=c['revision'],selections=[{'slot':0,'program':'physical-athletic','choices':{'physical':['boxing','hand-to-hand-martial-arts']}}])
   view=app.hero_program_view(c['id']);group=view['program_choices'][0]['groups'][0]
   self.assertEqual((group['credited'],group['remaining']),(4,0))
   self.assertEqual(view['secondary']['used'],0)
   self.assertEqual(c['attributes']['PS']['value'],14)
   self.assertEqual(view['combat']['totals']['attacks']['value'],5)
   self.assertEqual(view['combat']['totals']['roll_with_impact']['value'],4)
   self.assertEqual(view['warnings'],[])

 def test_program_training_addition_preserves_the_existing_active_profile(self):
  with tempfile.TemporaryDirectory() as directory:
   app=CharacterApplication(directory,die=lambda sides:4)
   c=app.create(game='heroes-unlimited')
   c=app.select_education(c['id'],revision=0,method='choose',education_id='high-school')
   c=app.select_hero_secondary(c['id'],revision=c['revision'],selections=['hand-to-hand-basic'])
   c=app.select_hero_programs(c['id'],revision=c['revision'],selections=[{'slot':0,'program':'physical-athletic','choices':{'physical':['boxing','hand-to-hand-martial-arts']}}])
   self.assertEqual(app.hero_program_view(c['id'])['combat']['training'],'Hand to Hand: Basic')
   self.assertEqual(c['hero_combat_training'],'hand-to-hand-basic')
   c=app.select_hero_training(c['id'],revision=c['revision'],training_id=None)
   c=app.select_hero_programs(c['id'],revision=c['revision'],selections=[])
   self.assertIsNone(c['hero_combat_training'])
   self.assertEqual(app.hero_program_view(c['id'])['combat']['training'],'No Hand to Hand')

 def test_weighted_choices_keep_duplicates_and_excess_and_apply_percentages_once(self):
  from copy import deepcopy
  with tempfile.TemporaryDirectory() as directory:
   app=CharacterApplication(directory,die=lambda sides:4)
   c=app.create(game='heroes-unlimited')
   c=app.select_education(c['id'],revision=0,method='choose',education_id='high-school')
   c=app.set_attribute(c['id'],revision=c['revision'],attribute='IQ',mode='fixed',value=16)
   selections=[{'slot':0,'program':'physical-athletic','choices':{'physical':['boxing','boxing','climbing','swimming','athletics','hand-to-hand-martial-arts','research']}}]
   c=app.select_hero_programs(c['id'],revision=c['revision'],selections=selections)
   view=app.hero_program_view(c['id']);group=view['program_choices'][0]['groups'][0]
   self.assertEqual((group['entered'],group['credited'],group['remaining']),(7,7,-3))
   self.assertTrue(any('repeated choices' in row for row in view['warnings']))
   self.assertTrue(any('outside-group' in row for row in view['warnings']))
   self.assertTrue(any('exceeds the allowance by 3' in row for row in view['warnings']))
   skills={row['id']:row for row in view['skills']}
   self.assertEqual((skills['climbing']['percentage'],skills['climbing']['additional_checks'][0]['percentage'],skills['swimming']['percentage']),(47,37,57))
   self.assertEqual(skills['research']['contributions']['education'],0)
   self.assertEqual(view['combat']['totals']['attacks']['value'],5)
   c=app.generate_resources(c['id'],revision=c['revision'])
   self.assertEqual(app.resource_view(c['id'])['resources']['SDC']['value'],50)
   receipts=deepcopy(c['physical_acquisitions']);snapshot=deepcopy(c['resource_attribute_snapshot'])
   c=app.select_hero_programs(c['id'],revision=c['revision'],selections=[])
   self.assertEqual(app.resource_view(c['id'])['resources']['SDC']['value'],30)
   c=app.select_hero_programs(c['id'],revision=c['revision'],selections=selections)
   self.assertEqual(c['physical_acquisitions'],receipts);self.assertEqual(c['resource_attribute_snapshot'],snapshot)
   restored=app.import_character(app.export_character(c['id']))
   self.assertEqual(app.hero_program_view(restored['id'])['physical'],app.hero_program_view(c['id'])['physical'])

 def test_pdf_shows_weighted_program_count_and_normal_boxing_entitlement(self):
  from io import BytesIO
  from pypdf import PdfReader
  with tempfile.TemporaryDirectory() as directory:
   app=CharacterApplication(directory,die=lambda sides:4)
   c=app.create(game='heroes-unlimited')
   c=app.select_education(c['id'],revision=0,method='choose',education_id='high-school')
   c=app.select_hero_programs(c['id'],revision=c['revision'],selections=[{'slot':0,'program':'physical-athletic','choices':{'physical':['boxing','hand-to-hand-martial-arts']}}])
   fields=PdfReader(BytesIO(app.export_pdf(c['id']))).get_fields();assert fields is not None
   text=' '.join(' '.join(str(row.get('/V','')) for row in fields.values()).split())
   self.assertIn('Physical skills: 4 selections used / 4 allowed / 0 remaining',text)
   self.assertIn('Expert costs two',text)
   self.assertIn('printed pp. 45, 46, 55 / PDF pp. 46, 47, 56',text)
   self.assertNotIn('Boxing is outside the eligible Secondary categories.',text)
   self.assertEqual(fields['ATTACKS']['/V'],'5')
   self.assertEqual(fields['SECONDARY_ALLOWANCE']['/V'],'0 / 10')
   self.assertTrue(all(not row.get('/Ff',0)&1 for row in fields.values()))

 def test_earlier_pin_requires_update_and_outside_group_physical_choices_stay_inactive(self):
  from copy import deepcopy
  from characters_unlimited.rules import RuleArchive
  with tempfile.TemporaryDirectory() as directory:
   archive=RuleArchive.load()
   earlier=CharacterApplication(directory,die=lambda sides:4,rule_archive=RuleArchive(archive.definitions(),{**archive.active_versions(),'heroes-program-skills':'1.17.0'}))
   c=earlier.create(game='heroes-unlimited')
   c=earlier.select_education(c['id'],revision=0,method='choose',education_id='high-school')
   c=earlier.select_hero_secondary(c['id'],revision=c['revision'],selections=['hand-to-hand-basic'])
   with self.assertRaises(ValueError):earlier.select_hero_programs(c['id'],revision=c['revision'],selections=[{'slot':0,'program':'physical-athletic'}])
   app=CharacterApplication(directory,die=lambda sides:4);preview=app.preview_rule_upgrade(c['id'])
   self.assertEqual(preview['combat'],[])
   c=app.apply_rule_upgrade(c['id'],revision=c['revision'],token=preview['token'])['character']
   c=app.select_hero_programs(c['id'],revision=c['revision'],selections=[{'slot':0,'program':'computer','choices':{'repair-radio':['boxing']}}])
   self.assertNotIn('boxing',c['physical_acquisitions']);self.assertEqual(c['attributes']['PS']['value'],12)
   selections=[{'slot':0,'program':'physical-athletic','choices':{'physical':['boxing','climbing','swimming','hand-to-hand-basic']}}]
   c=app.select_hero_programs(c['id'],revision=c['revision'],selections=selections)
   bad=app.export_character(c['id']);bad['character']['physical_acquisitions']['boxing']['rolls']['resource:SDC']=[7,4,4]
   with self.assertRaises(ValueError):app.import_character(bad)
   c=app.select_hero_programs(c['id'],revision=c['revision'],selections=[])
   target=deepcopy(archive.active('heroes-program-skills'));target['version']='99.0.0'
   next(row for row in target['skills'] if row['id']=='boxing')['combat']['attacks']=2
   newer=CharacterApplication(directory,rule_archive=RuleArchive([*archive.definitions(),target],{**archive.active_versions(),'heroes-program-skills':'99.0.0'}))
   with self.assertRaises(ValueError):newer.preview_rule_upgrade(c['id'])
   self.assertEqual(app.get(c['id']),c)

 def test_pending_repeat_retains_choices_without_certifying_or_granting_new_physical_effects(self):
  with tempfile.TemporaryDirectory() as directory:
   app=CharacterApplication(directory,die=lambda sides:4)
   c=app.create(game='heroes-unlimited')
   c=app.select_education(c['id'],revision=0,method='choose',education_id='high-school')
   selections=[{'slot':0,'program':'physical-athletic','choices':{'physical':['boxing','hand-to-hand-martial-arts']}},
               {'slot':1,'program':'physical-athletic','choices':{'physical':['body-building','running','swimming','athletics']}}]
   c=app.select_hero_programs(c['id'],revision=c['revision'],selections=selections)
   view=app.hero_program_view(c['id']);groups=[row['groups'][0] for row in view['program_choices']]
   self.assertEqual((groups[0]['credited'],groups[0]['remaining']),(4,0))
   self.assertEqual((groups[1]['credited'],groups[1]['remaining']),(0,4))
   self.assertFalse(groups[1]['credit_certified'])
   self.assertEqual(view['selections'],selections)
   self.assertNotIn('running',c['physical_acquisitions'])
   self.assertNotIn('swimming',[row['id'] for row in view['skills']])
   self.assertEqual((c['attributes']['PS']['value'],c['attributes']['PE']['value'],c['attributes']['SPD']['value']),(14,12,12))
   self.assertEqual(view['combat']['totals']['attacks']['value'],5)
   self.assertTrue(any('repeat entitlement' in row for row in view['warnings']))
   c=app.select_hero_programs(c['id'],revision=c['revision'],selections=[selections[1]])
   self.assertEqual(app.hero_program_view(c['id'])['program_choices'][0]['groups'][0]['credited'],4)
   self.assertIn('running',c['physical_acquisitions'])
