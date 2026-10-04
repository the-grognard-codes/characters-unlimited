import tempfile
import copy
import unittest
from io import BytesIO
from pypdf import PdfReader
from characters_unlimited.application import CharacterApplication
from characters_unlimited.rules import RuleArchive


class HeroesMentalEnduranceTests(unittest.TestCase):
    def test_chosen_mental_endurance_records_two_dice_and_explains_specific_saves(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides:4)
            hero = app.create(game='heroes-unlimited')
            hero = app.select_hero_powers(hero['id'], revision=0, selections=['extraordinary-mental-endurance'])
            self.assertEqual(hero['attributes']['ME']['value'],29)
            view = app.hero_powers_view(hero['id'])
            self.assertEqual(view['powers'][0]['rolls'],[4,4])
            self.assertEqual(view['powers'][0]['target'],29)
            saves = view['saving_bonuses']
            self.assertEqual(saves['psionics']['value'],7)
            self.assertEqual(saves['psionics']['target'],12)
            self.assertEqual(saves['insanity']['value'],12)
            self.assertEqual(saves['mind-altering-drugs']['value'],6)
            self.assertEqual(saves['horror-factor']['value'],6)
            self.assertEqual(saves['possession']['value'],13)
            self.assertEqual(saves['magical-illusions']['value'],1)

    def test_existing_affinity_character_explicitly_updates_power_rules_without_rerolling(self):
        with tempfile.TemporaryDirectory() as directory:
            archive = RuleArchive.load()
            legacy = RuleArchive(archive.definitions(),{**archive.active_versions(),'heroes-super-abilities':'1.0.0'})
            earlier = CharacterApplication(directory,die=lambda sides:4,rule_archive=legacy)
            hero = earlier.create(game='heroes-unlimited')
            hero = earlier.select_hero_powers(hero['id'],revision=0,selections=['extraordinary-mental-affinity'])
            current = CharacterApplication(directory,die=lambda sides:4)
            self.assertEqual(len(current.hero_powers_view(hero['id'])['catalog']),1)
            preview = current.preview_rule_upgrade(hero['id'])
            self.assertIn({'pack_id':'heroes-super-abilities','from':'1.0.0','to':'1.2.0'},preview['changes'])
            self.assertEqual(current.get(hero['id']),hero)
            updated = current.apply_rule_upgrade(hero['id'],revision=hero['revision'],token=preview['token'])['character']
            self.assertEqual(updated['attributes'],hero['attributes'])
            self.assertEqual(updated['hero_powers'],hero['hero_powers'])
            updated = current.select_hero_powers(hero['id'],revision=updated['revision'],selections=['extraordinary-mental-affinity','extraordinary-mental-endurance'])
            self.assertEqual([row['rolls'] for row in updated['hero_powers']['acquisitions']],[[4],[4,4]])

    def test_editable_sheet_keeps_bonus_and_target_separate(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory,die=lambda sides:4)
            hero = app.create(game='heroes-unlimited')
            hero = app.select_hero_powers(hero['id'],revision=0,selections=['extraordinary-mental-endurance'])
            fields = PdfReader(BytesIO(app.export_pdf(hero['id']))).get_fields()
            assert fields is not None
            self.assertEqual(fields['SAVE_PSIONICS']['/V'],'+7; target 12')
            self.assertEqual(fields['SAVE_INSANITY']['/V'],'+12')
            text = '\n'.join(str(row.get('/V','')) for row in fields.values())
            self.assertIn('Mind-altering drugs: +6',text)
            self.assertIn('Magical illusions: +1',text)

    def test_higher_manual_scores_and_reselection_retain_the_acquisition(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory,die=lambda sides:4)
            hero = app.create(game='heroes-unlimited')
            hero = app.select_hero_powers(hero['id'],revision=0,selections=['extraordinary-mental-endurance'])
            receipt = copy.deepcopy(hero['hero_powers']['acquisitions'])
            hero = app.set_attribute(hero['id'],revision=hero['revision'],attribute='ME',mode='adjustment',value=5)
            self.assertEqual(hero['attributes']['ME']['value'],34)
            self.assertEqual(app.hero_powers_view(hero['id'])['saving_bonuses']['psionics']['value'],8)
            hero = app.set_attribute(hero['id'],revision=hero['revision'],attribute='ME',mode='fixed',value=40)
            self.assertEqual(hero['attributes']['ME']['value'],40)
            self.assertEqual(app.hero_powers_view(hero['id'])['saving_bonuses']['insanity']['value'],13)
            hero = app.select_hero_powers(hero['id'],revision=hero['revision'],selections=[])
            app.die = lambda sides: self.fail('Reselection must reuse power dice')
            hero = app.select_hero_powers(hero['id'],revision=hero['revision'],selections=['extraordinary-mental-endurance'])
            self.assertEqual(hero['hero_powers']['acquisitions'],receipt)
            self.assertEqual(hero['attributes']['ME']['value'],40)
            imported = app.import_character(app.export_character(hero['id']))
            self.assertEqual(app.hero_powers_view(imported['id'])['saving_bonuses'],app.hero_powers_view(hero['id'])['saving_bonuses'])
            reopened = CharacterApplication(directory)
            self.assertEqual(reopened.get(hero['id']),hero)

    def test_invalid_d4s_and_changed_acquired_power_updates_reject_without_saving(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory,die=lambda sides:4)
            hero = app.create(game='heroes-unlimited')
            for invalid in (0,5,True,1.5):
                app.die = lambda sides:invalid
                with self.assertRaises(ValueError):
                    app.select_hero_powers(hero['id'],revision=0,selections=['extraordinary-mental-endurance'])
                self.assertEqual(app.get(hero['id']),hero)
            app.die = lambda sides:4
            hero = app.select_hero_powers(hero['id'],revision=0,selections=['extraordinary-mental-endurance'])
            bundle = app.export_character(hero['id'])
            bad = copy.deepcopy(bundle)
            bad['character']['hero_powers']['acquisitions'][0]['rolls']=[4]
            with self.assertRaises(ValueError):app.import_character(bad)
            archive = RuleArchive.load()
            definitions = archive.definitions()
            changed = copy.deepcopy(archive.active('heroes-super-abilities'))
            changed['version']='1.3.0'
            changed['powers'][1]['attribute_floor']['constant']=23
            incompatible = RuleArchive([*definitions,changed],{**archive.active_versions(),'heroes-super-abilities':'1.3.0'})
            current = CharacterApplication(directory,rule_archive=incompatible)
            with self.assertRaisesRegex(ValueError,'acquired power'):
                current.preview_rule_upgrade(hero['id'])
            self.assertEqual(current.get(hero['id']),hero)
