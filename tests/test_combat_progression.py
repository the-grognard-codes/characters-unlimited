"""Source-checked combat changes earned after the first experience level."""

import tempfile
import unittest

from characters_unlimited.application import CharacterApplication


class CombatProgressionTests(unittest.TestCase):
    def test_expert_and_knife_gain_their_third_training_level_once(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides: 4)
            hero = app.create()
            hero = app.select_combat(hero['id'], revision=hero['revision'], choices={
                'hand_to_hand': 'expert', 'ancient': ['knife'], 'modern': []})
            hero = app.generate_resources(hero['id'], revision=hero['revision'])
            hero = app.advance(hero['id'], revision=hero['revision'], method='level', value=3)

            combat = app.combat_view(hero['id'])
            self.assertEqual(combat['totals']['strike']['value'], 2)
            self.assertEqual(combat['totals']['disarm']['value'], 2)
            knife = next(item for item in combat['melee'] if item['id'] == 'knife')
            self.assertEqual(knife['strike']['contributions']['weapon_proficiency'], 1)
            self.assertEqual(knife['parry']['contributions']['weapon_proficiency'], 2)
            self.assertEqual(knife['thrown']['contributions']['weapon_proficiency'], 2)
            karate = next(item for item in combat['unarmed'] if item['id'] == 'karate-punch')
            self.assertEqual(karate['damage'], '2D4 S.D.C.')
            self.assertEqual(next(item for item in combat['unarmed']
                                  if item['id'] == 'power-karate-punch')['actions'], 2)

    def test_assassin_fifteenth_level_keeps_physical_and_gun_bonuses_separate(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides: 4)
            hero = app.create()
            hero = app.select_combat(hero['id'], revision=hero['revision'], choices={
                'hand_to_hand': 'assassin', 'ancient': ['knife'],
                'modern': ['handguns', 'energy-pistol']})
            hero = app.generate_resources(hero['id'], revision=hero['revision'])
            hero = app.set_attribute(hero['id'], revision=hero['revision'], attribute='PS', mode='fixed', value=20)
            hero = app.set_attribute(hero['id'], revision=hero['revision'], attribute='PP', mode='fixed', value=20)
            hero = app.advance(hero['id'], revision=hero['revision'], method='level', value=15)

            combat = app.combat_view(hero['id'])
            self.assertEqual(combat['totals']['attacks']['value'], 8)
            self.assertEqual(combat['totals']['initiative']['value'], 4)
            self.assertEqual(combat['totals']['strike']['contributions']['hand_to_hand'], 6)
            self.assertEqual(combat['totals']['strike']['value'], 9)
            self.assertEqual(combat['totals']['damage']['contributions'],
                             {'normal_strength': 5, 'hand_to_hand': 6})
            karate = next(item for item in combat['unarmed'] if item['id'] == 'karate-punch')
            self.assertEqual(karate['damage'], '2D4 + 11 S.D.C.')
            self.assertEqual(next(item for item in combat['unarmed']
                                  if item['id'] == 'power-karate-punch')['damage'],
                             '2 × 2D4 + 11 S.D.C.')
            knife = next(item for item in combat['melee'] if item['id'] == 'knife')
            self.assertEqual(knife['thrown']['value'], 11)
            handgun = next(item for item in combat['shooting'] if item['id'] == 'handguns')
            self.assertEqual(handgun['single']['value'], 10)
            self.assertEqual(handgun['burst']['contributions'],
                             {'weapon_proficiency_halved': 3, 'hand_to_hand_guns': 3})
            self.assertEqual(handgun['burst']['value'], 6)

    def test_training_first_selected_at_fifteen_starts_at_its_first_level(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides: 4)
            hero = app.create(level=15)
            selected = {'hand_to_hand': 'expert', 'ancient': ['knife'], 'modern': ['handguns']}
            hero = app.select_combat(hero['id'], revision=hero['revision'], choices=selected)
            combat = app.combat_view(hero['id'])
            self.assertEqual(combat['totals']['strike']['value'], 0)
            self.assertNotIn('karate-punch', {item['id'] for item in combat['unarmed']})
            self.assertEqual(combat['melee'][0]['parry']['contributions']['weapon_proficiency'], 1)
            self.assertEqual(next(item for item in combat['shooting']
                                  if item['id'] == 'handguns')['single']['value'], 0)
            hero = app.select_combat(hero['id'], revision=hero['revision'], choices={})
            hero = app.select_combat(hero['id'], revision=hero['revision'], choices=selected)
            retained = app.combat_view(hero['id'])
            self.assertEqual(retained['totals']['strike']['value'], 0)
            self.assertEqual(retained['melee'][0]['parry']['contributions']['weapon_proficiency'], 1)

    def test_low_strength_applies_the_correct_assassin_damage_band(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides: 4)
            hero = app.create()
            hero = app.select_combat(hero['id'], revision=hero['revision'], choices={
                'hand_to_hand': 'assassin', 'ancient': [], 'modern': []})
            hero = app.generate_resources(hero['id'], revision=hero['revision'])
            hero = app.advance(hero['id'], revision=hero['revision'], method='level', value=4)

            hero = app.set_attribute(hero['id'], revision=hero['revision'], attribute='PS', mode='fixed', value=6)
            weak = app.combat_view(hero['id'])
            self.assertNotIn('hand_to_hand', weak['totals']['damage']['contributions'])
            self.assertEqual(next(item for item in weak['unarmed']
                                  if item['id'] == 'karate-punch')['damage'], '2D4 S.D.C.')

            hero = app.set_attribute(hero['id'], revision=hero['revision'], attribute='PS', mode='fixed', value=4)
            weaker = app.combat_view(hero['id'])
            self.assertEqual(weaker['totals']['damage']['contributions']['hand_to_hand'], 4)
            self.assertEqual(next(item for item in weaker['unarmed']
                                  if item['id'] == 'karate-punch')['damage'], '½ × (2D4 + 4) S.D.C.')

    def test_assassin_gun_bonus_is_independent_of_weapon_proficiency(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides: 4)
            hero = app.create()
            hero = app.select_combat(hero['id'], revision=hero['revision'], choices={
                'hand_to_hand': 'assassin', 'ancient': [], 'modern': []})
            hero = app.generate_resources(hero['id'], revision=hero['revision'])
            hero = app.advance(hero['id'], revision=hero['revision'], method='level', value=8)

            handgun = next(item for item in app.combat_view(hero['id'])['shooting']
                           if item['id'] == 'handguns')
            self.assertFalse(handgun['trained'])
            self.assertEqual(handgun['single']['value'], 1)
            self.assertEqual(handgun['burst']['contributions'],
                             {'untrained': -3, 'hand_to_hand_guns': 1})
            self.assertEqual(handgun['burst']['value'], -2)
            self.assertIsNone(handgun['aimed']['value'])

    def test_expert_tenth_level_damage_bonus_is_inside_low_strength_halving(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides: 4)
            hero = app.create()
            hero = app.select_combat(hero['id'], revision=hero['revision'], choices={
                'hand_to_hand': 'expert', 'ancient': [], 'modern': []})
            hero = app.generate_resources(hero['id'], revision=hero['revision'])
            hero = app.advance(hero['id'], revision=hero['revision'], method='level', value=10)
            hero = app.set_attribute(hero['id'], revision=hero['revision'], attribute='PS', mode='fixed', value=3)
            combat = app.combat_view(hero['id'])
            self.assertEqual(combat['totals']['damage']['contributions']['hand_to_hand'], 3)
            self.assertEqual(next(item for item in combat['unarmed']
                                  if item['id'] == 'punch')['damage'], '½ × (1D4 + 3) S.D.C.')


if __name__ == '__main__':
    unittest.main()
