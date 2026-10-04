import copy
import tempfile
import unittest
from io import BytesIO
from pypdf import PdfReader

from characters_unlimited.application import CharacterApplication
from characters_unlimited.storage import SaveConflict


class HeroesPowerTests(unittest.TestCase):
    def test_inactive_power_receipts_remain_visible_and_require_selection_history(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides:4)
            hero = app.create(game='heroes-unlimited')
            hero = app.select_hero_powers(hero['id'], revision=0, selections=['extraordinary-mental-affinity'])
            hero = app.select_hero_powers(hero['id'], revision=hero['revision'], selections=[])
            bad = copy.deepcopy(app.export_character(hero['id']))
            bad['character']['hero_powers']['history'] = [[]]
            with self.assertRaises(ValueError):
                app.import_character(bad)
            receipt = app.hero_powers_view(hero['id'])['receipts'][0]
            self.assertFalse(receipt['active'])
            self.assertEqual((receipt['target'],receipt['rolls']), (28,[4]))
            fields = PdfReader(BytesIO(app.export_pdf(hero['id']))).get_fields()
            assert fields is not None
            self.assertIn('Retained inactive power: Extraordinary Mental Affinity', '\n'.join(str(field.get('/V','')) for field in fields.values()))

    def test_mortal_seduction_attribute_bonuses_stop_at_thirty_after_manual_edits(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides:4)
            hero = app.create(game='heroes-unlimited')
            hero = app.select_education(hero['id'], revision=0, method='choose', education_id='high-school')
            hero = app.select_hero_secondary(hero['id'], revision=hero['revision'], selections=['seduction'])
            hero = app.select_hero_powers(hero['id'], revision=hero['revision'], selections=['extraordinary-mental-affinity'])
            for attribute in ('MA','PB'):
                hero = app.set_attribute(hero['id'], revision=hero['revision'], attribute=attribute, mode='fixed', value=100)
            skill = next(row for row in app.hero_program_view(hero['id'])['skills'] if row['id']=='seduction')
            self.assertEqual(skill['percentage'], 46)
            self.assertEqual(hero['attributes']['MA']['value'], 100)
            self.assertEqual(app.hero_powers_view(hero['id'])['trust_intimidate'], 97)

    def test_power_and_seduction_attribute_bonuses_stack_once_on_selected_skills(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides:4)
            hero = app.create(game='heroes-unlimited')
            hero = app.select_education(hero['id'], revision=0, method='choose', education_id='high-school')
            hero = app.select_hero_secondary(hero['id'], revision=hero['revision'], selections=['pick-pockets','seduction'])
            hero = app.select_hero_powers(hero['id'], revision=hero['revision'], selections=['extraordinary-mental-affinity'])
            skills = {row['id']:row for row in app.hero_program_view(hero['id'])['skills']}
            self.assertEqual(skills['pick-pockets']['percentage'], 35)
            self.assertEqual(skills['pick-pockets']['additional_checks'][0]['percentage'], 40)
            self.assertEqual(skills['seduction']['percentage'], 38)
            self.assertEqual(skills['seduction']['additional_checks'][0]['percentage'], 43)
            self.assertEqual(skills['seduction']['contributions']['Extraordinary Mental Affinity'], 10)
            self.assertEqual(skills['seduction']['contributions']['Seduction M.A.'], 8)
            hero = app.set_attribute(hero['id'], revision=hero['revision'], attribute='PB', mode='fixed', value=23)
            self.assertEqual(next(row for row in app.hero_program_view(hero['id'])['skills'] if row['id']=='seduction')['percentage'], 41)
            hero = app.select_hero_powers(hero['id'], revision=hero['revision'], selections=[])
            skills = {row['id']:row for row in app.hero_program_view(hero['id'])['skills']}
            self.assertEqual(skills['pick-pockets']['percentage'], 25)
            self.assertEqual(skills['seduction']['percentage'], 23)
            self.assertNotIn('Extraordinary Mental Affinity', skills['seduction']['contributions'])
            self.assertNotIn('Extraordinary Mental Affinity', skills['mathematics-basic']['contributions'])

    def test_chosen_extraordinary_affinity_preserves_its_target_and_manual_values(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides:4)
            hero = app.create(game='heroes-unlimited')
            hero = app.select_power_budget(hero['id'], revision=0, method='choose', outcome_id='four-minor')
            hero = app.select_hero_powers(hero['id'], revision=hero['revision'], selections=['extraordinary-mental-affinity'])
            self.assertEqual(hero['attributes']['MA']['value'], 28)
            view = app.hero_powers_view(hero['id'])
            self.assertEqual(view['trust_intimidate'], 94)
            self.assertEqual(view['minor'], {'used':1, 'allowance':4, 'remaining':3})
            self.assertEqual(view['powers'][0]['target'], 28)
            self.assertEqual(view['powers'][0]['rolls'], [4])
            hero = app.set_attribute(hero['id'], revision=hero['revision'], attribute='MA', mode='fixed', value=19)
            self.assertEqual(app.hero_powers_view(hero['id'])['trust_intimidate'], 55)
            self.assertEqual(app.import_character(app.export_character(hero['id']))['hero_powers'], hero['hero_powers'])

    def test_rerolls_and_removal_reselection_keep_the_higher_score_and_recorded_target(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides:4)
            hero = app.create(game='heroes-unlimited')
            hero = app.select_hero_powers(hero['id'], revision=0, selections=['extraordinary-mental-affinity'])
            acquisition = copy.deepcopy(hero['hero_powers']['acquisitions'])
            dice = iter([6,6,6,6,6,5])
            app.die = lambda sides:next(dice)
            hero = app.reroll(hero['id'], revision=hero['revision'], attribute='MA')
            self.assertEqual(hero['attributes']['MA']['value'], 30)
            self.assertEqual(app.hero_powers_view(hero['id'])['trust_intimidate'], 97)
            hero = app.select_hero_powers(hero['id'], revision=hero['revision'], selections=[])
            self.assertEqual(hero['attributes']['MA']['value'], 30)
            self.assertEqual(hero['attributes']['MA']['modifiers'], [])
            app.die = lambda sides: self.fail('Reselecting a retained power must not roll again')
            hero = app.select_hero_powers(hero['id'], revision=hero['revision'], selections=['extraordinary-mental-affinity'])
            self.assertEqual(hero['hero_powers']['acquisitions'], acquisition)
            self.assertEqual(hero['attributes']['MA']['value'], 30)
            self.assertEqual(len(hero['hero_powers']['history']), 3)
            imported = app.import_character(app.export_character(hero['id']))
            self.assertEqual(imported['hero_powers'], hero['hero_powers'])
            self.assertEqual(CharacterApplication(directory).hero_powers_view(hero['id'])['powers'][0]['target'], 28)
            self.assertEqual(app.duplicate(hero['id'])['hero_powers'], hero['hero_powers'])

    def test_bad_dice_stale_writes_and_tampered_sources_reject_atomically(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides:4)
            hero = app.create(game='heroes-unlimited')
            for face in (0,7,True,2.5):
                app.die = lambda sides:face
                with self.assertRaises(ValueError):
                    app.select_hero_powers(hero['id'], revision=0, selections=['extraordinary-mental-affinity'])
                self.assertEqual(app.get(hero['id']), hero)
            app.die = lambda sides:4
            hero = app.select_hero_powers(hero['id'], revision=0, selections=['extraordinary-mental-affinity'])
            with self.assertRaises(SaveConflict):
                app.select_hero_powers(hero['id'], revision=0, selections=[])
            for change in ('die','source','duplicate','history','floor','pin'):
                bad = copy.deepcopy(app.export_character(hero['id']))
                record = bad['character']['hero_powers']
                if change == 'die':
                    record['acquisitions'][0]['rolls'] = [7]
                elif change == 'source':
                    record['acquisitions'][0]['source']['printed_page'] = 1
                elif change == 'duplicate':
                    record['acquisitions'].append(copy.deepcopy(record['acquisitions'][0]))
                elif change == 'history':
                    record['history'][-1] = []
                elif change == 'floor':
                    bad['character']['attributes']['MA']['modifiers'] = []
                    bad['character']['attributes']['MA']['value'] = 12
                else:
                    bad['character']['additional_rule_packs'] = {}
                with self.assertRaises(ValueError):
                    app.import_character(bad)
                self.assertEqual(len(app.list()), 1)
            rifts = app.create()
            with self.assertRaisesRegex(ValueError,'Heroes'):
                app.select_hero_powers(rifts['id'], revision=0, selections=[])

    def test_allowance_warnings_and_editable_pdf_explain_the_power(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides:4)
            hero = app.create(game='heroes-unlimited')
            hero = app.select_power_budget(hero['id'], revision=0, method='choose', outcome_id='two-major')
            hero = app.select_hero_powers(hero['id'], revision=hero['revision'], selections=['extraordinary-mental-affinity'])
            self.assertEqual(app.hero_powers_view(hero['id'])['minor'], {'used':1,'allowance':0,'remaining':-1})
            self.assertTrue(any('exceed' in line for line in app.hero_powers_view(hero['id'])['warnings']))
            fields = PdfReader(BytesIO(app.export_pdf(hero['id']))).get_fields()
            assert fields is not None
            values = '\n'.join(str(field.get('/V','')) for field in fields.values())
            self.assertIn('Extraordinary Mental Affinity: recorded target 28', values)
            self.assertIn('trust/intimidate: 94%', values)
