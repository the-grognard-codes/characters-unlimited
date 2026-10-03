from io import BytesIO
import tempfile
import unittest

from pypdf import PdfReader, PdfWriter

from characters_unlimited.application import CharacterApplication


class EditableSheetWorkflowTests(unittest.TestCase):
    def test_unicode_names_and_continuation_notes_preserve_values_and_embedded_appearances(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides: 4)
            name = '李 小龙 — Мария'
            character = app.create(name=name, notes=('dragon ♥ rune 中文 😀\n' * 30))
            reader = PdfReader(BytesIO(app.export_pdf(character['id'])))
            fields = reader.get_fields()
            assert fields is not None
            self.assertEqual(fields['NAME']['/V'], name)
            continuation = next(field for key, field in fields.items()
                                if key.startswith('continuation.') and '♥' in field.get('/V', ''))
            self.assertIn('中文 😀', continuation['/V'])
            widgets = [ref.get_object() for page in reader.pages for ref in page.get('/Annots', [])]
            for field in (next(widget for widget in widgets if widget.get('/T') == 'NAME'),
                          next(widget for widget in widgets if widget.get('/V') == continuation['/V'])):
                appearance = field['/AP']['/N']
                fonts = appearance['/Resources']['/Font']
                self.assertTrue(any('/FontFile2' in font.get_object().get('/FontDescriptor', {})
                                    for font in fonts.values()))
                self.assertTrue(appearance.get_data())
            writer = PdfWriter()
            writer.clone_document_from_reader(reader)
            writer.update_page_form_field_values(None, {'NAME': '新名字 — Ирина',
                                                       'continuation.1': '新笔记 ♥'}, auto_regenerate=False)
            saved = BytesIO()
            writer.write(saved)
            edited = PdfReader(saved)
            edited_fields = edited.get_fields()
            assert edited_fields is not None
            self.assertEqual(edited_fields['NAME']['/V'], '新名字 — Ирина')
            edited_name = next(ref.get_object() for ref in edited.pages[0].get('/Annots', [])
                               if ref.get_object().get('/T') == 'NAME')
            self.assertIn('/RPGUnicode', edited_name['/AP']['/N']['/Resources']['/Font'])
            self.assertIn('/RPGUnicode', edited_name['/DA'])

    def test_supported_values_export_and_missing_values_remain_blank(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides: 4)
            character = app.create(name='Rowan')
            before = app.get(character['id'])
            reader = PdfReader(BytesIO(app.export_pdf(character['id'])))
            fields = reader.get_fields()
            self.assertIsNotNone(fields)
            assert fields is not None
            self.assertEqual(fields['NAME']['/V'], 'Rowan')
            self.assertEqual(fields['PS']['/V'], '13')
            self.assertEqual(fields['OCC']['/V'], 'Vagabond')
            self.assertEqual(fields['HIT POINTS'].get('/V', ''), '')
            self.assertEqual(fields['PPE'].get('/V', ''), '')
            self.assertEqual(fields['STRIKE']['/V'], '0')
            self.assertEqual(app.get(character['id']), before)
            writer = PdfWriter()
            writer.clone_document_from_reader(reader)
            writer.update_page_form_field_values(None, {'NAME': 'Edited in a PDF reader'}, auto_regenerate=False)
            output = BytesIO()
            writer.write(output)
            reopened = PdfReader(output)
            reopened_fields = reopened.get_fields()
            assert reopened_fields is not None
            self.assertEqual(reopened_fields['NAME']['/V'], 'Edited in a PDF reader')

    def test_skills_notes_and_continuations_have_independently_editable_cells(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides: 4)
            notes = 'A traveler seeking ancient cities. ' * 120
            character = app.create(name='Long sheet', notes=notes)
            app.select_skills(character['id'], revision=0, selections=[
                {'skill_id': 'archaeology', 'pool': 'related'},
                {'skill_id': 'performance', 'pool': 'secondary'},
            ])
            reader = PdfReader(BytesIO(app.export_pdf(character['id'])))
            fields = reader.get_fields()
            assert fields is not None
            values = [str(field.get('/V', '')) for field in fields.values()]
            self.assertIn('Archaeology', values)
            self.assertIn('Recognize artifacts and infer their purpose', ' '.join(values))
            self.assertIn('Performance', values)
            self.assertGreater(len(reader.pages), 2)
            self.assertIn('ancient cities.', ' '.join(values))
            names = []
            appearances = []
            for page in reader.pages:
                for reference in page.get('/Annots', []):
                    widget = reference.get_object()
                    if widget.get('/Subtype') == '/Widget':
                        self.assertNotIn('/Parent', widget)
                        names.append(widget['/T'])
                        self.assertIn(widget['/T'], fields)
                        self.assertEqual(widget.get('/V', ''), fields[widget['/T']].get('/V', ''))
                        if widget.get('/V'):
                            self.assertIn('/N', widget['/AP'])
                            appearances.append(widget['/AP']['/N'].indirect_reference.idnum)
            self.assertEqual(len(names), len(set(names)))
            self.assertEqual(len(appearances), len(set(appearances)))
            archaeology_field = next(name for name, field in fields.items() if field.get('/V') == 'Archaeology')
            writer = PdfWriter()
            writer.clone_document_from_reader(reader)
            writer.update_page_form_field_values(None, {archaeology_field: 'Edited skill', 'continuation.0': 'Edited continuation'}, auto_regenerate=False)
            saved = BytesIO()
            writer.write(saved)
            reopened = PdfReader(saved).get_fields()
            assert reopened is not None
            self.assertEqual(reopened[archaeology_field]['/V'], 'Edited skill')
            self.assertEqual(reopened['continuation.0']['/V'], 'Edited continuation')
            self.assertEqual(sum(field.get('/V') == 'Performance' for field in reopened.values()), 1)
