from io import BytesIO
import tempfile
import unittest

from pypdf import PdfReader
from characters_unlimited.application import CharacterApplication
from characters_unlimited.advancement import learning_key
from characters_unlimited.rules import RuleArchive


def choices(*identities, pool='related'):
    return [{'skill_id':identity,'pool':pool} for identity in identities]


class MilitarySkillWorkflowTests(unittest.TestCase):
    def test_source_catalog_normal_percentages_and_secondary_allowance(self):
        expected = {'camouflage':(20,5),'demolitions':(60,3),'demolitions-disposal':(60,3),
            'demolitions-underwater':(56,4),'field-armorer':(40,5),'military-etiquette':(35,5),
            'military-fortification':(30,5),'naval-history':(30,5),'naval-tactics':(25,5),
            'nbc-warfare':(35,5),'parachuting':(40,5),'recognize-weapon-quality':(25,5),
            'trap-mine-detection':(20,5)}
        with tempfile.TemporaryDirectory() as directory:
            app=CharacterApplication(directory,die=lambda sides:4)
            for path in ('vagabond','city-rat'):
                hero=app.create(character_class=path)
                catalog={row['id']:row for row in app.skill_view(hero['id'])['catalog'] if row.get('category')=='military'}
                self.assertEqual({key:(row['base'],row['per_level']) for key,row in catalog.items()},expected)
                self.assertTrue(all(row['description'] and row['source']['pdf_pages'] for row in catalog.values()))
                hero=app.select_skills(hero['id'],revision=0,selections=choices(*expected))
                view=app.skill_view(hero['id'])
                self.assertEqual([row['percentage'] for row in view['selected']],[pair[0] for pair in expected.values()])
                self.assertEqual(len([note for note in view['warnings'] if 'not available in the related' in note]),13)
                app.select_skills(hero['id'],revision=hero['revision'],selections=choices(*expected,pool='secondary'))
                view=app.skill_view(hero['id'])
                unavailable=[note for note in view['warnings'] if 'not available in the secondary' in note]
                self.assertEqual(len(unavailable),11)
                self.assertFalse(any('Camouflage:' in note or 'Recognize Weapon Quality:' in note for note in unavailable))

    def test_automatic_mechanics_overlap_and_last_parent_removal(self):
        with tempfile.TemporaryDirectory() as directory:
            app=CharacterApplication(directory,die=lambda sides:4)
            hero=app.create()
            for identities,percentage,origins in [(('field-armorer',),30,1),
                    (('field-armorer','vehicle-armorer','field-armorer'),50,2),
                    (('field-armorer',),30,1)]:
                hero=app.select_skills(hero['id'],revision=hero['revision'],selections=choices(*identities))
                grant=next(row for row in app.skill_view(hero['id'])['grants'] if row['id']=='basic-mechanics')
                self.assertEqual((grant['percentage'],len(grant['grant_origins'])),(percentage,origins))
            hero=app.select_skills(hero['id'],revision=hero['revision'],selections=[])
            self.assertFalse(any(row['id']=='basic-mechanics' for row in app.skill_view(hero['id'])['grants']))
            self.assertEqual(hero.get('learning_levels',{}).get(learning_key('skill','basic-mechanics'),1),1)

    def test_jury_rig_alternative_training_bonus_applies_once_and_recalculates(self):
        with tempfile.TemporaryDirectory() as directory:
            app=CharacterApplication(directory,die=lambda sides:4)
            for path,base in [('vagabond',30),('city-rat',35)]:
                hero=app.create(character_class=path)
                for parents in [('field-armorer',),('electrical-engineer',),('mechanical-engineer',),
                        ('field-armorer','electrical-engineer','mechanical-engineer'),()]:
                    hero=app.select_skills(hero['id'],revision=hero['revision'],selections=choices('jury-rig',*parents))
                    row=app.skill_view(hero['id'])['selected'][0]
                    self.assertEqual(row['percentage'],base+(10 if parents else 0))
                    self.assertEqual(row['contributions'].get('engineering_or_field_armorer',0),10 if parents else 0)
                hero=app.select_skills(hero['id'],revision=hero['revision'],selections=[
                    *choices('jury-rig',pool='secondary'),*choices('field-armorer')])
                view=app.skill_view(hero['id'])
                self.assertEqual(view['selected'][0]['percentage'],35)
                self.assertFalse(any('Jury-Rig: not available' in note for note in view['warnings']))

    def test_jury_rig_prerequisites_accept_granted_mechanics_and_engineer_alternatives(self):
        with tempfile.TemporaryDirectory() as directory:
            app=CharacterApplication(directory,die=lambda sides:4)
            hero=app.create()
            for identities,missing in [(('jury-rig',),True),
                    (('jury-rig','field-armorer'),True),
                    (('jury-rig','field-armorer','basic-electronics'),False),
                    (('jury-rig','mechanical-engineer','electrical-engineer'),False),
                    (('jury-rig','basic-mechanics','basic-electronics'),False)]:
                hero=app.select_skills(hero['id'],revision=hero['revision'],selections=choices(*identities))
                self.assertEqual(any('Jury-Rig: missing prerequisite' in note for note in app.skill_view(hero['id'])['warnings']),missing)

    def test_late_parent_learning_advance_reselection_import_and_editable_sheet(self):
        with tempfile.TemporaryDirectory() as directory:
            app=CharacterApplication(directory,die=lambda sides:4)
            hero=app.create(level=3)
            hero=app.select_skills(hero['id'],revision=0,selections=choices('field-armorer','jury-rig','basic-electronics'))
            view=app.skill_view(hero['id'])
            self.assertEqual([row['percentage'] for row in view['selected']],[40,40,35])
            self.assertEqual(next(row for row in view['grants'] if row['id']=='basic-mechanics')['percentage'],30)
            self.assertEqual(hero['learning_levels'][learning_key('skill','basic-mechanics')],3)
            hero=app.advance(hero['id'],revision=hero['revision'],method='level',value=4)
            self.assertEqual([row['percentage'] for row in app.skill_view(hero['id'])['selected']],[45,45,40])
            hero=app.select_skills(hero['id'],revision=hero['revision'],selections=[])
            hero=app.select_skills(hero['id'],revision=hero['revision'],selections=choices('field-armorer','jury-rig','basic-electronics'))
            view=app.skill_view(hero['id'])
            self.assertEqual(next(row for row in view['grants'] if row['id']=='basic-mechanics')['percentage'],35)
            imported=app.import_character(app.export_character(hero['id']))
            reopened=CharacterApplication(directory)
            self.assertEqual(reopened.skill_view(imported['id'])['selected'],view['selected'])
            self.assertEqual(reopened.skill_view(imported['id'])['grants'],view['grants'])
            fields=PdfReader(BytesIO(app.export_pdf(hero['id']))).get_fields() or {}
            text=' '.join(str(row.get('/V','')) for row in fields.values())
            self.assertIn('Field Armorer',text)
            self.assertIn('Jury-Rig',text)
            self.assertIn('Basic Mechanics',text)

    def test_exact_old_pin_keeps_catalog_until_explicit_upgrade(self):
        archive=RuleArchive.load()
        old=RuleArchive(archive.definitions(),{**archive.active_versions(),'rifts-domestic-skills':'2.15.0'})
        with tempfile.TemporaryDirectory() as directory:
            earlier=CharacterApplication(directory,die=lambda sides:4,rule_archive=old)
            hero=earlier.create()
            hero=earlier.select_skills(hero['id'],revision=0,selections=choices('vehicle-armorer'))
            app=CharacterApplication(directory)
            before=app.skill_view(hero['id'])
            self.assertEqual(len(before['catalog']),100)
            self.assertFalse(any(row['id']=='field-armorer' for row in before['catalog']))
            preview=app.preview_rule_upgrade(hero['id'])
            self.assertEqual(preview['changes'][0]['to'],'2.21.0')
            app.apply_rule_upgrade(hero['id'],revision=hero['revision'],token=preview['token'])
            view=app.skill_view(hero['id'])
            self.assertEqual(len(view['catalog']),200)
            self.assertEqual(view['selected'],before['selected'])
            self.assertEqual(view['grants'],before['grants'])
