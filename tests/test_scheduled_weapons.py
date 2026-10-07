"""Public age-qualified weapon awards without changing old archived profiles."""
from pathlib import Path
from copy import deepcopy
import tempfile
import unittest
from typing import Any
from characters_unlimited.application import CharacterApplication
from characters_unlimited.rules import RuleArchive
from characters_unlimited.advancement import learning_key


class ScheduledWeaponTests(unittest.TestCase):
    archive = staticmethod(RuleArchive.load)
    choices: dict[str, Any] = {'ancient':['knife','sword','blunt'],'modern':['handguns','energy-pistol','energy-rifle','rifles'],'hand_to_hand':'basic'}

    def fixture(self,mutation=None):
        skills=self.archive().active('rifts-domestic-skills')
        skills['version']='weapon-schedule-fixture'
        profile=deepcopy(skills['class_profiles']['coalition-technical-officer-weapons'])
        for field in ('class_bonuses','advancement'):
         profile[field]['class_id']='vagabond'
        source={'book':'Synthetic framework fixture','section':'Source-scheduled weapon awards'}
        combat=profile['combat']
        shield=deepcopy(combat['ancient'][0]);shield.update(id='shield',name='Fixture Shield',source=source)
        combat['ancient'].append(shield)
        combat['fixed_proficiencies']={'ancient':[],'modern':[],'source':source}
        combat['required_proficiencies']={'ancient':'any','modern':'any'}
        combat['proficiency_counts']={'ancient':2,'modern':2}
        combat['additional_proficiency_cost']=1
        combat['proficiency_schedule']={'fixed':[{'level':2,'family':'ancient','id':'shield','source':source}],
         'awards':[{'id':'level-five','name':'Level five weapon training','level':5,'count':3,'source':source}],
         'initial_paid_minimum':{'count':3,'before_level':5,'source':source}}
        skills['class_profiles']['vagabond']=profile
        if mutation:
         mutation(skills)
        original=self.archive()
        return RuleArchive([*original.definitions(),skills],{**original.active_versions(),'rifts-domestic-skills':skills['version']})

    def no_roll(self,sides):
        self.fail('Retained training and portable replay must not reroll')

    def test_initial_paid_choices_and_later_awards_replay_and_undo(self):
        choices = self.choices
        with tempfile.TemporaryDirectory() as directory,tempfile.TemporaryDirectory() as copied:
         app=CharacterApplication(directory,die=lambda sides:3,rule_archive=self.fixture())
         hero=app.create()
         hero=app.select_combat(hero['id'],revision=hero['revision'],choices=choices)
         assert app.combat_view(hero['id'])['related_cost']==3
         hero=app.generate_resources(hero['id'],revision=hero['revision'])
         hero=app.advance(hero['id'],revision=hero['revision'],method='level',value=5)
         view=app.combat_view(hero['id'])
         assert view['related_cost']==3,view['weapon_entitlements']
         assert view['remaining']['weapon_awards']==3
         assert view['weapon_entitlements']['initial_paid_requirement']['remaining']==0
         assert 'shield' in view['fixed_proficiencies']['ancient']
         app.die=self.no_roll
         later=deepcopy(choices);later['modern']+=['shotgun','submachine-gun','heavy-military']
         hero=app.select_combat(hero['id'],revision=hero['revision'],choices=later)
         view=app.combat_view(hero['id'])
         assert view['related_cost']==3 and view['remaining']['weapon_awards']==0,view['weapon_entitlements']
         bundle=app.export_character(hero['id'])
         other=CharacterApplication(copied,die=self.no_roll,rule_archive=self.fixture())
         restored=other.import_character(bundle)
         assert restored['learning_levels']==hero['learning_levels']
         forged=deepcopy(bundle)
         forged['character']['learning_levels'][learning_key('weapon','energy-rifle')]=5
         try:
          other.import_character(forged)
         except ValueError:
          pass
         else:
          raise AssertionError('Forged earlier learning age accepted')
         hero=app.undo_advancement(hero['id'],revision=hero['revision'])['character']
         assert hero['level']==4
         other.import_character(app.export_character(hero['id']))


    def test_backdated_new_training_costs_related_and_later_history_rejects_age_forgery(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory,die=lambda sides:3,rule_archive=self.fixture())
            hero = app.create()
            hero = app.select_combat(hero['id'],revision=hero['revision'],choices=self.choices)
            hero = app.generate_resources(hero['id'],revision=hero['revision'])
            hero = app.advance(hero['id'],revision=hero['revision'],method='level',value=5)
            later = deepcopy(self.choices)
            later['modern'].append('shotgun')
            app.die = self.no_roll
            hero = app.select_combat(hero['id'],revision=hero['revision'],choices=later,learned_level=3)
            self.assertEqual(app.combat_view(hero['id'])['related_cost'],4)
            self.assertEqual(app.combat_view(hero['id'])['remaining']['weapon_awards'],3)
            app.import_character(app.export_character(hero['id']))
            app.die = lambda sides:3
            hero = app.advance(hero['id'],revision=hero['revision'],method='level',value=6)
            app.die = self.no_roll
            forged = app.export_character(hero['id'])
            forged['character']['learning_levels'][learning_key('weapon','shotgun')] = 5
            with self.assertRaises(ValueError):
                app.import_character(forged)
            self.assertEqual(app.get(hero['id']),hero)

    def test_scheduled_shield_preserves_earlier_manual_training(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory,die=lambda sides:3,rule_archive=self.fixture())
            hero = app.create()
            choices = deepcopy(self.choices)
            choices['ancient'] = ['knife','shield']
            hero = app.select_combat(hero['id'],revision=hero['revision'],choices=choices)
            hero = app.generate_resources(hero['id'],revision=hero['revision'])
            hero = app.advance(hero['id'],revision=hero['revision'],method='level',value=3)
            view = app.combat_view(hero['id'])
            self.assertEqual(view['weapon_entitlements']['grant_levels']['shield'],1)
            self.assertEqual(len([row for row in view['melee'] if row['id']=='shield']),1)
            app.die = self.no_roll
            restored = app.import_character(app.export_character(hero['id']))
            self.assertEqual(restored['learning_levels'],hero['learning_levels'])

    def test_partial_stored_combat_choices_keep_prerequisite_guidance(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory,die=lambda sides:3,rule_archive=self.fixture())
            hero = app.create()
            hero = app.select_skills(hero['id'],revision=hero['revision'],selections=[
                {'skill_id':'fencing','pool':'related','specialty':''}])
            bundle = app.export_character(hero['id'])
            bundle['character']['combat_choices'] = {'ancient':[]}
            app.die = self.no_roll
            restored = app.import_character(bundle)
            view = app.skill_view(restored['id'])
            self.assertTrue(any('missing prerequisite' in warning for warning in view['warnings']))
            self.assertEqual(app.get(restored['id'])['combat_choices'],{'hand_to_hand':'basic','ancient':[],'modern':[]})

    def test_invalid_inactive_schedule_rejects_before_dice_and_save(self):
        for field,value in [('level',True),('level',1),('family',[]),('id','unknown'),('source',None)]:
            def mutate(skills):
                inactive = next(row for key,row in skills['class_profiles'].items() if key!='vagabond')
                inactive['combat'] = deepcopy(skills['class_profiles']['vagabond']['combat'])
                inactive['combat']['proficiency_schedule']['fixed'][0][field] = value
            with self.subTest(field=field,value=value),tempfile.TemporaryDirectory() as directory:
                app = CharacterApplication(directory,die=self.no_roll,rule_archive=self.fixture(mutate))
                with self.assertRaises(ValueError):
                    app.create()
                self.assertEqual(app.list(),[])

    def test_invalid_inactive_paid_minimum_rejects_before_dice_and_save(self):
        for fault in ('zero-cost','absent-cost','impossible-count'):
            def mutate(skills):
                inactive = next(row for key,row in skills['class_profiles'].items() if key!='vagabond')
                inactive['combat'] = deepcopy(skills['class_profiles']['vagabond']['combat'])
                rules = inactive['combat']
                if fault == 'zero-cost':
                    rules['additional_proficiency_cost'] = 0
                elif fault == 'absent-cost':
                    rules.pop('additional_proficiency_cost')
                else:
                    rules['proficiency_schedule']['initial_paid_minimum']['count'] = 1000
            with self.subTest(fault=fault),tempfile.TemporaryDirectory() as directory:
                app = CharacterApplication(directory,die=self.no_roll,rule_archive=self.fixture(mutate))
                with self.assertRaises(ValueError):
                    app.create()
                self.assertEqual(app.list(),[])
