import tempfile,unittest
from copy import deepcopy
from characters_unlimited.application import CharacterApplication
class HeroesAcrobaticsTests(unittest.TestCase):
 def test_acrobatics_has_independent_checks_and_retained_physical_effects(self):
  with tempfile.TemporaryDirectory() as directory:
   app=CharacterApplication(directory,die=lambda sides:4);c=app.create(game='heroes-unlimited')
   c=app.select_education(c['id'],revision=0,method='choose',education_id='high-school')
   c=app.select_hero_programs(c['id'],revision=c['revision'],selections=[{'slot':0,'program':'physical-athletic','choices':{'physical':['acrobatics','hand-to-hand-basic','swimming']}}])
   view=app.hero_program_view(c['id']);acro=next(row for row in view['skills'] if row['id']=='acrobatics')
   self.assertEqual((acro['primary_check_name'],acro['percentage'],acro['per_level']),('Sense of balance',65,2))
   self.assertEqual([(row['name'],row['percentage'],row['per_level']) for row in acro['additional_checks']],
    [('Walk tightrope or high wire',65,3),('Climb rope',75,2),('Back flip',55,5),('Base climb ability',45,0),('Base prowl ability',35,0)])
   self.assertEqual(tuple(c['attributes'][key]['value'] for key in ['PS','PP','PE']),(13,13,13))
   self.assertEqual(view['combat']['totals']['roll_with_impact']['value'],4)
   self.assertEqual(view['combat']['totals']['attacks']['value'],4)
   self.assertEqual(c['physical_acquisitions']['acrobatics']['rolls']['resource:SDC'],[4])
   c=app.generate_resources(c['id'],revision=c['revision'])
   self.assertEqual(app.resource_view(c['id'])['resources']['SDC']['value'],34)
   self.assertEqual(app.resource_view(c['id'])['resources']['HP']['value'],17)

 def test_actual_skills_replace_fallbacks_and_bonuses_disappear_with_acrobatics(self):
  with tempfile.TemporaryDirectory() as directory:
   app=CharacterApplication(directory,die=lambda sides:4);c=app.create(game='heroes-unlimited')
   c=app.select_education(c['id'],revision=0,method='choose',education_id='high-school')
   c=app.select_hero_secondary(c['id'],revision=c['revision'],selections=['prowl'])
   selections=[{'slot':0,'program':'physical-athletic','choices':{'physical':['acrobatics','climbing','hand-to-hand-basic','swimming']}}]
   c=app.select_hero_programs(c['id'],revision=c['revision'],selections=selections)
   view=app.hero_program_view(c['id']);skills={row['id']:row for row in view['skills']}
   self.assertEqual(view['warnings'],[])
   self.assertEqual((skills['climbing']['percentage'],skills['climbing']['additional_checks'][0]['percentage'],skills['prowl']['percentage']),(60,50,30))
   self.assertEqual(skills['climbing']['contributions']['Acrobatics'],15)
   self.assertEqual(len(skills['acrobatics']['additional_checks']),3)
   self.assertEqual(skills['acrobatics']['additional_checks'][1]['percentage'],75)
   c=app.generate_resources(c['id'],revision=c['revision']);snapshot=deepcopy(c['resource_attribute_snapshot']);receipts=deepcopy(c['physical_acquisitions'])
   c=app.select_hero_programs(c['id'],revision=c['revision'],selections=[{'slot':0,'program':'physical-athletic','choices':{'physical':['climbing','hand-to-hand-basic','swimming']}}])
   skills={row['id']:row for row in app.hero_program_view(c['id'])['skills']}
   self.assertEqual((skills['climbing']['percentage'],skills['climbing']['additional_checks'][0]['percentage'],skills['prowl']['percentage']),(45,35,25))
   self.assertEqual(app.resource_view(c['id'])['resources']['SDC']['value'],30)
   self.assertEqual(app.resource_view(c['id'])['resources']['HP']['value'],17)
   c=app.select_hero_programs(c['id'],revision=c['revision'],selections=selections)
   self.assertEqual(c['physical_acquisitions'],receipts);self.assertEqual(c['resource_attribute_snapshot'],snapshot)
   restored=app.import_character(app.export_character(c['id']))
   self.assertEqual(app.hero_program_view(restored['id'])['skills'],app.hero_program_view(c['id'])['skills'])

 def test_secondary_duplicates_fixed_values_and_prior_hp_snapshot(self):
  with tempfile.TemporaryDirectory() as directory:
   app=CharacterApplication(directory,die=lambda sides:4);c=app.create(game='heroes-unlimited')
   c=app.select_education(c['id'],revision=0,method='choose',education_id='high-school')
   c=app.generate_resources(c['id'],revision=c['revision'])
   c=app.set_attribute(c['id'],revision=c['revision'],attribute='IQ',mode='fixed',value=16)
   c=app.set_attribute(c['id'],revision=c['revision'],attribute='PS',mode='fixed',value=20)
   c=app.select_hero_secondary(c['id'],revision=c['revision'],selections=['acrobatics','acrobatics'])
   view=app.hero_program_view(c['id']);acro=next(row for row in view['skills'] if row['id']=='acrobatics')
   self.assertEqual(acro['percentage'],62)
   self.assertEqual([row['percentage'] for row in acro['additional_checks']],[62,72,52,42,32])
   self.assertEqual(c['attributes']['PS']['value'],20)
   self.assertEqual(c['attributes']['PE']['value'],13)
   self.assertEqual(view['combat']['totals']['attacks']['value'],3)
   self.assertEqual(view['combat']['parry_actions'],1)
   self.assertEqual(app.resource_view(c['id'])['resources']['HP']['value'],16)
   self.assertNotIn('acrobatics',view['secondary']['eligible_skill_ids'])
   self.assertTrue(any('Acrobatics is outside the eligible Secondary categories.' in row for row in view['warnings']))
   self.assertEqual(c['physical_acquisitions']['acrobatics']['rolls']['resource:SDC'],[4])
   bad=app.export_character(c['id']);bad['character']['physical_acquisitions']['acrobatics']['rolls']['resource:SDC']=[7]
   with self.assertRaises(ValueError):app.import_character(bad)
   self.assertEqual(app.get(c['id']),c)

 def test_outside_group_and_pending_repeat_have_no_physical_proficiency_or_bonuses(self):
  with tempfile.TemporaryDirectory() as directory:
   app=CharacterApplication(directory,die=lambda sides:4);c=app.create(game='heroes-unlimited')
   c=app.select_education(c['id'],revision=0,method='choose',education_id='high-school')
   c=app.select_hero_secondary(c['id'],revision=c['revision'],selections=['prowl'])
   selections=[{'slot':0,'program':'computer','choices':{'repair-radio':['acrobatics','swimming','climbing']}}]
   c=app.select_hero_programs(c['id'],revision=c['revision'],selections=selections)
   view=app.hero_program_view(c['id']);skills={row['id']:row for row in view['skills']}
   self.assertFalse(set(['acrobatics','swimming','climbing']).intersection(skills))
   self.assertEqual(skills['prowl']['percentage'],25)
   self.assertNotIn('acrobatics',c['physical_acquisitions'])
   selections=[{'slot':0,'program':'physical-athletic','choices':{'physical':['climbing']}},{'slot':1,'program':'physical-athletic','choices':{'physical':['acrobatics']}}]
   c=app.select_hero_programs(c['id'],revision=c['revision'],selections=selections)
   skills={row['id']:row for row in app.hero_program_view(c['id'])['skills']}
   self.assertNotIn('acrobatics',skills);self.assertEqual(skills['climbing']['percentage'],45)
   self.assertNotIn('acrobatics',c['physical_acquisitions'])

 def test_legacy_upgrade_keeps_prior_definitions_and_binds_inactive_modifiers(self):
  from characters_unlimited.rules import RuleArchive
  with tempfile.TemporaryDirectory() as directory:
   archive=RuleArchive.load();earlier=CharacterApplication(directory,die=lambda sides:4,rule_archive=RuleArchive(archive.definitions(),{**archive.active_versions(),'heroes-program-skills':'1.19.0'}))
   c=earlier.create(game='heroes-unlimited');c=earlier.select_education(c['id'],revision=0,method='choose',education_id='high-school')
   c=earlier.select_hero_secondary(c['id'],revision=c['revision'],selections=['climbing','prowl'])
   receipts=deepcopy(c['physical_acquisitions'])
   with self.assertRaises(ValueError):earlier.select_hero_secondary(c['id'],revision=c['revision'],selections=['acrobatics'])
   app=CharacterApplication(directory,die=lambda sides:4);preview=app.preview_rule_upgrade(c['id'])
   self.assertTrue(all(row['before']==row['after'] for row in preview['skills']))
   self.assertEqual(preview['combat'],[])
   c=app.apply_rule_upgrade(c['id'],revision=c['revision'],token=preview['token'])['character']
   self.assertEqual(c['physical_acquisitions'],receipts)
   c=app.select_hero_secondary(c['id'],revision=c['revision'],selections=['climbing','prowl','acrobatics'])
   c=app.select_hero_secondary(c['id'],revision=c['revision'],selections=['climbing','prowl'])
   target=deepcopy(archive.active('heroes-program-skills'));target['version']='99.0.0'
   next(row for row in target['skills'] if row['id']=='acrobatics')['skill_bonuses'][0]['amount']=20
   newer=CharacterApplication(directory,rule_archive=RuleArchive([*archive.definitions(),target],{**archive.active_versions(),'heroes-program-skills':'99.0.0'}))
   with self.assertRaises(ValueError):newer.preview_rule_upgrade(c['id'])
   self.assertEqual(app.get(c['id']),c)

 def test_pdf_labels_balance_and_preserves_all_separate_check_rates(self):
  from io import BytesIO
  from pypdf import PdfReader
  with tempfile.TemporaryDirectory() as directory:
   app=CharacterApplication(directory,die=lambda sides:4);c=app.create(game='heroes-unlimited')
   c=app.select_education(c['id'],revision=0,method='choose',education_id='high-school')
   c=app.select_hero_programs(c['id'],revision=c['revision'],selections=[{'slot':0,'program':'physical-athletic','choices':{'physical':['acrobatics']}}])
   fields=PdfReader(BytesIO(app.export_pdf(c['id']))).get_fields();assert fields is not None
   self.assertEqual(fields['skills.acrobatics.name']['/V'],'Acrobatics: Sense of balance')
   for index,rate in enumerate([3,2,5,0,0]):self.assertEqual(fields[f'skills.acrobatics.check{index}.rate']['/V'],str(rate))
   text=' '.join(' '.join(str(row.get('/V','')) for row in fields.values()).split())
   self.assertIn('Acrobatics',text);self.assertIn('printed pp. 55 / PDF pp. 56',text)
   self.assertIn('implementation interpretation',text)
   self.assertTrue(all(not row.get('/Ff',0)&1 for row in fields.values()))
if __name__=='__main__':unittest.main()
