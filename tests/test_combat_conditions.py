import tempfile
import unittest
from io import BytesIO

from pypdf import PdfReader
from characters_unlimited.application import CharacterApplication
from characters_unlimited.rules import RuleArchive


class CombatConditionWorkflowTests(unittest.TestCase):
    def test_reviewed_update_preserves_old_historical_rules_and_dice(self):
        with tempfile.TemporaryDirectory() as directory:
            archive = RuleArchive.load()
            versions = {**archive.active_versions(), 'rifts-domestic-skills':'2.6.0'}
            earlier = CharacterApplication(directory, die=lambda sides:4,
                rule_archive=RuleArchive(archive.definitions(), versions))
            hero = earlier.create(level=3)
            current = CharacterApplication(directory, die=lambda sides: self.fail('Update rerolled dice'))
            self.assertEqual(current.combat_view(hero['id'])['conditions'], {})
            preview = current.preview_rule_upgrade(hero['id'])
            critical = next(item for item in preview['combat'] if item['name']=='Critical natural roll')
            self.assertIsNone(critical['before'])
            self.assertEqual(critical['after'], 'Natural 20')
            upgraded = current.apply_rule_upgrade(hero['id'], revision=hero['revision'], token=preview['token'])['character']
            self.assertEqual(upgraded['later_advancements'], hero['later_advancements'])
            self.assertEqual(upgraded['resources'], hero['resources'])
            self.assertEqual(current.combat_view(hero['id'])['conditions']['critical']['natural_min'],20)
            copy = current.import_character(current.export_character(hero['id']))
            self.assertEqual(copy['later_advancements'], hero['later_advancements'])
            restored = current.undo_advancement(hero['id'], revision=upgraded['revision'])['character']
            self.assertEqual(restored['additional_rule_packs']['rifts-domestic-skills'], '2.6.0')
            self.assertEqual(current.combat_view(hero['id'])['conditions'], {})

    def test_common_maneuvers_and_leap_kick_export_without_unlocking_unsupported_moves(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides: 4)
            hero = app.create()
            moves = {item['id']:item for item in app.combat_view(hero['id'])['unarmed']}
            self.assertEqual(moves['knee']['damage'], '1D6 S.D.C.')
            self.assertEqual(moves['body-flip']['damage'], '1D6 S.D.C.')
            self.assertNotIn('leap-kick',moves)
            self.assertNotIn('backward-sweep',moves)
            hero = app.select_combat(hero['id'], revision=0, choices={'hand_to_hand':'martial-arts'})
            hero = app.generate_resources(hero['id'], revision=hero['revision'])
            hero = app.advance(hero['id'], revision=hero['revision'], method='level', value=5)
            moves = {item['id']:item for item in app.combat_view(hero['id'])['unarmed']}
            self.assertIsNone(moves['backward-sweep']['damage'])
            self.assertEqual(moves['leap-kick']['actions'], 2)
            self.assertNotIn('power-leap-kick',moves)
            fields = PdfReader(BytesIO(app.export_pdf(hero['id']))).get_fields()
            assert fields is not None
            self.assertEqual(fields['LEAP KICK']['/V'], '3D8')
            self.assertEqual(fields['BODY FLIP THROW']['/V'], '1D6')
            hero = app.set_attribute(hero['id'], revision=hero['revision'], attribute='PS', mode='fixed', value=1)
            moves = {item['id']:item for item in app.combat_view(hero['id'])['unarmed']}
            self.assertEqual(moves['knee']['damage'], '1D4 S.D.C.')
            self.assertIn('Pending', moves['body-flip']['damage'])

    def test_natural_roll_conditions_follow_the_style_and_its_learned_age(self):
        # Original RUE pp.347–348: Assassin7 KO17–20,10 critical19–20,12 death19–20.
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides: 4)
            hero = app.create()
            hero = app.select_combat(hero['id'], revision=0, choices={'hand_to_hand':'assassin'})
            hero = app.generate_resources(hero['id'], revision=hero['revision'])
            hero = app.advance(hero['id'], revision=hero['revision'], method='level', value=12)
            conditions = app.combat_view(hero['id'])['conditions']
            self.assertEqual(conditions['critical']['natural_min'], 19)
            self.assertEqual(conditions['knockout']['natural_min'], 17)
            self.assertEqual(conditions['death_blow']['natural_min'], 19)
            fields = PdfReader(BytesIO(app.export_pdf(hero['id']))).get_fields()
            assert fields is not None
            # The reference artwork supplies the final 20 after this field.
            self.assertEqual(fields['CRITICAL STRIKE']['/V'], 'Natural 19–')
            self.assertEqual(fields['COMBAT KNOCK OUT']['/V'], 'Natural 17–20')
            self.assertEqual(fields['DEATH']['/V'], 'Natural 19–20')
            hero = app.select_combat(hero['id'], revision=hero['revision'], choices={'hand_to_hand':'expert'})
            conditions = app.combat_view(hero['id'])['conditions']
            self.assertEqual(conditions['critical']['natural_min'], 20)
            self.assertNotIn('knockout', conditions)
            self.assertNotIn('death_blow', conditions)
            fields = PdfReader(BytesIO(app.export_pdf(hero['id']))).get_fields()
            assert fields is not None
            self.assertEqual(fields['CRITICAL STRIKE']['/V'], 'Natural')
