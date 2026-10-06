from io import BytesIO
from copy import deepcopy
import tempfile
import unittest
from pypdf import PdfReader
from characters_unlimited.application import CharacterApplication
from characters_unlimited.rules import RuleArchive


def choices(*ids,pool='related'):
    return [{'skill_id':key,'pool':pool} for key in ids]


class RemainingPhysicalWorkflowTests(unittest.TestCase):
    def test_climbing_improves_spelunking_once_and_removal_restores(self):
        with tempfile.TemporaryDirectory() as directory:
            app=CharacterApplication(directory,die=lambda sides:4);hero=app.create()
            hero=app.select_skills(hero['id'],revision=0,selections=choices('spelunking','climbing','climbing'))
            row=app.skill_view(hero['id'])['selected'][0]
            self.assertEqual(row['percentage'],40);self.assertEqual(row['contributions']['Climbing'],5)
            hero=app.select_skills(hero['id'],revision=hero['revision'],selections=choices('spelunking'))
            self.assertEqual(app.skill_view(hero['id'])['selected'][0]['percentage'],35)

    def test_weapon_prerequisite_tracks_combat_training_without_granting_it(self):
        with tempfile.TemporaryDirectory() as directory:
            app=CharacterApplication(directory,die=lambda sides:4);hero=app.create()
            hero=app.select_skills(hero['id'],revision=0,selections=choices('fencing'))
            self.assertTrue(any('Fencing: missing prerequisite W.P. Sword' in note for note in app.skill_view(hero['id'])['warnings']))
            hero=app.select_combat(hero['id'],revision=hero['revision'],choices={'ancient':['sword','sword']})
            self.assertFalse(any('Fencing: missing prerequisite' in note for note in app.skill_view(hero['id'])['warnings']))
            imported=app.import_character(app.export_character(hero['id']))
            self.assertFalse(any('Fencing: missing prerequisite' in note for note in CharacterApplication(directory).skill_view(imported['id'])['warnings']))
            app.select_combat(hero['id'],revision=hero['revision'],choices={})
            self.assertTrue(any('Fencing: missing prerequisite' in note for note in app.skill_view(hero['id'])['warnings']))

    def test_invalid_weapon_prerequisites_reject_before_initial_dice(self):
        installed=RuleArchive.load()
        accepted=next(pack for pack in installed.definitions() if pack['id']=='rifts-domestic-skills' and pack['version']==installed.active_versions()['rifts-domestic-skills'])
        for change in [{'family':'unknown'},{'id':'absent'},{'source':{}},{'extra':True}]:
            pack=deepcopy(accepted);pack['version']='9.99.0'
            next(row for row in pack['skills'] if row['id']=='fencing')['weapon_prerequisites'][0].update(change)
            archive=RuleArchive(installed.definitions()+[pack],{**installed.active_versions(),pack['id']:pack['version']})
            with self.subTest(change=change),tempfile.TemporaryDirectory() as directory:
                draws=[]
                def die(sides):
                    draws.append(sides)
                    return 4
                app=CharacterApplication(directory,die=die,rule_archive=archive)
                with self.assertRaises(ValueError):app.create()
                self.assertEqual(draws,[])

    def test_normal_checks_iq_and_class_training(self):
        with tempfile.TemporaryDirectory() as directory:
            app=CharacterApplication(directory,die=lambda sides:4)
            for path,bonus in [('vagabond',0),('city-rat',5)]:
                hero=app.create(character_class=path)
                hero=app.select_skills(hero['id'],revision=0,selections=choices('climbing','aerobic-athletics','juggling','scuba'))
                rows=app.skill_view(hero['id'])['selected']
                self.assertEqual([row['percentage'] for row in rows],[40+bonus,30+bonus,35+bonus,50])
                self.assertEqual(rows[0]['additional_checks'][0]['percentage'],30+bonus)
                hero=app.set_attribute(hero['id'],revision=hero['revision'],attribute='IQ',mode='fixed',value=16)
                rows=app.skill_view(hero['id'])['selected']
                self.assertEqual(rows[0]['percentage'],42+bonus)
                self.assertEqual(rows[0]['additional_checks'][0]['percentage'],32+bonus)

    def test_prerequisites_and_secondary_permissions(self):
        with tempfile.TemporaryDirectory() as directory:
            app=CharacterApplication(directory,die=lambda sides:4);hero=app.create()
            hero=app.select_skills(hero['id'],revision=0,selections=choices('scuba','outdoorsmanship','climbing','aerobic-athletics',pool='secondary'))
            warnings=app.skill_view(hero['id'])['warnings']
            self.assertEqual(sum('missing prerequisite' in note for note in warnings),2)
            self.assertEqual(sum('not available in the secondary' in note for note in warnings),2)
            app.select_skills(hero['id'],revision=hero['revision'],selections=choices('scuba','outdoorsmanship','swimming','wilderness-survival'))
            self.assertFalse(any('missing prerequisite' in note for note in app.skill_view(hero['id'])['warnings']))

    def test_outdoorsmanship_synergies_once_and_deactivate(self):
        targets=['dowsing','fasting','identify-plants-fruit','wilderness-survival']
        with tempfile.TemporaryDirectory() as directory:
            app=CharacterApplication(directory,die=lambda sides:4);hero=app.create()
            hero=app.select_skills(hero['id'],revision=0,selections=choices(*targets))
            before=[row['percentage'] for row in app.skill_view(hero['id'])['selected']]
            hero=app.select_skills(hero['id'],revision=hero['revision'],selections=choices(*targets,'outdoorsmanship','outdoorsmanship'))
            rows=app.skill_view(hero['id'])['selected'][:4]
            self.assertEqual([row['percentage'] for row in rows],[value+5 for value in before])
            self.assertTrue(all(row['contributions']['Outdoorsmanship']==5 for row in rows))
            app.select_skills(hero['id'],revision=hero['revision'],selections=choices(*targets))
            self.assertEqual([row['percentage'] for row in app.skill_view(hero['id'])['selected']],before)

    def test_retained_attributes_resource_dice_and_initiative_once(self):
        ids=['forced-march','outdoorsmanship','wrestling','kick-boxing','aerobic-athletics','juggling']
        with tempfile.TemporaryDirectory() as directory:
            faces=[]
            def die(sides):faces.append(sides);return 4
            app=CharacterApplication(directory,die=die);hero=app.create()
            hero=app.select_skills(hero['id'],revision=0,selections=choices(*ids,'juggling','wrestling'))
            self.assertEqual(tuple(hero['attributes'][key]['value'] for key in ['PS','PE','SPD']),(16,19,16))
            receipts=hero['physical_acquisitions'];count=len(faces)
            self.assertEqual(app.combat_view(hero['id'])['totals']['initiative']['value'],1)
            self.assertEqual(app.combat_view(hero['id'])['totals']['initiative']['contributions']['Juggling'],1)
            hero=app.select_skills(hero['id'],revision=hero['revision'],selections=[])
            self.assertEqual(app.combat_view(hero['id'])['totals']['initiative']['value'],0)
            hero=app.select_skills(hero['id'],revision=hero['revision'],selections=choices(*ids))
            self.assertEqual(hero['physical_acquisitions'],receipts);self.assertEqual(len(faces),count)
            hero=app.generate_resources(hero['id'],revision=hero['revision'])
            self.assertEqual(sum(row['effects']['resources'].get('SDC',{}).get('value',0) for row in app.skill_view(hero['id'])['selected']),44)
            imported=app.import_character(app.export_character(hero['id']))
            self.assertEqual(app.get(imported['id'])['physical_acquisitions'],receipts)
            self.assertEqual(CharacterApplication(directory).combat_view(imported['id'])['totals']['initiative']['value'],1)

    def test_late_climbing_pair_advances_and_undo_restores(self):
        with tempfile.TemporaryDirectory() as directory:
            app=CharacterApplication(directory,die=lambda sides:4);hero=app.create(level=3)
            hero=app.select_skills(hero['id'],revision=0,selections=choices('climbing','juggling'))
            hero=app.advance(hero['id'],revision=hero['revision'],method='level',value=4)
            row=app.skill_view(hero['id'])['selected'][0]
            self.assertEqual((row['percentage'],row['additional_checks'][0]['percentage']),(45,35))
            hero=app.undo_advancement(hero['id'],revision=hero['revision'])['character']
            self.assertEqual(app.skill_view(hero['id'])['selected'][0]['percentage'],40)

    def test_old_pin_and_upgrade_preserve_existing_acquisitions(self):
        installed=RuleArchive.load();old=RuleArchive(installed.definitions(),{**installed.active_versions(),'rifts-domestic-skills':'2.20.0'})
        with tempfile.TemporaryDirectory() as directory:
            app=CharacterApplication(directory,die=lambda sides:4,rule_archive=old);hero=app.create()
            hero=app.select_skills(hero['id'],revision=0,selections=choices('boxing'))
            receipts=hero['physical_acquisitions'];app=CharacterApplication(directory)
            self.assertEqual(len(app.skill_view(hero['id'])['catalog']),191)
            preview=app.preview_rule_upgrade(hero['id']);hero=app.apply_rule_upgrade(hero['id'],revision=hero['revision'],token=preview['token'])['character']
            self.assertEqual(hero['physical_acquisitions'],receipts)
            self.assertEqual(len(app.skill_view(hero['id'])['catalog']),200)

    def test_pdf_keeps_source_percentages_and_contextual_effects_editable(self):
        with tempfile.TemporaryDirectory() as directory:
            app=CharacterApplication(directory,die=lambda sides:4);hero=app.create()
            hero=app.select_skills(hero['id'],revision=0,selections=choices('climbing','juggling','fencing','kick-boxing'))
            self.assertEqual(app.combat_view(hero['id'])['totals']['strike']['value'],0)
            reader=PdfReader(BytesIO(app.export_pdf(hero['id'])));fields=reader.get_fields() or {}
            self.assertTrue(fields)
            text='\n'.join(str(field.get('/V','')) for field in fields.values())
            self.assertIn('Rappelling',text);self.assertIn('Fencing',text);self.assertIn('W.P. Sword',text)
            self.assertNotIn('Climbing: .',text);self.assertNotIn('Fencing: .',text)


