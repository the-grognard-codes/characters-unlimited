import tempfile
import unittest
from copy import deepcopy

from characters_unlimited.application import CharacterApplication
from characters_unlimited.rules import RuleArchive


SOURCE = {'book': 'Rifts - Ultimate Edition', 'section': 'Cartography and related skill allocations', 'pages': [99], 'pdf_pages': [102]}


def choices(*identifiers, pool='related'):
    return [{'skill_id': identifier, 'pool': pool} for identifier in identifiers]


def archive(change):
    installed = RuleArchive.load()
    pack = deepcopy(installed.resolve('rifts-domestic-skills', '2.23.0'))
    pack['version'] = '9.99.0'
    change(pack)
    return RuleArchive(installed.definitions() + [pack], {**installed.active_versions(), pack['id']: pack['version']})


def cartography(pack):
    pack['required']['grants'].append({'id': 'cartography', 'name': 'Cartography', 'base': 40, 'per_level': 5,
        'class_bonus': 20, 'source': SOURCE, 'proficiency_rules': {'independent_checks': True, 'source': SOURCE},
        'additional_checks': [{'name': 'Basic mathematics', 'base': 50, 'per_level': 0,
            'bonus_policy': 'intelligence-only', 'unless_skill': 'math-basic', 'unless_pool': 'related'}]})
    pack['skill_effects'] = [{'id': 'cartography-math', 'name': 'Cartography', 'operation': 'add', 'amount': 5,
        'selector': {'any_of': [{'ids': ['math-basic']}]}, 'selection_pool': 'related', 'source': SOURCE},
        {'id': 'parent-bonus', 'name': 'Parent bonus', 'operation': 'add', 'amount': 9,
         'selector': {'any_of': [{'ids': ['cartography']}]}, 'source': SOURCE}]


