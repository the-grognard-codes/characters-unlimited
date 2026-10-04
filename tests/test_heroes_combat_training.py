import tempfile,unittest
from characters_unlimited.application import CharacterApplication

class HeroesCombatTrainingTests(unittest.TestCase):
    def test_training_costs_and_level_one_profiles_use_one_active_style(self):
        with tempfile.TemporaryDirectory() as directory:
            app=CharacterApplication(directory,die=lambda sides:4)
            c=app.create(game='heroes-unlimited')
            c=app.select_education(c['id'],revision=0,method='choose',education_id='high-school')
            c=app.set_attribute(c['id'],revision=c['revision'],attribute='PS',mode='fixed',value=20)
            c=app.set_attribute(c['id'],revision=c['revision'],attribute='PP',mode='fixed',value=18)
            c=app.select_hero_secondary(c['id'],revision=c['revision'],selections=['hand-to-hand-expert'])
            view=app.hero_program_view(c['id'])
            self.assertEqual(view['secondary']['used'],2)
            self.assertEqual(view['combat']['training'],'Hand to Hand: Expert')
            self.assertEqual(view['combat']['totals']['attacks']['value'],4)
            c=app.select_hero_secondary(c['id'],revision=c['revision'],selections=['hand-to-hand-expert','hand-to-hand-martial-arts','hand-to-hand-assassin'])
            self.assertEqual(app.hero_program_view(c['id'])['secondary']['used'],8)
            self.assertEqual(app.hero_program_view(c['id'])['combat']['training'],'Hand to Hand: Expert')
            for style,attacks,initiative,strike,pull,roll in [
                ('martial-arts',4,2,2,3,3),('assassin',3,1,4,2,0),('expert',4,0,2,2,2)]:
                c=app.select_hero_training(c['id'],revision=c['revision'],training_id='hand-to-hand-'+style)
                view=app.hero_program_view(c['id'])['combat']
                self.assertEqual([view['totals'][n]['value'] for n in ['attacks','initiative','strike','pull_punch','roll_with_impact']],[attacks,initiative,strike,pull,roll])
                self.assertEqual(view['parry_actions'],0)
                self.assertEqual(view['totals']['damage']['value'],5)
            c=app.select_hero_training(c['id'],revision=c['revision'],training_id=None)
            view=app.hero_program_view(c['id'])['combat']
            self.assertEqual(view['training'],'No Hand to Hand')
            self.assertEqual(view['totals']['attacks']['value'],3)
            self.assertEqual(view['parry_actions'],1)

    def test_ambiguous_initial_styles_explicit_none_and_removal_keep_retained_receipts(self):
        from copy import deepcopy
        with tempfile.TemporaryDirectory() as directory:
            app=CharacterApplication(directory,die=lambda sides:4)
            c=app.create(game='heroes-unlimited')
            c=app.select_education(c['id'],revision=0,method='choose',education_id='high-school')
            choices=['body-building','running','hand-to-hand-basic','hand-to-hand-martial-arts']
            c=app.select_hero_secondary(c['id'],revision=c['revision'],selections=choices)
            view=app.hero_program_view(c['id'])
            self.assertEqual(view['combat']['training'],'No Hand to Hand')
            self.assertEqual(view['combat']['totals']['attacks']['value'],3)
            self.assertTrue(any('Multiple training' in note for note in view['combat']['guidance']))
            receipts=deepcopy(c['physical_acquisitions'])
            attributes=deepcopy(c['attributes'])
            c=app.select_hero_training(c['id'],revision=c['revision'],training_id='hand-to-hand-martial-arts')
            c=app.select_hero_secondary(c['id'],revision=c['revision'],selections=['body-building','running','hand-to-hand-basic'])
            self.assertEqual(c['hero_combat_training'],'hand-to-hand-martial-arts')
            self.assertEqual(app.hero_program_view(c['id'])['combat']['totals']['attacks']['value'],3)
            removed=next(row for row in app.hero_program_view(c['id'])['combat']['training_receipts'] if row['id']=='hand-to-hand-martial-arts')
            self.assertFalse(removed['selected'])
            self.assertFalse(removed['active'])
            self.assertEqual(removed['rolls'],{})
            self.assertEqual(removed['source']['pages'],[55,71])
            restored=app.import_character(app.export_character(c['id']))
            self.assertEqual(restored['physical_acquisitions'],receipts)
            c=app.select_hero_secondary(c['id'],revision=c['revision'],selections=choices)
            self.assertEqual(app.hero_program_view(c['id'])['combat']['training'],'Hand to Hand: Martial Arts')
            self.assertEqual(c['physical_acquisitions'],receipts)
            self.assertEqual(c['attributes'],attributes)
            c=app.select_hero_training(c['id'],revision=c['revision'],training_id=None)
            c=app.select_hero_secondary(c['id'],revision=c['revision'],selections=['hand-to-hand-expert'])
            self.assertEqual(app.hero_program_view(c['id'])['combat']['training'],'No Hand to Hand')
            for invalid in ['hand-to-hand-martial-arts','unknown',False,[]]:
                with self.assertRaises(ValueError):app.select_hero_training(c['id'],revision=c['revision'],training_id=invalid)
                self.assertEqual(app.get(c['id']),c)

    def test_portable_training_requires_a_known_acquired_exact_game_profile(self):
        from copy import deepcopy
        with tempfile.TemporaryDirectory() as directory:
            app=CharacterApplication(directory,die=lambda sides:4)
            c=app.create(game='heroes-unlimited')
            c=app.select_education(c['id'],revision=0,method='choose',education_id='high-school')
            c=app.select_hero_secondary(c['id'],revision=c['revision'],selections=['hand-to-hand-basic'])
            bundle=app.export_character(c['id'])
            for invalid in ['hand-to-hand-expert','unknown',False,[],{}]:
                bad=deepcopy(bundle);bad['character']['hero_combat_training']=invalid
                with self.assertRaises(ValueError):app.import_character(bad)
                self.assertEqual(app.get(c['id']),c)
            rifts=app.create()
            bad=app.export_character(rifts['id']);bad['character']['hero_combat_training']=None
            with self.assertRaises(ValueError):app.import_character(bad)
            self.assertEqual(app.get(rifts['id']),rifts)

    def test_legacy_basic_update_keeps_receipt_and_training_and_guards_inactive_styles(self):
        from copy import deepcopy
        from characters_unlimited.rules import RuleArchive
        with tempfile.TemporaryDirectory() as directory:
            archive=RuleArchive.load()
            earlier=CharacterApplication(directory,die=lambda sides:4,rule_archive=RuleArchive(archive.definitions(),{**archive.active_versions(),'heroes-program-skills':'1.12.0'}))
            c=earlier.create(game='heroes-unlimited')
            c=earlier.select_education(c['id'],revision=0,method='choose',education_id='high-school')
            c=earlier.select_hero_secondary(c['id'],revision=c['revision'],selections=['hand-to-hand-basic'])
            with self.assertRaises(ValueError):earlier.select_hero_training(c['id'],revision=c['revision'],training_id=None)
            app=CharacterApplication(directory,die=lambda sides:4)
            preview=app.preview_rule_upgrade(c['id'])
            self.assertEqual(preview['combat'],[])
            c=app.apply_rule_upgrade(c['id'],revision=c['revision'],token=preview['token'])['character']
            self.assertEqual(c['physical_acquisitions'],{'hand-to-hand-basic':{'rolls':{}}})
            c=app.select_hero_secondary(c['id'],revision=c['revision'],selections=['hand-to-hand-basic','hand-to-hand-assassin','hand-to-hand-assassin'])
            self.assertEqual(app.hero_program_view(c['id'])['secondary']['used'],7)
            self.assertEqual(app.hero_program_view(c['id'])['combat']['training'],'Hand to Hand: Basic')
            self.assertTrue(any('requires evil alignment' in note for note in app.hero_program_view(c['id'])['warnings']))
            c=app.select_hero_secondary(c['id'],revision=c['revision'],selections=['hand-to-hand-basic'])
            target=deepcopy(archive.active('heroes-program-skills'));target['version']='99.0.0'
            next(row for row in target['skills'] if row['id']=='hand-to-hand-assassin')['combat']['attacks']=2
            newer=CharacterApplication(directory,rule_archive=RuleArchive([*archive.definitions(),target],{**archive.active_versions(),'heroes-program-skills':'99.0.0'}))
            with self.assertRaises(ValueError):newer.preview_rule_upgrade(c['id'])
            self.assertEqual(app.get(c['id']),c)

    def test_pdf_training_and_inactive_profiles_remain_editable_and_do_not_leak_later_bonuses(self):
        from io import BytesIO
        from pypdf import PdfReader
        with tempfile.TemporaryDirectory() as directory:
            app=CharacterApplication(directory,die=lambda sides:4)
            c=app.create(game='heroes-unlimited')
            c=app.select_education(c['id'],revision=0,method='choose',education_id='high-school')
            c=app.select_hero_secondary(c['id'],revision=c['revision'],selections=['hand-to-hand-basic','hand-to-hand-martial-arts'])
            c=app.select_hero_training(c['id'],revision=c['revision'],training_id='hand-to-hand-martial-arts')
            fields=PdfReader(BytesIO(app.export_pdf(c['id']))).get_fields();assert fields is not None
            self.assertEqual(fields['COMBAT_SKILL']['/V'],'Hand to Hand: Martial Arts')
            self.assertEqual(fields['ATTACKS']['/V'],'4')
            self.assertEqual(fields['INITIATIVE']['/V'],'2')
            self.assertEqual(fields['STRIKE']['/V'],'0')
            text='\n'.join(str(row.get('/V','')) for row in fields.values())
            self.assertIn('Hand to Hand: Basic (inactive training)',text)
            self.assertNotIn('skills.hand-to-hand-martial-arts.percentage',fields)
            self.assertNotIn('Karate-style kick:',text)
