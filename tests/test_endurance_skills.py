import tempfile
import unittest
from copy import deepcopy
from io import BytesIO

from pypdf import PdfReader

from characters_unlimited.application import CharacterApplication
from characters_unlimited.rules import RuleArchive
from characters_unlimited.storage import SaveConflict


class EnduranceSkillWorkflowTests(unittest.TestCase):
    def test_physical_endurance_bonuses_feed_initial_hp_and_running_distances(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides:4)
            character = app.create(generation={'reroll_ones':True, 'extra_die':True})
            faces = iter([2,3,1,2,3,4,1])
            calls: list[int] = []
            def training_die(sides):
                calls.append(sides)
                return next(faces)
            app.die = training_die
            choices = [{'skill_id':'physical-labor','pool':'related'},
                       {'skill_id':'running','pool':'secondary'}]
            character = app.select_skills(character['id'],revision=0,selections=choices)
            self.assertEqual(calls,[8,8,4,4,4,4,6])
            self.assertEqual(character['attributes']['PS']['value'],15)
            self.assertEqual(character['attributes']['PE']['value'],16)
            self.assertEqual(character['attributes']['SPD']['value'],22)
            view = app.skill_view(character['id'])
            self.assertFalse(any('Running: not available' in warning for warning in view['warnings']))
            running = next(skill for skill in view['selected'] if skill['id']=='running')
            activities = {item['id']:item for item in running['activities']}
            self.assertEqual(activities['half-speed']['speed_attribute'],11)
            self.assertEqual(activities['half-speed']['miles'],8)
            self.assertEqual(activities['half-speed']['kilometers'],12.8)
            self.assertAlmostEqual(activities['maximum-speed']['miles'],8/3)
            self.assertEqual(activities['maximum-speed']['speed_attribute'],22)
            self.assertNotIn('percentage',running)
            app.die = lambda sides:5
            character = app.generate_resources(character['id'],revision=character['revision'])
            self.assertEqual(app.resource_view(character['id'])['resources']['HP']['value'],21)
            self.assertEqual(app.resource_view(character['id'])['resources']['SDC']['value'],48)
            character = app.select_skills(character['id'],revision=character['revision'],selections=[])
            self.assertEqual(character['attributes']['PE']['value'],14)
            self.assertEqual(app.resource_view(character['id'])['resources']['HP']['value'],21)
            character = app.select_skills(character['id'],revision=character['revision'],selections=choices)
            self.assertEqual(character['attributes']['SPD']['value'],22)
            self.assertEqual(calls,[8,8,4,4,4,4,6])
            imported = app.import_character(app.export_character(character['id']))
            self.assertEqual(imported['physical_acquisitions'],character['physical_acquisitions'])
            self.assertEqual(app.skill_view(imported['id'])['selected'],app.skill_view(character['id'])['selected'])
            self.assertEqual(CharacterApplication(directory).resource_view(character['id'])['resources']['HP']['value'],21)
            fields = PdfReader(BytesIO(app.export_pdf(character['id']))).get_fields()
            assert fields is not None
            notes = [str(field.get('/V','')) for field in fields.values()]
            self.assertFalse(any('Running at half speed: Spd 11; 8.000 miles' in value for value in notes))
            self.assertFalse(any('12.800 km' in value for value in notes))
            character = app.select_skills(character['id'],revision=character['revision'],selections=[
                {'skill_id':'physical-labor','pool':'secondary'},
                {'skill_id':'running','pool':'secondary'}])
            warnings = app.skill_view(character['id'])['warnings']
            self.assertTrue(any('Physical Labor: not available in the secondary pool' in warning for warning in warnings))
            self.assertFalse(any('Running: not available' in warning for warning in warnings))
            self.assertEqual(character['physical_acquisitions'],imported['physical_acquisitions'])

    def test_old_pins_invalid_dice_manual_activity_values_and_explicit_activity_preview(self):
        with tempfile.TemporaryDirectory() as directory:
            archive = RuleArchive.load()
            active = archive.active_versions()
            active['rifts-domestic-skills'] = '2.1.0'
            earlier = CharacterApplication(directory,die=lambda sides:4,
                                            rule_archive=RuleArchive(archive.definitions(),active))
            character = earlier.create()
            app = CharacterApplication(directory,die=lambda sides:4)
            choices = [{'skill_id':'running','pool':'related'}]
            with self.assertRaises(ValueError):
                app.select_skills(character['id'],revision=0,selections=choices)
            preview = app.preview_rule_upgrade(character['id'])
            character = app.apply_rule_upgrade(character['id'],revision=0,token=preview['token'])['character']
            self.assertEqual(character['additional_rule_packs']['rifts-domestic-skills'],'2.30.0')
            for face in (True,0,5):
                app.die = lambda sides:face
                with self.assertRaises(ValueError):
                    app.select_skills(character['id'],revision=character['revision'],selections=choices)
                self.assertEqual(app.get(character['id']),character)
            def forbidden_draw(sides):
                raise AssertionError('Stale request drew dice')
            app.die = forbidden_draw
            with self.assertRaises(SaveConflict):
                app.select_skills(character['id'],revision=0,selections=choices)
            app.die = lambda sides:1
            character = app.select_skills(character['id'],revision=character['revision'],selections=choices*2)
            self.assertEqual(character['attributes']['PE']['value'],15)
            self.assertEqual(character['attributes']['SPD']['value'],16)
            character = app.set_attribute(character['id'],revision=character['revision'],attribute='PE',mode='fixed',value=20)
            view = app.skill_view(character['id'])
            self.assertEqual(view['selected'][0]['activities'][0]['miles'],10)
            target = deepcopy(archive.resolve('rifts-domestic-skills','2.2.0'))
            target['version'] = '99.2.0'
            next(skill for skill in target['skills'] if skill['id']=='running')['activities']['running']['maximum_speed_distance_divisor'] = 2
            invalid = deepcopy(target)
            invalid['version'] = '99.2.1'
            next(skill for skill in invalid['skills'] if skill['id']=='running')['activities']['running']['maximum_speed_distance_divisor'] = 10**1000
            invalid_app = CharacterApplication(directory,rule_archive=RuleArchive(
                [*archive.definitions(),invalid],{**active,'rifts-domestic-skills':'99.2.1'}))
            with self.assertRaisesRegex(ValueError, 'Invalid Running'):
                invalid_app.preview_rule_upgrade(character['id'])
            self.assertEqual(app.get(character['id']),character)
            active['rifts-domestic-skills'] = '99.2.0'
            updated = CharacterApplication(directory,rule_archive=RuleArchive([*archive.definitions(),target],active))
            preview = updated.preview_rule_upgrade(character['id'])
            change = next(row for row in preview['skills'] if row.get('unit')=='miles'
                          and row['name']=='Running — Running at maximum speed')
            self.assertAlmostEqual(change['before'],10/3)
            self.assertEqual(change['after'],5)
            acquisitions = deepcopy(character['physical_acquisitions'])
            character = updated.apply_rule_upgrade(character['id'],revision=character['revision'],token=preview['token'])['character']
            self.assertEqual(character['physical_acquisitions'],acquisitions)
            character = updated.set_attribute(character['id'],revision=character['revision'],attribute='PE',mode='fixed',value=0)
            activity = updated.skill_view(character['id'])['selected'][0]['activities'][0]
            self.assertIsNone(activity['miles'])
            self.assertIn('Positive effective',activity['guidance'])
            character = updated.set_attribute(character['id'],revision=character['revision'],attribute='PE',mode='fixed',value=10**400)
            activity = updated.skill_view(character['id'])['selected'][0]['activities'][0]
            self.assertEqual(character['attributes']['PE']['value'],10**400)
            self.assertIsNone(activity['miles'])
            self.assertIn('supported numeric range',activity['guidance'])
            character = updated.set_attribute(character['id'],revision=character['revision'],attribute='PE',mode='fixed',value=20)
            character = updated.set_attribute(character['id'],revision=character['revision'],attribute='SPD',mode='fixed',value=10**400)
            self.assertIsNone(updated.skill_view(character['id'])['selected'][0]['activities'][0]['speed_attribute'])
