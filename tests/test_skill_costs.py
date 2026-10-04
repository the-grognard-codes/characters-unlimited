"""Source-defined optional skill costs through the character workflow."""

import tempfile
import unittest
from io import BytesIO
from pypdf import PdfReader
from characters_unlimited.application import CharacterApplication
from characters_unlimited.rules import RuleArchive


class WeightedSkillWorkflowTests(unittest.TestCase):
    def test_city_rat_paramedic_uses_two_related_slots_and_grows_normally(self):
        # Ultimate Edition p.88 explicitly charges two selections for Paramedic.
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides:4)
            hero = app.create(character_class='city-rat')
            hero = app.select_skills(hero['id'], revision=hero['revision'],
                selections=[{'skill_id':'paramedic','pool':'related'}])
            view = app.skill_view(hero['id'])
            self.assertEqual(view['remaining'],{'related':8,'secondary':8})
            self.assertEqual(view['selected'][0]['selection_cost'],2)
            self.assertEqual(view['selected'][0]['percentage'],50)
            hero = app.generate_resources(hero['id'], revision=hero['revision'])
            hero = app.advance(hero['id'], revision=hero['revision'], method='level', value=3)
            self.assertEqual(app.skill_view(hero['id'])['remaining'],{'related':9,'secondary':9})
            self.assertEqual(app.skill_view(hero['id'])['selected'][0]['percentage'],60)
            copy = app.import_character(app.export_character(hero['id']))
            self.assertEqual(app.skill_view(copy['id'])['remaining'],{'related':9,'secondary':9})
            reader=PdfReader(BytesIO(app.export_pdf(hero['id'])))
            fields = reader.get_fields()
            assert fields is not None
            notes = ' '.join(' '.join(str(field.get('/V','')).split()) for field in fields.values())
            self.assertIn('Paramedic: uses 2 related selections.',notes)

    def test_old_pin_requires_review_before_changing_slot_cost_and_excess_is_retained(self):
        with tempfile.TemporaryDirectory() as directory:
            archive=RuleArchive.load()
            old=RuleArchive(archive.definitions(),{**archive.active_versions(),'rifts-domestic-skills':'2.9.0'})
            previous=CharacterApplication(directory, die=lambda sides:4, rule_archive=old)
            hero=previous.create(character_class='city-rat')
            hero=previous.select_skills(hero['id'], revision=hero['revision'],
                selections=[{'skill_id':'paramedic','pool':'related'}])
            hero=previous.generate_resources(hero['id'], revision=hero['revision'])
            current=CharacterApplication(directory, die=lambda sides:self.fail('Cost update rolled dice'))
            self.assertEqual(current.skill_view(hero['id'])['remaining']['related'],9)
            preview=current.preview_rule_upgrade(hero['id'])
            self.assertEqual((preview['before_remaining']['related'],preview['after_remaining']['related']),(9,8))
            updated=current.apply_rule_upgrade(hero['id'],revision=hero['revision'],token=preview['token'])['character']
            self.assertEqual(updated['attributes'],hero['attributes'])
            self.assertEqual(updated['resources'],hero['resources'])
            self.assertEqual(current.skill_view(hero['id'])['remaining']['related'],8)
            selections=[{'skill_id':'paramedic','pool':'related'}]*6
            updated=current.select_skills(hero['id'],revision=updated['revision'],selections=selections)
            view=current.skill_view(hero['id'])
            self.assertEqual(view['remaining']['related'],-2)
            self.assertEqual(len(view['selected']),6)
            self.assertTrue(all(item['percentage']==50 for item in view['selected']))
            self.assertTrue(any('over' in note for note in view['warnings']))
            self.assertEqual(current.import_character(current.export_character(hero['id']))['skill_selections'],updated['skill_selections'])
