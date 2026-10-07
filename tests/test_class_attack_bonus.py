"""Class actions stay distinct from retained Hand to Hand training."""
import tempfile
import unittest
from characters_unlimited.application import CharacterApplication
from characters_unlimited.recorded_formulas import MAX_INTEGER
from tests.test_owned_class_profiles import owned_pack, archive_with


class ClassAttackBonusTests(unittest.TestCase):
    def fixture(self, amount=1):
        pack = owned_pack()
        rules = pack['class_profiles']['vagabond']['class_bonuses']
        rules['combat'] = {'attacks': amount}
        rules['source'] = {'book': 'Synthetic class fixture', 'section': 'Additional class action'}
        return archive_with(pack)

    def test_class_action_stacks_with_training_and_survives_no_roll_portability(self):
        with tempfile.TemporaryDirectory() as directory, tempfile.TemporaryDirectory() as copied:
            app = CharacterApplication(directory, die=lambda sides: 3, rule_archive=self.fixture())
            hero = app.create()
            before = app.combat_view(hero['id'])['totals']['attacks']
            self.assertEqual(before['value'], 5)
            self.assertEqual(before['effect_contributions'][0]['amount'], 1)
            self.assertEqual(before['effect_contributions'][0]['id'], 'class:vagabond:combat:attacks')
            hero = app.generate_resources(hero['id'], revision=hero['revision'])
            hero = app.advance(hero['id'], revision=hero['revision'], method='level', value=4)
            after = app.combat_view(hero['id'])['totals']['attacks']
            self.assertEqual(after['value'], 6)
            self.assertEqual(after['effect_contributions'][0]['amount'], 1)
            def no_roll(sides):
                self.fail('Portable retained actions must not draw dice')
            other = CharacterApplication(copied, die=no_roll, rule_archive=self.fixture())
            restored = other.import_character(app.export_character(hero['id']))
            self.assertEqual(other.combat_view(restored['id'])['totals']['attacks'], after)
            reopened = CharacterApplication(copied, die=no_roll, rule_archive=self.fixture())
            self.assertEqual(reopened.combat_view(restored['id'])['totals']['attacks'], after)

    def test_invalid_inactive_attack_amount_rejects_before_dice_and_save(self):
        for amount in (True, MAX_INTEGER + 1, '1'):
            with self.subTest(amount=amount), tempfile.TemporaryDirectory() as directory:
                pack = owned_pack()
                pack['class_profiles']['city-rat']['class_bonuses']['combat'] = {'attacks': amount}
                def no_roll(sides):
                    self.fail('Inactive malformed class must preflight before dice')
                app = CharacterApplication(directory, die=no_roll, rule_archive=archive_with(pack))
                with self.assertRaisesRegex(ValueError, 'city-rat.*class_bonuses'):
                    app.create()
                self.assertEqual(app.list(), [])
