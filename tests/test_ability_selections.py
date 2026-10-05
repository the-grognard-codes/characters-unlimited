from copy import deepcopy
import json
import unittest

from characters_unlimited.ability_selections import select_abilities, project_abilities
from characters_unlimited.recorded_formulas import MAX_INTEGER
from characters_unlimited.skill_effects import matching_skill_effects


SOURCE = {'book': 'Synthetic adapter fixture', 'section': 'Common ability witness'}
SKILLS = [{'id': 'concealment', 'category': 'Rogue'}, {'id': 'biology', 'category': 'Science'}]


def catalog(game='rifts'):
    return {'id': 'fixture-abilities', 'version': '1', 'game': game, 'format': 'abilities-v1',
        'options': [
            {'id': 'sense', 'name': 'Sense', 'category': 'Sensitive', 'source': SOURCE,
             'description': 'A descriptive psychic sense.',
             'parameters': [{'id': 'range', 'name': 'Range', 'source': SOURCE,
                'quantity': {'base': 10, 'per_level': 5, 'unit': 'feet', 'level_origin': 1}}],
             'requirements': [{'id': 'training', 'name': 'Training', 'source': SOURCE,
                'selected_options': {'catalog': 'skills', 'selector': {'any_of': [{'ids': ['biology']}]},
                                     'minimum': 1}}],
             'acquisition_formulas': {'capacity': {'count': 2, 'sides': 6, 'constant': 3}},
             'skill_effects': [{'id': 'bonus', 'name': 'Ability bonus', 'operation': 'add',
                 'amount': 10, 'selector': {'any_of': [{'ids': ['concealment']}]}, 'source': SOURCE}]},
            {'id': 'heal', 'name': 'Heal', 'category': 'Healing', 'source': SOURCE,
             'description': 'A descriptive healing power.'}],
        'groups': [{'id': 'sensitive', 'name': 'Sensitive choices', 'count': 1,
            'selector': {'any_of': [{'categories': ['Sensitive']}]}, 'source': SOURCE}]}


