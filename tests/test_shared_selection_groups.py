"""Shared entitlement behavior observed through character workflows."""

from copy import deepcopy
import tempfile
import unittest

from characters_unlimited.application import CharacterApplication
from characters_unlimited.rules import RuleArchive


def replace_definition(installed, target):
    definitions = [target if (row['id'], row['version']) == (target['id'], target['version'])
                   else row for row in installed.definitions()]
    return RuleArchive(definitions, installed.active_versions())


class SharedSelectionGroupTests(unittest.TestCase):
    def test_required_group_uses_declared_weights_and_credits_duplicates_once(self):
        installed = RuleArchive.load()
        skills = installed.active('rifts-domestic-skills')
        group = next(row for row in skills['required']['groups'] if row['id'] == 'pilot')
        group['count'] = 2
        group['selection_costs'] = {'motorcycle': 2}
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides: 4,
                                       rule_archive=replace_definition(installed, skills))
            character = app.create()
            character = app.select_required_skills(character['id'], revision=0,
                                                   choices={'pilot': ['motorcycle', 'motorcycle']})
            view = app.skill_view(character['id'])
            self.assertEqual(view['required_remaining']['pilot'], 0)
            self.assertEqual(len([row for row in view['grants'] if row['id'] == 'motorcycle']), 1)
            self.assertTrue(any('duplicate' in note for note in view['warnings']))
            restored = app.import_character(app.export_character(character['id']))
            self.assertEqual(restored['required_skill_choices'], character['required_skill_choices'])
            self.assertEqual(app.skill_view(restored['id'])['required_remaining']['pilot'], 0)
            character = app.select_required_skills(character['id'], revision=character['revision'],
                                                   choices={'pilot': ['motorcycle', 'automobile']})
            self.assertEqual(app.skill_view(character['id'])['required_remaining']['pilot'], -1)
            self.assertEqual(app.get(character['id'])['required_skill_choices']['pilot'],
                             ['motorcycle', 'automobile'])

    def test_invalid_program_costs_and_references_reject_before_saving(self):
        mutations = [
            lambda group: group['selection_costs'].update(boxing=0),
            lambda group: group['selection_costs'].update(boxing=1.5),
            lambda group: group['selection_costs'].update(boxing=True),
            lambda group: group['selection_costs'].update(unknown=1),
            lambda group: group.update(count=True),
        ]
        for mutation in mutations:
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as directory:
                installed = RuleArchive.load()
                skills = installed.active('heroes-program-skills')
                program = next(row for row in skills['programs'] if row['id'] == 'physical-athletic')
                mutation(program['choice_groups'][0])
                original = CharacterApplication(directory, die=lambda sides: 4)
                hero = original.create(game='heroes-unlimited')
                hero = original.select_education(hero['id'], revision=0, method='choose', education_id='high-school')
                app = CharacterApplication(directory, die=lambda sides: 4,
                                           rule_archive=replace_definition(installed, skills))
                before = deepcopy(app.get(hero['id']))
                with self.assertRaises(ValueError):
                    app.select_hero_programs(hero['id'], revision=hero['revision'], selections=[
                        {'slot': 0, 'program': 'physical-athletic', 'choices': {'physical': ['boxing']}}])
                self.assertEqual(app.get(hero['id']), before)

    def test_required_option_identity_and_cost_remain_case_sensitive(self):
        installed = RuleArchive.load()
        skills = installed.active('rifts-domestic-skills')
        group = next(row for row in skills['required']['groups'] if row['id'] == 'pilot')
        group['count'] = 2
        group['options'][0]['id'] = 'PilotA'
        group['options'][1]['id'] = 'pilota'
        group['selection_costs'] = {'PilotA': 2}
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides: 4,
                                       rule_archive=replace_definition(installed, skills))
            character = app.create()
            character = app.select_required_skills(character['id'], revision=0,
                                                   choices={'pilot': ['PilotA']})
            self.assertEqual(app.skill_view(character['id'])['required_remaining']['pilot'], 0)
            character = app.select_required_skills(character['id'], revision=character['revision'],
                                                   choices={'pilot': ['PilotA', 'pilota']})
            view = app.skill_view(character['id'])
            self.assertEqual(view['required_remaining']['pilot'], -1)
            self.assertEqual(len([row for row in view['grants'] if row['id'] in ('PilotA', 'pilota')]), 2)

    def test_minor_power_group_counts_only_its_declared_category(self):
        installed = RuleArchive.load()
        powers = installed.active('heroes-super-abilities')
        powers['powers'][0]['category'] = 'major'  # Synthetic catalog-category fixture.
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides: 4,
                                       rule_archive=replace_definition(installed, powers))
            hero = app.create(game='heroes-unlimited')
            hero = app.select_power_budget(hero['id'], revision=0, method='choose', outcome_id='four-minor')
            hero = app.select_hero_powers(hero['id'], revision=hero['revision'],
                                          selections=['extraordinary-mental-affinity'])
            view = app.hero_powers_view(hero['id'])
            self.assertEqual(view['minor'], {'used': 0, 'allowance': 4, 'remaining': 4})
            self.assertEqual(view['selections'], ['extraordinary-mental-affinity'])
            hero = app.select_hero_powers(hero['id'], revision=hero['revision'],
                                          selections=['extraordinary-mental-affinity', 'extraordinary-mental-endurance'])
            self.assertEqual(app.hero_powers_view(hero['id'])['minor'],
                             {'used': 1, 'allowance': 4, 'remaining': 3})
            restored = app.import_character(app.export_character(hero['id']))
            self.assertEqual(app.hero_powers_view(restored['id'])['minor'],
                             {'used': 1, 'allowance': 4, 'remaining': 3})

    def test_invalid_power_allowance_cannot_be_saved_as_a_budget_outcome(self):
        for count in (True, -1, 1001):
            with self.subTest(count=count), tempfile.TemporaryDirectory() as directory:
                installed = RuleArchive.load()
                budgets = installed.active('heroes-mutant-power-budget')
                outcome = next(row for row in budgets['outcomes'] if row['id'] == 'four-minor')
                outcome['budgets'][0]['count'] = count
                app = CharacterApplication(directory, die=lambda sides: 4,
                                           rule_archive=replace_definition(installed, budgets))
                hero = app.create(game='heroes-unlimited')
                before = deepcopy(app.get(hero['id']))
                with self.assertRaises(ValueError):
                    app.select_power_budget(hero['id'], revision=0, method='choose', outcome_id='four-minor')
                self.assertEqual(app.get(hero['id']), before)
