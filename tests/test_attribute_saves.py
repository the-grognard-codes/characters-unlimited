import tempfile
import unittest
from characters_unlimited.application import CharacterApplication
from characters_unlimited.rules import RuleArchive
from pypdf import PdfReader
from io import BytesIO


class AttributeSavingWorkflowTests(unittest.TestCase):
    def test_reviewed_saving_bonuses_follow_fixed_attributes_and_show_sources(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides:4)
            character = app.create()
            app.set_attribute(character['id'], revision=0, attribute='ME', mode='fixed', value=20)
            app.set_attribute(character['id'], revision=1, attribute='PE', mode='fixed', value=16)
            saves = app.combat_view(character['id'])['saving_bonuses']
            self.assertEqual(saves['psionics']['value'], 3)
            self.assertEqual(saves['insanity']['value'], 3)
            self.assertEqual(saves['magic']['value'], 1)
            self.assertEqual(saves['poison']['value'], 1)
            self.assertEqual(saves['disease']['value'], 1)
            self.assertEqual(saves['coma_death']['value'], 4)
            self.assertEqual(saves['coma_death']['unit'], '%')
            self.assertEqual(saves['psionics']['contributions'], {'mental_endurance':3})
            self.assertIn(281, saves['psionics']['sources'][0]['pages'])

    def test_low_penalties_and_high_caps_follow_the_original_source(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides:4)
            character = app.create()
            identifier = character['id']
            for attribute, value in [('ME',4), ('PE',3), ('IQ',40)]:
                saved = app.get(identifier)
                app.set_attribute(identifier, revision=saved['revision'], attribute=attribute, mode='fixed', value=value)
            saves = app.combat_view(identifier)['saving_bonuses']
            self.assertEqual([saves[key]['value'] for key in ('psionics','insanity','horror_factor','possession','illusions')],
                             [-3,-2,-6,-3,0])
            self.assertEqual([saves[key]['value'] for key in ('magic','poison','drugs','disease','coma_death')],
                             [-4,-5,-5,-6,-10])
            self.assertTrue(any('25% longer' in note for note in app.combat_view(identifier)['saving_notes']))
            for attribute, value in [('ME',40), ('PE',35), ('IQ',100)]:
                saved = app.get(identifier)
                app.set_attribute(identifier, revision=saved['revision'], attribute=attribute, mode='fixed', value=value)
            view = app.combat_view(identifier)
            self.assertEqual([view['saving_bonuses'][key]['value'] for key in ('psionics','insanity','possession','magic','coma_death','illusions')],
                             [8,13,0,8,35,7])
            self.assertTrue(any('impervious' in note for note in view['saving_notes']))

    def test_fatigue_ranges_and_magic_exceptions_survive_pdf_notes(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides:4)
            character = app.create(notes='Player text first.\n' + 'Long player note.\n' * 15)
            for score, expected in [(1,'75% faster'), (2,'75% faster'), (3,'25% longer'),
                                    (4,'25% longer'), (5,'50% faster'), (7,'50% faster'),
                                    (8,None), (29,None), (30,'half the normal')]:
                current = app.get(character['id'])
                app.set_attribute(character['id'], revision=current['revision'], attribute='PE', mode='fixed', value=score)
                notes = app.combat_view(character['id'])['saving_notes']
                fatigue = [note for note in notes if 'Fatigue' in note]
                self.assertEqual(bool(fatigue), expected is not None)
                if expected:
                    self.assertIn(expected, fatigue[0])
            reader = PdfReader(BytesIO(app.export_pdf(character['id'])))
            fields = reader.get_fields()
            assert fields is not None
            text = ' '.join(' '.join(str(field.get('/V', '')) for field in fields.values()).split())
            self.assertIn('Player text first.', text)
            self.assertIn('demonic curses or possession', text)
            self.assertIn('half the normal rate', text)

    def test_old_pins_preview_saves_and_pdf_blanks_undefined_values(self):
        archive = RuleArchive.load()
        active = archive.active_versions(); active['rifts-domestic-skills'] = '1.7.0'
        with tempfile.TemporaryDirectory() as directory, tempfile.TemporaryDirectory() as other:
            earlier = CharacterApplication(directory, die=lambda sides:4, rule_archive=RuleArchive(archive.definitions(),active))
            character = earlier.create(name='Saving check')
            self.assertEqual(earlier.combat_view(character['id'])['saving_bonuses'], {})
            app = CharacterApplication(directory)
            preview = app.preview_rule_upgrade(character['id'])
            self.assertTrue(any('psionic' in row['name'] and row['before'] is None for row in preview['combat']))
            app.apply_rule_upgrade(character['id'], revision=0, token=preview['token'])
            app.set_attribute(character['id'], revision=1, attribute='ME', mode='fixed', value=20)
            app.set_attribute(character['id'], revision=2, attribute='PE', mode='fixed', value=16)
            reader = PdfReader(BytesIO(app.export_pdf(character['id'])))
            fields = reader.get_fields()
            assert fields is not None
            widget = next(ref.get_object() for ref in reader.pages[0].get('/Annots', [])
                          if abs(float(ref.get_object()['/Rect'][1])-701.1) < .2)
            self.assertEqual(fields[widget['/T']]['/V'], '+3')
            reopened = CharacterApplication(other)
            imported = reopened.import_character(app.export_character(character['id']))
            self.assertEqual(reopened.combat_view(imported['id'])['saving_bonuses'],app.combat_view(character['id'])['saving_bonuses'])
            app.set_attribute(character['id'], revision=3, attribute='PE', mode='fixed', value=0)
            self.assertIsNone(app.combat_view(character['id'])['saving_bonuses']['magic']['value'])
            reader = PdfReader(BytesIO(app.export_pdf(character['id'])))
            fields = reader.get_fields()
            assert fields is not None
            widget = next(ref.get_object() for ref in reader.pages[0].get('/Annots', [])
                          if abs(float(ref.get_object()['/Rect'][0])-134.6) < .2
                          and abs(float(ref.get_object()['/Rect'][1])-720) < .2)
            self.assertEqual(fields[widget['/T']].get('/V', ''), '')