class AbilitySelectionTests(unittest.TestCase):
    def context(self, game='rifts', **changes):
        return dict(game=game, skill_catalog=SKILLS, level=1, attributes={'ME': 12}, **changes)

    def no_roll(self, sides):
        self.fail('Preflight, deselection and replay must not draw dice')

    def test_retained_receipts_replay_across_deselection_json_and_level(self):
        pack = catalog()
        faces = iter([2, 6])
        state = select_abilities(pack, None, ['sense'], lambda sides: next(faces), **self.context())
        original = deepcopy(state)
        inactive = select_abilities(pack, state, [], self.no_roll, **self.context())
        self.assertEqual(inactive['acquisitions'], state['acquisitions'])
        reselected = select_abilities(pack, json.loads(json.dumps(inactive)), ['sense'],
                                     self.no_roll, **self.context())
        self.assertEqual(reselected, original)
        context = self.context(skill_selections=['biology'])
        context['level'] = 3
        view = project_abilities(pack, reselected, **context)
        self.assertEqual(view['abilities'][0]['acquired_values'], {'capacity': 11})
        self.assertEqual(view['abilities'][0]['parameters'][0]['value'], 20)
        self.assertTrue(view['abilities'][0]['requirements'][0]['satisfied'])
        self.assertEqual(view['groups'][0]['remaining'], 0)
        self.assertEqual(matching_skill_effects('concealment', view['skill_effects'])[0]['value'], 10)
        self.assertEqual(matching_skill_effects('biology', view['skill_effects']), [])
        self.assertEqual(state, original)
        view['abilities'][0]['source']['book'] = 'Changed output'
        self.assertEqual(pack['options'][0]['source'], SOURCE)

    def test_honor_system_keeps_outside_and_over_allowance_without_markers(self):
        pack = catalog()
        pack['groups'][0]['count'] = 0
        state = select_abilities(pack, None, ['sense', 'heal'], lambda sides: 1, **self.context())
        view = project_abilities(pack, state, **self.context())
        self.assertEqual(state['selections'], ['sense', 'heal'])
        self.assertEqual(view['groups'][0]['remaining'], -1)
        self.assertEqual(view['groups'][0]['outside'], ['heal'])
        self.assertFalse(view['abilities'][0]['requirements'][0]['satisfied'])
        self.assertEqual(set(state), {'pin', 'selections', 'acquisitions'})
        self.assertEqual(state['acquisitions']['heal'], {'rolls': {}})

    def test_same_boundary_supports_games_and_descriptive_spell_mutant_options(self):
        for game, identifier in [('rifts', 'spell'), ('heroes-unlimited', 'mutant')]:
            pack = catalog(game)
            pack['options'][1]['id'] = identifier
            state = select_abilities(pack, None, [identifier], self.no_roll, **self.context(game))
            self.assertEqual(project_abilities(pack, state, **self.context(game))['abilities'][0]['id'], identifier)
            other = 'heroes-unlimited' if game == 'rifts' else 'rifts'
            with self.assertRaises(ValueError):
                select_abilities(pack, state, [], self.no_roll, **self.context(other))

    def test_whole_catalog_errors_reject_before_dice(self):
        mutations = [
            lambda p: p['options'][1].update(source={}),
            lambda p: p['options'][1].update(acquisition_formulas={'bad': {'count': True, 'sides': 6}}),
            lambda p: p['options'][1].update(parameters=[{'id': 'x', 'name': 'x', 'source': SOURCE,
                'quantity': {'base': MAX_INTEGER, 'per_level': 1, 'unit': 'feet'}}]),
            lambda p: p['groups'][0].update(selector={'any_of': [{'ids': ['missing']}]}),
            lambda p: p['groups'][0].update(costs={'heal': 2}),
            lambda p: p['options'][1].update(requirements=[{'id': 'x', 'name': 'x', 'source': SOURCE,
                'attribute_minimum': {'attribute': 'missing', 'value': 10}}]),
        ]
        for mutate in mutations:
            with self.subTest(mutation=mutate):
                pack = catalog()
                mutate(pack)
                with self.assertRaises(ValueError):
                    select_abilities(pack, None, ['sense'], self.no_roll, **self.context())

    def test_state_and_dependencies_require_exact_content_even_for_inactive_receipts(self):
        pack = catalog()
        state = select_abilities(pack, None, ['sense'], lambda sides: 2, **self.context())
        state = select_abilities(pack, state, [], self.no_roll, **self.context())
        forged = deepcopy(state)
        forged['acquisitions']['sense']['rolls']['capacity'][0] = 7
        with self.assertRaises(ValueError):
            select_abilities(pack, forged, ['heal'], self.no_roll, **self.context())
        changed = deepcopy(pack)
        changed['options'][0]['description'] += ' Changed.'
        with self.assertRaises(ValueError):
            project_abilities(changed, state, **self.context())
        context = self.context()
        context['skill_catalog'] = [*SKILLS, {'id': 'new-skill'}]
        with self.assertRaises(ValueError):
            project_abilities(pack, state, **context)
        for selections in [['missing'], ['heal', 'heal']]:
            with self.assertRaises(ValueError):
                select_abilities(pack, state, selections, self.no_roll, **self.context())
        context = self.context()
        context['level'] = True
        with self.assertRaises(ValueError):
            select_abilities(pack, None, [], self.no_roll, **context)

    def test_effect_names_are_scoped_and_total_bounds_preflight(self):
        pack = catalog()
        pack['options'][1]['skill_effects'] = deepcopy(pack['options'][0]['skill_effects'])
        state = select_abilities(pack, None, ['sense', 'heal'], lambda sides: 1, **self.context())
        effects = project_abilities(pack, state, **self.context())['skill_effects']
        self.assertEqual(len({effect['id'] for effect in effects}), 2)
        self.assertEqual(sum(row['value'] for row in matching_skill_effects('concealment', effects)), 20)
        for option in pack['options']:
            option['skill_effects'][0]['amount'] = MAX_INTEGER
        with self.assertRaises(ValueError):
            select_abilities(pack, None, ['sense', 'heal'], self.no_roll, **self.context())
