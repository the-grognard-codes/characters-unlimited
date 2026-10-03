import copy
import tempfile
import unittest

from characters_unlimited.application import CharacterApplication
from characters_unlimited.rules import RuleArchive
from characters_unlimited.storage import SaveConflict


class HeroesProgramWorkflowTests(unittest.TestCase):
    def test_business_program_uses_education_and_iq_once_and_reopens(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides: 4)
            hero = app.create(game='heroes-unlimited')
            hero = app.select_education(hero['id'], revision=0, method='choose', education_id='college-one')
            hero = app.set_attribute(hero['id'], attribute='IQ', revision=hero['revision'], mode='fixed', value=16)
            hero = app.select_hero_programs(hero['id'], revision=hero['revision'], selections=[{'slot':0, 'program':'business'}])
            skills = {item['id']:item for item in app.hero_program_view(hero['id'])['skills']}
            self.assertEqual(skills['research']['percentage'], 62)
            self.assertEqual(skills['mathematics-basic']['percentage'], 57)
            self.assertEqual(skills['pilot-automobile']['percentage'], 62)
            self.assertEqual(skills['law-general']['percentage'], 37)
            self.assertEqual(skills['computer-operation']['percentage'], 52)
            self.assertEqual(skills['business-finance']['percentage'], 47)
            self.assertEqual(skills['research']['per_level'], 5)
            imported = app.import_character(app.export_character(hero['id']))
            self.assertEqual(imported['hero_program_selections'], hero['hero_program_selections'])
            self.assertEqual(CharacterApplication(directory).hero_program_view(hero['id'])['skills'], app.hero_program_view(hero['id'])['skills'])

    def test_repeated_and_ineligible_programs_are_retained_without_extra_bonuses(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides: 4)
            hero = app.create(game='heroes-unlimited')
            hero = app.select_education(hero['id'], revision=0, method='choose', education_id='military-specialist')
            choices = [{'slot':4,'program':'business'}, {'slot':0,'program':'business'}]
            hero = app.select_hero_programs(hero['id'], revision=hero['revision'], selections=choices)
            view = app.hero_program_view(hero['id'])
            self.assertEqual(next(item for item in view['skills'] if item['id'] == 'research')['percentage'], 60)
            self.assertTrue(any('Repeated' in message for message in view['warnings']))
            self.assertEqual(view['selections'], choices)
            hero = app.select_hero_programs(hero['id'], revision=hero['revision'], selections=[{'slot':0,'program':'business'}])
            view = app.hero_program_view(hero['id'])
            self.assertEqual(next(item for item in view['skills'] if item['id'] == 'research')['percentage'], 50)
            self.assertTrue(any('outside' in message for message in view['warnings']))
            hero = app.select_education(hero['id'], revision=hero['revision'], method='choose', education_id='street-schooled')
            self.assertTrue(any('literacy' in message for message in app.hero_program_view(hero['id'])['warnings']))

    def test_invalid_stale_and_tampered_programs_cannot_replace_saved_choices(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides: 4)
            hero = app.create(game='heroes-unlimited')
            with self.assertRaises(ValueError):
                app.select_hero_programs(hero['id'], revision=0, selections=[])
            hero = app.select_education(hero['id'], revision=0, method='choose', education_id='doctorate')
            hero = app.select_hero_programs(hero['id'], revision=1, selections=[{'slot':0,'program':'business'}])
            for choices in ([{'slot':True,'program':'business'}], [{'slot':-1,'program':'business'}], [{'slot':0,'program':'unknown'}]):
                with self.assertRaises(ValueError):
                    app.select_hero_programs(hero['id'], revision=hero['revision'], selections=choices)
            with self.assertRaises(SaveConflict):
                app.select_hero_programs(hero['id'], revision=1, selections=[])
            self.assertEqual(app.get(hero['id']), hero)
            original = app.export_character(hero['id'])
            for change in ('pin','slot','education'):
                bad = copy.deepcopy(original)
                if change == 'pin':
                    bad['character']['additional_rule_packs'].pop('heroes-program-skills')
                elif change == 'slot':
                    bad['character']['hero_program_selections'][0]['slot'] = 0.5
                else:
                    bad['character'].pop('education')
                with self.assertRaises(ValueError):
                    app.import_character(bad)
            self.assertEqual(len(app.list()), 1)
            rifts = app.create()
            with self.assertRaises(ValueError):
                app.select_hero_programs(rifts['id'], revision=0, selections=[])

    def test_ineligible_and_eligible_entries_use_the_same_bonus_in_either_order(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides: 4)
            hero = app.create(game='heroes-unlimited')
            hero = app.select_education(hero['id'], revision=0, method='choose', education_id='military')
            choices = [{'slot':0,'program':'business'}, {'slot':2,'program':'business'}]
            for order in (choices, list(reversed(choices))):
                hero = app.select_hero_programs(hero['id'], revision=hero['revision'], selections=order)
                view = app.hero_program_view(hero['id'])
                self.assertEqual(next(item for item in view['skills'] if item['id'] == 'research')['percentage'], 55)
                self.assertEqual(len(view['skills']), 6)

    def test_saved_program_version_survives_corrections_and_education_changes(self):
        with tempfile.TemporaryDirectory() as directory:
            archive = RuleArchive.load()
            legacy = RuleArchive(archive.definitions(), {**archive.active_versions(), 'heroes-program-skills':'1.0.0'})
            app = CharacterApplication(directory, die=lambda sides: 4, rule_archive=legacy)
            hero = app.create(game='heroes-unlimited')
            hero = app.select_education(hero['id'], revision=0, method='choose', education_id='doctorate')
            hero = app.select_hero_programs(hero['id'], revision=hero['revision'], selections=[{'slot':0,'program':'business'}])
            hero = app.set_attribute(hero['id'], attribute='IQ', revision=hero['revision'], mode='fixed', value=30)
            self.assertEqual(next(item for item in app.hero_program_view(hero['id'])['skills'] if item['id'] == 'research')['percentage'], 96)
            correction = archive.active('heroes-program-skills')
            correction['version'] = '1.3.0'
            correction['skills'][2]['base'] = 60
            newer = CharacterApplication(directory, rule_archive=RuleArchive([*archive.definitions(),correction], {**archive.active_versions(),'heroes-program-skills':'1.3.0'}))
            self.assertEqual(next(item for item in newer.hero_program_view(hero['id'])['skills'] if item['id'] == 'research')['percentage'], 96)
            hero = newer.select_education(hero['id'], revision=hero['revision'], method='choose', education_id='high-school')
            self.assertEqual(next(item for item in newer.hero_program_view(hero['id'])['skills'] if item['id'] == 'research')['percentage'], 71)
            self.assertEqual(hero['additional_rule_packs']['heroes-program-skills'], '1.0.0')
            fresh = newer.create(game='heroes-unlimited')
            fresh = newer.select_education(fresh['id'], revision=0, method='choose', education_id='doctorate')
            fresh = newer.select_hero_programs(fresh['id'], revision=fresh['revision'], selections=[{'slot':0,'program':'business'}])
            newer.set_attribute(fresh['id'], attribute='IQ', revision=fresh['revision'], mode='fixed', value=30)
            research = next(item for item in newer.hero_program_view(fresh['id'])['skills'] if item['id'] == 'research')
            self.assertEqual(research['percentage'], 98)
            self.assertEqual(research['uncapped_percentage'], 106)


if __name__ == '__main__':
    unittest.main()
