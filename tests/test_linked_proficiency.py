"""A training percentage uses its learned source, never an invented new base."""
from copy import deepcopy
import tempfile
import unittest
from io import BytesIO
from pypdf import PdfReader
from typing import Any
from characters_unlimited.application import CharacterApplication
from characters_unlimited.rules import RuleArchive


class LinkedProficiencyTests(unittest.TestCase):
    archive = staticmethod(RuleArchive.load)
    declaration: Any = None

    def fixture(self,*,grant=True,mutation=None):
        original = self.archive()
        skills = original.active('rifts-domestic-skills')
        skills['version'] = 'linked-proficiency-fixture'
        declaration = deepcopy(self.declaration if self.declaration is not None else
                               next(row for row in skills['skills'] if row['id']=='trick-riding'))
        skills['skills'] = [row for row in skills['skills'] if row['id']!=declaration['id']]
        skills['skills'].append(declaration)
        profile = skills['class_profiles']['vagabond']
        profile['selection_rules']['related']['cowboy'] = {'allow':['trick-riding'],'bonus':0}
        profile['selection_rules']['related']['horsemanship'] = {'allow':'any','bonus':0}
        if grant:
            horse = deepcopy(next(row for row in skills['skills'] if row['id']=='horse-cyber-knight'))
            horse.update(catalog_skill_id=horse['id'],class_bonus=0)
            profile['required']['grants'].append(horse)
        if mutation:
            mutation(skills)
        return RuleArchive([*original.definitions(),skills],{**original.active_versions(),'rifts-domestic-skills':skills['version']})

    def no_roll(self,sides):
        self.fail('Linked proficiency and portable replay must not draw dice')

    def test_later_acquisition_uses_existing_growth_and_iq_once(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory,die=lambda sides:3,rule_archive=self.fixture())
            hero = app.create()
            hero = app.generate_resources(hero['id'],revision=hero['revision'])
            hero = app.advance(hero['id'],revision=hero['revision'],method='level',value=3)
            app.die = self.no_roll
            hero = app.select_skills(hero['id'],revision=hero['revision'],selections=[
                {'skill_id':'trick-riding','pool':'related','specialty':''}])
            trick = next(row for row in app.skill_view(hero['id'])['selected'] if row['id']=='trick-riding')
            self.assertEqual((trick['percentage'],trick['per_level']),(76,3))
            self.assertEqual(trick['contributions'],{'referenced_proficiency':76})
            hero = app.set_attribute(hero['id'],revision=hero['revision'],attribute='IQ',mode='fixed',value=20)
            trick = next(row for row in app.skill_view(hero['id'])['selected'] if row['id']=='trick-riding')
            self.assertEqual(trick['percentage'],82)
            self.assertEqual(trick['contributions'],{'referenced_proficiency':82})
            restored = app.import_character(app.export_character(hero['id']))
            self.assertEqual(app.skill_view(restored['id'])['selected'],app.skill_view(hero['id'])['selected'])
            self.assertEqual(CharacterApplication(directory,die=self.no_roll,rule_archive=self.fixture()).get(hero['id']),hero)

    def test_source_cap_and_rate_are_retained_without_new_growth(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory,die=lambda sides:3,rule_archive=self.fixture())
            hero = app.create()
            hero = app.generate_resources(hero['id'],revision=hero['revision'])
            hero = app.advance(hero['id'],revision=hero['revision'],method='level',value=15)
            app.die = self.no_roll
            hero = app.select_skills(hero['id'],revision=hero['revision'],selections=[
                {'skill_id':'trick-riding','pool':'related','specialty':''}])
            trick = next(row for row in app.skill_view(hero['id'])['selected'] if row['id']=='trick-riding')
            self.assertEqual((trick['percentage'],trick['uncapped_percentage'],trick['per_level']),(98,112,3))
            self.assertEqual(trick['contributions'],{'referenced_proficiency':112})
            app.import_character(app.export_character(hero['id']))

    def test_missing_learned_source_retains_training_and_prerequisite_guidance(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory,die=lambda sides:3,rule_archive=self.fixture(grant=False))
            hero = app.create()
            hero = app.select_skills(hero['id'],revision=hero['revision'],selections=[
                {'skill_id':'trick-riding','pool':'related','specialty':''}])
            view = app.skill_view(hero['id'])
            trick = next(row for row in view['selected'] if row['id']=='trick-riding')
            self.assertNotIn('percentage',trick)
            self.assertTrue(any('missing prerequisite' in text for text in view['warnings']))
            app.die = self.no_roll
            app.import_character(app.export_character(hero['id']))

    def test_malformed_inactive_reference_rejects_before_dice_and_save(self):
        source: dict[str, Any] | None
        for options,source in [([],{}),(['unknown'],{}),(['trick-riding'],{}),
                              (['horse-general','horse-general'],{}),(['horse-general'],None)]:
            def mutate(skills):
                row = next(row for row in skills['skills'] if row['id']=='trick-riding')
                row['proficiency_reference'] = {'options':options,'source':source}
            with self.subTest(options=options,source=source),tempfile.TemporaryDirectory() as directory:
                app = CharacterApplication(directory,die=self.no_roll,rule_archive=self.fixture(mutation=mutate))
                with self.assertRaises(ValueError):
                    app.create()
                self.assertEqual(app.list(),[])

    def test_best_learned_primary_is_used_in_editable_pdf_without_combat_check(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory,die=lambda sides:3,rule_archive=self.fixture(grant=False))
            hero = app.create()
            hero = app.select_skills(hero['id'],revision=hero['revision'],selections=[
                {'skill_id':key,'pool':'related','specialty':''} for key in ('horse-general','horse-exotic','trick-riding')])
            view = app.skill_view(hero['id'])
            trick = next(row for row in view['selected'] if row['id']=='trick-riding')
            self.assertEqual((trick['percentage'],trick['per_level']),(40,4))
            self.assertEqual(trick['proficiency_origin']['id'],'horse-general')
            self.assertNotIn('additional_checks',trick)
            app.die = self.no_roll
            reader = PdfReader(BytesIO(app.export_pdf(hero['id'])))
            found = False
            for page in reader.pages:
                widgets = [ref.get_object() for ref in page.get('/Annots',[])
                           if ref.get_object().get('/Subtype')=='/Widget']
                for widget in widgets:
                    if str(widget.get('/V',''))!='Trick Riding':
                        continue
                    x,y = float(widget['/Rect'][0]),float(widget['/Rect'][1])
                    rate = next(row for row in widgets if abs(float(row['/Rect'][0])-x-136)<2 and abs(float(row['/Rect'][1])-y)<1)
                    percentage = next(row for row in widgets if abs(float(row['/Rect'][0])-x-153)<2 and abs(float(row['/Rect'][1])-y)<1)
                    self.assertEqual(str(rate.get('/V','')),'4')
                    self.assertEqual(str(percentage.get('/V','')),'40')
                    self.assertIn('/AP',percentage)
                    found = True
            self.assertTrue(found,'Editable Trick Riding percentage row is required')
