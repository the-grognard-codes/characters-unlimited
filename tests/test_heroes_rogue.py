from io import BytesIO
from pypdf import PdfReader
from characters_unlimited.rules import RuleArchive
import tempfile,unittest
from characters_unlimited.application import CharacterApplication

class HeroesRogueTests(unittest.TestCase):
    def test_cardsharp_stacks_palming_and_mental_affinity_with_seduced_context(self):
        with tempfile.TemporaryDirectory() as directory:
            app=CharacterApplication(directory,die=lambda sides:4)
            hero=app.create(game='heroes-unlimited')
            hero=app.select_education(hero['id'],revision=0,method='choose',education_id='high-school')
            hero=app.select_hero_secondary(hero['id'],revision=hero['revision'],selections=['cardsharp','palming','seduction'])
            hero=app.select_hero_powers(hero['id'],revision=hero['revision'],selections=['extraordinary-mental-affinity','extraordinary-physical-beauty'])
            view=app.hero_program_view(hero['id'])
            skill=next(row for row in view['skills'] if row['id']=='cardsharp')
            self.assertEqual(skill['percentage'],38)
            self.assertEqual(skill['contributions']['Palming'],4)
            self.assertNotIn('Extraordinary Physical Beauty',skill['contributions'])
            self.assertEqual(skill['additional_checks'][0]['percentage'],43)
            self.assertEqual(view['secondary']['used'],3)
            self.assertFalse(any('outside' in warning for warning in view['warnings']))

    def test_concealment_keeps_item_bonuses_in_separate_contexts(self):
        with tempfile.TemporaryDirectory() as directory:
            app=CharacterApplication(directory,die=lambda sides:4)
            hero=app.create(game='heroes-unlimited')
            hero=app.select_education(hero['id'],revision=0,method='choose',education_id='doctorate')
            hero=app.set_attribute(hero['id'],revision=hero['revision'],attribute='IQ',mode='fixed',value=16)
            hero=app.select_hero_secondary(hero['id'],revision=hero['revision'],selections=['concealment'])
            hero=app.select_hero_powers(hero['id'],revision=hero['revision'],selections=['extraordinary-mental-affinity','extraordinary-physical-beauty'])
            view=app.hero_program_view(hero['id'])
            skill=next(row for row in view['skills'] if row['id']=='concealment')
            self.assertEqual(skill['percentage'],32)
            self.assertEqual([row['percentage'] for row in skill['additional_checks']],[37,37])
            self.assertEqual(skill['contributions']['education'],0)
            self.assertEqual(skill['contributions']['Extraordinary Mental Affinity'],10)
            self.assertNotIn('Extraordinary Physical Beauty',skill['contributions'])
            self.assertEqual(view['secondary']['used'],1)

    def test_locks_prowl_and_streetwise_use_their_own_source_values(self):
        with tempfile.TemporaryDirectory() as directory:
            app=CharacterApplication(directory,die=lambda sides:4)
            hero=app.create(game='heroes-unlimited')
            hero=app.select_education(hero['id'],revision=0,method='choose',education_id='high-school')
            hero=app.select_hero_secondary(hero['id'],revision=hero['revision'],selections=['pick-locks','prowl','streetwise'])
            hero=app.select_hero_powers(hero['id'],revision=hero['revision'],selections=['extraordinary-mental-affinity','extraordinary-physical-beauty'])
            view=app.hero_program_view(hero['id'])
            skills={row['id']:row for row in view['skills']}
            self.assertEqual(skills['pick-locks']['percentage'],30)
            self.assertEqual(skills['pick-locks']['per_level'],5)
            self.assertEqual(skills['prowl']['percentage'],25)
            self.assertEqual(skills['prowl']['per_level'],5)
            self.assertEqual(skills['streetwise']['percentage'],20)
            self.assertEqual(skills['streetwise']['per_level'],4)
            self.assertEqual(view['secondary']['remaining'],7)

    def test_legacy_update_and_portable_reopening_keep_choices_and_pdf_values(self):
        with tempfile.TemporaryDirectory() as directory:
            archive=RuleArchive.load()
            legacy=RuleArchive(archive.definitions(),{**archive.active_versions(),'heroes-program-skills':'1.8.0'})
            earlier=CharacterApplication(directory,die=lambda sides:4,rule_archive=legacy)
            hero=earlier.create(game='heroes-unlimited')
            hero=earlier.select_education(hero['id'],revision=0,method='choose',education_id='high-school')
            hero=earlier.select_hero_secondary(hero['id'],revision=hero['revision'],selections=['palming','seduction'])
            app=CharacterApplication(directory,die=lambda sides:4)
            with self.assertRaises(ValueError):
                app.select_hero_secondary(hero['id'],revision=hero['revision'],selections=['cardsharp'])
            preview=app.preview_rule_upgrade(hero['id'])
            self.assertEqual(app.get(hero['id']),hero)
            self.assertIn({'pack_id':'heroes-program-skills','from':'1.8.0','to':'1.16.0'},preview['changes'])
            hero=app.apply_rule_upgrade(hero['id'],revision=hero['revision'],token=preview['token'])['character']
            choices=['cardsharp','palming','seduction','concealment','pick-locks','prowl','streetwise']
            hero=app.select_hero_secondary(hero['id'],revision=hero['revision'],selections=choices)
            expected=app.hero_program_view(hero['id'])['skills']
            imported=app.import_character(app.export_character(hero['id']))
            self.assertEqual(app.hero_program_view(imported['id'])['skills'],expected)
            self.assertEqual(CharacterApplication(directory).get(hero['id']),hero)
            fields=PdfReader(BytesIO(app.export_pdf(hero['id']))).get_fields()
            assert fields is not None
            self.assertEqual(fields['skills.cardsharp.percentage']['/V'],'28')
            self.assertEqual(fields['skills.concealment.percentage']['/V'],'20')
            text='\n'.join(str(row.get('/V','')) for row in fields.values())
            self.assertIn('Cardsharp',text)
            self.assertEqual(fields['skills.cardsharp.check0.percentage']['/V'],'33')
            self.assertEqual(fields['skills.concealment.check0.percentage']['/V'],'25')

    def test_removing_synergy_and_context_skills_recalculates_without_power_grants(self):
        with tempfile.TemporaryDirectory() as directory:
            app=CharacterApplication(directory,die=lambda sides:4)
            hero=app.create(game='heroes-unlimited')
            hero=app.select_education(hero['id'],revision=0,method='choose',education_id='high-school')
            hero=app.select_hero_secondary(hero['id'],revision=hero['revision'],selections=['cardsharp','palming','seduction'])
            hero=app.select_hero_secondary(hero['id'],revision=hero['revision'],selections=['cardsharp'])
            card=next(row for row in app.hero_program_view(hero['id'])['skills'] if row['id']=='cardsharp')
            self.assertEqual(card['percentage'],24)
            self.assertEqual(card['additional_checks'],[])
            hero=app.select_hero_powers(hero['id'],revision=hero['revision'],selections=['extraordinary-mental-affinity'])
            card=next(row for row in app.hero_program_view(hero['id'])['skills'] if row['id']=='cardsharp')
            self.assertEqual(card['percentage'],34)
            self.assertEqual(card['additional_checks'],[])
