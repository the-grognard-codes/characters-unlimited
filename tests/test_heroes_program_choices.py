import tempfile
import unittest

from characters_unlimited.application import CharacterApplication, SaveConflict
from copy import deepcopy
from characters_unlimited.rules import RuleArchive


class HeroesProgramChoiceWorkflowTests(unittest.TestCase):
    def test_high_school_computer_program_grants_source_skills_and_choice_and_reopens(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory,die=lambda sides:4)
            hero = app.create(game='heroes-unlimited')
            hero = app.select_education(hero['id'],revision=0,method='choose',education_id='high-school')
            hero = app.set_attribute(hero['id'],revision=hero['revision'],attribute='IQ',mode='fixed',value=16)
            selections = [{'slot':0,'program':'computer','choices':{'repair-radio':['computer-repair']}}]
            hero = app.select_hero_programs(hero['id'],revision=hero['revision'],selections=selections)
            view = app.hero_program_view(hero['id'])
            skills = {skill['id']:skill for skill in view['skills']}
            self.assertEqual(skills['computer-programming']['percentage'],37)
            self.assertEqual(skills['computer-operation']['percentage'],47)
            self.assertEqual(skills['electronics-basic']['percentage'],37)
            self.assertEqual(skills['computer-repair']['percentage'],32)
            self.assertEqual(skills['mathematics-basic']['percentage'],47)
            self.assertEqual(skills['pilot-automobile']['percentage'],62)
            group = view['program_choices'][0]['groups'][0]
            self.assertEqual((group['entered'],group['credited'],group['remaining']),(1,1,0))
            self.assertEqual(hero['hero_program_selections'],selections)
            imported = app.import_character(app.export_character(hero['id']))
            self.assertEqual(imported['hero_program_selections'],selections)
            self.assertEqual(CharacterApplication(directory).hero_program_view(hero['id'])['skills'],view['skills'])

    def test_all_explicit_alternatives_and_context_checks_use_their_source_values(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory,die=lambda sides:4)
            hero = app.create(game='heroes-unlimited')
            hero = app.select_education(hero['id'],revision=0,method='choose',education_id='high-school')
            hero = app.set_attribute(hero['id'],revision=hero['revision'],attribute='IQ',mode='fixed',value=16)
            for alternative,expected in [('computer-repair',32),('radio-basic',52),('radio-scramblers',42),('radio-satellite',32)]:
                hero = app.select_hero_programs(hero['id'],revision=hero['revision'],selections=[
                    {'slot':0,'program':'computer','choices':{'repair-radio':[alternative]}}])
                skills = {skill['id']:skill for skill in app.hero_program_view(hero['id'])['skills']}
                self.assertEqual(skills[alternative]['percentage'],expected)
                hacking = skills['computer-programming']['additional_checks'][0]
                self.assertEqual(hacking['percentage'],-3)
                if alternative=='computer-repair':
                    self.assertEqual(skills[alternative]['additional_checks'][0]['percentage'],32)

    def test_missing_duplicate_outside_and_excess_choices_are_retained_with_distinct_counts(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory,die=lambda sides:4)
            hero = app.create(game='heroes-unlimited')
            hero = app.select_education(hero['id'],revision=0,method='choose',education_id='high-school')
            hero = app.select_hero_programs(hero['id'],revision=hero['revision'],selections=[{'slot':0,'program':'computer'}])
            view = app.hero_program_view(hero['id'])
            self.assertEqual(view['program_choices'][0]['groups'][0]['remaining'],1)
            choices = ['radio-basic','radio-basic','radio-satellite','biology']
            selections = [{'slot':0,'program':'computer','choices':{'repair-radio':choices}}]
            hero = app.select_hero_programs(hero['id'],revision=hero['revision'],selections=selections)
            view = app.hero_program_view(hero['id'])
            group = view['program_choices'][0]['groups'][0]
            self.assertEqual((group['entered'],group['credited'],group['remaining']),(4,2,-1))
            for fragment in ('-1 distinct','repeated choices','outside-group'):
                self.assertTrue(any(fragment in warning for warning in view['warnings']))
            biology = next(skill for skill in view['skills'] if skill['id']=='biology')
            self.assertEqual(biology['percentage'],30)
            self.assertEqual(biology['contributions']['education'],0)
            self.assertEqual(hero['hero_program_selections'],selections)

    def test_repeated_program_does_not_automate_its_unimplemented_repeat_choice_entitlement(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory,die=lambda sides:4)
            hero = app.create(game='heroes-unlimited')
            hero = app.select_education(hero['id'],revision=0,method='choose',education_id='high-school')
            choices = [{'slot':0,'program':'computer','choices':{'repair-radio':['computer-repair']}},
                       {'slot':1,'program':'computer','choices':{'repair-radio':['radio-basic']}}]
            hero = app.select_hero_programs(hero['id'],revision=hero['revision'],selections=choices)
            view = app.hero_program_view(hero['id'])
            radio = next(skill for skill in view['skills'] if skill['id']=='radio-basic')
            self.assertEqual(radio['percentage'],45)
            self.assertTrue(view['program_choices'][1]['repeat'])
            self.assertTrue(any('repeat entitlement' in warning for warning in view['warnings']))

    def test_invalid_group_data_and_portable_tampering_cannot_replace_saved_choices(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory,die=lambda sides:4)
            hero = app.create(game='heroes-unlimited')
            hero = app.select_education(hero['id'],revision=0,method='choose',education_id='high-school')
            selection = {'slot':0,'program':'computer','choices':{'repair-radio':['radio-basic']}}
            hero = app.select_hero_programs(hero['id'],revision=hero['revision'],selections=[selection])
            choices: object
            for choices in (None,[],{'unknown':['radio-basic']},{'repair-radio':[True]},
                            {'repair-radio':['unknown']},{'repair-radio':['radio-basic']*101}):
                with self.assertRaises(ValueError):
                    app.select_hero_programs(hero['id'],revision=hero['revision'],selections=[{**selection,'choices':choices}])
            with self.assertRaises(ValueError):
                app.select_hero_programs(hero['id'],revision=hero['revision'],selections=[{'slot':1,'program':'business','choices':{}}])
            with self.assertRaises(SaveConflict):
                app.select_hero_programs(hero['id'],revision=1,selections=[])
            self.assertEqual(app.get(hero['id']),hero)
            bundle = app.export_character(hero['id'])
            bad = deepcopy(bundle)
            bad['character']['hero_program_selections'][0]['choices']={'unknown':['radio-basic']}
            with self.assertRaises(ValueError):
                app.import_character(bad)
            self.assertEqual(len(app.list()),1)

    def test_older_two_field_selections_and_secondary_work_survive_explicit_catalog_update(self):
        with tempfile.TemporaryDirectory() as directory:
            archive = RuleArchive.load()
            earlier = CharacterApplication(directory,die=lambda sides:4,rule_archive=RuleArchive(
                archive.definitions(),{**archive.active_versions(),'heroes-program-skills':'1.3.0'}))
            hero = earlier.create(game='heroes-unlimited')
            hero = earlier.select_education(hero['id'],revision=0,method='choose',education_id='high-school')
            old_selection = [{'slot':0,'program':'business'}]
            hero = earlier.select_hero_programs(hero['id'],revision=hero['revision'],selections=old_selection)
            hero = earlier.select_hero_secondary(hero['id'],revision=hero['revision'],selections=['research'])
            current = CharacterApplication(directory)
            imported = current.import_character(current.export_character(hero['id']))
            self.assertEqual(imported['hero_program_selections'],old_selection)
            self.assertEqual(imported['additional_rule_packs']['heroes-program-skills'],'1.3.0')
            with self.assertRaises(ValueError):
                current.select_hero_programs(hero['id'],revision=hero['revision'],selections=[{'slot':0,'program':'computer'}])
            preview = current.preview_rule_upgrade(hero['id'])
            hero = current.apply_rule_upgrade(hero['id'],revision=hero['revision'],token=preview['token'])['character']
            self.assertEqual(hero['hero_program_selections'],old_selection)
            self.assertEqual(hero['hero_secondary_selections'],['research'])
            hero = current.select_hero_programs(hero['id'],revision=hero['revision'],selections=[
                {'slot':0,'program':'computer','choices':{'repair-radio':['radio-basic']}}])
            self.assertEqual(hero['hero_secondary_selections'],['research'])


if __name__ == '__main__':
    unittest.main()
