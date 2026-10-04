import tempfile,unittest
from characters_unlimited.application import CharacterApplication

class HeroesPhysicalProficiencyTests(unittest.TestCase):
    def test_climbing_rappelling_and_swimming_keep_separate_checks_and_effective_limits(self):
        with tempfile.TemporaryDirectory() as directory:
            app=CharacterApplication(directory,die=lambda sides:4)
            c=app.create(game='heroes-unlimited')
            c=app.select_education(c['id'],revision=0,method='choose',education_id='high-school')
            c=app.set_attribute(c['id'],revision=c['revision'],attribute='IQ',mode='fixed',value=16)
            c=app.set_attribute(c['id'],revision=c['revision'],attribute='PS',mode='fixed',value=20)
            c=app.select_hero_secondary(c['id'],revision=c['revision'],selections=['climbing','swimming'])
            view=app.hero_program_view(c['id'])
            skills={row['id']:row for row in view['skills']}
            self.assertEqual(skills['climbing']['percentage'],42)
            self.assertEqual(skills['climbing']['additional_checks'][0]['percentage'],32)
            self.assertEqual(skills['swimming']['percentage'],52)
            self.assertEqual(skills['swimming']['per_level'],5)
            self.assertEqual(view['secondary']['used'],2)
            self.assertEqual(c['physical_acquisitions'],{'climbing':{'rolls':{}},'swimming':{'rolls':{}}})
            swimming=next(row for row in view['physical']['selected'] if row['id']=='swimming')['activities'][0]
            self.assertEqual(swimming['yards_per_melee'],60)
            self.assertEqual(swimming['minutes'],12)
            c=app.select_power_budget(c['id'],revision=c['revision'],method='choose',outcome_id='four-minor')
            c=app.select_hero_powers(c['id'],revision=c['revision'],selections=['extraordinary-physical-endurance'])
            swimming=next(row for row in app.hero_program_view(c['id'])['physical']['selected'] if row['id']=='swimming')['activities'][0]
            self.assertEqual(swimming['ordinary_minutes'],21)
            self.assertEqual(swimming['minutes'],210)
            self.assertEqual(swimming['yards_per_melee'],60)
            self.assertEqual(swimming['fatigue_rate'],{'numerator':1,'denominator':10})

    def test_pdf_shows_separate_climbing_checks_and_source_bound_swimming_limits(self):
        from io import BytesIO
        from pypdf import PdfReader
        with tempfile.TemporaryDirectory() as directory:
            app=CharacterApplication(directory,die=lambda sides:4)
            c=app.create(game='heroes-unlimited')
            c=app.select_education(c['id'],revision=0,method='choose',education_id='high-school')
            c=app.select_hero_secondary(c['id'],revision=c['revision'],selections=['climbing','swimming'])
            fields=PdfReader(BytesIO(app.export_pdf(c['id']))).get_fields();assert fields is not None
            self.assertEqual(fields['skills.climbing.percentage']['/V'],'40')
            self.assertEqual(fields['skills.climbing.check0.percentage']['/V'],'30')
            self.assertEqual(fields['skills.swimming.percentage']['/V'],'50')
            text='\n'.join(str(row.get('/V','')) for row in fields.values())
            self.assertIn('Swimming pace: 36 yards/meters per melee',text)
            self.assertIn('12 minutes; ordinary 12 minutes; fatigue 1/1 normal',text)

    def test_activity_changes_retain_receipts_hp_snapshot_and_independent_proficiency(self):
        from copy import deepcopy
        with tempfile.TemporaryDirectory() as directory:
            app=CharacterApplication(directory,die=lambda sides:4)
            c=app.create(game='heroes-unlimited')
            c=app.select_education(c['id'],revision=0,method='choose',education_id='high-school')
            c=app.select_hero_secondary(c['id'],revision=c['revision'],selections=['climbing','swimming','swimming'])
            self.assertEqual(app.hero_program_view(c['id'])['secondary']['used'],3)
            c=app.generate_resources(c['id'],revision=c['revision'])
            hp_snapshot=deepcopy(c['resource_attribute_snapshot'])
            resource_rolls=deepcopy(c['resources'])
            receipts=deepcopy(c['physical_acquisitions'])
            c=app.select_power_budget(c['id'],revision=c['revision'],method='choose',outcome_id='four-minor')
            c=app.select_hero_powers(c['id'],revision=c['revision'],selections=['extraordinary-physical-endurance'])
            c=app.set_attribute(c['id'],revision=c['revision'],attribute='PS',mode='fixed',value=18)
            view=app.hero_program_view(c['id'])
            self.assertEqual(next(r for r in view['skills'] if r['id']=='swimming')['percentage'],50)
            activity=next(r for r in view['physical']['selected'] if r['id']=='swimming')['activities'][0]
            self.assertEqual((activity['yards_per_melee'],activity['ordinary_minutes'],activity['minutes']),(54,21,210))
            self.assertEqual(activity['fatigue_sources'][0]['printed_page'],232)
            c=app.select_hero_powers(c['id'],revision=c['revision'],selections=[])
            activity=next(r for r in app.hero_program_view(c['id'])['physical']['selected'] if r['id']=='swimming')['activities'][0]
            self.assertEqual(activity['minutes'],12)
            self.assertEqual(activity['fatigue_sources'],[])
            c=app.select_hero_secondary(c['id'],revision=c['revision'],selections=['climbing'])
            self.assertNotIn('swimming',[r['id'] for r in app.hero_program_view(c['id'])['physical']['selected']])
            c=app.select_hero_secondary(c['id'],revision=c['revision'],selections=['climbing','swimming'])
            self.assertEqual(c['physical_acquisitions'],receipts)
            self.assertEqual(c['resources'],resource_rolls)
            self.assertEqual(c['resource_attribute_snapshot'],hp_snapshot)
            restored=app.import_character(app.export_character(c['id']))
            self.assertEqual(app.hero_program_view(restored['id'])['physical'],app.hero_program_view(c['id'])['physical'])
            c=app.set_attribute(c['id'],revision=c['revision'],attribute='PE',mode='fixed',value=0)
            activity=next(r for r in app.hero_program_view(c['id'])['physical']['selected'] if r['id']=='swimming')['activities'][0]
            self.assertIsNone(activity['minutes'])
            self.assertEqual(activity['yards_per_melee'],54)
            c=app.set_attribute(c['id'],revision=c['revision'],attribute='PE',mode='fixed',value=12)
            c=app.set_attribute(c['id'],revision=c['revision'],attribute='PS',mode='fixed',value=0)
            activity=next(r for r in app.hero_program_view(c['id'])['physical']['selected'] if r['id']=='swimming')['activities'][0]
            self.assertIsNone(activity['yards_per_melee'])
            self.assertEqual(activity['minutes'],12)

    def test_outside_group_and_invalid_physical_receipts_cannot_certify_swimming_activity(self):
        from copy import deepcopy
        with tempfile.TemporaryDirectory() as directory:
            app=CharacterApplication(directory,die=lambda sides:4)
            c=app.create(game='heroes-unlimited')
            c=app.select_education(c['id'],revision=0,method='choose',education_id='college-one')
            c=app.select_hero_programs(c['id'],revision=c['revision'],selections=[{'slot':0,'program':'computer','choices':{'repair-radio':['swimming']}}])
            self.assertEqual(c['physical_acquisitions'],{})
            self.assertNotIn('swimming',[r['id'] for r in app.hero_program_view(c['id'])['physical']['selected']])
            c=app.select_hero_secondary(c['id'],revision=c['revision'],selections=['climbing','swimming'])
            bundle=app.export_character(c['id'])
            for identifier in ['climbing','swimming']:
                bad=deepcopy(bundle);bad['character']['physical_acquisitions'][identifier]['rolls']['attribute:PE']=[]
                with self.assertRaises(ValueError):app.import_character(bad)
                self.assertEqual(app.get(c['id']),c)

    def test_legacy_update_preserves_training_and_rejects_changed_inactive_activity_rules(self):
        from copy import deepcopy
        from characters_unlimited.rules import RuleArchive
        with tempfile.TemporaryDirectory() as directory:
            archive=RuleArchive.load()
            earlier=CharacterApplication(directory,die=lambda sides:4,rule_archive=RuleArchive(archive.definitions(),{**archive.active_versions(),'heroes-program-skills':'1.13.0'}))
            c=earlier.create(game='heroes-unlimited')
            c=earlier.select_education(c['id'],revision=0,method='choose',education_id='high-school')
            c=earlier.select_hero_secondary(c['id'],revision=c['revision'],selections=['hand-to-hand-martial-arts','running'])
            with self.assertRaises(ValueError):earlier.select_hero_secondary(c['id'],revision=c['revision'],selections=['swimming'])
            app=CharacterApplication(directory,die=lambda sides:4)
            preview=app.preview_rule_upgrade(c['id'])
            self.assertEqual(preview['combat'],[])
            c=app.apply_rule_upgrade(c['id'],revision=c['revision'],token=preview['token'])['character']
            c=app.select_hero_secondary(c['id'],revision=c['revision'],selections=['hand-to-hand-martial-arts','running','swimming'])
            self.assertEqual(app.hero_program_view(c['id'])['combat']['training'],'Hand to Hand: Martial Arts')
            c=app.select_hero_secondary(c['id'],revision=c['revision'],selections=['hand-to-hand-martial-arts','running'])
            target=deepcopy(archive.active('heroes-program-skills'));target['version']='99.0.0'
            next(r for r in target['skills'] if r['id']=='swimming')['activities']['swimming']['yards_per_ps']=4
            newer=CharacterApplication(directory,rule_archive=RuleArchive([*archive.definitions(),target],{**archive.active_versions(),'heroes-program-skills':'99.0.0'}))
            with self.assertRaises(ValueError):newer.preview_rule_upgrade(c['id'])
            self.assertEqual(app.get(c['id']),c)

    def test_fatigue_duration_preserves_exact_supported_boundary_and_blanks_overflow(self):
        from characters_unlimited.physical import MAX_ACTIVITY_ATTRIBUTE
        with tempfile.TemporaryDirectory() as directory:
            app=CharacterApplication(directory,die=lambda sides:4)
            c=app.create(game='heroes-unlimited')
            c=app.select_education(c['id'],revision=0,method='choose',education_id='high-school')
            c=app.select_hero_secondary(c['id'],revision=c['revision'],selections=['swimming'])
            c=app.select_power_budget(c['id'],revision=c['revision'],method='choose',outcome_id='four-minor')
            c=app.select_hero_powers(c['id'],revision=c['revision'],selections=['extraordinary-physical-endurance'])
            for value in [MAX_ACTIVITY_ATTRIBUTE//10,MAX_ACTIVITY_ATTRIBUTE//10+1]:
                c=app.set_attribute(c['id'],revision=c['revision'],attribute='PE',mode='fixed',value=value)
                activity=next(r for r in app.hero_program_view(c['id'])['physical']['selected'] if r['id']=='swimming')['activities'][0]
                self.assertEqual(activity['ordinary_minutes'],value)
                self.assertEqual(activity['yards_per_melee'],36)
                self.assertEqual(activity['fatigue_sources'][0]['printed_page'],232)
                if value*10 <= MAX_ACTIVITY_ATTRIBUTE:
                    self.assertEqual(activity['minutes'],value*10)
                    self.assertIsInstance(activity['minutes'],int)
                else:
                    self.assertIsNone(activity['minutes'])
                    self.assertIn('supported numeric range',activity['guidance'])
