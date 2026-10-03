import tempfile
import unittest
from io import BytesIO

from pypdf import PdfReader

from characters_unlimited.application import CharacterApplication
from characters_unlimited.rules import RuleArchive


class BoxingWorkflowTests(unittest.TestCase):
    def test_boxing_adds_one_attack_and_recorded_bonuses_without_stacking(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides: 4)
            character = app.create(generation={'reroll_ones':True, 'extra_die':True})
            faces = iter([1,2,3])
            calls: list[int] = []
            def training_die(sides):
                calls.append(sides)
                return next(faces)
            app.die = training_die
            choices = [{'skill_id':'boxing','pool':'related'},
                       {'skill_id':'boxing','pool':'secondary'}]
            character = app.select_skills(character['id'],revision=0,selections=choices)
            view = app.skill_view(character['id'])
            self.assertEqual(calls,[6,6,6])
            self.assertEqual(character['attributes']['PS']['value'],15)
            self.assertEqual(character['physical_acquisitions']['boxing']['rolls'],{'resource:SDC':[1,2,3]})
            totals = view['combat']['totals']
            self.assertEqual(totals['attacks']['value'],5)
            self.assertEqual(totals['attacks']['contributions'],{'hand_to_hand':4,'Boxing':1})
            self.assertEqual(totals['parry']['value'],2)
            self.assertEqual(totals['dodge']['value'],2)
            self.assertEqual(totals['roll_with_impact']['value'],3)
            self.assertEqual(totals['gun_dodge']['value'],0)
            self.assertTrue(any('Boxing: not available' in warning for warning in view['warnings']))
            self.assertTrue(any('duplicate' in warning for warning in view['warnings']))
            app.die = lambda sides:4
            character = app.generate_resources(character['id'],revision=character['revision'])
            self.assertEqual(app.resource_view(character['id'])['resources']['SDC']['value'],44)
            reader = PdfReader(BytesIO(app.export_pdf(character['id'])))
            fields = reader.get_fields()
            self.assertIsNotNone(fields)
            assert fields is not None
            notes = ' '.join(str(field.get('/V','')) for field in fields.values())
            self.assertIn('Natural 20',notes)
            self.assertIn('1D6 melee rounds',notes)
            self.assertIn('attacks +1',notes)
            def no_draw(sides):
                raise AssertionError('Previously acquired Boxing must not roll again')
            app.die = no_draw
            character = app.select_skills(character['id'],revision=character['revision'],selections=[])
            self.assertEqual(app.skill_view(character['id'])['combat']['totals']['attacks']['value'],4)
            self.assertEqual(app.resource_view(character['id'])['resources']['SDC']['value'],38)
            character = app.select_skills(character['id'],revision=character['revision'],selections=choices[:1])
            self.assertEqual(app.skill_view(character['id'])['combat']['totals']['attacks']['value'],5)
            imported = app.import_character(app.export_character(character['id']))
            self.assertEqual(imported['physical_acquisitions'],character['physical_acquisitions'])
            self.assertEqual(CharacterApplication(directory).skill_view(character['id']),app.skill_view(character['id']))

    def test_older_rules_require_explicit_upgrade_for_boxing(self):
        with tempfile.TemporaryDirectory() as directory:
            archive = RuleArchive.load()
            active = archive.active_versions()
            active['rifts-domestic-skills'] = '2.2.0'
            old = CharacterApplication(directory,die=lambda sides:4,
                rule_archive=RuleArchive(archive.definitions(),active))
            character = old.create()
            app = CharacterApplication(directory,die=lambda sides:1)
            choices = [{'skill_id':'boxing','pool':'related'}]
            with self.assertRaises(ValueError):
                app.select_skills(character['id'],revision=0,selections=choices)
            self.assertEqual(app.get(character['id']),character)
            preview = app.preview_rule_upgrade(character['id'])
            character = app.apply_rule_upgrade(character['id'],revision=0,token=preview['token'])['character']
            character = app.select_skills(character['id'],revision=character['revision'],selections=choices)
            self.assertEqual(app.skill_view(character['id'])['combat']['totals']['attacks']['value'],5)
            self.assertEqual(character['physical_acquisitions']['boxing']['rolls'],{'resource:SDC':[1,1,1]})
