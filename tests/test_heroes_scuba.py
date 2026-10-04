import tempfile,unittest
from characters_unlimited.application import CharacterApplication

class HeroesScubaTests(unittest.TestCase):
    def test_scuba_has_separate_underwater_pace_and_honor_system_swimming_prerequisite(self):
        with tempfile.TemporaryDirectory() as directory:
            app=CharacterApplication(directory,die=lambda sides:4)
            c=app.create(game='heroes-unlimited')
            c=app.select_education(c['id'],revision=0,method='choose',education_id='high-school')
            c=app.set_attribute(c['id'],revision=c['revision'],attribute='IQ',mode='fixed',value=16)
            c=app.set_attribute(c['id'],revision=c['revision'],attribute='PS',mode='fixed',value=20)
            c=app.select_hero_secondary(c['id'],revision=c['revision'],selections=['scuba'])
            view=app.hero_program_view(c['id'])
            self.assertTrue(any('S.C.U.B.A.' in warning and 'Swimming' in warning for warning in view['warnings']))
            c=app.select_hero_secondary(c['id'],revision=c['revision'],selections=['scuba','swimming'])
            view=app.hero_program_view(c['id'])
            self.assertFalse(any('S.C.U.B.A.' in warning and 'Swimming' in warning for warning in view['warnings']))
            skills={row['id']:row for row in view['skills']}
            self.assertEqual(skills['scuba']['percentage'],52)
            self.assertEqual(skills['scuba']['per_level'],5)
            activities={row['id']:row['activities'][0] for row in view['physical']['selected']}
            self.assertEqual((activities['scuba']['yards_per_melee'],activities['swimming']['yards_per_melee']),(40,60))
            self.assertEqual(activities['scuba']['id'],'underwater-swimming')
            self.assertEqual(activities['scuba']['minutes'],12)
            self.assertEqual(c['physical_acquisitions']['scuba'],{'rolls':{}})
            c=app.select_power_budget(c['id'],revision=c['revision'],method='choose',outcome_id='four-minor')
            c=app.select_hero_powers(c['id'],revision=c['revision'],selections=['extraordinary-physical-endurance'])
            activity=next(row for row in app.hero_program_view(c['id'])['physical']['selected'] if row['id']=='scuba')['activities'][0]
            self.assertEqual((activity['yards_per_melee'],activity['ordinary_minutes'],activity['minutes']),(40,21,210))
            self.assertEqual(activity['fatigue_sources'][0]['printed_page'],232)
    def test_removed_or_outside_group_swimming_does_not_satisfy_prerequisite_and_receipts_survive(self):
        from copy import deepcopy
        with tempfile.TemporaryDirectory() as directory:
            app=CharacterApplication(directory,die=lambda sides:4)
            c=app.create(game='heroes-unlimited')
            c=app.select_education(c['id'],revision=0,method='choose',education_id='college-one')
            c=app.select_hero_secondary(c['id'],revision=c['revision'],selections=['scuba','scuba','swimming'])
            self.assertEqual(app.hero_program_view(c['id'])['secondary']['used'],3)
            receipts=deepcopy(c['physical_acquisitions'])
            c=app.generate_resources(c['id'],revision=c['revision'])
            resources=deepcopy(c['resources']);snapshot=deepcopy(c['resource_attribute_snapshot'])
            c=app.select_hero_secondary(c['id'],revision=c['revision'],selections=['scuba'])
            c=app.select_hero_programs(c['id'],revision=c['revision'],selections=[{'slot':0,'program':'computer','choices':{'repair-radio':['swimming']}}])
            view=app.hero_program_view(c['id'])
            self.assertTrue(any('S.C.U.B.A.' in warning and 'Swimming' in warning for warning in view['warnings']))
            self.assertEqual([row['id'] for row in view['physical']['selected']],['scuba'])
            c=app.select_hero_secondary(c['id'],revision=c['revision'],selections=[])
            self.assertEqual(app.hero_program_view(c['id'])['physical']['selected'],[])
            c=app.select_hero_secondary(c['id'],revision=c['revision'],selections=['scuba','swimming'])
            self.assertEqual(c['physical_acquisitions'],receipts)
            self.assertEqual(c['resources'],resources)
            self.assertEqual(c['resource_attribute_snapshot'],snapshot)
            restored=app.import_character(app.export_character(c['id']))
            self.assertEqual(app.hero_program_view(restored['id'])['physical'],app.hero_program_view(c['id'])['physical'])
            bad=app.export_character(c['id']);bad['character']['physical_acquisitions']['scuba']['rolls']['attribute:PS']=[]
            with self.assertRaises(ValueError):app.import_character(bad)
            self.assertEqual(app.get(c['id']),c)

    def test_legacy_update_preserves_surface_activity_and_rejects_changed_inactive_scuba(self):
        from copy import deepcopy
        from characters_unlimited.rules import RuleArchive
        with tempfile.TemporaryDirectory() as directory:
            archive=RuleArchive.load()
            earlier=CharacterApplication(directory,die=lambda sides:4,rule_archive=RuleArchive(archive.definitions(),{**archive.active_versions(),'heroes-program-skills':'1.15.0'}))
            c=earlier.create(game='heroes-unlimited')
            c=earlier.select_education(c['id'],revision=0,method='choose',education_id='high-school')
            c=earlier.select_hero_secondary(c['id'],revision=c['revision'],selections=['swimming','athletics','hand-to-hand-basic'])
            before=earlier.hero_program_view(c['id'])['physical'];receipts=deepcopy(c['physical_acquisitions'])
            with self.assertRaises(ValueError):earlier.select_hero_secondary(c['id'],revision=c['revision'],selections=['scuba'])
            app=CharacterApplication(directory,die=lambda sides:4)
            preview=app.preview_rule_upgrade(c['id'])
            self.assertEqual(preview['combat'],[])
            c=app.apply_rule_upgrade(c['id'],revision=c['revision'],token=preview['token'])['character']
            self.assertEqual(app.hero_program_view(c['id'])['physical'],before)
            self.assertEqual(c['physical_acquisitions'],receipts)
            c=app.select_hero_secondary(c['id'],revision=c['revision'],selections=['scuba','swimming','athletics','hand-to-hand-basic'])
            c=app.select_hero_secondary(c['id'],revision=c['revision'],selections=['swimming','athletics','hand-to-hand-basic'])
            target=deepcopy(archive.active('heroes-program-skills'));target['version']='99.0.0'
            next(row for row in target['skills'] if row['id']=='scuba')['activities']['swimming']['minutes_per_pe']=2
            newer=CharacterApplication(directory,rule_archive=RuleArchive([*archive.definitions(),target],{**archive.active_versions(),'heroes-program-skills':'99.0.0'}))
            with self.assertRaises(ValueError):newer.preview_rule_upgrade(c['id'])
            self.assertEqual(app.get(c['id']),c)

    def test_pdf_keeps_surface_and_underwater_checks_pace_and_missing_prerequisite(self):
        from io import BytesIO
        from pypdf import PdfReader
        with tempfile.TemporaryDirectory() as directory:
            app=CharacterApplication(directory,die=lambda sides:4)
            c=app.create(game='heroes-unlimited')
            c=app.select_education(c['id'],revision=0,method='choose',education_id='high-school')
            c=app.select_hero_secondary(c['id'],revision=c['revision'],selections=['swimming','scuba'])
            fields=PdfReader(BytesIO(app.export_pdf(c['id']))).get_fields();assert fields is not None
            self.assertEqual(fields['skills.scuba.percentage']['/V'],'50')
            self.assertEqual(fields['skills.swimming.percentage']['/V'],'50')
            text='\n'.join(str(row.get('/V','')) for row in fields.values())
            self.assertIn('Swimming pace: 36 yards/meters per melee',text)
            self.assertIn('S.C.U.B.A. (Advanced Swimming) pace: 24 yards/meters per melee',text)
            self.assertIn('120 feet (36.5 meters)',text)
            self.assertIn('equipment-assisted underwater',text)
            c=app.select_hero_secondary(c['id'],revision=c['revision'],selections=['scuba'])
            fields=PdfReader(BytesIO(app.export_pdf(c['id']))).get_fields();assert fields is not None
            self.assertIn('Selection retained on the honor system','\n'.join(str(row.get('/V','')) for row in fields.values()))

    def test_long_sheet_retains_scuba_in_an_editable_continuation_field(self):
        from io import BytesIO
        from pypdf import PdfReader
        with tempfile.TemporaryDirectory() as directory:
            app=CharacterApplication(directory,die=lambda sides:4)
            c=app.create(game='heroes-unlimited')
            c=app.select_education(c['id'],revision=0,method='choose',education_id='high-school')
            catalog=app.hero_program_view(c['id'])['skill_catalog']
            c=app.select_hero_secondary(c['id'],revision=c['revision'],selections=[row['id'] for row in catalog if 'base' in row])
            fields=PdfReader(BytesIO(app.export_pdf(c['id']))).get_fields();assert fields is not None
            self.assertNotIn('skills.scuba.percentage',fields)
            matching=[row for row in fields.values() if row.get('/V')=='S.C.U.B.A. (Advanced Swimming): 50% (+5% per level)']
            self.assertEqual(len(matching),1)
            self.assertEqual(matching[0]['/FT'],'/Tx')
            self.assertFalse(int(matching[0]['/Ff']) & 1)
