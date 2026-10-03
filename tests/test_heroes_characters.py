import copy
import tempfile
import unittest

from characters_unlimited.application import CharacterApplication


class HeroesCharacterWorkflowTests(unittest.TestCase):
    def test_heroes_exceptional_sixes_repeat_and_portable_history_reopens(self):
        with tempfile.TemporaryDirectory() as directory:
            draws = iter([6, 6, 6, 6, 6, 6, 2] + [4] * 24)
            app = CharacterApplication(directory, die=lambda sides: next(draws))
            hero = app.create(name='Beacon', game='heroes-unlimited')
            self.assertEqual(hero['character_class'], 'mutant')
            self.assertEqual(hero['attributes']['IQ']['bonus_rolls'], [6, 6, 6, 2])
            self.assertEqual(hero['attributes']['IQ']['base'], 38)
            self.assertEqual(hero['attributes']['IQ']['value'], 30)
            self.assertEqual(hero['additional_rule_packs'], {})
            reopened = CharacterApplication(directory).get(hero['id'])
            self.assertEqual(reopened['attributes'], hero['attributes'])
            imported = app.import_character(app.export_character(hero['id']))
            self.assertEqual(imported['attributes'], hero['attributes'])
            self.assertNotEqual(imported['id'], hero['id'])
            fixed = app.set_attribute(hero['id'], revision=0, attribute='IQ', mode='fixed', value=42)
            rerolled = app.reroll(fixed['id'], revision=1, attribute='IQ')
            self.assertEqual(rerolled['attributes']['IQ']['value'], 42)
            self.assertEqual(len(rerolled['roll_history']), 2)
            self.assertEqual(app.import_character(app.export_character(rerolled['id']))['attributes']['IQ']['value'], 42)
            with self.assertRaisesRegex(ValueError, 'Heroes'):
                app.select_skills(hero['id'], revision=0, selections=[{'skill_id':'cook','pool':'domestic'}])
            with self.assertRaisesRegex(ValueError, 'game'):
                app.create(game='heroes-unlimited', character_class='vagabond')

    def test_heroes_house_rules_and_manual_values_do_not_change_bonus_dice(self):
        with tempfile.TemporaryDirectory() as directory:
            draws = iter([1, 1, 6, 6, 6, 2, 6, 1] + [4] * 28)
            app = CharacterApplication(directory, die=lambda sides: next(draws))
            hero = app.create(game='heroes-unlimited', generation={'reroll_ones':True,'extra_die':True})
            iq = hero['attributes']['IQ']
            self.assertEqual(iq['kept'], [6, 6, 6])
            self.assertEqual(iq['discarded'], [2])
            self.assertEqual(iq['bonus_rolls'], [6, 1])
            changed = app.set_attribute(hero['id'], revision=0, attribute='IQ', mode='fixed', value=19)
            imported = app.import_character(app.export_character(changed['id']))
            self.assertEqual(imported['attributes']['IQ']['value'], 19)
            self.assertEqual(imported['attributes']['IQ']['bonus_rolls'], [6, 1])
            bad = copy.deepcopy(app.export_character(changed['id']))
            bad['character']['additional_rule_packs'] = {'rifts-domestic-skills':'1.8.0'}
            with self.assertRaisesRegex(ValueError, 'game'):
                app.import_character(bad)

    def test_normal_mortal_caps_keep_raw_totals_and_allow_manual_adjustments(self):
        with tempfile.TemporaryDirectory() as directory:
            chain = [6, 6, 6] + [6] * 8 + [2]
            draws = iter(chain * 8)
            app = CharacterApplication(directory, die=lambda sides: next(draws))
            hero = app.create(game='heroes-unlimited')
            for attribute, cap in {'IQ':30,'ME':30,'MA':30,'PB':30,'PS':40,'PP':50}.items():
                self.assertEqual(hero['attributes'][attribute]['base'], 68)
                self.assertEqual(hero['attributes'][attribute]['value'], cap)
            self.assertEqual(hero['attributes']['PE']['value'], 68)
            self.assertEqual(hero['attributes']['SPD']['value'], 68)
            adjusted = app.set_attribute(hero['id'], revision=0, attribute='ME', mode='adjustment', value=5)
            self.assertEqual(adjusted['attributes']['ME']['value'], 35)
            bundle = app.export_character(hero['id'])
            self.assertEqual(app.import_character(bundle)['attributes']['ME']['value'], 35)
            bad = copy.deepcopy(bundle)
            bad['character']['attributes']['IQ']['cap'] = 40
            with self.assertRaisesRegex(ValueError, 'ceiling'):
                app.import_character(bad)

    def test_broken_exceptional_source_saves_nothing(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides: 6)
            with self.assertRaisesRegex(ValueError, 'failed to finish'):
                app.create(game='heroes-unlimited')
            self.assertEqual(app.list(), [])
