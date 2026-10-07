import tempfile,unittest,json
from io import BytesIO
from typing import Any
from pypdf import PdfReader
from pathlib import Path
from copy import deepcopy
from characters_unlimited.application import CharacterApplication
from characters_unlimited.rules import RuleArchive

def choices(*ids):return [{'skill_id':key,'pool':'related'} for key in ids]
def checks(view,identifier):
 row=next(row for row in view['selected'] if row['id']==identifier)
 return [row['percentage'],*[check['percentage'] for check in row['additional_checks']]]
class IndependentPhysicalChecksTests(unittest.TestCase):
 def test_each_check_advances_at_its_own_rate_and_fixed_checks_stay_fixed(self):
  with tempfile.TemporaryDirectory() as directory:
   app=CharacterApplication(directory,die=lambda sides:4);hero=app.create(character_class='city-rat')
   hero=app.select_skills(hero['id'],revision=0,selections=choices('acrobatics','gymnastics'))
   self.assertEqual(checks(app.skill_view(hero['id']),'acrobatics'),[65,65,85,65,45,35])
   hero=app.generate_resources(hero['id'],revision=hero['revision'])
   hero=app.advance(hero['id'],revision=hero['revision'],method='level',value=2)
   self.assertEqual(checks(app.skill_view(hero['id']),'acrobatics'),[70,68,87,70,45,35])
   self.assertEqual(checks(app.skill_view(hero['id']),'gymnastics'),[58,68,77,67,30,35])
   hero=app.undo_advancement(hero['id'],revision=hero['revision'])['character']
   self.assertEqual(checks(app.skill_view(hero['id']),'acrobatics'),[65,65,85,65,45,35])
 def test_fixed_training_does_not_backdate_later_full_skills_and_restores_on_removal(self):
  with tempfile.TemporaryDirectory() as directory:
   app=CharacterApplication(directory,die=lambda sides:4);hero=app.create(level=3,character_class='city-rat')
   hero=app.select_skills(hero['id'],revision=0,selections=choices('acrobatics'))
   hero=app.advance(hero['id'],revision=hero['revision'],method='level',value=4)
   hero=app.select_skills(hero['id'],revision=hero['revision'],selections=choices('acrobatics','climbing','prowl'))
   view=app.skill_view(hero['id']);self.assertEqual(checks(view,'acrobatics'),[70,68,87,70])
   self.assertEqual(checks(view,'climbing'),[60,50]);self.assertEqual(checks(view,'prowl'),[45])
   hero=app.advance(hero['id'],revision=hero['revision'],method='level',value=5)
   self.assertEqual(checks(app.skill_view(hero['id']),'climbing'),[65,55])
   hero=app.select_skills(hero['id'],revision=hero['revision'],selections=choices('acrobatics'))
   self.assertEqual(checks(app.skill_view(hero['id']),'acrobatics')[-2:],[45,35])
   imported=app.import_character(app.export_character(hero['id']))
   app=CharacterApplication(directory);self.assertEqual(checks(app.skill_view(imported['id']),'acrobatics')[-2:],[45,35])
 def test_shared_check_rules_reject_invalid_growth_and_selectors_before_dice(self):
  installed=RuleArchive.load();accepted=next(row for row in installed.definitions() if row['id']=='rifts-domestic-skills' and row['version']==installed.active_versions()['rifts-domestic-skills'])
  for change in [{'per_level':True},{'per_level':-1},{'unless_skill':'absent'},{'unexpected':1}]:
   pack=deepcopy(accepted);pack['version']='9.99.0';next(row for row in pack['skills'] if row['id']=='acrobatics')['additional_checks'][0].update(change)
   archive=RuleArchive(installed.definitions()+[pack],{**installed.active_versions(),pack['id']:pack['version']})
   with self.subTest(change=change),tempfile.TemporaryDirectory() as directory:
    draws=[]
    def die(sides):draws.append(sides);return 4
    app=CharacterApplication(directory,die=die,rule_archive=archive)
    with self.assertRaises(ValueError):app.create(character_class='city-rat')
    self.assertEqual(draws,[])


 def test_duplicate_training_bonuses_and_dice_survive_remove_reselect(self):
  with tempfile.TemporaryDirectory() as directory:
   draws=[]
   def die(sides):draws.append(sides);return 4
   app=CharacterApplication(directory,die=die);hero=app.create(character_class='city-rat')
   hero=app.select_skills(hero['id'],revision=0,selections=choices('acrobatics','acrobatics','gymnastics','climbing','prowl'))
   view=app.skill_view(hero['id']);self.assertEqual(checks(view,'climbing'),[65,55]);self.assertEqual(checks(view,'prowl'),[50])
   self.assertEqual([hero['attributes'][key]['value'] for key in ['PS','PP','PE']],[15,14,16])
   contributions=app.combat_view(hero['id'])['totals']['roll_with_impact']['contributions']
   self.assertEqual((contributions['Acrobatics'],contributions['Gymnastics']),(2,2))
   receipts=hero['physical_acquisitions'];count=len(draws)
   hero=app.select_skills(hero['id'],revision=hero['revision'],selections=[])
   hero=app.select_skills(hero['id'],revision=hero['revision'],selections=choices('acrobatics','gymnastics','climbing','prowl'))
   self.assertEqual(hero['physical_acquisitions'],receipts);self.assertEqual(len(draws),count)
   self.assertEqual(sum(row['effects']['resources']['SDC']['value'] for row in app.skill_view(hero['id'])['selected'] if row['id'] in ('acrobatics','gymnastics')),12)
 def test_old_pin_upgrades_explicitly_and_preserves_existing_physical_receipts(self):
  installed=RuleArchive.load();old=RuleArchive(installed.definitions(),{**installed.active_versions(),'rifts-domestic-skills':'2.21.0'})
  with tempfile.TemporaryDirectory() as directory:
   app=CharacterApplication(directory,die=lambda sides:4,rule_archive=old);hero=app.create(character_class='city-rat')
   hero=app.select_skills(hero['id'],revision=0,selections=choices('climbing','juggling'));receipts=hero['physical_acquisitions']
   app=CharacterApplication(directory);self.assertEqual(len(app.skill_view(hero['id'])['catalog']),200)
   with self.assertRaises(ValueError):app.select_skills(hero['id'],revision=hero['revision'],selections=choices('acrobatics'))
   preview=app.preview_rule_upgrade(hero['id']);hero=app.apply_rule_upgrade(hero['id'],revision=hero['revision'],token=preview['token'])['character']
   self.assertEqual(hero['physical_acquisitions'],receipts);self.assertEqual(len(app.skill_view(hero['id'])['catalog']),213)
 def test_editable_pdf_uses_projected_checks_and_suppresses_basic_training(self):
  with tempfile.TemporaryDirectory() as directory:
   app=CharacterApplication(directory,die=lambda sides:4);hero=app.create(character_class='city-rat')
   hero=app.select_skills(hero['id'],revision=0,selections=choices('acrobatics','gymnastics','climbing','prowl'))
   hero=app.generate_resources(hero['id'],revision=hero['revision']);app.advance(hero['id'],revision=hero['revision'],method='level',value=2)
   fields=PdfReader(BytesIO(app.export_pdf(hero['id']))).get_fields() or {}
   text='\n'.join(str(row.get('/V','')) for row in fields.values())
   self.assertIn('Tightrope or high wire',text);self.assertIn('Parallel bars and rings',text)
   self.assertNotIn(' ? Basic climb',text);self.assertNotIn(' ? Basic prowl',text)
 def test_required_checks_share_growth_and_validate_before_dice(self):
  installed=RuleArchive.load();accepted=next(row for row in installed.definitions() if row['id']=='rifts-domestic-skills' and row['version']==installed.active_versions()['rifts-domestic-skills'])
  pack=deepcopy(accepted);pack['version']='9.99.0';source={'book':'Test source','section':'Required drills'}
  grant: dict[str,Any]={'id':'source-check','name':'Source check','base':10,'per_level':1,'class_bonus':0,'source':source,'additional_checks':[{'name':'Timing','base':20,'per_level':3}],'proficiency_rules':{'independent_checks':True,'source':source}}
  pack['class_profiles']['vagabond']['required']['grants'].append(grant)
  def archive():return RuleArchive(installed.definitions()+[pack],{**installed.active_versions(),pack['id']:pack['version']})
  with tempfile.TemporaryDirectory() as directory:
   app=CharacterApplication(directory,die=lambda sides:4,rule_archive=archive());hero=app.create(level=3)
   row=next(row for row in app.skill_view(hero['id'])['grants'] if row['id']=='source-check')
   self.assertEqual((row['percentage'],row['additional_checks'][0]['percentage']),(12,26))
  grant['additional_checks'][0]['per_level']=True
  with tempfile.TemporaryDirectory() as directory:
   draws=[]
   def die(sides):draws.append(sides);return 4
   app=CharacterApplication(directory,die=die,rule_archive=archive())
   with self.assertRaises(ValueError):app.create(character_class='city-rat')
   self.assertEqual(draws,[])

 def test_intelligence_applies_to_fixed_checks_without_experience_growth(self):
  with tempfile.TemporaryDirectory() as directory:
   app=CharacterApplication(directory,die=lambda sides:4);hero=app.create(level=3,character_class='city-rat')
   hero=app.select_skills(hero['id'],revision=0,selections=choices('acrobatics','gymnastics'))
   hero=app.set_attribute(hero['id'],revision=hero['revision'],attribute='IQ',mode='fixed',value=16)
   hero=app.advance(hero['id'],revision=hero['revision'],method='level',value=15)
   self.assertEqual(checks(app.skill_view(hero['id']),'acrobatics'),[98,98,98,98,47,37])
   self.assertEqual(checks(app.skill_view(hero['id']),'gymnastics')[-2:],[32,37])
 def test_independent_declaration_shape_and_source_reject_before_dice(self):
  installed=RuleArchive.load();accepted=next(row for row in installed.definitions() if row['id']=='rifts-domestic-skills' and row['version']==installed.active_versions()['rifts-domestic-skills'])
  for rules in [None,{}, {'independent_checks':False,'source':{'book':'Test','section':'Checks'}}, {'independent_checks':True,'source':{}}, {'independent_checks':True,'source':{'book':'Test','section':'Checks'},'extra':True}]:
   pack=deepcopy(accepted);pack['version']='9.99.0';next(row for row in pack['skills'] if row['id']=='acrobatics')['proficiency_rules']=rules
   archive=RuleArchive(installed.definitions()+[pack],{**installed.active_versions(),pack['id']:pack['version']})
   with self.subTest(rules=rules),tempfile.TemporaryDirectory() as directory:
    draws=[]
    def die(sides):draws.append(sides);return 4
    app=CharacterApplication(directory,die=die,rule_archive=archive)
    with self.assertRaises(ValueError):app.create()
    self.assertEqual(draws,[])

 def test_required_profile_checks_resolve_selectors_against_the_shared_catalog(self):
  installed=RuleArchive.load();accepted=next(row for row in installed.definitions() if row['id']=='rifts-domestic-skills' and row['version']==installed.active_versions()['rifts-domestic-skills'])
  pack=deepcopy(accepted);pack['version']='9.99.0';source={'book':'Test source','section':'Required profile checks'}
  grant: dict[str,Any]={'id':'source-check','name':'Source check','base':10,'per_level':1,'class_bonus':0,'source':source,'additional_checks':[{'name':'Basic stealth','base':20,'per_level':0,'unless_skill':'prowl'}],'proficiency_rules':{'independent_checks':True,'source':source}}
  pack['class_profiles']['city-rat']['required']['grants'].append(grant)
  archive=RuleArchive(installed.definitions()+[pack],{**installed.active_versions(),pack['id']:pack['version']})
  with tempfile.TemporaryDirectory() as directory:
   app=CharacterApplication(directory,die=lambda sides:4,rule_archive=archive);hero=app.create(level=3,character_class='city-rat')
   row=next(row for row in app.skill_view(hero['id'])['grants'] if row['id']=='source-check')
   self.assertEqual(row['additional_checks'][0]['percentage'],20)
   app.select_skills(hero['id'],revision=hero['revision'],selections=choices('prowl'))
   row=next(row for row in app.skill_view(hero['id'])['grants'] if row['id']=='source-check')
   self.assertEqual(row['additional_checks'],[])
