from io import BytesIO
from pathlib import Path
import tempfile
import unittest

from pypdf import PdfReader
from characters_unlimited.application import CharacterApplication
from characters_unlimited.rules import RuleArchive


def choices(*identities,pool='secondary',specialty=''):
    return [{'skill_id':key,'pool':pool,'specialty':specialty} for key in identities]


class RemainingTechnicalWorkflowTests(unittest.TestCase):
    def test_source_values_normal_pairs_and_class_training(self):
        expected={'appraise-goods':(30,5),'begging':(30,3),'breed-dogs':(40,5),
            'cybernetics-basic':(25,5),'excavation':(30,5),'gemology':(25,5),'general-repair':(35,5),
            'lore-american-indians':(25,5),'lore-cattle-animals':(30,5),'lore-dbee':(25,5),
            'lore-demons-monsters':(25,5),'lore-faeries-magic-creatures':(25,5),'lore-juicer':(30,5),
            'lore-magic':(25,5),'lore-psychics':(25,5),'mining':(35,5),'mythology':(30,5),
            'salvage':(35,5),'whittling-sculpting':(30,5)}
        with tempfile.TemporaryDirectory() as directory:
            app=CharacterApplication(directory,die=lambda sides:4)
            for path,bonus in [('vagabond',5),('city-rat',10)]:
                hero=app.create(character_class=path)
                catalog={row['id']:row for row in app.skill_view(hero['id'])['catalog']}
                self.assertEqual({key:(catalog[key]['base'],catalog[key]['per_level']) for key in expected},expected)
                self.assertEqual(len(catalog),211)
                app.select_skills(hero['id'],revision=0,selections=choices('breed-dogs','lore-magic',pool='related'))
                selected=app.skill_view(hero['id'])['selected']
                self.assertEqual([row['percentage'] for row in selected],[40+bonus,25+bonus])
                self.assertEqual(selected[0]['additional_checks'][0]['percentage'],20+bonus)
                self.assertEqual([row['percentage'] for row in selected[1]['additional_checks']],[15+bonus,10+bonus])

    def test_old_parent_training_synergies_apply_once_and_remove(self):
        with tempfile.TemporaryDirectory() as directory:
            app=CharacterApplication(directory,die=lambda sides:4)
            hero=app.create()
            target=choices('lore-magic','lore-juicer','mining','spelunking')+choices('lore-demons-monsters',specialty='North America')
            parents=choices('anthropology','archaeology','chemistry-pharmaceutical','gemology','excavation')+choices('mythology',specialty='North America')
            hero=app.select_skills(hero['id'],revision=0,selections=target+parents+parents)
            rows={row['id']:row for row in app.skill_view(hero['id'])['selected']}
            self.assertEqual([rows[key]['percentage'] for key in ['lore-magic','lore-juicer','mining','spelunking','lore-demons-monsters']],[37,47,40,40,37])
            self.assertEqual([check['percentage'] for check in rows['lore-magic']['additional_checks']],[27,22])
            app.select_skills(hero['id'],revision=hero['revision'],selections=target)
            self.assertEqual([row['percentage'] for row in app.skill_view(hero['id'])['selected']],[25,30,35,35,25])

    def test_repeated_quality_and_specialties_remain_distinct(self):
        with tempfile.TemporaryDirectory() as directory:
            app=CharacterApplication(directory,die=lambda sides:4)
            hero=app.create()
            selection=choices('whittling-sculpting')+choices('appraise-goods',specialty='Magic items')
            hero=app.select_skills(hero['id'],revision=0,selections=selection)
            self.assertEqual(app.skill_view(hero['id'])['selected'][0]['quality'],'amateur')
            hero=app.select_skills(hero['id'],revision=hero['revision'],selections=selection*3)
            rows=app.skill_view(hero['id'])['selected']
            self.assertEqual([row['percentage'] for row in rows],[40,45]*3)
            self.assertEqual(rows[0]['quality'],'professional')
            self.assertEqual(rows[1]['specialty'],'Magic items')
            imported=app.import_character(app.export_character(hero['id']))
            self.assertEqual(app.skill_view(imported['id'])['selected'],rows)

    def test_source_conditional_checks_are_explicit_and_capped(self):
        with tempfile.TemporaryDirectory() as directory:
            app=CharacterApplication(directory,die=lambda sides:4)
            hero=app.create()
            hero=app.select_skills(hero['id'],revision=0,selections=choices('lore-american-indians')+choices('lore-dbee',specialty='North America'))
            rows=app.skill_view(hero['id'])['selected']
            self.assertEqual([row['percentage'] for row in rows],[25,25])
            self.assertEqual([row['additional_checks'][0]['percentage'] for row in rows],[35,35])
            self.assertIn('descent only',rows[0]['additional_checks'][0]['name'])
            self.assertIn('region only',rows[1]['additional_checks'][0]['name'])
            hero=app.set_attribute(hero['id'],revision=hero['revision'],attribute='IQ',mode='fixed',value=300)
            rows=app.skill_view(hero['id'])['selected']
            self.assertEqual([row['additional_checks'][0]['percentage'] for row in rows],[98,98])

    def test_late_learning_locale_import_and_undo_keep_normal_skill_age(self):
        with tempfile.TemporaryDirectory() as directory:
            app=CharacterApplication(directory,die=lambda sides:4)
            hero=app.create(level=3)
            selected=choices('lore-demons-monsters',specialty='Europe')+choices('breed-dogs','lore-magic')
            hero=app.select_skills(hero['id'],revision=0,selections=selected)
            hero=app.advance(hero['id'],revision=hero['revision'],method='level',value=4)
            view=app.skill_view(hero['id'])
            self.assertEqual([row['percentage'] for row in view['selected']],[30,45,30])
            self.assertEqual(view['selected'][1]['additional_checks'][0]['percentage'],25)
            imported=app.import_character(app.export_character(hero['id']))
            self.assertEqual(CharacterApplication(directory).skill_view(imported['id'])['selected'],view['selected'])
            hero=app.undo_advancement(hero['id'],revision=hero['revision'])['character']
            self.assertEqual([row['percentage'] for row in app.skill_view(hero['id'])['selected']],[25,40,25])

    def test_old_pin_requires_explicit_upgrade_and_retains_existing_choices(self):
        installed=RuleArchive.load()
        old=RuleArchive(installed.definitions(),{**installed.active_versions(),'rifts-domestic-skills':'2.18.0'})
        with tempfile.TemporaryDirectory() as directory:
            earlier=CharacterApplication(directory,die=lambda sides:4,rule_archive=old)
            hero=earlier.create()
            hero=earlier.select_skills(hero['id'],revision=0,selections=choices('research','rope-works','recycle'))
            app=CharacterApplication(directory)
            self.assertEqual(len(app.skill_view(hero['id'])['catalog']),162)
            before=app.get(hero['id'])
            with self.assertRaises(ValueError):
                app.select_skills(hero['id'],revision=before['revision'],selections=choices('salvage'))
            self.assertEqual(app.get(hero['id']),before)
            preview=app.preview_rule_upgrade(hero['id'])
            self.assertEqual(preview['changes'][0]['to'],'2.34.0')
            hero=app.apply_rule_upgrade(hero['id'],revision=before['revision'],token=preview['token'])['character']
            self.assertEqual(len(app.skill_view(hero['id'])['catalog']),211)
            self.assertEqual([row['id'] for row in app.skill_view(hero['id'])['selected']],['research','rope-works','recycle'])

    def test_editable_pdf_retains_magic_dog_checks_and_source_guidance(self):
        with tempfile.TemporaryDirectory() as directory:
            app=CharacterApplication(directory,die=lambda sides:4)
            hero=app.create(name='Technical investigator')
            app.select_skills(hero['id'],revision=0,selections=choices('lore-magic','breed-dogs','cybernetics-basic'))
            reader=PdfReader(BytesIO(app.export_pdf(hero['id'])))
            fields=reader.get_fields() or {}
            text=' '.join(str(row.get('/V','')) for row in fields.values())
            for phrase in ['Recognize enchantment','Train tricks or work tasks','Cybernetics: Basic','Cannot perform surgery']:
                self.assertIn(phrase,text)
            self.assertTrue(any(page.get('/Annots') for page in reader.pages))
