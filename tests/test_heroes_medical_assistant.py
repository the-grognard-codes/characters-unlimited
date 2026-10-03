import tempfile
import unittest

from characters_unlimited.application import CharacterApplication
from characters_unlimited.rules import RuleArchive


class HeroesMedicalAssistantWorkflowTests(unittest.TestCase):
    def test_medical_assistant_grants_source_percentages_and_reopens_portably(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides:4)
            hero = app.create(game='heroes-unlimited')
            hero = app.select_education(hero['id'], revision=0, method='choose', education_id='college-one')
            hero = app.set_attribute(hero['id'], revision=hero['revision'], attribute='IQ', mode='fixed', value=16)
            choices = [{'slot':0,'program':'medical-assistant'}]
            hero = app.select_hero_programs(hero['id'], revision=hero['revision'], selections=choices)
            view = app.hero_program_view(hero['id'])
            skills = {skill['id']:skill for skill in view['skills']}
            self.assertEqual({key:skill['percentage'] for key,skill in skills.items()}, {
                'pilot-automobile':62, 'mathematics-basic':57, 'business-finance':47,
                'computer-operation':52, 'biology':42, 'paramedic':52})
            self.assertEqual(skills['biology']['per_level'],5)
            self.assertEqual(skills['paramedic']['per_level'],5)
            self.assertEqual(skills['paramedic']['source']['pages'],[53])
            imported = app.import_character(app.export_character(hero['id']))
            self.assertEqual(imported['hero_program_selections'],choices)
            self.assertEqual(CharacterApplication(directory).hero_program_view(hero['id'])['skills'],view['skills'])
            self.assertEqual(app.hero_program_view(imported['id'])['skills'],view['skills'])

    def test_shared_grants_take_highest_bonus_once_and_warnings_name_the_program(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides:4)
            hero = app.create(game='heroes-unlimited')
            hero = app.select_education(hero['id'],revision=0,method='choose',education_id='military')
            choices = [{'slot':2,'program':'business'},{'slot':0,'program':'medical-assistant'}]
            for order in (choices,list(reversed(choices))):
                hero = app.select_hero_programs(hero['id'],revision=hero['revision'],selections=order)
                view = app.hero_program_view(hero['id'])
                skills = {skill['id']:skill for skill in view['skills']}
                self.assertEqual(skills['mathematics-basic']['percentage'],50)
                self.assertEqual(skills['computer-operation']['percentage'],45)
                self.assertEqual(skills['biology']['percentage'],30)
                self.assertEqual(skills['paramedic']['percentage'],40)
                self.assertEqual(len(skills),8)
                self.assertTrue(any('Medical Assistant is outside' in warning for warning in view['warnings']))
            hero = app.select_education(hero['id'],revision=hero['revision'],method='choose',education_id='doctorate')
            hero = app.set_attribute(hero['id'],revision=hero['revision'],attribute='IQ',mode='fixed',value=30)
            hero = app.select_hero_programs(hero['id'],revision=hero['revision'],selections=[
                {'slot':0,'program':'medical-assistant'},{'slot':1,'program':'medical-assistant'}])
            view = app.hero_program_view(hero['id'])
            self.assertTrue(any('Repeated Medical Assistant' in warning for warning in view['warnings']))
            skills = {skill['id']:skill for skill in view['skills']}
            self.assertEqual(skills['paramedic']['percentage'],86)
            self.assertEqual(skills['biology']['percentage'],76)
            self.assertEqual(len(skills),6)

    def test_existing_pin_requires_explicit_update_to_gain_medical_assistant(self):
        with tempfile.TemporaryDirectory() as directory:
            archive = RuleArchive.load()
            earlier = CharacterApplication(directory,die=lambda sides:4,rule_archive=RuleArchive(
                archive.definitions(),{**archive.active_versions(),'heroes-program-skills':'1.1.0'}))
            hero = earlier.create(game='heroes-unlimited')
            hero = earlier.select_education(hero['id'],revision=0,method='choose',education_id='college-one')
            hero = earlier.select_hero_programs(hero['id'],revision=hero['revision'],selections=[{'slot':0,'program':'business'}])
            current = CharacterApplication(directory)
            self.assertEqual([program['id'] for program in current.hero_program_view(hero['id'])['catalog']],['business'])
            with self.assertRaises(ValueError):
                current.select_hero_programs(hero['id'],revision=hero['revision'],selections=[{'slot':1,'program':'medical-assistant'}])
            self.assertEqual(current.get(hero['id']),hero)
            preview = current.preview_rule_upgrade(hero['id'])
            self.assertEqual(preview['changes'],[{'pack_id':'heroes-program-skills','from':'1.1.0','to':'1.5.0'}])
            updated = current.apply_rule_upgrade(hero['id'],revision=hero['revision'],token=preview['token'])['character']
            self.assertEqual(updated['hero_program_selections'],hero['hero_program_selections'])
            self.assertEqual(current.hero_program_view(hero['id'])['skills'],earlier.hero_program_view(hero['id'])['skills'])
            current.select_hero_programs(hero['id'],revision=updated['revision'],selections=[{'slot':1,'program':'medical-assistant'}])
            self.assertIn('medical-assistant',[program['id'] for program in current.hero_program_view(hero['id'])['catalog']])


if __name__ == '__main__':
    unittest.main()
