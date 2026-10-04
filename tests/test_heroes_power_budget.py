import copy
import tempfile
import unittest
from io import BytesIO
from unittest.mock import patch
from pypdf import PdfReader

from characters_unlimited.application import CharacterApplication
from characters_unlimited.storage import SaveConflict


class HeroesPowerBudgetTests(unittest.TestCase):
    def test_percentile_boundaries_match_the_mutant_table(self):
        expected = [(1,15,'major-three-minor',[1,3]), (16,30,'four-minor',[4]),
                    (31,45,'major-two-minor',[1,2]), (46,55,'two-major',[2]),
                    (56,65,'five-minor',[5]), (66,75,'psionic-mix',[1,6]),
                    (76,80,'psychic-mutant',[4,4,4,1]), (81,90,'continuous-mutation',[1]),
                    (91,100,'unstable-powers',[1,2])]
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides:4)
            hero = app.create(game='heroes-unlimited')
            for low, high, identifier, counts in expected:
                for roll in (low, high):
                    app.die = lambda sides: roll if sides == 100 else 4
                    hero = app.select_power_budget(hero['id'], revision=hero['revision'], method='roll')
                    view = app.power_budget_view(hero['id'])
                    self.assertEqual(view['selection']['id'], identifier)
                    self.assertEqual([row['count'] for row in view['budgets']], counts)

    def test_pdf_uses_one_saved_snapshot_during_a_concurrent_outcome_change(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides: 4)
            hero = app.create(game='heroes-unlimited', name='Before')
            hero = app.select_power_budget(hero['id'], revision=0, method='choose', outcome_id='four-minor')
            original_get = app.get
            changed = False
            def read_then_change(identifier):
                nonlocal changed
                snapshot = original_get(identifier)
                if not changed:
                    changed = True
                    other = CharacterApplication(directory)
                    updated = other.select_power_budget(identifier, revision=snapshot['revision'], method='choose', outcome_id='two-major')
                    other.edit(identifier, revision=updated['revision'], name='After')
                return snapshot
            with patch.object(app, 'get', side_effect=read_then_change):
                fields = PdfReader(BytesIO(app.export_pdf(hero['id']))).get_fields()
            assert fields is not None
            self.assertEqual(fields['NAME']['/V'], 'Before')
            self.assertIn('Minor super abilities: 4', fields['POWERS']['/V'])
            self.assertNotIn('Major super abilities: 2', fields['POWERS']['/V'])

    def test_mutant_rolls_starting_budget_and_retains_it_portably(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides: 4)
            hero = app.create(game='heroes-unlimited')
            dice = iter([70, 4])
            app.die = lambda sides: next(dice)
            saved = app.select_power_budget(hero['id'], revision=0, method='roll')
            view = app.power_budget_view(hero['id'])
            self.assertEqual(view['selection'], {'id':'psionic-mix', 'method':'roll', 'roll':70, 'rolls':[4]})
            self.assertEqual(view['budgets'], [{'name':'Major super abilities', 'count':1},
                                              {'name':'Minor psionic powers (any non-Super category)', 'count':6}])
            reopened = CharacterApplication(directory)
            self.assertEqual(reopened.power_budget_view(hero['id']), view)
            imported = app.import_character(app.export_character(hero['id']))
            self.assertEqual(imported['power_budget'], saved['power_budget'])
            self.assertEqual(imported['additional_rule_packs']['heroes-mutant-power-budget'], '1.0.0')

    def test_psychic_and_continuous_outcomes_only_include_starting_allowances(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides: 4)
            hero = app.create(game='heroes-unlimited')
            dice = iter([1, 3, 4])
            app.die = lambda sides: next(dice)
            hero = app.select_power_budget(hero['id'], revision=0, method='choose', outcome_id='psychic-mutant')
            self.assertEqual([row['count'] for row in app.power_budget_view(hero['id'])['budgets']], [1,3,4,1])
            hero = app.select_power_budget(hero['id'], revision=hero['revision'], method='choose', outcome_id='continuous-mutation')
            self.assertEqual(app.power_budget_view(hero['id'])['budgets'], [{'name':'Major super ability OR Super psionic power','count':1}])
            self.assertEqual(hero['power_budget']['selection']['rolls'], [])
            hero = app.select_power_budget(hero['id'], revision=hero['revision'], method='choose', outcome_id='unstable-powers')
            self.assertTrue(any('Unstable Powers Table' in note for note in app.power_budget_view(hero['id'])['guidance']))
            pdf = PdfReader(BytesIO(app.export_pdf(hero['id'])))
            fields = pdf.get_fields()
            assert fields is not None
            self.assertIn('Unstable Powers', fields['POWERS']['/V'])
            self.assertIn('Minor super abilities: 2', fields['POWERS']['/V'])

    def test_invalid_stale_and_tampered_outcomes_leave_character_unchanged(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides: 4)
            hero = app.create(game='heroes-unlimited')
            for face in (True, 0, 101, 1.5):
                app.die = lambda sides: face
                with self.assertRaises(ValueError):
                    app.select_power_budget(hero['id'], revision=0, method='roll')
                self.assertEqual(app.get(hero['id']), hero)
            app.die = lambda sides: 4
            hero = app.select_power_budget(hero['id'], revision=0, method='choose', outcome_id='psionic-mix')
            with self.assertRaises(SaveConflict):
                app.select_power_budget(hero['id'], revision=0, method='roll')
            for change in ('faces','history','pin','game'):
                bad = copy.deepcopy(app.export_character(hero['id']))
                record = bad['character']['power_budget']
                if change == 'faces':
                    record['history'][0]['rolls'] = [5]
                elif change == 'history':
                    record['selection'] = {'id':'four-minor','method':'choose','rolls':[]}
                elif change == 'pin':
                    bad['character']['additional_rule_packs'] = {}
                else:
                    bad['character']['game'] = 'rifts'
                with self.assertRaises(ValueError):
                    app.import_character(bad)
                self.assertEqual(len(app.list()), 1)
            rifts = app.create()
            with self.assertRaisesRegex(ValueError, 'Heroes'):
                app.power_budget_view(rifts['id'])