class ScoutSkillContractTests(unittest.TestCase):
    def test_fixed_weapon_training_is_automatic_and_never_consumes_elective_allowance(self):
        def change(pack):
            pack['combat']['fixed_proficiencies'] = {'ancient':['knife'], 'modern':[], 'source':SOURCE}
            pack['combat']['combined_proficiency_count'] = 3
            pack['combat']['required_proficiencies'] = {'ancient':'any', 'modern':'any'}
        with tempfile.TemporaryDirectory() as directory:
            app=CharacterApplication(directory,die=lambda sides:4,rule_archive=archive(change))
            hero=app.create(level=6)
            before=app.combat_view(hero['id'])
            knife=next(row for row in before['melee'] if row['id']=='knife')
            self.assertEqual(before['fixed_proficiencies']['ancient'], ['knife'])
            self.assertEqual(before['choices']['ancient'], [])
            self.assertEqual(before['remaining']['proficiencies'], 3)
            hero=app.select_combat(hero['id'],revision=0,choices={'ancient':['knife','sword'],'modern':['handguns','energy-rifle']})
            after=app.combat_view(hero['id'])
            self.assertEqual(after['remaining']['proficiencies'],0)
            self.assertEqual(next(row for row in after['melee'] if row['id']=='knife')['strike'],knife['strike'])

    def test_class_milestone_saves_and_combat_bonuses_follow_retained_level_and_undo(self):
        def change(pack):
            pack['class_bonuses']['combat']={'initiative':1,'roll_with_impact':2}
            pack['class_bonuses']['saving']['horror_factor']=0
            pack['class_bonuses']['level_bonuses']=[{'target':'saving:horror_factor','levels':[2,4,6,9,12,15],'amount':1}]
        with tempfile.TemporaryDirectory() as directory:
            app=CharacterApplication(directory,die=lambda sides:4,rule_archive=archive(change))
            hero=app.create()
            view=app.combat_view(hero['id'])
            self.assertEqual(view['totals']['initiative']['value'],1)
            self.assertEqual(view['totals']['roll_with_impact']['value'],4)
            self.assertEqual(view['saving_bonuses']['horror_factor']['value'],0)
            hero=app.generate_resources(hero['id'],revision=0)
            hero=app.advance(hero['id'],revision=hero['revision'],method='level',value=2)
            self.assertEqual(app.combat_view(hero['id'])['saving_bonuses']['horror_factor']['value'],1)
            hero=app.advance(hero['id'],revision=hero['revision'],method='level',value=4)
            self.assertEqual(app.combat_view(hero['id'])['saving_bonuses']['horror_factor']['value'],2)
            hero=app.undo_advancement(hero['id'],revision=hero['revision'])['character']
            self.assertEqual(app.combat_view(hero['id'])['saving_bonuses']['horror_factor']['value'],1)

    def test_fixed_intelligence_check_ignores_parent_growth_class_and_other_effects(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides: 4, rule_archive=archive(cartography))
            hero = app.create(level=3)
            hero = app.set_attribute(hero['id'], revision=0, attribute='IQ', mode='fixed', value=16)
            parent = next(row for row in app.skill_view(hero['id'])['grants'] if row['id']=='cartography')
            self.assertEqual(parent['percentage'], 81)
            self.assertEqual(parent['additional_checks'][0]['contributions'], {'base':50, 'intelligence':2})
            hero = app.advance(hero['id'], revision=hero['revision'], method='level', value=4)
            parent = next(row for row in app.skill_view(hero['id'])['grants'] if row['id']=='cartography')
            self.assertEqual(parent['percentage'], 86)
            self.assertEqual(parent['additional_checks'][0]['percentage'], 52)

    def test_math_pool_controls_bonus_and_fallback_without_backdating_actual_learning(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides: 4, rule_archive=archive(cartography))
            hero = app.create(level=3)
            hero = app.select_skills(hero['id'], revision=0, selections=choices('math-basic', pool='secondary'))
            before = app.skill_view(hero['id'])
            self.assertEqual(before['selected'][0]['percentage'], 45)
            self.assertEqual(next(row for row in before['grants'] if row['id']=='cartography')['additional_checks'][0]['percentage'], 50)
            learned = deepcopy(hero['learning_levels'])
            hero = app.select_skills(hero['id'], revision=hero['revision'], selections=choices('math-basic'))
            after = app.skill_view(hero['id'])
            self.assertEqual(after['selected'][0]['percentage'], 55)
            self.assertEqual(after['selected'][0]['effect_contributions'][0]['value'], 5)
            self.assertEqual(next(row for row in after['grants'] if row['id']=='cartography')['additional_checks'], [])
            self.assertEqual(hero['learning_levels'], learned)
            hero = app.select_skills(hero['id'], revision=hero['revision'], selections=[])
            self.assertEqual(next(row for row in app.skill_view(hero['id'])['grants'] if row['id']=='cartography')['additional_checks'][0]['percentage'], 50)
            imported = app.import_character(app.export_character(hero['id']))
            self.assertEqual(app.skill_view(imported['id'])['grants'], app.skill_view(hero['id'])['grants'])

    def test_category_minima_credit_distinct_eligible_choices_and_retain_every_selection(self):
        def change(pack):
            pack['pools']['related']['requirements'] = [
                {'id':'physical', 'name':'Physical choices', 'count':2, 'selector':{'any_of':[{'categories':['physical']}]}, 'source':SOURCE},
                {'id':'wilderness', 'name':'Wilderness choice', 'count':1, 'selector':{'any_of':[{'categories':['wilderness']}]}, 'source':SOURCE}]
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides:4, rule_archive=archive(change))
            hero = app.create()
            hero = app.select_skills(hero['id'], revision=0, selections=choices('running', 'running', 'acrobatics', 'hunting'))
            view = app.skill_view(hero['id'])
            self.assertEqual([row['remaining'] for row in view['pool_requirements']], [1,0])
            self.assertEqual(len(view['selected']), 4)
            self.assertTrue(any('Physical choices' in warning for warning in view['warnings']))
            hero = app.select_skills(hero['id'], revision=hero['revision'], selections=choices('running', 'swimming', 'hunting'))
            self.assertEqual([row['remaining'] for row in app.skill_view(hero['id'])['pool_requirements']], [0,0])

    def test_invalid_pool_policy_and_requirements_on_an_unselected_owner_reject_before_dice(self):
        changes = [lambda pack: next(row for row in pack['required']['grants'] if row['id']=='cartography')['additional_checks'][0].update(per_level=1),
            lambda pack: next(row for row in pack['required']['grants'] if row['id']=='cartography')['additional_checks'][0].update(unless_pool='absent'),
            lambda pack: pack['skill_effects'][0].update(selection_pool='absent'),
            lambda pack: pack['class_bonuses'].update(level_bonuses=[{'target':'saving:horror_factor','levels':[True],'amount':1}]),
            lambda pack: pack['class_profiles']['city-rat']['class_bonuses'].update(combat={'initiative':True}),
            lambda pack: pack['class_profiles']['city-rat']['combat'].update(fixed_proficiencies={'ancient':['absent'],'modern':[],'source':SOURCE}),
            lambda pack: pack['class_profiles']['city-rat']['pools']['related'].update(requirements=[
                {'id':'bad', 'name':'Bad', 'count':2, 'selector':{'any_of':[{'ids':['missing']}]}, 'source':SOURCE}])]
        for invalid in changes:
            def change(pack):
                cartography(pack)
                invalid(pack)
            with self.subTest(change=invalid), tempfile.TemporaryDirectory() as directory:
                draws=[]
                def die(sides):
                    draws.append(sides)
                    return 4
                app=CharacterApplication(directory,die=die,rule_archive=archive(change))
                with self.assertRaises(ValueError):
                    app.create()
                self.assertEqual(draws, [])
