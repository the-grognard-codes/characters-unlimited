import copy
import tempfile
import unittest

from characters_unlimited.application import CharacterApplication
from characters_unlimited.storage import SaveConflict
from characters_unlimited.rules import RuleArchive


class HeroesEducationWorkflowTests(unittest.TestCase):
    def test_player_rolls_or_chooses_education_and_keeps_its_history(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides: 4)
            hero = app.create(game='heroes-unlimited')
            self.assertIsNone(app.education_view(hero['id'])['selection'])
            app.die = lambda sides: 83
            rolled = app.select_education(hero['id'], revision=0, method='roll')
            view = app.education_view(hero['id'])
            self.assertEqual(view['selection'], {'id':'military-specialist', 'method':'roll', 'roll':83})
            self.assertEqual(view['outcome']['secondary_count'], 5)
            self.assertEqual([slot['bonus'] for slot in view['outcome']['program_slots']], [20,20,15,None,10])
            selected = app.select_education(hero['id'], revision=rolled['revision'], method='choose', education_id='doctorate')
            self.assertEqual(app.education_view(hero['id'])['outcome']['program_slots'][0]['bonus'], 30)
            self.assertEqual(len(selected['education']['history']), 2)
            reopened = CharacterApplication(directory).get(hero['id'])
            self.assertEqual(reopened['education'], selected['education'])
            imported = app.import_character(app.export_character(hero['id']))
            self.assertEqual(imported['education'], selected['education'])
            self.assertEqual(imported['additional_rule_packs'], {'heroes-education':'1.0.0'})

    def test_table_boundaries_and_street_allowances_match_the_book(self):
        expected = [(1,10,'street-schooled',8),(11,20,'high-school',10),(21,30,'military',8),
                    (31,40,'trade-school',8),(41,50,'college-one',8),(51,60,'college-two',10),
                    (61,70,'college-three',8),(71,80,'college-four',10),(81,85,'military-specialist',5),
                    (86,90,'bachelors',10),(91,95,'masters',10),(96,100,'doctorate',10)]
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides: 4)
            hero = app.create(game='heroes-unlimited')
            for low, high, identifier, secondary in expected:
                for roll in (low, high):
                    app.die = lambda sides: roll
                    hero = app.select_education(hero['id'], revision=hero['revision'], method='roll')
                    view = app.education_view(hero['id'])
                    self.assertEqual(view['selection']['id'], identifier)
                    self.assertEqual(view['selection']['roll'], roll)
                    self.assertEqual(view['outcome']['secondary_count'], secondary)
            hero = app.select_education(hero['id'], revision=hero['revision'], method='choose', education_id='street-schooled')
            street = app.education_view(hero['id'])['outcome']
            self.assertEqual(street['program_slots'], [])
            self.assertEqual(street['street_choices'], {'Rogue':3,'Domestic':2,'Technical':2})
            self.assertIn('Streetwise (+14%)', street['street_grants'])

    def test_invalid_stale_and_cross_game_changes_preserve_saved_education(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides: 4)
            hero = app.create(game='heroes-unlimited')
            for roll in (0,101,True,12.5):
                app.die = lambda sides: roll
                with self.assertRaises(ValueError):
                    app.select_education(hero['id'], revision=0, method='roll')
                self.assertEqual(app.get(hero['id']), hero)
            hero = app.select_education(hero['id'], revision=0, method='choose', education_id='military')
            with self.assertRaises(SaveConflict):
                app.select_education(hero['id'], revision=0, method='roll')
            with self.assertRaises(ValueError):
                app.select_education(hero['id'], revision=1, method='choose', education_id='unknown')
            self.assertEqual(app.get(hero['id']), hero)
            app.die = lambda sides: 4
            rifts = app.create()
            with self.assertRaisesRegex(ValueError, 'Heroes'):
                app.select_education(rifts['id'], revision=0, method='choose', education_id='doctorate')

    def test_portable_education_rejects_tampered_rolls_history_and_missing_pins(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides: 4)
            hero = app.create(game='heroes-unlimited')
            app.die = lambda sides: 100
            app.select_education(hero['id'], revision=0, method='roll')
            original = app.export_character(hero['id'])
            for change in ('roll','history','pin'):
                bad = copy.deepcopy(original)
                if change == 'roll':
                    bad['character']['education']['history'][0]['roll'] = 1
                elif change == 'history':
                    bad['character']['education']['selection'] = {'id':'masters','method':'choose'}
                else:
                    bad['character']['additional_rule_packs'] = {}
                with self.assertRaises(ValueError):
                    app.import_character(bad)
                self.assertEqual(len(app.list()), 1)

    def test_accepted_corrections_do_not_silently_change_saved_education(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides: 4)
            hero = app.create(game='heroes-unlimited')
            hero = app.select_education(hero['id'], revision=0, method='choose', education_id='masters')
            archive = RuleArchive.load()
            correction = archive.active('heroes-education')
            correction['version'] = '1.1.0'
            for outcome in correction['outcomes']:
                if outcome['id'] == 'masters':
                    for slot in outcome['program_slots']:
                        slot['bonus'] = 30
            updated = RuleArchive([*archive.definitions(), correction], {**archive.active_versions(), 'heroes-education':'1.1.0'})
            newer = CharacterApplication(directory, die=lambda sides: 4, rule_archive=updated)
            self.assertEqual(newer.education_view(hero['id'])['outcome']['program_slots'][0]['bonus'], 25)
            hero = newer.select_education(hero['id'], revision=hero['revision'], method='choose', education_id='masters')
            self.assertEqual(hero['additional_rule_packs']['heroes-education'], '1.0.0')
            fresh = newer.create(game='heroes-unlimited')
            newer.select_education(fresh['id'], revision=0, method='choose', education_id='masters')
            self.assertEqual(newer.education_view(fresh['id'])['outcome']['program_slots'][0]['bonus'], 30)


if __name__ == '__main__':
    unittest.main()
