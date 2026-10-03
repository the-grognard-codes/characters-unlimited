import tempfile
import unittest
from copy import deepcopy
from io import BytesIO
from pypdf import PdfReader

from characters_unlimited.application import CharacterApplication


class VagabondProgressionWorkflowTests(unittest.TestCase):
    def test_above_level_one_creation_can_complete_starting_combat_choices(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides: 4)
            hero = app.create(level=15)
            choices = {'hand_to_hand':'expert', 'ancient':['knife'], 'modern':['energy-pistol']}
            hero = app.select_combat(hero['id'], revision=0, choices=choices, learned_level=1)
            combat = app.combat_view(hero['id'])
            self.assertEqual(combat['melee'][0]['strike']['contributions']['weapon_proficiency'], 5)
            self.assertEqual(combat['totals']['attacks']['value'], 7)
            self.assertEqual(next(item for item in combat['shooting'] if item['id']=='energy-pistol')['single']['value'], 8)
            hero = app.select_combat(hero['id'], revision=hero['revision'], choices={})
            hero = app.select_combat(hero['id'], revision=hero['revision'], choices=choices, learned_level=15)
            self.assertEqual(app.combat_view(hero['id'])['melee'][0]['strike']['contributions']['weapon_proficiency'], 5)
            with self.assertRaises(ValueError):
                app.select_combat(hero['id'], revision=hero['revision'], choices=choices, learned_level=16)

    def test_equipped_weapons_use_earned_training_and_physical_damage(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides: 4)
            hero = app.create()
            hero = app.select_combat(hero['id'], revision=0, choices={
                'hand_to_hand':'assassin', 'ancient':['knife'], 'modern':['energy-pistol']})
            hero = app.generate_resources(hero['id'], revision=hero['revision'])
            hero = app.advance(hero['id'], revision=hero['revision'], method='level', value=15)
            hero = app.purchase_equipment(hero['id'], revision=hero['revision'], item_id='knife-large', unit_cost=30)
            hero = app.purchase_equipment(hero['id'], revision=hero['revision'], item_id='wilks-320')
            inventory = deepcopy(hero['equipment'])
            for item in inventory['items']: item['equipped'] = True
            hero = app.set_equipment(hero['id'], revision=hero['revision'], inventory=inventory)
            view = app.equipment_view(hero['id'])
            self.assertEqual(view['melee_attacks'][0]['damage'], '1D6 + 6 S.D.C.')
            self.assertEqual(view['attacks'][0]['single']['value'], 11)
            self.assertEqual(view['attacks'][0]['aimed']['value'], 15)
            pdf = PdfReader(BytesIO(app.export_pdf(hero['id'])))
            content = '\n'.join(page.extract_text() for page in pdf.pages)
            fields = pdf.get_fields(); assert fields is not None
            content += '\n'.join(str(field.get('/V','')) for field in fields.values())
            content = ' '.join(content.split())
            self.assertIn('Death blow on natural 19', content)
            self.assertIn('Level-15 advancement HP die: 4 (active)', content)
            for strength, damage in [(3,'½ × (1D6 + 6) S.D.C.'),(5,'1D6 S.D.C.'),(1,'½ × (1D6) S.D.C.')]:
                hero = app.set_attribute(hero['id'], revision=hero['revision'], attribute='PS', mode='fixed', value=strength)
                self.assertEqual(app.equipment_view(hero['id'])['melee_attacks'][0]['damage'], damage)

    def test_creation_above_one_generates_each_gain_and_xp_edits_do_not_reroll(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides: 4)
            hero = app.create(level=4)
            self.assertEqual(hero['level'], 4)
            self.assertEqual(app.resource_view(hero['id'])['resources']['HP']['value'], 30)
            self.assertEqual(hero['experience'], 7251)
            app.die = lambda sides: self.fail('XP within the level must not roll')
            hero = app.advance(hero['id'], revision=0, method='xp', value=14100)
            self.assertEqual(hero['level'], 4)
            self.assertEqual(hero['experience'], 14100)
            for method, value in [('level', 3), ('xp', 7250), ('level', 16), ('xp', 326501)]:
                with self.assertRaises(ValueError):
                    app.advance(hero['id'], revision=hero['revision'], method=method, value=value)
                self.assertEqual(app.get(hero['id']), hero)

    def test_experience_can_reach_fifteen_and_rejects_corrupt_historic_gains(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides: 4)
            hero = app.create()
            hero = app.generate_resources(hero['id'], revision=0)
            hero = app.advance(hero['id'], revision=hero['revision'], method='xp', value=286501)
            self.assertEqual(hero['level'], 15)
            self.assertEqual(app.resource_view(hero['id'])['resources']['HP']['value'], 74)
            self.assertEqual(app.skill_view(hero['id'])['remaining'], {'domestic': 2, 'related': 9, 'secondary': 14})
            bundle = app.export_character(hero['id'])
            for mutation in ('missing', 'face', 'source', 'nested', 'xp', 'missing_xp'):
                broken = deepcopy(bundle)
                record = broken['character']['later_advancements'][0]
                if mutation == 'missing': broken['character']['later_advancements'].pop(0)
                if mutation == 'face': record['hp_roll'] = True
                if mutation == 'source': record['source'] = {}
                if mutation == 'nested': record['before']['later_advancements'] = []
                if mutation == 'xp': record['before']['experience'] = 0
                if mutation == 'missing_xp': broken['character'].pop('experience')
                with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                    app.import_character(broken)
            imported = app.import_character(bundle)
            self.assertEqual(app.resource_view(imported['id'])['resources']['HP']['value'], 74)

    def test_third_level_opens_new_skill_slots_and_can_undo_each_recorded_gain(self):
        # RUE pp.98,287,295,347: level3 has Related6/Secondary9, +1D6 HP each level.
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides: 4)
            hero = app.create()
            hero = app.generate_resources(hero['id'], revision=0)
            hero = app.advance(hero['id'], revision=hero['revision'], method='level', value=3)
            self.assertEqual(hero['level'], 3)
            self.assertEqual(app.resource_view(hero['id'])['resources']['HP']['value'], 26)
            view = app.skill_view(hero['id'])
            self.assertEqual(view['remaining']['related'], 6)
            self.assertEqual(view['remaining']['secondary'], 9)
            self.assertEqual(next(s for s in view['grants'] if s['id'] == 'cook')['percentage'], 60)
            hero = app.edit(hero['id'], revision=hero['revision'], notes='Level-three journal')
            undone = app.undo_advancement(hero['id'], revision=hero['revision'])
            hero = undone['character']
            self.assertEqual(hero['level'], 2)
            self.assertEqual(app.resource_view(hero['id'])['resources']['HP']['value'], 22)
            self.assertEqual(app.get(undone['recovery']['id'])['notes'], 'Level-three journal')
            hero = app.undo_advancement(hero['id'], revision=hero['revision'])['character']
            self.assertEqual(hero['level'], 1)
            self.assertEqual(app.resource_view(hero['id'])['resources']['HP']['value'], 18)
            imported = app.import_character(app.export_character(hero['id']))
            app.die = lambda sides: self.fail('Both replayed gains must reuse their recorded dice')
            hero = app.advance(imported['id'], revision=imported['revision'], method='level', value=3)
            self.assertEqual(app.resource_view(hero['id'])['resources']['HP']['value'], 26)
