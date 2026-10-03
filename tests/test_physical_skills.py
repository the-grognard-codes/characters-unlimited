import tempfile
import unittest
from copy import deepcopy
from io import BytesIO

from pypdf import PdfReader

from characters_unlimited.application import CharacterApplication
from characters_unlimited.application import SaveConflict
from characters_unlimited.rules import RuleArchive


class PhysicalSkillWorkflowTests(unittest.TestCase):
    def test_acquired_bonuses_combine_with_class_and_reopen_without_new_rolls(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory,die=lambda sides:4)
            hero = app.create()
            calls: list[int] = []
            def bonus_die(sides):
                calls.append(sides)
                return {6:3,8:5}[sides]
            app.die = bonus_die
            choices = [{'skill_id':'athletics','pool':'related'}, {'skill_id':'body-building','pool':'related'}]
            hero = app.select_skills(hero['id'],revision=0,selections=choices)
            self.assertEqual(calls,[6,8])
            self.assertEqual(hero['attributes']['PS']['value'],16)
            self.assertEqual(hero['attributes']['SPD']['value'],15)
            view = app.skill_view(hero['id'])
            self.assertEqual(view['remaining']['related'],3)
            self.assertEqual(sum(item['value'] for item in view['physical']['resources']),15)
            self.assertEqual(view['combat']['totals']['parry']['value'],1)
            self.assertEqual(view['combat']['totals']['dodge']['value'],1)
            self.assertEqual(view['combat']['totals']['roll_with_impact']['value'],3)
            self.assertEqual(view['combat']['totals']['damage']['value'],1)
            self.assertEqual(view['combat']['totals']['gun_dodge']['value'],0)
            self.assertNotIn('percentage',next(item for item in view['selected'] if item['id']=='athletics'))
            imported = app.import_character(app.export_character(hero['id']))
            self.assertEqual(imported['physical_acquisitions'],hero['physical_acquisitions'])
            self.assertEqual(CharacterApplication(directory).skill_view(hero['id']),view)
            self.assertEqual(calls,[6,8])

    def test_duplicate_choices_removal_reselection_and_stale_acquisition_preserve_rolls(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory,die=lambda sides:4)
            hero = app.create()
            choices = [{'skill_id':'athletics','pool':'related'}, {'skill_id':'athletics','pool':'secondary'}]
            hero = app.select_skills(hero['id'],revision=0,selections=choices)
            self.assertEqual(hero['attributes']['PS']['value'],14)
            self.assertEqual(sum(item['value'] for item in app.skill_view(hero['id'])['physical']['resources']),4)
            self.assertTrue(any('duplicate' in warning for warning in app.skill_view(hero['id'])['warnings']))
            acquisitions = hero['physical_acquisitions']
            def no_draw(sides):
                raise AssertionError('Existing bonuses must not roll again')
            app.die = no_draw
            hero = app.select_skills(hero['id'],revision=hero['revision'],selections=[])
            self.assertEqual(hero['attributes']['PS']['value'],13)
            self.assertEqual(hero['attributes']['SPD']['value'],12)
            self.assertEqual(app.skill_view(hero['id'])['physical']['resources'],[])
            hero = app.select_skills(hero['id'],revision=hero['revision'],selections=choices[:1])
            self.assertEqual(hero['attributes']['SPD']['value'],16)
            self.assertEqual(hero['physical_acquisitions'],acquisitions)
            with self.assertRaises(SaveConflict):
                app.select_skills(hero['id'],revision=0,selections=[{'skill_id':'body-building','pool':'related'}])
            self.assertEqual(app.get(hero['id']),hero)

    def test_bad_bonus_dice_and_stale_acquisition_cannot_change_saved_work(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory,die=lambda sides:4)
            hero = app.create()
            choices = [{'skill_id':'athletics','pool':'related'}]
            for face in (True,0,7):
                app.die = lambda sides:face
                with self.assertRaises(ValueError):
                    app.select_skills(hero['id'],revision=0,selections=choices)
                self.assertEqual(app.get(hero['id']),hero)
            app.die = lambda sides:3 if sides==6 else 9
            with self.assertRaises(ValueError):
                app.select_skills(hero['id'],revision=0,selections=choices)
            self.assertEqual(app.get(hero['id']),hero)
            hero = app.edit(hero['id'],revision=0,notes='A newer save')
            def no_draw(sides):
                raise AssertionError('Stale requests must reject before rolling')
            app.die = no_draw
            with self.assertRaises(SaveConflict):
                app.select_skills(hero['id'],revision=0,selections=choices)
            self.assertEqual(app.get(hero['id']),hero)

    def test_manual_values_rerolls_history_and_portable_tampering_preserve_bonus_identity(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory,die=lambda sides:4)
            hero = app.create(generation={'reroll_ones':True,'extra_die':True})
            app.die = lambda sides:1
            hero = app.select_skills(hero['id'],revision=0,selections=[{'skill_id':'athletics','pool':'secondary'}])
            self.assertEqual(hero['physical_acquisitions']['athletics']['rolls'],{'attribute:SPD':[1],'resource:SDC':[1]})
            hero = app.set_attribute(hero['id'],revision=hero['revision'],attribute='PS',mode='fixed',value=50)
            self.assertEqual(hero['attributes']['PS']['value'],50)
            hero = app.set_attribute(hero['id'],revision=hero['revision'],attribute='PS',mode='calculated')
            self.assertEqual(hero['attributes']['PS']['value'],14)
            app.die = lambda sides:4
            hero = app.reroll(hero['id'],revision=hero['revision'],attribute='SPD')
            self.assertEqual(hero['attributes']['SPD']['value'],13)
            hero = app.select_skills(hero['id'],revision=hero['revision'],selections=[])
            bundle = app.export_character(hero['id'])
            imported = app.import_character(bundle)
            self.assertEqual(imported['physical_acquisitions'],hero['physical_acquisitions'])
            bad = deepcopy(bundle)
            bad['character']['physical_acquisitions']['athletics']['rolls']['resource:SDC']=[9]
            with self.assertRaises(ValueError):
                app.import_character(bad)
            bad = deepcopy(bundle)
            record = bad['character']['roll_history'][-1]['attributes']['SPD']
            record['modifiers'][0]['value']+=1
            record['value']+=1
            with self.assertRaises(ValueError):
                app.import_character(bad)
            bad = deepcopy(bundle)
            bad['character']['roll_history'][-1]['attributes']['SPD']['modifiers'][0]['source']['pages']=[316.0]
            with self.assertRaises(ValueError):
                app.import_character(bad)
            self.assertEqual(app.get(hero['id']),hero)

    def test_editable_pdf_keeps_physical_names_and_bonuses_without_percentages(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory,die=lambda sides:4)
            hero = app.create()
            hero = app.select_skills(hero['id'],revision=0,selections=[{'skill_id':'athletics','pool':'related'}])
            reader = PdfReader(BytesIO(app.export_pdf(hero['id'])))
            fields = reader.get_fields()
            assert fields is not None
            values = [field.get('/V','') for field in fields.values()]
            self.assertIn('Athletics (General)',values)
            self.assertEqual(fields['PS']['/V'],'14')
            self.assertEqual(fields['SPD']['/V'],'16')
            self.assertTrue(any('S.D.C.' in str(value) and 'bonus' in str(value) for value in values))

    def test_old_pins_update_before_acquisition_and_changed_bonus_rules_do_not_silently_migrate(self):
        with tempfile.TemporaryDirectory() as directory:
            archive = RuleArchive.load()
            earlier = CharacterApplication(directory,die=lambda sides:4,rule_archive=RuleArchive(
                archive.definitions(),{**archive.active_versions(),'rifts-domestic-skills':'1.9.0'}))
            hero = earlier.create()
            choices = [{'skill_id':'athletics','pool':'related'}]
            with self.assertRaises(ValueError):
                earlier.select_skills(hero['id'],revision=0,selections=choices)
            current = CharacterApplication(directory,die=lambda sides:4)
            preview = current.preview_rule_upgrade(hero['id'])
            self.assertEqual(current.get(hero['id']),hero)
            hero = current.apply_rule_upgrade(hero['id'],revision=0,token=preview['token'])['character']
            hero = current.select_skills(hero['id'],revision=hero['revision'],selections=choices)
            same = current.preview_rule_upgrade(hero['id'])
            self.assertTrue(any(row.get('unit')=='' and row['name'].endswith('PS') for row in same['skills']))
            compatible = archive.active('rifts-domestic-skills')
            original_bundle = current.export_character(hero['id'])
            compatible['version']='2.0.1'
            next(skill for skill in compatible['skills'] if skill['id']=='cook')['base']+=1
            updated_app = CharacterApplication(directory,rule_archive=RuleArchive([*archive.definitions(),compatible],
                {**archive.active_versions(),'rifts-domestic-skills':'2.0.1'}))
            same = updated_app.preview_rule_upgrade(hero['id'])
            unchanged = updated_app.apply_rule_upgrade(hero['id'],revision=hero['revision'],token=same['token'])['character']
            self.assertEqual(unchanged['physical_acquisitions'],hero['physical_acquisitions'])
            self.assertEqual(unchanged['attributes'],hero['attributes'])
            hero = unchanged
            correction = archive.active('rifts-domestic-skills')
            correction['version']='2.1.0'
            next(skill for skill in correction['skills'] if skill['id']=='athletics')['attributes']['PS']['bonus']=2
            newer = CharacterApplication(directory,rule_archive=RuleArchive([*archive.definitions(),compatible,correction],
                {**archive.active_versions(),'rifts-domestic-skills':'2.1.0'}))
            with self.assertRaisesRegex(ValueError,'Acquisition/history migration'):
                newer.preview_rule_upgrade(hero['id'])
            self.assertEqual(newer.get(hero['id']),hero)
            imported = newer.import_character(original_bundle)
            self.assertEqual(imported['additional_rule_packs']['rifts-domestic-skills'],'2.0.0')



if __name__ == '__main__':
    unittest.main()
