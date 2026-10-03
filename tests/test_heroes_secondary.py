import tempfile
import unittest

from characters_unlimited.application import CharacterApplication, SaveConflict
from characters_unlimited.rules import RuleArchive
from copy import deepcopy


class HeroesSecondaryWorkflowTests(unittest.TestCase):
    def test_secondary_uses_iq_without_education_and_reopens_portably(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory,die=lambda sides:4)
            hero = app.create(game='heroes-unlimited')
            hero = app.select_education(hero['id'],revision=0,method='choose',education_id='doctorate')
            hero = app.set_attribute(hero['id'],revision=hero['revision'],attribute='IQ',mode='fixed',value=16)
            choices = ['research','computer-operation','mathematics-basic']
            hero = app.select_hero_secondary(hero['id'],revision=hero['revision'],selections=choices)
            view = app.hero_program_view(hero['id'])
            skills = {skill['id']:skill for skill in view['skills']}
            self.assertEqual(skills['research']['percentage'],52)
            self.assertEqual(skills['computer-operation']['percentage'],42)
            self.assertEqual(skills['mathematics-basic']['percentage'],47)
            self.assertTrue(all(skill['contributions']['education']==0 for skill in skills.values()))
            self.assertEqual(view['secondary']['remaining'],7)
            self.assertEqual(view['secondary']['allowance'],10)
            self.assertEqual(view['secondary']['selections'],choices)
            imported = app.import_character(app.export_character(hero['id']))
            self.assertEqual(imported['hero_secondary_selections'],choices)
            self.assertEqual(CharacterApplication(directory).hero_program_view(hero['id'])['skills'],view['skills'])
            self.assertEqual(app.hero_program_view(imported['id'])['secondary'],view['secondary'])

    def test_shared_program_skill_occurs_once_and_ineligible_excess_choices_stay_saved(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory,die=lambda sides:4)
            hero = app.create(game='heroes-unlimited')
            hero = app.select_education(hero['id'],revision=0,method='choose',education_id='college-one')
            hero = app.set_attribute(hero['id'],revision=hero['revision'],attribute='IQ',mode='fixed',value=16)
            hero = app.select_hero_programs(hero['id'],revision=hero['revision'],selections=[{'slot':0,'program':'business'}])
            choices = ['research','biology','paramedic']+['law-general']*6
            hero = app.select_hero_secondary(hero['id'],revision=hero['revision'],selections=choices)
            view = app.hero_program_view(hero['id'])
            skills = {skill['id']:skill for skill in view['skills']}
            self.assertEqual(skills['research']['percentage'],62)
            self.assertEqual(skills['law-general']['percentage'],37)
            self.assertEqual(skills['biology']['percentage'],32)
            self.assertEqual(skills['paramedic']['percentage'],42)
            self.assertEqual(len(skills),8)
            self.assertEqual(view['secondary']['remaining'],-1)
            self.assertEqual(view['secondary']['selections'],choices)
            for fragment in ('Repeated Secondary Law','Biology is outside','Paramedic is outside','exceed'):
                self.assertTrue(any(fragment in warning for warning in view['warnings']))
            hero = app.select_hero_programs(hero['id'],revision=hero['revision'],selections=[])
            research = next(skill for skill in app.hero_program_view(hero['id'])['skills'] if skill['id']=='research')
            self.assertEqual(research['percentage'],52)
            self.assertEqual(hero['hero_secondary_selections'],choices)

    def test_invalid_stale_wrong_game_and_tampered_choices_preserve_saved_work(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory,die=lambda sides:4)
            hero = app.create(game='heroes-unlimited')
            with self.assertRaises(ValueError):
                app.select_hero_secondary(hero['id'],revision=0,selections=['research'])
            hero = app.select_education(hero['id'],revision=0,method='choose',education_id='high-school')
            hero = app.select_hero_secondary(hero['id'],revision=hero['revision'],selections=['research'])
            for choices in ('research',['unknown'],[True],['research']*101):
                with self.assertRaises(ValueError):
                    app.select_hero_secondary(hero['id'],revision=hero['revision'],selections=choices)
            with self.assertRaises(SaveConflict):
                app.select_hero_secondary(hero['id'],revision=1,selections=[])
            self.assertEqual(app.get(hero['id']),hero)
            rifts = app.create()
            with self.assertRaises(ValueError):
                app.select_hero_secondary(rifts['id'],revision=0,selections=[])
            bundle = app.export_character(hero['id'])
            for mutation in ('pin','education','unknown'):
                bad = deepcopy(bundle)
                if mutation=='pin':
                    bad['character']['additional_rule_packs'].pop('heroes-program-skills')
                elif mutation=='education':
                    bad['character'].pop('education')
                else:
                    bad['character']['hero_secondary_selections']=['unknown']
                with self.assertRaises(ValueError):
                    app.import_character(bad)
            self.assertEqual(len(app.list()),2)

    def test_older_program_pin_needs_update_before_secondary_and_preview_preserves_choices(self):
        with tempfile.TemporaryDirectory() as directory:
            archive = RuleArchive.load()
            old_archive = RuleArchive(archive.definitions(),{**archive.active_versions(),'heroes-program-skills':'1.2.0'})
            earlier = CharacterApplication(directory,die=lambda sides:4,rule_archive=old_archive)
            hero = earlier.create(game='heroes-unlimited')
            hero = earlier.select_education(hero['id'],revision=0,method='choose',education_id='high-school')
            hero = earlier.select_hero_programs(hero['id'],revision=hero['revision'],selections=[])
            current = CharacterApplication(directory)
            self.assertFalse(current.hero_program_view(hero['id'])['secondary']['supported'])
            with self.assertRaises(ValueError):
                current.select_hero_secondary(hero['id'],revision=hero['revision'],selections=['research'])
            preview = current.preview_rule_upgrade(hero['id'])
            self.assertEqual(current.get(hero['id']),hero)
            hero = current.apply_rule_upgrade(hero['id'],revision=hero['revision'],token=preview['token'])['character']
            hero = current.select_hero_secondary(hero['id'],revision=hero['revision'],selections=['research'])
            correction = archive.active('heroes-program-skills')
            correction['version']='1.5.0'
            next(skill for skill in correction['skills'] if skill['id']=='research')['base']=55
            next_app = CharacterApplication(directory,rule_archive=RuleArchive([*archive.definitions(),correction],
                {**archive.active_versions(),'heroes-program-skills':'1.5.0'}))
            preview = next_app.preview_rule_upgrade(hero['id'])
            research = next(skill for skill in preview['skills'] if skill['name']=='Research')
            self.assertEqual((research['before'],research['after']),(50,55))
            updated = next_app.apply_rule_upgrade(hero['id'],revision=hero['revision'],token=preview['token'])['character']
            self.assertEqual(updated['hero_secondary_selections'],['research'])


if __name__ == '__main__':
    unittest.main()
