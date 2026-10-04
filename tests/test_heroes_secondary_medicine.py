import tempfile
import unittest

from characters_unlimited.application import CharacterApplication, SaveConflict
from characters_unlimited.rules import RuleArchive


class HeroesSecondaryMedicineWorkflowTests(unittest.TestCase):
    def test_medical_secondary_costs_percentages_and_removal_reopen(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory,die=lambda sides:4)
            hero = app.create(game='heroes-unlimited')
            hero = app.select_education(hero['id'],revision=0,method='choose',education_id='doctorate')
            hero = app.set_attribute(hero['id'],revision=hero['revision'],attribute='IQ',mode='fixed',value=16)
            hero = app.select_hero_secondary(hero['id'],revision=hero['revision'],selections=['first-aid','holistic-medicine'])
            view = app.hero_program_view(hero['id'])
            self.assertEqual((view['secondary']['used'],view['secondary']['remaining']),(3,7))
            self.assertEqual(view['secondary']['selection_costs']['holistic-medicine'],2)
            self.assertEqual(view['secondary']['selection_costs']['first-aid'],1)
            skills = {skill['id']:skill for skill in view['skills']}
            self.assertEqual(skills['first-aid']['percentage'],47)
            self.assertEqual(skills['holistic-medicine']['percentage'],22)
            self.assertEqual(skills['holistic-medicine']['contributions']['education'],0)
            imported = app.import_character(app.export_character(hero['id']))
            self.assertEqual(imported['hero_secondary_selections'],hero['hero_secondary_selections'])
            self.assertEqual(CharacterApplication(directory).hero_program_view(hero['id']),view)
            hero = app.select_hero_secondary(hero['id'],revision=hero['revision'],selections=['first-aid'])
            self.assertEqual(app.hero_program_view(hero['id'])['secondary']['remaining'],9)

    def test_duplicate_two_cost_choices_are_retained_counted_and_do_not_stack(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory,die=lambda sides:4)
            hero = app.create(game='heroes-unlimited')
            hero = app.select_education(hero['id'],revision=0,method='choose',education_id='street-schooled')
            choices = ['holistic-medicine']*5
            hero = app.select_hero_secondary(hero['id'],revision=hero['revision'],selections=choices)
            view = app.hero_program_view(hero['id'])
            self.assertEqual((view['secondary']['used'],view['secondary']['remaining']),(10,-2))
            self.assertEqual(hero['hero_secondary_selections'],choices)
            holistic = [skill for skill in view['skills'] if skill['id']=='holistic-medicine']
            self.assertEqual(len(holistic),1)
            self.assertEqual(holistic[0]['percentage'],20)
            self.assertTrue(any('Repeated Secondary Holistic' in warning for warning in view['warnings']))
            self.assertTrue(any('allowance by 2' in warning for warning in view['warnings']))
            with self.assertRaises(SaveConflict):
                app.select_hero_secondary(hero['id'],revision=0,selections=[])
            self.assertEqual(app.get(hero['id']),hero)

    def test_prior_choices_gain_medicine_only_after_explicit_rule_update(self):
        with tempfile.TemporaryDirectory() as directory:
            archive = RuleArchive.load()
            earlier = CharacterApplication(directory,die=lambda sides:4,rule_archive=RuleArchive(
                archive.definitions(),{**archive.active_versions(),'heroes-program-skills':'1.5.0'}))
            hero = earlier.create(game='heroes-unlimited')
            hero = earlier.select_education(hero['id'],revision=0,method='choose',education_id='college-one')
            choices = [{'slot':0,'program':'communications','choices':{'communications':['cryptography']}}]
            hero = earlier.select_hero_programs(hero['id'],revision=hero['revision'],selections=choices)
            hero = earlier.select_hero_secondary(hero['id'],revision=hero['revision'],selections=['research','tv-video'])
            current = CharacterApplication(directory)
            old = current.import_character(current.export_character(hero['id']))
            self.assertEqual(old['additional_rule_packs']['heroes-program-skills'],'1.5.0')
            with self.assertRaises(ValueError):
                current.select_hero_secondary(hero['id'],revision=hero['revision'],selections=['first-aid'])
            self.assertEqual(current.get(hero['id']),hero)
            preview = current.preview_rule_upgrade(hero['id'])
            self.assertEqual(preview['changes'],[{'pack_id':'heroes-program-skills','from':'1.5.0','to':'1.17.0'}])
            hero = current.apply_rule_upgrade(hero['id'],revision=hero['revision'],token=preview['token'])['character']
            self.assertEqual(hero['hero_program_selections'],choices)
            self.assertEqual(hero['hero_secondary_selections'],['research','tv-video'])
            hero = current.select_hero_secondary(hero['id'],revision=hero['revision'],selections=[*hero['hero_secondary_selections'],'holistic-medicine'])
            view = current.hero_program_view(hero['id'])
            self.assertEqual((view['secondary']['used'],view['secondary']['remaining']),(4,4))
            self.assertEqual(hero['hero_program_selections'],choices)


if __name__ == '__main__':
    unittest.main()
