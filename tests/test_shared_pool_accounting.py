"""Entry-count pools share import validation without changing player choices."""
from copy import deepcopy
import tempfile
import unittest
from characters_unlimited.application import CharacterApplication
from characters_unlimited.rules import RuleArchive


def replace_definition(installed, target):
    definitions = [target if (row['id'], row['version']) == (target['id'], target['version'])
                   else row for row in installed.definitions()]
    return RuleArchive(definitions, installed.active_versions())


class SharedPoolAccountingTests(unittest.TestCase):
    def test_invalid_unselected_secondary_cost_rejects_atomically(self):
        for costs in ({'research': 0}, {'research': True}, {'research': 1.5}, {'unknown': 2}):
            with self.subTest(costs=costs), tempfile.TemporaryDirectory() as directory:
                installed = RuleArchive.load()
                skills = installed.active('heroes-program-skills')
                skills['secondary']['selection_costs'] = costs
                original = CharacterApplication(directory, die=lambda sides: 4)
                hero = original.create(game='heroes-unlimited')
                hero = original.select_education(hero['id'], revision=0, method='choose', education_id='high-school')
                app = CharacterApplication(directory, die=lambda sides: 4,
                    rule_archive=replace_definition(installed, skills))
                before = deepcopy(app.get(hero['id']))
                with self.assertRaises(ValueError):
                    app.select_hero_secondary(hero['id'], revision=hero['revision'], selections=[])
                self.assertEqual(app.get(hero['id']), before)

    def test_invalid_unselected_rifts_pool_rules_reject_atomically(self):
        mutations = [
            lambda pack: pack['pools']['related'].update(count=True),
            lambda pack: pack['pools']['related'].update(count=-1),
            lambda pack: next(iter(pack['selection_rules']['related'].values())).update(costs={'cook': 0}),
            lambda pack: next(iter(pack['selection_rules']['related'].values())).update(costs={'unknown': 2}),
        ]
        for mutation in mutations:
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as directory:
                installed = RuleArchive.load()
                skills = installed.active('rifts-domestic-skills')
                mutation(skills['class_profiles']['vagabond'] if skills.get('class_profile_format') == 'owned-v1' else skills)
                original = CharacterApplication(directory, die=lambda sides: 4)
                character = original.create()
                app = CharacterApplication(directory, die=lambda sides: 4,
                    rule_archive=replace_definition(installed, skills))
                before = deepcopy(app.get(character['id']))
                with self.assertRaises(ValueError):
                    app.select_skills(character['id'], revision=character['revision'], selections=[])
                self.assertEqual(app.get(character['id']), before)
