import tempfile, unittest
from characters_unlimited.application import CharacterApplication

class HeroesAdditionalSecondaryTests(unittest.TestCase):
    def test_reviewed_secondaries_use_own_bases_no_education_bonus_and_half_repair_context(self):
        with tempfile.TemporaryDirectory() as directory:
            app=CharacterApplication(directory,die=lambda sides:4)
            hero=app.create(game='heroes-unlimited')
            hero=app.select_education(hero['id'],revision=0,method='choose',education_id='doctorate')
            hero=app.set_attribute(hero['id'],revision=hero['revision'],attribute='IQ',mode='fixed',value=16)
            hero=app.select_hero_secondary(hero['id'],revision=hero['revision'],selections=['ventriloquism','art','photography','general-repair-maintenance'])
            view=app.hero_program_view(hero['id'])
            skills={row['id']:row for row in view['skills']}
            self.assertEqual(skills['ventriloquism']['percentage'],18)
            for name in ['art','photography','general-repair-maintenance']:
                self.assertEqual(skills[name]['percentage'],37)
                self.assertEqual(skills[name]['contributions']['education'],0)
                self.assertEqual(skills[name]['per_level'],5)
            repair=skills['general-repair-maintenance']['additional_checks'][0]
            self.assertEqual(repair['percentage'],18.5)
            self.assertEqual(repair['per_level'],2.5)
            self.assertEqual(view['secondary']['used'],4)
            self.assertFalse(any('outside' in warning for warning in view['warnings']))

    def test_deception_power_applies_only_to_acquired_ventriloquism_and_is_reversible(self):
        with tempfile.TemporaryDirectory() as directory:
            app=CharacterApplication(directory,die=lambda sides:4)
            hero=app.create(game='heroes-unlimited')
            hero=app.select_education(hero['id'],revision=0,method='choose',education_id='high-school')
            hero=app.set_attribute(hero['id'],revision=hero['revision'],attribute='IQ',mode='fixed',value=16)
            choices=['ventriloquism','art','photography','general-repair-maintenance']
            hero=app.select_hero_secondary(hero['id'],revision=hero['revision'],selections=choices)
            hero=app.select_hero_powers(hero['id'],revision=hero['revision'],selections=['extraordinary-mental-affinity','extraordinary-physical-beauty'])
            skills={row['id']:row for row in app.hero_program_view(hero['id'])['skills']}
            self.assertEqual(skills['ventriloquism']['percentage'],28)
            self.assertNotIn('Extraordinary Physical Beauty',skills['ventriloquism']['contributions'])
            self.assertEqual(skills['art']['percentage'],37)
            self.assertEqual(skills['general-repair-maintenance']['additional_checks'][0]['percentage'],18.5)
            hero=app.select_hero_powers(hero['id'],revision=hero['revision'],selections=[])
            skills={row['id']:row for row in app.hero_program_view(hero['id'])['skills']}
            self.assertEqual(skills['ventriloquism']['percentage'],18)
            hero=app.select_hero_secondary(hero['id'],revision=hero['revision'],selections=[])
            self.assertFalse(any(row['id']=='ventriloquism' for row in app.hero_program_view(hero['id'])['skills']))

    def test_exact_legacy_pins_require_explicit_update_and_portable_pdf_preserves_fraction(self):
        from characters_unlimited.rules import RuleArchive
        from io import BytesIO
        from pypdf import PdfReader
        with tempfile.TemporaryDirectory() as directory:
            archive=RuleArchive.load()
            legacy=RuleArchive(archive.definitions(),{**archive.active_versions(),'heroes-program-skills':'1.9.0'})
            old=CharacterApplication(directory,die=lambda sides:4,rule_archive=legacy)
            hero=old.create(game='heroes-unlimited')
            hero=old.select_education(hero['id'],revision=0,method='choose',education_id='high-school')
            hero=old.select_hero_secondary(hero['id'],revision=hero['revision'],selections=['palming'])
            app=CharacterApplication(directory,die=lambda sides:4)
            with self.assertRaises(ValueError):app.select_hero_secondary(hero['id'],revision=hero['revision'],selections=['art'])
            self.assertEqual(app.get(hero['id']),hero)
            imported_old=app.import_character(app.export_character(hero['id']))
            self.assertEqual(imported_old['additional_rule_packs']['heroes-program-skills'],'1.9.0')
            preview=app.preview_rule_upgrade(hero['id'])
            self.assertEqual(app.get(hero['id']),hero)
            self.assertIn({'pack_id':'heroes-program-skills','from':'1.9.0','to':'1.19.0'},preview['changes'])
            hero=app.apply_rule_upgrade(hero['id'],revision=hero['revision'],token=preview['token'])['character']
            hero=app.select_hero_secondary(hero['id'],revision=hero['revision'],selections=['art','photography','general-repair-maintenance','ventriloquism'])
            view=app.hero_program_view(hero['id'])
            restored=app.import_character(app.export_character(hero['id']))
            self.assertEqual(app.hero_program_view(restored['id'])['skills'],view['skills'])
            self.assertEqual(CharacterApplication(directory).get(hero['id']),hero)
            fields=PdfReader(BytesIO(app.export_pdf(hero['id']))).get_fields()
            assert fields is not None
            self.assertEqual(fields['skills.general-repair-maintenance.percentage']['/V'],'35')
            self.assertEqual(fields['skills.general-repair-maintenance.check0.percentage']['/V'],'17.5')
            self.assertEqual(fields['skills.ventriloquism.percentage']['/V'],'16')
