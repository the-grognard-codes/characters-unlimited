from io import BytesIO
import tempfile
import unittest
from pypdf import PdfReader
from characters_unlimited.application import CharacterApplication
from characters_unlimited.rules import RuleArchive


def choices(*ids,pool='related'):
    return [{'skill_id':key,'pool':pool} for key in ids]


class RidingWorkflowTests(unittest.TestCase):
    def test_all_source_pairs_and_iq_apply_to_both_checks(self):
        expected={'horse-general':(40,20,4),'horse-exotic':(30,20,5),'horse-cowboy':(66,50,3),
            'horse-cossack':(55,45,5),'horse-cyber-knight':(70,50,3),'horse-equestrian':(40,30,5)}
        with tempfile.TemporaryDirectory() as directory:
            app=CharacterApplication(directory,die=lambda sides:4)
            hero=app.create()
            hero=app.select_skills(hero['id'],revision=0,selections=choices(*expected))
            rows=app.skill_view(hero['id'])['selected']
            self.assertEqual([(row['percentage'],row['additional_checks'][0]['percentage'],row['per_level']) for row in rows],list(expected.values()))
            hero=app.set_attribute(hero['id'],revision=hero['revision'],attribute='IQ',mode='fixed',value=16)
            rows=app.skill_view(hero['id'])['selected']
            self.assertEqual([(row['percentage'],row['additional_checks'][0]['percentage']) for row in rows],[(base+2,second+2) for base,second,rate in expected.values()])
            self.assertTrue(all(row['source']['pdf_pages'] and row['description'] for row in rows))
            cowboy=next(row for row in rows if row['id']=='horse-cowboy')
            self.assertIn('levels 2/5/10/15',cowboy['description'])
            self.assertNotIn('levels 1/2',cowboy['description'])

    def test_cowboy_source_rates_and_current_pool_permissions(self):
        with tempfile.TemporaryDirectory() as directory:
            app=CharacterApplication(directory,die=lambda sides:4)
            selected=choices('branding','tame-wild-horse','herding-cattle','roping','horse-general','horse-exotic')
            for path in ['vagabond','city-rat']:
                hero=app.create(character_class=path)
                hero=app.select_skills(hero['id'],revision=0,selections=selected)
                view=app.skill_view(hero['id'])
                self.assertEqual([row['percentage'] for row in view['selected']],[50,20,30,20,40,30])
                self.assertEqual(sum('not available in the related' in note for note in view['warnings']),5 if path=='vagabond' else 6)
                app.select_skills(hero['id'],revision=hero['revision'],selections=choices('horse-general','horse-exotic','horse-cowboy','roping',pool='secondary'))
                self.assertEqual(sum('not available in the secondary' in note for note in app.skill_view(hero['id'])['warnings']),2)

    def test_required_general_training_reconciles_once_and_deactivates(self):
        with tempfile.TemporaryDirectory() as directory:
            app=CharacterApplication(directory,die=lambda sides:4)
            hero=app.create()
            hero=app.select_required_skills(hero['id'],revision=0,choices={'repair':'horse-general'})
            hero=app.select_skills(hero['id'],revision=hero['revision'],selections=choices('horse-general','horse-general'))
            view=app.skill_view(hero['id'])
            rows=[row for row in view['grants']+view['selected'] if row['id']=='horse-general']
            self.assertEqual([row['percentage'] for row in rows],[45]*3)
            self.assertEqual([row['additional_checks'][0]['percentage'] for row in rows],[25]*3)
            hero=app.select_required_skills(hero['id'],revision=hero['revision'],choices={})
            self.assertEqual([row['percentage'] for row in app.skill_view(hero['id'])['selected']],[40,40])

    def test_late_learning_reselection_import_and_undo_keep_pair_age(self):
        with tempfile.TemporaryDirectory() as directory:
            app=CharacterApplication(directory,die=lambda sides:4)
            hero=app.create(level=3)
            hero=app.select_skills(hero['id'],revision=0,selections=choices('horse-exotic','roping'))
            hero=app.advance(hero['id'],revision=hero['revision'],method='level',value=4)
            view=app.skill_view(hero['id'])
            self.assertEqual([row['percentage'] for row in view['selected']],[35,25])
            self.assertEqual(view['selected'][0]['additional_checks'][0]['percentage'],25)
            hero=app.select_skills(hero['id'],revision=hero['revision'],selections=[])
            hero=app.select_skills(hero['id'],revision=hero['revision'],selections=choices('horse-exotic','roping'))
            imported=app.import_character(app.export_character(hero['id']))
            self.assertEqual(CharacterApplication(directory).skill_view(imported['id'])['selected'],view['selected'])
            hero=app.undo_advancement(hero['id'],revision=hero['revision'])['character']
            self.assertEqual([row['percentage'] for row in app.skill_view(hero['id'])['selected']],[30,20])

    def test_old_required_general_age_survives_explicit_catalog_upgrade(self):
        installed=RuleArchive.load()
        old=RuleArchive(installed.definitions(),{**installed.active_versions(),'rifts-domestic-skills':'2.19.0'})
        with tempfile.TemporaryDirectory() as directory:
            earlier=CharacterApplication(directory,die=lambda sides:4,rule_archive=old)
            hero=earlier.create(level=3)
            hero=earlier.select_required_skills(hero['id'],revision=0,choices={'repair':'horse-general'})
            app=CharacterApplication(directory)
            self.assertEqual(len(app.skill_view(hero['id'])['catalog']),181)
            with self.assertRaises(ValueError):
                app.select_skills(hero['id'],revision=hero['revision'],selections=choices('horse-general'))
            preview=app.preview_rule_upgrade(hero['id'])
            self.assertEqual(preview['changes'][0]['to'],'2.33.0')
            hero=app.apply_rule_upgrade(hero['id'],revision=hero['revision'],token=preview['token'])['character']
            hero=app.select_skills(hero['id'],revision=hero['revision'],selections=choices('horse-general'))
            rows=[row for row in app.skill_view(hero['id'])['grants']+app.skill_view(hero['id'])['selected'] if row['id']=='horse-general']
            self.assertEqual([row['percentage'] for row in rows],[53,53])
            self.assertEqual([row['additional_checks'][0]['percentage'] for row in rows],[33,33])
            self.assertEqual(len(app.skill_view(hero['id'])['catalog']),210)

    def test_specialized_riding_retains_source_eligibility_and_no_global_mounted_bonus(self):
        with tempfile.TemporaryDirectory() as directory:
            app=CharacterApplication(directory,die=lambda sides:4)
            hero=app.create()
            before=app.combat_view(hero['id'])
            app.select_skills(hero['id'],revision=0,selections=choices('horse-cowboy','horse-cossack','horse-cyber-knight','horse-equestrian'))
            view=app.skill_view(hero['id'])
            self.assertEqual(sum('not available in the related' in note for note in view['warnings']),4)
            self.assertIn('Exclusive to the Cossack',view['selected'][1]['description'])
            self.assertEqual(app.combat_view(hero['id']),before)

    def test_editable_pdf_retains_normal_riding_pair_and_descriptive_sources(self):
        with tempfile.TemporaryDirectory() as directory:
            app=CharacterApplication(directory,die=lambda sides:4)
            hero=app.create(name='Riding proof')
            app.select_skills(hero['id'],revision=0,selections=choices('horse-general','horse-exotic','tame-wild-horse'))
            reader=PdfReader(BytesIO(app.export_pdf(hero['id'])))
            text=' '.join(str(row.get('/V','')) for row in (reader.get_fields() or {}).values())
            for phrase in ['Horsemanship: General','Jumping and other special maneuvers','Exotic Animals','Breaking/Taming']:
                self.assertIn(phrase,text)
            self.assertTrue(any(page.get('/Annots') for page in reader.pages))
