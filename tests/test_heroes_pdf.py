from io import BytesIO
import tempfile
import unittest

from pypdf import PdfReader, PdfWriter

from characters_unlimited.application import CharacterApplication


class HeroesPdfWorkflowTests(unittest.TestCase):
    def test_education_skills_and_blank_unsupported_values_export_editably(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides: 4)
            hero = app.create(game='heroes-unlimited', name='Beacon')
            hero = app.select_education(hero['id'], revision=0, method='choose', education_id='college-one')
            hero = app.set_attribute(hero['id'], attribute='IQ', revision=hero['revision'], mode='fixed', value=16)
            hero = app.select_hero_programs(hero['id'], revision=hero['revision'], selections=[{'slot':0, 'program':'business'}])
            before = app.get(hero['id'])
            reader = PdfReader(BytesIO(app.export_pdf(hero['id'])))
            fields = reader.get_fields()
            assert fields is not None
            self.assertEqual(fields['NAME']['/V'], 'Beacon')
            self.assertEqual(fields['IQ']['/V'], '16')
            self.assertEqual(fields['EDUCATION']['/V'], 'One Year of College')
            self.assertEqual(fields['skills.research.percentage']['/V'], '62')
            self.assertEqual(fields['skills.research.rate']['/V'], '5')
            self.assertIn('Business', fields['PROGRAMS']['/V'])
            for key in ('HP', 'SDC', 'EQUIPMENT'):
                self.assertEqual(fields[key].get('/V', ''), '')
            self.assertEqual(fields['STRIKE']['/V'],'0')
            self.assertEqual(fields['ATTACKS']['/V'],'3')
            self.assertEqual(fields['SAVE_PSIONICS']['/V'], '+0')
            self.assertNotIn('SAVE_INSANITY', fields)
            self.assertIn('Psionic attacks: +0', fields['POWERS']['/V'])
            self.assertEqual(app.get(hero['id']), before)
            text = '\n'.join(page.extract_text() for page in reader.pages)
            self.assertIn('HEROES UNLIMITED', text)
            self.assertNotIn('RIFTS', text)
            self.assertNotIn('DRAFT', text)
            writer = PdfWriter()
            writer.clone_document_from_reader(reader)
            writer.update_page_form_field_values(None, {'NAME':'Edited Beacon', 'POWERS':'Flight'}, auto_regenerate=False)
            edited = BytesIO()
            writer.write(edited)
            edited_fields = PdfReader(edited).get_fields()
            assert edited_fields is not None
            self.assertEqual(edited_fields['POWERS']['/V'], 'Flight')
            self.assertEqual(edited_fields['NAME']['/V'], 'Edited Beacon')

    def test_unicode_long_notes_and_missing_education_survive_continuations(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides: 4)
            notes = '\n'.join(f'Journal {index}: 李 — Мария ♥' for index in range(140))
            hero = app.create(game='heroes-unlimited', name='李 — Мария', notes=notes)
            reader = PdfReader(BytesIO(app.export_pdf(hero['id'])))
            fields = reader.get_fields()
            assert fields is not None
            self.assertEqual(fields['NAME']['/V'], '李 — Мария')
            self.assertEqual(fields['EDUCATION'].get('/V', ''), '')
            self.assertEqual(fields['SECONDARY_ALLOWANCE'].get('/V', ''), '')
            values = '\n'.join(field.get('/V', '') for field in fields.values())
            self.assertIn('Journal 139: 李 — Мария ♥', values)
            self.assertGreater(len(reader.pages), 2)
            self.assertTrue(all('HEROES UNLIMITED' in page.extract_text() for page in reader.pages))
            keys = [ref.get_object()['/T'] for page in reader.pages for ref in page.get('/Annots', [])]
            self.assertEqual(len(keys), len(set(keys)))
            writer = PdfWriter()
            writer.clone_document_from_reader(reader)
            writer.update_page_form_field_values(None, {'NAME':'新名字', 'continuation.0':'新笔记 ♥'}, auto_regenerate=False)
            output = BytesIO()
            writer.write(output)
            edited = PdfReader(output).get_fields()
            assert edited is not None
            self.assertEqual(edited['NAME']['/V'], '新名字')
            self.assertEqual(edited['continuation.0']['/V'], '新笔记 ♥')

    def test_long_program_lists_keep_entitlements_and_recorded_choices_legible(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides: 4)
            hero = app.create(game='heroes-unlimited')
            hero = app.select_education(hero['id'], revision=0, method='choose', education_id='college-one')
            hero = app.select_hero_programs(hero['id'], revision=hero['revision'], selections=[
                {'slot':index, 'program':'computer', 'choices':{'repair-radio':['radio-basic']}}
                for index in range(25)])
            reader = PdfReader(BytesIO(app.export_pdf(hero['id'])))
            fields = reader.get_fields()
            assert fields is not None
            values = '\n'.join(field.get('/V', '') for field in fields.values())
            self.assertIn('Slot 25: Computer', values)
            self.assertIn('Recorded choice: Computer slot 25', values)
            self.assertIn('Radio: Basic', values)
            self.assertIn('Program allowance: Program 1', values)
            self.assertIn('+10%', values)
