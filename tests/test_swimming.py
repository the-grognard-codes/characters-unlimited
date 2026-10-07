from io import BytesIO
from copy import deepcopy
import tempfile
import unittest

from pypdf import PdfReader

from characters_unlimited.application import CharacterApplication
from characters_unlimited.rules import RuleArchive


class SwimmingWorkflowTests(unittest.TestCase):
    def test_swimming_proficiency_contexts_and_limits_use_source_attributes(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides: 4)
            hero = app.create()
            for key, value in (('IQ',16), ('PS',20), ('PE',16), ('SPD',99)):
                hero = app.set_attribute(hero['id'], attribute=key, revision=hero['revision'], mode='fixed', value=value)
            attributes = hero['attributes']
            calls = []
            def die(sides):
                calls.append(sides)
                return 4
            app.die = die
            hero = app.select_skills(hero['id'], revision=hero['revision'], selections=[
                {'skill_id':'swimming','pool':'related'}, {'skill_id':'swimming','pool':'secondary'}])
            view = app.skill_view(hero['id'])
            swim = next(row for row in view['selected'] if row['id']=='swimming')
            self.assertEqual(swim['percentage'],52)
            self.assertEqual(swim['per_level'],5)
            self.assertEqual([check['percentage'] for check in swim['additional_checks']], [32,7])
            activity = swim['activities'][0]
            self.assertEqual(activity['yards_per_melee'],60)
            self.assertEqual(activity['meters_per_melee'],60)
            self.assertEqual(activity['minutes'],16)
            self.assertEqual(hero['attributes'], attributes)
            self.assertEqual(calls,[])
            self.assertFalse(any('not available' in message for message in view['warnings']))
            self.assertTrue(any('duplicate' in message for message in view['warnings']))
            self.assertEqual(app.import_character(app.export_character(hero['id']))['physical_acquisitions'], hero['physical_acquisitions'])
            self.assertEqual(CharacterApplication(directory).skill_view(hero['id']),view)
            fields = PdfReader(BytesIO(app.export_pdf(hero['id']))).get_fields()
            assert fields is not None
            values = ' '.join(' '.join(field.get('/V','') for field in fields.values()).split())
            self.assertNotIn('60 yards / 60 meters per melee', values)
            self.assertNotIn('16 minutes', values)
            self.assertIn('three consecutive', values.lower())

    def test_old_pins_and_activity_corrections_remain_explicit_and_atomic(self):
        with tempfile.TemporaryDirectory() as directory:
            archive = RuleArchive.load()
            earlier = CharacterApplication(directory, die=lambda sides:4,
                rule_archive=RuleArchive(archive.definitions(), {**archive.active_versions(), 'rifts-domestic-skills':'2.3.0'}))
            hero = earlier.create()
            with self.assertRaises(ValueError):
                earlier.select_skills(hero['id'], revision=0, selections=[{'skill_id':'swimming','pool':'related'}])
            current = CharacterApplication(directory)
            preview = current.preview_rule_upgrade(hero['id'])
            hero = current.apply_rule_upgrade(hero['id'], revision=0, token=preview['token'])['character']
            hero = current.select_skills(hero['id'], revision=hero['revision'], selections=[{'skill_id':'swimming','pool':'related'}])
            corrected = deepcopy(archive.active('rifts-domestic-skills'))
            corrected['version'] = '99.0.0'
            swimming = next(row for row in corrected['skills'] if row['id']=='swimming')
            swimming['base'] = 55
            swimming['activities']['swimming']['yards_per_ps'] = 4
            # This simulated catalog correction must update dependent required
            # receipts too, before the shared preflight checks every owner.
            def update_required_swimming(node):
                if isinstance(node, dict):
                    if node.get('id') == 'swimming' and 'base' in node:
                        node['base'] = 55
                    for value in node.values():
                        update_required_swimming(value)
                elif isinstance(node, list):
                    for value in node:
                        update_required_swimming(value)
            update_required_swimming(corrected)
            updated = CharacterApplication(directory, rule_archive=RuleArchive([*archive.definitions(),corrected],
                {**archive.active_versions(), corrected['id']:corrected['version']}))
            preview = updated.preview_rule_upgrade(hero['id'])
            self.assertTrue(any(row['name']=='Swimming' and row['before']==50 and row['after']==55 for row in preview['skills']))
            self.assertTrue(any(row['before']==39 and row['after']==52 and row['unit']=='yards/melee' for row in preview['skills']))
            self.assertEqual(updated.get(hero['id']),hero)
            hero = updated.apply_rule_upgrade(hero['id'], revision=hero['revision'], token=preview['token'])['character']
            swim = updated.skill_view(hero['id'])['selected'][0]
            self.assertEqual(swim['percentage'],55)
            self.assertEqual(swim['activities'][0]['yards_per_melee'],52)
            hero = updated.set_attribute(hero['id'], attribute='PS', revision=hero['revision'], mode='fixed', value=0)
            self.assertIsNone(updated.skill_view(hero['id'])['selected'][0]['activities'][0]['yards_per_melee'])

    def test_large_manual_attributes_keep_exact_integer_limits_in_pdf(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides:4)
            hero = app.create()
            for attribute in ('PS','PE'):
                hero = app.set_attribute(hero['id'], attribute=attribute, revision=hero['revision'], mode='fixed', value=1234567)
            hero = app.select_skills(hero['id'], revision=hero['revision'], selections=[{'skill_id':'swimming','pool':'secondary'}])
            fields = PdfReader(BytesIO(app.export_pdf(hero['id']))).get_fields()
            assert fields is not None
            values = ' '.join(' '.join(field.get('/V','') for field in fields.values()).split())
            self.assertNotIn('3703701 yards / 3703701 meters per melee for 1234567 minutes', values)
