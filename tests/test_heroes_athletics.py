import tempfile,unittest
from copy import deepcopy
from characters_unlimited.application import CharacterApplication

class HeroesAthleticsTests(unittest.TestCase):
    def test_athletics_adds_once_to_training_and_retains_rolls_when_removed(self):
        with tempfile.TemporaryDirectory() as directory:
            draws=[]
            def die(sides):draws.append(sides);return 4
            app=CharacterApplication(directory,die=die)
            c=app.create(game='heroes-unlimited')
            c=app.select_education(c['id'],revision=0,method='choose',education_id='high-school')
            c=app.select_hero_secondary(c['id'],revision=c['revision'],selections=['hand-to-hand-basic'])
            before=len(draws)
            c=app.select_hero_secondary(c['id'],revision=c['revision'],selections=['hand-to-hand-basic','athletics','athletics'])
            self.assertEqual(draws[before:],[6,4,4])
            self.assertEqual((c['attributes']['PS']['value'],c['attributes']['SPD']['value']),(13,16))
            view=app.hero_program_view(c['id'])
            self.assertEqual(view['secondary']['used'],3)
            self.assertEqual(view['combat']['training'],'Hand to Hand: Basic')
            self.assertEqual(view['combat']['parry_actions'],0)
            for stat,value in [('attacks',4),('parry',1),('dodge',1),('roll_with_impact',3)]:
                self.assertEqual(view['combat']['totals'][stat]['value'],value)
            self.assertEqual(view['combat']['totals']['parry']['contributions']['Athletics (general)'],1)
            c=app.generate_resources(c['id'],revision=c['revision'])
            self.assertEqual(app.resource_view(c['id'])['resources']['SDC']['value'],38)
            snapshot=deepcopy(c['resource_attribute_snapshot']);receipts=deepcopy(c['physical_acquisitions'])
            before=len(draws)
            c=app.select_hero_secondary(c['id'],revision=c['revision'],selections=['hand-to-hand-basic'])
            self.assertEqual((c['attributes']['PS']['value'],c['attributes']['SPD']['value']),(12,12))
            self.assertEqual(app.resource_view(c['id'])['resources']['SDC']['value'],30)
            c=app.select_hero_secondary(c['id'],revision=c['revision'],selections=['hand-to-hand-basic','athletics'])
            self.assertEqual(len(draws),before)
            self.assertEqual(c['physical_acquisitions'],receipts)
            self.assertEqual(c['resource_attribute_snapshot'],snapshot)
            self.assertEqual(app.hero_program_view(c['id'])['combat']['totals']['parry']['value'],1)

    def test_untrained_fixed_attributes_and_portable_receipts_keep_independent_effects(self):
        with tempfile.TemporaryDirectory() as directory:
            app=CharacterApplication(directory,die=lambda sides:4)
            c=app.create(game='heroes-unlimited')
            c=app.select_education(c['id'],revision=0,method='choose',education_id='high-school')
            c=app.set_attribute(c['id'],revision=c['revision'],attribute='PS',mode='fixed',value=20)
            c=app.select_hero_secondary(c['id'],revision=c['revision'],selections=['athletics','body-building','running'])
            self.assertEqual((c['attributes']['PS']['value'],c['attributes']['SPD']['value']),(20,32))
            view=app.hero_program_view(c['id'])
            self.assertEqual(view['combat']['training'],'No Hand to Hand')
            self.assertEqual(view['combat']['parry_actions'],1)
            self.assertEqual(view['combat']['totals']['attacks']['value'],3)
            self.assertEqual(view['combat']['totals']['damage']['value'],5)
            c=app.generate_resources(c['id'],revision=c['revision'])
            self.assertEqual(app.resource_view(c['id'])['resources']['SDC']['value'],52)
            bundle=app.export_character(c['id'])
            restored=app.import_character(bundle)
            self.assertEqual(restored['physical_acquisitions'],c['physical_acquisitions'])
            self.assertEqual(app.hero_program_view(restored['id'])['combat'],view['combat'])
            bad=deepcopy(bundle);bad['character']['physical_acquisitions']['athletics']['rolls']['attribute:SPD']=[7]
            with self.assertRaises(ValueError):app.import_character(bad)
            self.assertEqual(app.get(c['id']),c)
    def test_legacy_update_preserves_acquired_activity_and_guards_inactive_athletics(self):
        from characters_unlimited.rules import RuleArchive
        with tempfile.TemporaryDirectory() as directory:
            archive=RuleArchive.load()
            earlier=CharacterApplication(directory,die=lambda sides:4,rule_archive=RuleArchive(archive.definitions(),{**archive.active_versions(),'heroes-program-skills':'1.14.0'}))
            c=earlier.create(game='heroes-unlimited')
            c=earlier.select_education(c['id'],revision=0,method='choose',education_id='high-school')
            c=earlier.select_hero_secondary(c['id'],revision=c['revision'],selections=['climbing','swimming','hand-to-hand-basic'])
            receipts=deepcopy(c['physical_acquisitions'])
            with self.assertRaises(ValueError):earlier.select_hero_secondary(c['id'],revision=c['revision'],selections=['athletics'])
            app=CharacterApplication(directory,die=lambda sides:4)
            preview=app.preview_rule_upgrade(c['id'])
            self.assertEqual(preview['combat'],[])
            c=app.apply_rule_upgrade(c['id'],revision=c['revision'],token=preview['token'])['character']
            self.assertEqual(c['physical_acquisitions'],receipts)
            c=app.select_hero_secondary(c['id'],revision=c['revision'],selections=['athletics'])
            c=app.select_hero_secondary(c['id'],revision=c['revision'],selections=[])
            future=deepcopy(archive.active('heroes-program-skills'));future['version']='99.0.0'
            next(row for row in future['skills'] if row['id']=='athletics')['combat']['parry']=2
            newer=CharacterApplication(directory,rule_archive=RuleArchive([*archive.definitions(),future],{**archive.active_versions(),'heroes-program-skills':'99.0.0'}))
            with self.assertRaises(ValueError):newer.preview_rule_upgrade(c['id'])
            self.assertEqual(app.get(c['id']),c)

    def test_editable_pdf_includes_combined_combat_and_athletics_dice_source(self):
        from io import BytesIO
        from pypdf import PdfReader
        with tempfile.TemporaryDirectory() as directory:
            app=CharacterApplication(directory,die=lambda sides:4)
            c=app.create(game='heroes-unlimited')
            c=app.select_education(c['id'],revision=0,method='choose',education_id='high-school')
            c=app.select_hero_secondary(c['id'],revision=c['revision'],selections=['athletics','hand-to-hand-basic'])
            c=app.generate_resources(c['id'],revision=c['revision'])
            fields=PdfReader(BytesIO(app.export_pdf(c['id']))).get_fields();assert fields is not None
            for name,value in [('PS','13'),('SPD','16'),('SDC','38'),('PARRY','1'),('DODGE','1'),('ATTACKS','4')]:
                self.assertEqual(fields[name]['/V'],value)
            text='\n'.join(str(row.get('/V','')) for row in fields.values())
            self.assertIn('Athletics (general)',text)
            self.assertIn('Speed+1D6',text)
            self.assertIn('printed pp. 55 / PDF pp. 56',text)
            self.assertNotIn('skills.athletics.percentage',fields)
