"""Source-permitted power kicks and the user-confirmed damage interpretation."""

from io import BytesIO
import tempfile
import unittest
from pypdf import PdfReader
from characters_unlimited.application import CharacterApplication
from characters_unlimited.rules import RuleArchive


class PowerKickTests(unittest.TestCase):
    def test_assassin_power_kicks_double_dice_and_add_both_bonuses_once(self):
        with tempfile.TemporaryDirectory() as directory:
            app=CharacterApplication(directory,die=lambda sides:4)
            hero=app.create(character_class='city-rat')
            self.assertNotIn('power-kick',{move['id'] for move in app.combat_view(hero['id'])['unarmed']})
            hero=app.select_combat(hero['id'],revision=hero['revision'],choices={'hand_to_hand':'assassin'})
            hero=app.generate_resources(hero['id'],revision=hero['revision'])
            hero=app.set_attribute(hero['id'],revision=hero['revision'],attribute='PS',mode='fixed',value=20)
            hero=app.advance(hero['id'],revision=hero['revision'],method='level',value=4)
            moves={move['id']:move for move in app.combat_view(hero['id'])['unarmed']}
            self.assertEqual(moves['power-kick']['damage'],'2 × 1D8 + 9 S.D.C.')
            self.assertEqual(moves['power-karate-kick']['damage'],'2 × 2D6 + 9 S.D.C.')
            self.assertEqual(moves['power-kick']['actions'],2)
            self.assertEqual(moves['power-karate-kick']['actions'],2)
            self.assertNotIn('power-knee',moves)
            self.assertNotIn('power-body-flip',moves)
            fields=PdfReader(BytesIO(app.export_pdf(hero['id']))).get_fields()
            assert fields is not None
            values=' '.join(str(field.get('/V','')) for field in fields.values())
            self.assertIn('Power kick: 2 × 1D8 + 9',values)
            self.assertIn('Power karate kick: 2 × 2D6 + 9',values)
            hero=app.set_attribute(hero['id'],revision=hero['revision'],attribute='PS',mode='fixed',value=4)
            weak={move['id']:move for move in app.combat_view(hero['id'])['unarmed']}
            self.assertEqual(weak['power-karate-kick']['damage'],'½ × (2 × 2D6 + 4) S.D.C.')
            hero=app.set_attribute(hero['id'],revision=hero['revision'],attribute='PS',mode='fixed',value=20)
            hero=app.advance(hero['id'],revision=hero['revision'],method='level',value=7)
            moves={move['id']:move for move in app.combat_view(hero['id'])['unarmed']}
            self.assertEqual(moves['leap-kick']['damage'],'3D8 + 9 S.D.C.')
            self.assertNotIn('power-leap-kick',moves)
            reopened=CharacterApplication(directory)
            imported=reopened.import_character(reopened.export_character(hero['id']))
            self.assertEqual(reopened.combat_view(imported['id'])['unarmed'],list(moves.values()))
            hero=reopened.undo_advancement(hero['id'],revision=hero['revision'])['character']
            self.assertNotIn('leap-kick',{move['id'] for move in reopened.combat_view(hero['id'])['unarmed']})

    def test_old_pin_preview_and_historical_undo_preserve_recorded_dice(self):
        with tempfile.TemporaryDirectory() as directory:
            archive=RuleArchive.load()
            old=RuleArchive(archive.definitions(),{**archive.active_versions(),'rifts-domestic-skills':'2.11.0'})
            previous=CharacterApplication(directory,die=lambda sides:4,rule_archive=old)
            hero=previous.create()
            hero=previous.select_combat(hero['id'],revision=hero['revision'],choices={'hand_to_hand':'assassin'})
            hero=previous.generate_resources(hero['id'],revision=hero['revision'])
            hero=previous.advance(hero['id'],revision=hero['revision'],method='level',value=4)
            current=CharacterApplication(directory,die=lambda sides:self.fail('Update must not reroll'))
            self.assertNotIn('power-kick',{move['id'] for move in current.combat_view(hero['id'])['unarmed']})
            preview=current.preview_rule_upgrade(hero['id'])
            change=next(row for row in preview['combat'] if row['name']=='Power kick damage')
            self.assertIsNone(change['before'])
            self.assertEqual(change['after'],'2 × 1D8 + 4 S.D.C.')
            updated=current.apply_rule_upgrade(hero['id'],revision=hero['revision'],token=preview['token'])['character']
            for field in ('attributes','resources','physical_acquisitions','later_advancements','combat_choices'):
                self.assertEqual(updated.get(field),hero.get(field))
            restored=current.undo_advancement(hero['id'],revision=updated['revision'])['character']
            self.assertEqual(restored['additional_rule_packs']['rifts-domestic-skills'],'2.11.0')
            self.assertNotIn('power-kick',{move['id'] for move in current.combat_view(hero['id'])['unarmed']})

    def test_style_unlocks_use_training_age_and_keep_low_strength_explicit(self):
        for style,unlock in [('expert',5),('martial-arts',3),('assassin',4)]:
            with self.subTest(style=style),tempfile.TemporaryDirectory() as directory:
                app=CharacterApplication(directory,die=lambda sides:4)
                hero=app.create()
                hero=app.select_combat(hero['id'],revision=hero['revision'],choices={'hand_to_hand':style})
                hero=app.generate_resources(hero['id'],revision=hero['revision'])
                move_ids={move['id'] for move in app.combat_view(hero['id'])['unarmed']}
                self.assertIn('power-kick',move_ids)
                self.assertNotIn('power-karate-kick',move_ids)
                hero=app.advance(hero['id'],revision=hero['revision'],method='level',value=unlock)
                self.assertIn('power-karate-kick',{move['id'] for move in app.combat_view(hero['id'])['unarmed']})
                hero=app.set_attribute(hero['id'],revision=hero['revision'],attribute='PS',mode='fixed',value=1)
                moves={move['id']:move for move in app.combat_view(hero['id'])['unarmed']}
                self.assertIn('Pending low-strength power-kick',moves['power-kick']['damage'])
                self.assertIn('Pending',moves['power-karate-kick']['damage'])
                self.assertTrue(any('power-punch and power-kick' in gap for gap in app.combat_view(hero['id'])['gaps']))
                hero=app.select_combat(hero['id'],revision=hero['revision'],choices={'hand_to_hand':'basic'})
                self.assertNotIn('power-kick',{move['id'] for move in app.combat_view(hero['id'])['unarmed']})
        with tempfile.TemporaryDirectory() as directory:
            app=CharacterApplication(directory,die=lambda sides:4)
            hero=app.create(level=15)
            hero=app.select_combat(hero['id'],revision=hero['revision'],choices={'hand_to_hand':'expert'})
            move_ids={move['id'] for move in app.combat_view(hero['id'])['unarmed']}
            self.assertIn('power-kick',move_ids)
            self.assertNotIn('power-karate-kick',move_ids)
