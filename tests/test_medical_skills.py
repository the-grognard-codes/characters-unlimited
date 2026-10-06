from io import BytesIO
import tempfile
import unittest
from pypdf import PdfReader
from characters_unlimited.application import CharacterApplication

class MedicalSkillWorkflowTests(unittest.TestCase):
    def test_medical_synergies_and_contexts_use_correct_checks_once(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides: 4)
            hero = app.create()
            choices = [{'skill_id':name,'pool':'secondary'} for name in ('brewing-medicinal','holistic-medicine','medical-doctor','field-surgery','pathology','forensics','animal-husbandry')]
            app.select_skills(hero['id'], revision=0, selections=choices)
            view = app.skill_view(hero['id'])
            skills = {s['id']:s for s in view['selected']}
            self.assertEqual(skills['brewing-medicinal']['percentage'], 35)
            self.assertEqual(skills['brewing-medicinal']['additional_checks'][0]['percentage'], 40)
            self.assertEqual(skills['holistic-medicine']['percentage'], 35)
            checks = {c['name']:c['percentage'] for c in skills['holistic-medicine']['additional_checks']}
            self.assertEqual(checks['Treatment'], 25)
            self.assertEqual(checks['Treat disease, infection or poison'], 15)
            self.assertEqual(checks['Treat alien creatures'], -5)
            self.assertEqual(skills['field-surgery']['percentage'], 30)
            self.assertEqual(skills['field-surgery']['additional_checks'][0]['percentage'], 15)
            self.assertEqual(skills['forensics']['percentage'], 40)
            self.assertEqual(skills['animal-husbandry']['additional_checks'][0]['percentage'], 17.5)
            self.assertTrue(any('Medical Doctor: not available' in w for w in view['warnings']))

    def test_contexts_follow_caps_and_exact_portable_pins(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides: 4)
            hero = app.create()
            hero = app.set_attribute(hero['id'], revision=0, attribute='IQ', mode='fixed', value=200)
            app.select_skills(hero['id'], revision=hero['revision'], selections=[{'skill_id':'animal-husbandry','pool':'secondary'},{'skill_id':'medical-doctor','pool':'secondary'}])
            view = app.skill_view(hero['id'])
            self.assertEqual(view['selected'][0]['percentage'], 98)
            self.assertEqual(view['selected'][0]['additional_checks'][0]['percentage'], 49)
            doctor = {c['name']:c['percentage'] for c in view['selected'][1]['additional_checks']}
            self.assertEqual(view['selected'][1]['percentage'], 98)
            self.assertEqual(doctor['Treatment'], 98)
            self.assertEqual(doctor['Animal treatment'], 63)
            imported = app.import_character(app.export_character(hero['id']))
            self.assertEqual(app.skill_view(imported['id'])['selected'], view['selected'])

    def test_medical_pool_entitlements_prerequisites_and_remaining_bases(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides:4)
            hero = app.create()
            choices = [{'skill_id':i,'pool':'secondary'} for i in ('paramedic','psychology','veterinary-science','animal-husbandry')]
            choices += [{'skill_id':'first-aid','pool':'related'},{'skill_id':'animal-husbandry','pool':'related'}]
            saved = app.select_skills(hero['id'], revision=0, selections=choices)
            view = app.skill_view(saved['id'])
            self.assertEqual([s['percentage'] for s in view['selected']], [40,35,50,35,50,35])
            self.assertTrue(any('Psychology: missing prerequisite' in w for w in view['warnings']))
            self.assertTrue(any('Animal Husbandry: not available in the related' in w for w in view['warnings']))
            self.assertFalse(any('Animal Husbandry: not available in the secondary' in w for w in view['warnings']))
            choices += [{'skill_id':i,'pool':'secondary'} for i in ('biology','chemistry','literacy-native')]
            app.select_skills(saved['id'], revision=saved['revision'], selections=choices)
            self.assertFalse(any('missing prerequisite' in w for w in app.skill_view(saved['id'])['warnings']))

    def test_new_medical_pack_requires_reviewed_upgrade_and_pdf_retains_half_rate(self):
        from characters_unlimited.rules import RuleArchive
        with tempfile.TemporaryDirectory() as directory:
            archive = RuleArchive.load()
            active = archive.active_versions()
            active['rifts-domestic-skills'] = '1.8.0'
            older = CharacterApplication(directory, die=lambda sides:4, rule_archive=RuleArchive(archive.definitions(), active))
            hero = older.create()
            app = CharacterApplication(directory)
            self.assertNotIn('animal-husbandry', {s['id'] for s in app.skill_view(hero['id'])['catalog']})
            preview = app.preview_rule_upgrade(hero['id'])
            self.assertEqual(preview['changes'][0]['to'], '2.19.0')
            updated = app.apply_rule_upgrade(hero['id'], revision=0, token=preview['token'])['character']
            self.assertEqual(len(app.skill_view(hero['id'])['catalog']), 181)
            app.select_skills(hero['id'], revision=updated['revision'], selections=[{'skill_id':'animal-husbandry','pool':'secondary'}])
            check = app.skill_view(hero['id'])['selected'][0]['additional_checks'][0]
            self.assertEqual(check['per_level'], 2.5)
            fields = PdfReader(BytesIO(app.export_pdf(hero['id']))).get_fields()
            self.assertIsNotNone(fields)
            assert fields is not None
            values = [str(field.get('/V','')) for field in fields.values()]
            self.assertTrue(any('17.5% (+2.5% per level)' in value for value in values))
