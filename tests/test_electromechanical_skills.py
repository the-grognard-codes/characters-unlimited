from io import BytesIO
import tempfile
import unittest

from pypdf import PdfReader
from characters_unlimited.application import CharacterApplication
from characters_unlimited.rules import RuleArchive


class ElectromechanicalSkillWorkflowTests(unittest.TestCase):
    def test_source_reviewed_catalog_and_separate_normal_repair_checks(self):
        expected = {'basic-electronics':30,'computer-repair':30,'electrical-engineer':35,
            'electricity-generation':50,'robot-electronics':30,'aircraft-mechanics':25,
            'automotive-mechanics':25,'basic-mechanics':30,'bioware-mechanics':30,
            'locksmith':25,'mechanical-engineer':25,'robot-mechanics':20,'weapons-engineer':25,'vehicle-armorer':30}
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory,die=lambda sides:4)
            hero = app.create()
            catalog = {row['id']:row for row in app.skill_view(hero['id'])['catalog']
                       if row.get('category') in ('electrical','mechanical')}
            self.assertEqual({key:row['base'] for key,row in catalog.items()},expected)
            self.assertTrue(all(row['per_level']==5 and row['description'] and row['source']['pdf_pages'] for row in catalog.values()))
            app.select_skills(hero['id'],revision=0,selections=[
                {'skill_id':'computer-repair','pool':'secondary'}, {'skill_id':'mechanical-engineer','pool':'related'}])
            selected = app.skill_view(hero['id'])['selected']
            self.assertEqual([row['percentage'] for row in selected],[30,25])
            self.assertEqual([row['percentage'] for row in selected[0]['additional_checks']],[30])
            self.assertEqual([row['percentage'] for row in selected[1]['additional_checks']],[25,25])

    def test_normal_engineer_synergies_apply_once_and_removal_recalculates(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory,die=lambda sides:4)
            hero = app.create()
            hero = app.set_attribute(hero['id'],revision=0,attribute='ME',mode='fixed',value=15)
            selections = [{'skill_id':name,'pool':'related'} for name in
                ('locksmith','electrical-engineer','mechanical-engineer','mechanical-engineer','surveillance','safe-cracking')]
            hero = app.select_skills(hero['id'],revision=hero['revision'],selections=selections)
            selected = {row['id']:row for row in app.skill_view(hero['id'])['selected']}
            self.assertEqual([selected[key]['percentage'] for key in ('locksmith','surveillance','safe-cracking')],[35,35,34])
            self.assertEqual(selected['locksmith']['contributions']['mechanical_engineer'],5)
            self.assertFalse(any('Surveillance: missing prerequisite' in note for note in app.skill_view(hero['id'])['warnings']))
            selections = [row for row in selections if row['skill_id']!='mechanical-engineer']
            app.select_skills(hero['id'],revision=hero['revision'],selections=selections)
            selected = {row['id']:row for row in app.skill_view(hero['id'])['selected']}
            self.assertEqual([selected[key]['percentage'] for key in ('locksmith','surveillance','safe-cracking')],[30,30,28])

    def test_prerequisites_use_learned_identities_and_named_literacy(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory,die=lambda sides:4)
            hero = app.create()
            selections = [{'skill_id':name,'pool':'related'} for name in
                ('electrical-engineer','electricity-generation','robot-electronics','bioware-mechanics',
                 'locksmith','mechanical-engineer','robot-mechanics','weapons-engineer')]
            hero = app.select_skills(hero['id'],revision=0,selections=selections)
            self.assertTrue(any('missing prerequisite' in note for note in app.skill_view(hero['id'])['warnings']))
            selections += [{'skill_id':name,'pool':'related'} for name in
                ('basic-electronics','math-basic','math-advanced','computer-operation','computer-programming')]
            selections.append({'skill_id':'literacy-other','pool':'related','specialty':''})
            hero = app.select_skills(hero['id'],revision=hero['revision'],selections=selections)
            self.assertTrue(any('Electrical Engineer: missing prerequisite' in note for note in app.skill_view(hero['id'])['warnings']))
            selections[-1]['specialty']='Dragonese'
            app.select_skills(hero['id'],revision=hero['revision'],selections=selections)
            self.assertFalse(any('missing prerequisite' in note for note in app.skill_view(hero['id'])['warnings']))

    def test_class_related_bonuses_and_secondary_exceptions_are_preserved(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory,die=lambda sides:4)
            for character_class,expected in [('vagabond',[35,30,35,30]),('city-rat',[35,35,40,35])]:
                hero = app.create(character_class=character_class)
                app.select_skills(hero['id'],revision=0,selections=[{'skill_id':name,'pool':'related'} for name in
                    ('basic-electronics','computer-repair','basic-mechanics','automotive-mechanics')])
                self.assertEqual([row['percentage'] for row in app.skill_view(hero['id'])['selected']],expected)
                hero = app.get(hero['id'])
                app.select_skills(hero['id'],revision=hero['revision'],selections=[{'skill_id':name,'pool':'secondary'} for name in
                    ('basic-electronics','computer-repair','basic-mechanics','automotive-mechanics','electrical-engineer','robot-mechanics')])
                view = app.skill_view(hero['id'])
                self.assertEqual([row['percentage'] for row in view['selected']],[30,30,30,25,35,20])
                unavailable = [note for note in view['warnings'] if 'not available in the secondary' in note]
                self.assertEqual(len(unavailable),2)
                self.assertTrue(any('Electrical Engineer:' in note for note in unavailable))
                self.assertTrue(any('Robot Mechanics:' in note for note in unavailable))

    def test_old_pins_upgrade_late_learning_reopening_and_editable_pdf(self):
        archive = RuleArchive.load()
        old = RuleArchive(archive.definitions(),{**archive.active_versions(),'rifts-domestic-skills':'2.13.0'})
        with tempfile.TemporaryDirectory() as directory:
            earlier = CharacterApplication(directory,die=lambda sides:4,rule_archive=old)
            hero = earlier.create(level=3)
            earlier.select_skills(hero['id'],revision=0,learned_level=1,selections=[{'skill_id':'computer-repair','pool':'secondary'}])
            app = CharacterApplication(directory,die=lambda sides:4)
            hero = app.get(hero['id'])
            self.assertEqual(len(app.skill_view(hero['id'])['catalog']),90)
            self.assertEqual(app.skill_view(hero['id'])['selected'][0]['additional_checks'],[])
            preview = app.preview_rule_upgrade(hero['id'])
            self.assertEqual(preview['changes'][0]['to'],'2.26.0')
            hero = app.apply_rule_upgrade(hero['id'],revision=hero['revision'],token=preview['token'])['character']
            self.assertEqual(len(app.skill_view(hero['id'])['catalog']),206)
            self.assertEqual(app.skill_view(hero['id'])['selected'][0]['additional_checks'][0]['percentage'],40)
            hero = app.select_skills(hero['id'],revision=hero['revision'],learned_level=3,selections=[{'skill_id':'mechanical-engineer','pool':'related'}])
            self.assertEqual(app.skill_view(hero['id'])['selected'][0]['percentage'],25)
            hero = app.advance(hero['id'],revision=hero['revision'],method='level',value=4)
            self.assertEqual(app.skill_view(hero['id'])['selected'][0]['percentage'],30)
            imported = app.import_character(app.export_character(hero['id']))
            reopened = CharacterApplication(directory)
            self.assertEqual(reopened.skill_view(imported['id'])['selected'],app.skill_view(hero['id'])['selected'])
            fields = PdfReader(BytesIO(app.export_pdf(hero['id']))).get_fields()
            values = ' '.join(str(row.get('/V','')) for row in (fields or {}).values())
            self.assertIn('Mechanical Engineer',values)
            self.assertIn('Verify completed work',values)
