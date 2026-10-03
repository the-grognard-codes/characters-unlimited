import tempfile
import unittest

from characters_unlimited.application import CharacterApplication
from characters_unlimited.rules import RuleArchive


class HeroesCommunicationsWorkflowTests(unittest.TestCase):
    def test_communications_grants_and_optic_bonus_reopen_with_exact_choices(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides: 4)
            hero = app.create(game='heroes-unlimited')
            hero = app.select_education(hero['id'], revision=0, method='choose', education_id='college-one')
            hero = app.set_attribute(hero['id'], revision=hero['revision'], attribute='IQ', mode='fixed', value=16)
            choices = [{'slot':0, 'program':'communications', 'choices':{'communications':['optic-systems']}}]
            hero = app.select_hero_programs(hero['id'], revision=hero['revision'], selections=choices)
            view = app.hero_program_view(hero['id'])
            skills = {skill['id']:skill for skill in view['skills']}
            self.assertEqual(skills['tv-video']['percentage'],42)
            self.assertEqual(skills['tv-video']['per_level'],4)
            self.assertEqual(skills['tv-video']['contributions']['Optic Systems'],5)
            self.assertEqual(skills['optic-systems']['percentage'],42)
            self.assertEqual(skills['radio-basic']['percentage'],57)
            self.assertEqual(skills['radio-scramblers']['percentage'],47)
            self.assertEqual(skills['electronics-basic']['percentage'],42)
            self.assertEqual(view['program_choices'][0]['groups'][0]['remaining'],0)
            imported = app.import_character(app.export_character(hero['id']))
            self.assertEqual(imported['hero_program_selections'],choices)
            self.assertEqual(CharacterApplication(directory).hero_program_view(hero['id'])['skills'],view['skills'])

    def test_all_alternatives_and_short_study_context_use_original_values(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides:4)
            hero = app.create(game='heroes-unlimited')
            hero = app.select_education(hero['id'],revision=0,method='choose',education_id='college-one')
            for identifier,expected in [('cryptography',35),('laser',40),('optic-systems',40),
                                         ('surveillance-systems',40),('read-sensory-equipment',40),('radio-satellite',35)]:
                hero = app.select_hero_programs(hero['id'],revision=hero['revision'],selections=[
                    {'slot':0,'program':'communications','choices':{'communications':[identifier]}}])
                view = app.hero_program_view(hero['id'])
                skill = next(item for item in view['skills'] if item['id']==identifier)
                self.assertEqual(skill['percentage'],expected)
                self.assertEqual(view['program_choices'][0]['groups'][0]['remaining'],0)
                if identifier=='cryptography':
                    self.assertEqual(skill['additional_checks'][0]['percentage'],5)
                    self.assertEqual(skill['prerequisites'],['Literacy'])
                if identifier=='surveillance-systems':
                    self.assertTrue(any('complex, high-tech' in note for note in skill['notes']))

    def test_synergy_is_once_only_and_removed_with_its_source(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory,die=lambda sides:4)
            hero = app.create(game='heroes-unlimited')
            hero = app.select_education(hero['id'],revision=0,method='choose',education_id='doctorate')
            hero = app.set_attribute(hero['id'],revision=hero['revision'],attribute='IQ',mode='fixed',value=30)
            choices = [{'slot':0,'program':'communications','choices':{'communications':['optic-systems','optic-systems']}}]
            hero = app.select_hero_programs(hero['id'],revision=hero['revision'],selections=choices)
            view = app.hero_program_view(hero['id'])
            video = next(item for item in view['skills'] if item['id']=='tv-video')
            self.assertEqual(video['percentage'],76)
            self.assertEqual(video['contributions']['Optic Systems'],5)
            hero = app.select_hero_programs(hero['id'],revision=hero['revision'],selections=[{'slot':0,'program':'communications'}])
            video = next(item for item in app.hero_program_view(hero['id'])['skills'] if item['id']=='tv-video')
            self.assertEqual(video['percentage'],71)
            self.assertNotIn('Optic Systems',video['contributions'])

    def test_fixed_duplicate_credit_pending_and_ineligible_high_school_keep_work(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory,die=lambda sides:4)
            hero = app.create(game='heroes-unlimited')
            hero = app.select_education(hero['id'],revision=0,method='choose',education_id='high-school')
            for identifier,expected in [('radio-basic',45),('radio-scramblers',35),('tv-video',25)]:
                choices = [{'slot':0,'program':'communications','choices':{'communications':[identifier]}}]
                hero = app.select_hero_programs(hero['id'],revision=hero['revision'],selections=choices)
                view = app.hero_program_view(hero['id'])
                self.assertEqual(view['selections'],choices)
                self.assertEqual(next(skill for skill in view['skills'] if skill['id']==identifier)['percentage'],expected)
                self.assertEqual(view['program_choices'][0]['groups'][0]['remaining'],1)
                self.assertTrue(any('pending interpretation' in warning for warning in view['warnings']))
                self.assertTrue(any('eligible education slot' in warning for warning in view['warnings']))

    def test_video_secondary_and_explicit_upgrade_preserve_computer_choices(self):
        with tempfile.TemporaryDirectory() as directory:
            archive = RuleArchive.load()
            earlier = CharacterApplication(directory,die=lambda sides:4,rule_archive=RuleArchive(
                archive.definitions(),{**archive.active_versions(),'heroes-program-skills':'1.4.0'}))
            hero = earlier.create(game='heroes-unlimited')
            hero = earlier.select_education(hero['id'],revision=0,method='choose',education_id='college-one')
            choices = [{'slot':0,'program':'computer','choices':{'repair-radio':['radio-basic']}}]
            hero = earlier.select_hero_programs(hero['id'],revision=hero['revision'],selections=choices)
            hero = earlier.select_hero_secondary(hero['id'],revision=hero['revision'],selections=['research'])
            current = CharacterApplication(directory)
            with self.assertRaises(ValueError):
                current.select_hero_secondary(hero['id'],revision=hero['revision'],selections=['tv-video'])
            preview = current.preview_rule_upgrade(hero['id'])
            self.assertEqual(current.get(hero['id']),hero)
            hero = current.apply_rule_upgrade(hero['id'],revision=hero['revision'],token=preview['token'])['character']
            self.assertEqual(hero['hero_program_selections'],choices)
            hero = current.select_hero_secondary(hero['id'],revision=hero['revision'],selections=['research','tv-video','optic-systems'])
            view = current.hero_program_view(hero['id'])
            video = next(skill for skill in view['skills'] if skill['id']=='tv-video')
            self.assertEqual(video['percentage'],30)
            self.assertEqual(video['contributions']['education'],0)
            self.assertEqual(view['secondary']['remaining'],5)
            self.assertIn('tv-video',view['secondary']['eligible_skill_ids'])
            self.assertNotIn('optic-systems',view['secondary']['eligible_skill_ids'])
            imported = current.import_character(current.export_character(hero['id']))
            self.assertEqual(current.hero_program_view(imported['id'])['skills'],view['skills'])


if __name__ == '__main__':
    unittest.main()
