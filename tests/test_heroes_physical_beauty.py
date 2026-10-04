import tempfile
import unittest
from io import BytesIO
from pypdf import PdfReader
from characters_unlimited.application import CharacterApplication
from characters_unlimited.rules import RuleArchive


class HeroesPhysicalBeautyTests(unittest.TestCase):
    def test_chosen_beauty_records_two_dice_and_charm_percentage(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory,die=lambda sides:4)
            hero = app.create(game='heroes-unlimited')
            hero = app.select_hero_powers(hero['id'],revision=0,selections=['extraordinary-physical-beauty'])
            self.assertEqual(hero['attributes']['PB']['value'],28)
            view = app.hero_powers_view(hero['id'])
            self.assertEqual(view['charm_impress'],86)
            self.assertEqual(view['powers'][0]['rolls'],[4,4])
            self.assertEqual(view['powers'][0]['target'],28)

    def test_named_power_bonuses_and_palming_synergy_stack_once(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory,die=lambda sides:4)
            hero = app.create(game='heroes-unlimited')
            hero = app.select_education(hero['id'],revision=0,method='choose',education_id='high-school')
            hero = app.select_hero_secondary(hero['id'],revision=hero['revision'],selections=['palming','pick-pockets','seduction'])
            hero = app.select_hero_powers(hero['id'],revision=hero['revision'],selections=['extraordinary-mental-affinity','extraordinary-physical-beauty'])
            skills = {row['id']:row for row in app.hero_program_view(hero['id'])['skills']}
            self.assertEqual(skills['palming']['percentage'],40)
            self.assertEqual(skills['palming']['additional_checks'][0]['percentage'],45)
            self.assertEqual(skills['pick-pockets']['percentage'],50)
            self.assertEqual(skills['seduction']['percentage'],53)
            self.assertEqual(skills['pick-pockets']['contributions']['Palming'],5)
            self.assertNotIn('Extraordinary Physical Beauty',skills['mathematics-basic']['contributions'])

    def test_beauty_does_not_grant_skills_and_adds_ten_to_acquired_research(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory,die=lambda sides:4)
            hero = app.create(game='heroes-unlimited')
            hero = app.select_hero_powers(hero['id'],revision=0,selections=['extraordinary-physical-beauty'])
            self.assertNotIn('research',{row['id'] for row in app.hero_program_view(hero['id'])['skills']})
            hero = app.select_education(hero['id'],revision=hero['revision'],method='choose',education_id='college-one')
            hero = app.select_hero_programs(hero['id'],revision=hero['revision'],selections=[{'slot':0,'program':'business'}])
            skills = {row['id']:row for row in app.hero_program_view(hero['id'])['skills']}
            self.assertEqual(skills['research']['percentage'],70)
            self.assertEqual(skills['research']['contributions']['Extraordinary Physical Beauty'],10)
            fields = PdfReader(BytesIO(app.export_pdf(hero['id']))).get_fields()
            assert fields is not None
            text = '\n'.join(str(row.get('/V','')) for row in fields.values())
            self.assertIn('charm/impress: 86%',text)
            self.assertIn('Extraordinary Physical Beauty',text)
            self.assertEqual(fields['skills.research.percentage']['/V'],'70')

    def test_fixed_beauty_scores_keep_precedence_and_bonus_cap_without_rerolling(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory,die=lambda sides:4)
            hero = app.create(game='heroes-unlimited')
            hero = app.select_hero_powers(hero['id'],revision=0,selections=['extraordinary-physical-beauty'])
            receipt = hero['hero_powers']['acquisitions']
            hero = app.set_attribute(hero['id'],revision=hero['revision'],attribute='PB',mode='fixed',value=40)
            self.assertEqual(hero['attributes']['PB']['value'],40)
            self.assertEqual(app.hero_powers_view(hero['id'])['charm_impress'],92)
            hero = app.select_hero_powers(hero['id'],revision=hero['revision'],selections=[])
            app.die = lambda sides:self.fail('Power reselection must retain dice')
            hero = app.select_hero_powers(hero['id'],revision=hero['revision'],selections=['extraordinary-physical-beauty'])
            self.assertEqual(hero['hero_powers']['acquisitions'],receipt)
            hero = app.set_attribute(hero['id'],revision=hero['revision'],attribute='PB',mode='fixed',value=10)
            self.assertIsNone(app.hero_powers_view(hero['id'])['charm_impress'])
            imported = app.import_character(app.export_character(hero['id']))
            self.assertEqual(imported['hero_powers'],hero['hero_powers'])
            self.assertEqual(CharacterApplication(directory).get(hero['id']),hero)

    def test_existing_pins_preview_new_charm_and_palming_before_explicit_update(self):
        with tempfile.TemporaryDirectory() as directory:
            archive = RuleArchive.load()
            legacy = RuleArchive(archive.definitions(),{**archive.active_versions(),'heroes-super-abilities':'1.1.0','heroes-program-skills':'1.7.0'})
            earlier = CharacterApplication(directory,die=lambda sides:4,rule_archive=legacy)
            hero = earlier.create(game='heroes-unlimited')
            hero = earlier.select_education(hero['id'],revision=0,method='choose',education_id='high-school')
            hero = earlier.select_hero_secondary(hero['id'],revision=hero['revision'],selections=['pick-pockets'])
            hero = earlier.select_hero_powers(hero['id'],revision=hero['revision'],selections=['extraordinary-mental-affinity'])
            hero = earlier.set_attribute(hero['id'],revision=hero['revision'],attribute='PB',mode='fixed',value=28)
            current = CharacterApplication(directory,die=lambda sides:4)
            self.assertIsNone(current.hero_powers_view(hero['id'])['charm_impress'])
            preview = current.preview_rule_upgrade(hero['id'])
            self.assertIn({'name':'Charm/impress (%)','before':None,'after':86},preview['combat'])
            self.assertEqual(current.get(hero['id']),hero)
            updated = current.apply_rule_upgrade(hero['id'],revision=hero['revision'],token=preview['token'])['character']
            self.assertEqual(updated['hero_powers'],hero['hero_powers'])
            self.assertEqual(updated['attributes'],hero['attributes'])
            updated = current.select_hero_secondary(hero['id'],revision=updated['revision'],selections=['pick-pockets','palming'])
            updated = current.select_hero_powers(hero['id'],revision=updated['revision'],selections=['extraordinary-mental-affinity','extraordinary-physical-beauty'])
            self.assertEqual(current.hero_powers_view(hero['id'])['charm_impress'],86)
            self.assertEqual(updated['hero_powers']['acquisitions'][0],hero['hero_powers']['acquisitions'][0])
