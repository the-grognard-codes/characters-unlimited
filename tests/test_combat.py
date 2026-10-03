import tempfile
import unittest
from characters_unlimited.application import CharacterApplication, SaveConflict
from characters_unlimited.rules import RuleArchive


class RiftsCombatWorkflowTests(unittest.TestCase):
    def test_hand_to_hand_costs_and_melee_proficiencies_are_explained_once(self):
        with tempfile.TemporaryDirectory() as directory:
            app=CharacterApplication(directory,die=lambda sides:4)
            character=app.create()
            app.set_attribute(character['id'],revision=0,attribute='PP',mode='fixed',value=20)
            saved=app.select_combat(character['id'],revision=1,choices={'hand_to_hand':'assassin','ancient':['knife','knife'],'modern':['energy-pistol']})
            view=app.combat_view(saved['id'])
            self.assertEqual(view['totals']['attacks']['value'],3)
            self.assertEqual(view['totals']['strike']['value'],5)
            self.assertEqual(view['totals']['parry']['value'],3)
            knife=next(row for row in view['melee'] if row['id']=='knife')
            self.assertEqual((knife['strike']['value'],knife['parry']['value']),(5,4))
            self.assertEqual(app.skill_view(saved['id'])['remaining']['related'],3)
            self.assertTrue(any('duplicate' in warning for warning in view['warnings']))
            self.assertTrue(any('over' in warning for warning in view['warnings']))

    def test_guns_exclude_pp_and_damage_bonuses_with_context_specific_costs(self):
        with tempfile.TemporaryDirectory() as directory:
            app=CharacterApplication(directory,die=lambda sides:4)
            character=app.create()
            app.set_attribute(character['id'],revision=0,attribute='PP',mode='fixed',value=30)
            app.set_attribute(character['id'],revision=1,attribute='PS',mode='fixed',value=40)
            app.select_combat(character['id'],revision=2,choices={'modern':['energy-pistol']})
            view=app.combat_view(character['id'])
            shot=next(row for row in view['shooting'] if row['id']=='energy-pistol')
            self.assertEqual(shot['single']['value'],1)
            self.assertEqual((shot['aimed']['value'],shot['aimed']['actions']),(3,2))
            self.assertEqual(shot['burst']['value'],0)
            self.assertEqual(shot['wild']['value'],-5)
            untrained=next(row for row in view['shooting'] if row['id']=='handguns')
            self.assertIsNone(untrained['aimed']['value'])
            self.assertEqual(untrained['burst']['value'],-3)
            self.assertEqual(view['totals']['damage']['value'],25)
            self.assertEqual(view['unarmed'][2]['damage'],'2 × 1D4 + 25 S.D.C.')

    def test_low_strength_and_missing_low_pp_rules_do_not_invent_totals(self):
        with tempfile.TemporaryDirectory() as directory:
            app=CharacterApplication(directory,die=lambda sides:4)
            character=app.create()
            app.set_attribute(character['id'],revision=0,attribute='PS',mode='fixed',value=2)
            app.set_attribute(character['id'],revision=1,attribute='PP',mode='fixed',value=5)
            view=app.combat_view(character['id'])
            self.assertEqual(view['unarmed'][0]['damage'],'1 S.D.C.')
            self.assertEqual(view['unarmed'][1]['damage'],'1D4 S.D.C.')
            self.assertIsNone(view['totals']['strike']['value'])
            self.assertTrue(any('P.P.' in gap for gap in view['gaps']))

    def test_portable_choices_and_stale_rejection_preserve_work(self):
        with tempfile.TemporaryDirectory() as directory, tempfile.TemporaryDirectory() as other:
            app=CharacterApplication(directory,die=lambda sides:4)
            character=app.create()
            saved=app.select_combat(character['id'],revision=0,choices={'hand_to_hand':'expert','ancient':['sword'],'modern':['energy-rifle']})
            with self.assertRaises(SaveConflict): app.select_combat(character['id'],revision=0,choices={})
            with self.assertRaises(ValueError): app.select_combat(character['id'],revision=1,choices={'ancient':['invented']})
            self.assertEqual(app.get(character['id']),saved)
            reopened=CharacterApplication(other)
            imported=reopened.import_character(app.export_character(character['id']))
            self.assertEqual(imported['combat_choices'],saved['combat_choices'])
            self.assertEqual(reopened.combat_view(imported['id']),app.combat_view(saved['id']))

    def test_old_pins_gain_combat_only_through_explicit_previewed_update(self):
        archive=RuleArchive.load()
        active=archive.active_versions(); active['rifts-domestic-skills']='1.4.0'
        with tempfile.TemporaryDirectory() as directory:
            earlier=CharacterApplication(directory,die=lambda sides:4,rule_archive=RuleArchive(archive.definitions(),active))
            character=earlier.create()
            current=CharacterApplication(directory)
            self.assertIsNone(current.combat_view(character['id'])['catalog'])
            preview=current.preview_rule_upgrade(character['id'])
            self.assertTrue(preview['combat'])
            self.assertEqual(current.get(character['id']),character)
            current.apply_rule_upgrade(character['id'],revision=0,token=preview['token'])
            self.assertEqual(current.combat_view(character['id'])['totals']['attacks']['value'],4)

    def test_beyond_thirty_and_slow_speed_apply_without_raising_pp_accuracy_cap(self):
        with tempfile.TemporaryDirectory() as directory:
            app=CharacterApplication(directory,die=lambda sides:4)
            character=app.create()
            for value,initiative in [(30,0),(31,1),(33,1),(34,2),(46,6),(55,6)]:
                character=app.set_attribute(character['id'],revision=character['revision'],attribute='PP',mode='fixed',value=value)
                view=app.combat_view(character['id'])
                self.assertEqual(view['totals']['strike']['value'],8)
                self.assertEqual(view['totals']['initiative']['value'],initiative)
            character=app.set_attribute(character['id'],revision=character['revision'],attribute='SPD',mode='fixed',value=6)
            view=app.combat_view(character['id'])
            self.assertEqual(view['totals']['initiative']['value'],5)
            self.assertEqual(view['totals']['dodge']['value'],7)
            self.assertEqual(view['totals']['gun_dodge']['value'],7)
            character=app.set_attribute(character['id'],revision=character['revision'],attribute='PS',mode='fixed',value=4)
            self.assertEqual(app.combat_view(character['id'])['unarmed'][0]['damage'],'½ × (1D4) S.D.C.')

    def test_required_energy_weapon_and_assassin_alignment_conditions_stay_visible(self):
        with tempfile.TemporaryDirectory() as directory:
            app=CharacterApplication(directory,die=lambda sides:4)
            character=app.create()
            saved=app.select_combat(character['id'],revision=0,choices={'hand_to_hand':'assassin','modern':['handguns']})
            view=app.combat_view(saved['id'])
            self.assertEqual(view['remaining']['modern'],1)
            self.assertTrue(any('energy weapon' in warning for warning in view['warnings']))
            self.assertTrue(any('Evil alignment' in warning for warning in view['warnings']))
            self.assertEqual(saved['combat_choices']['modern'],['handguns'])
            self.assertTrue(next(row for row in view['shooting'] if row['id']=='handguns')['trained'])
            app.select_combat(saved['id'],revision=saved['revision'],choices={'modern':['handguns','energy-pistol']})
            view=app.combat_view(saved['id'])
            self.assertEqual(view['remaining']['modern'],0)
            self.assertTrue(any('extra training is retained' in warning for warning in view['warnings']))
            self.assertFalse(any('choose an eligible energy weapon' in warning for warning in view['warnings']))
