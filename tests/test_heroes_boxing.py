import tempfile,unittest
from copy import deepcopy
from characters_unlimited.application import CharacterApplication

class HeroesBoxingTests(unittest.TestCase):
    def test_boxing_adds_once_with_basic_training_and_retains_sdc_rolls(self):
        with tempfile.TemporaryDirectory() as directory:
            app=CharacterApplication(directory,die=lambda sides:4)
            c=app.create(game='heroes-unlimited')
            c=app.select_education(c['id'],revision=0,method='choose',education_id='high-school')
            c=app.select_hero_secondary(c['id'],revision=c['revision'],selections=['boxing','boxing','hand-to-hand-basic'])
            view=app.hero_program_view(c['id'])
            self.assertEqual(view['secondary']['used'],3)
            self.assertNotIn('boxing',view['secondary']['eligible_skill_ids'])
            self.assertIn('boxing',[row['id'] for row in view['secondary']['catalog']])
            self.assertIn('Boxing is outside the eligible Secondary categories. Choice retained without an education bonus.',view['warnings'])
            self.assertEqual(c['attributes']['PS']['value'],14)
            self.assertEqual(c['physical_acquisitions']['boxing'],{'rolls':{'resource:SDC':[4,4,4]}})
            for stat,value in [('attacks',5),('parry',2),('dodge',2),('roll_with_impact',3)]:
                self.assertEqual(view['combat']['totals'][stat]['value'],value)
            self.assertEqual(view['combat']['training'],'Hand to Hand: Basic')
            self.assertEqual(view['combat']['parry_actions'],0)
            c=app.generate_resources(c['id'],revision=c['revision'])
            self.assertEqual(app.resource_view(c['id'])['resources']['SDC']['value'],42)
            snapshot=deepcopy(c['resource_attribute_snapshot']);receipts=deepcopy(c['physical_acquisitions'])
            c=app.select_hero_secondary(c['id'],revision=c['revision'],selections=['hand-to-hand-basic'])
            self.assertEqual(app.hero_program_view(c['id'])['combat']['totals']['attacks']['value'],4)
            self.assertEqual(app.resource_view(c['id'])['resources']['SDC']['value'],30)
            c=app.select_hero_secondary(c['id'],revision=c['revision'],selections=['boxing','hand-to-hand-basic'])
            self.assertEqual(c['physical_acquisitions'],receipts)
            self.assertEqual(c['resource_attribute_snapshot'],snapshot)
    def test_untrained_boxing_keeps_parry_cost_fixed_attributes_and_portable_receipts(self):
        with tempfile.TemporaryDirectory() as directory:
            app=CharacterApplication(directory,die=lambda sides:4)
            c=app.create(game='heroes-unlimited')
            c=app.select_education(c['id'],revision=0,method='choose',education_id='high-school')
            c=app.set_attribute(c['id'],revision=c['revision'],attribute='PS',mode='fixed',value=20)
            c=app.select_hero_secondary(c['id'],revision=c['revision'],selections=['boxing','athletics'])
            view=app.hero_program_view(c['id'])
            self.assertEqual(c['attributes']['PS']['value'],20)
            self.assertEqual(view['combat']['training'],'No Hand to Hand')
            self.assertEqual(view['combat']['parry_actions'],1)
            for stat,value in [('attacks',4),('parry',3),('dodge',3),('roll_with_impact',2),('damage',5)]:
                self.assertEqual(view['combat']['totals'][stat]['value'],value)
            self.assertNotIn('boxing',[row['id'] for row in view['skills']])
            restored=app.import_character(app.export_character(c['id']))
            self.assertEqual(app.hero_program_view(restored['id'])['physical'],view['physical'])
            bad=app.export_character(c['id']);bad['character']['physical_acquisitions']['boxing']['rolls']['resource:SDC']=[7,4,4]
            with self.assertRaises(ValueError):app.import_character(bad)
            self.assertEqual(app.get(c['id']),c)

    def test_legacy_update_preserves_acquisitions_and_rejects_changed_inactive_boxing(self):
        from characters_unlimited.rules import RuleArchive
        with tempfile.TemporaryDirectory() as directory:
            archive=RuleArchive.load()
            earlier=CharacterApplication(directory,die=lambda sides:4,rule_archive=RuleArchive(archive.definitions(),{**archive.active_versions(),'heroes-program-skills':'1.16.0'}))
            c=earlier.create(game='heroes-unlimited')
            c=earlier.select_education(c['id'],revision=0,method='choose',education_id='high-school')
            c=earlier.select_hero_secondary(c['id'],revision=c['revision'],selections=['swimming','scuba','athletics','hand-to-hand-basic'])
            receipts=deepcopy(c['physical_acquisitions'])
            with self.assertRaises(ValueError):earlier.select_hero_secondary(c['id'],revision=c['revision'],selections=['boxing'])
            app=CharacterApplication(directory,die=lambda sides:4)
            preview=app.preview_rule_upgrade(c['id'])
            self.assertEqual(preview['combat'],[])
            c=app.apply_rule_upgrade(c['id'],revision=c['revision'],token=preview['token'])['character']
            self.assertEqual(c['physical_acquisitions'],receipts)
            c=app.select_hero_secondary(c['id'],revision=c['revision'],selections=['boxing'])
            c=app.select_hero_secondary(c['id'],revision=c['revision'],selections=[])
            target=deepcopy(archive.active('heroes-program-skills'));target['version']='99.0.0'
            next(row for row in target['skills'] if row['id']=='boxing')['combat']['attacks']=2
            newer=CharacterApplication(directory,rule_archive=RuleArchive([*archive.definitions(),target],{**archive.active_versions(),'heroes-program-skills':'99.0.0'}))
            with self.assertRaises(ValueError):newer.preview_rule_upgrade(c['id'])
            self.assertEqual(app.get(c['id']),c)

    def test_pdf_has_combined_totals_and_conditional_fist_knockout_guidance(self):
        from io import BytesIO
        from pypdf import PdfReader
        with tempfile.TemporaryDirectory() as directory:
            app=CharacterApplication(directory,die=lambda sides:4)
            c=app.create(game='heroes-unlimited')
            c=app.select_education(c['id'],revision=0,method='choose',education_id='high-school')
            c=app.select_hero_secondary(c['id'],revision=c['revision'],selections=['boxing','hand-to-hand-basic'])
            c=app.generate_resources(c['id'],revision=c['revision'])
            fields=PdfReader(BytesIO(app.export_pdf(c['id']))).get_fields();assert fields is not None
            for name,value in [('ATTACKS','5'),('PARRY','2'),('DODGE','2'),('PS','14'),('SDC','42')]:
                self.assertEqual(fields[name]['/V'],value)
            text=' '.join(' '.join(str(row.get('/V','')) for row in fields.values()).split())
            self.assertIn('natural 20 automatically',text)
            self.assertIn('for 1D6 melees',text)
            self.assertIn('No knockout announcement is required',text)
            self.assertIn('stunned instead: -4 to strike, parry and dodge',text)
            self.assertIn('Bionic characters',text)
            self.assertIn('printed pp. 55 / PDF pp. 56',text)
            self.assertNotIn('skills.boxing.percentage',fields)
            self.assertIn('Boxing is outside the eligible Secondary categories.',text)
