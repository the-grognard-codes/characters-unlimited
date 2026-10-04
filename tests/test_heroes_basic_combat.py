import tempfile,unittest
from characters_unlimited.application import CharacterApplication

class HeroesBasicCombatTests(unittest.TestCase):
    def test_heroes_attribute_chart_limits_and_initiative_do_not_use_rifts_rules(self):
        with tempfile.TemporaryDirectory() as directory:
            app=CharacterApplication(directory,die=lambda sides:4)
            c=app.create(game='heroes-unlimited')
            c=app.set_attribute(c['id'],revision=0,attribute='SPD',mode='fixed',value=1)
            combat=app.hero_program_view(c['id'])['combat']
            self.assertEqual(combat['totals']['initiative']['value'],0)
            self.assertEqual(combat['totals']['dodge']['value'],0)
            for pp,bonus,initiative in [(16,1,0),(30,8,0),(31,8,0),(34,8,1),(38,8,2),(50,8,5),(51,None,None),(7,None,None)]:
                c=app.set_attribute(c['id'],revision=c['revision'],attribute='PP',mode='fixed',value=pp)
                totals=app.hero_program_view(c['id'])['combat']['totals']
                self.assertEqual(totals['strike']['value'],bonus)
                self.assertEqual(totals['initiative']['value'],initiative)
                self.assertEqual(totals['attacks']['value'],3)
                if bonus is None:
                    self.assertNotIn('P.P.',totals['strike']['contributions'])
                    self.assertNotIn('P.P.',totals['initiative']['contributions'])
            c=app.select_education(c['id'],revision=c['revision'],method='choose',education_id='high-school')
            c=app.select_hero_secondary(c['id'],revision=c['revision'],selections=['hand-to-hand-basic'])
            totals=app.hero_program_view(c['id'])['combat']['totals']
            self.assertEqual(totals['pull_punch']['value'],2)
            self.assertEqual(totals['roll_with_impact']['value'],2)
            for ps,damage in [(8,0),(16,1),(30,15),(31,16),(40,25),(41,None),(7,None)]:
                c=app.set_attribute(c['id'],revision=c['revision'],attribute='PS',mode='fixed',value=ps)
                result=app.hero_program_view(c['id'])['combat']['totals']['damage']
                self.assertEqual(result['value'],damage)
                if damage is None:self.assertNotIn('Ordinary P.S.',result['contributions'])

    def test_outside_group_training_and_tampered_empty_receipts_cannot_grant_basic(self):
        from copy import deepcopy
        from characters_unlimited.rules import RuleArchive
        with tempfile.TemporaryDirectory() as directory:
            app=CharacterApplication(directory,die=lambda sides:4)
            c=app.create(game='heroes-unlimited')
            c=app.select_education(c['id'],revision=0,method='choose',education_id='college-one')
            c=app.select_hero_programs(c['id'],revision=c['revision'],selections=[{'slot':0,'program':'computer','choices':{'repair-radio':['hand-to-hand-basic']}}])
            self.assertEqual(c['physical_acquisitions'],{})
            self.assertEqual(app.hero_program_view(c['id'])['combat']['totals']['attacks']['value'],3)
            c=app.select_hero_secondary(c['id'],revision=c['revision'],selections=['hand-to-hand-basic'])
            c=app.select_hero_secondary(c['id'],revision=c['revision'],selections=[])
            bundle=app.export_character(c['id'])
            for issue in ('source','rolls'):
                bad=deepcopy(bundle);receipt=bad['character']['physical_acquisitions']['hand-to-hand-basic']
                if issue=='source':receipt['source']={'pages':[1]}
                else:receipt['rolls']['attribute:PE']=[]
                with self.assertRaises(ValueError):app.import_character(bad)
                self.assertEqual(app.get(c['id']),c)
            archive=RuleArchive.load();changed=deepcopy(archive.active('heroes-program-skills'));changed['version']='99.0.0'
            next(row for row in changed['skills'] if row['id']=='hand-to-hand-basic')['combat']['attacks']=3
            newer=CharacterApplication(directory,rule_archive=RuleArchive([*archive.definitions(),changed],{**archive.active_versions(),'heroes-program-skills':'99.0.0'}))
            with self.assertRaises(ValueError):newer.preview_rule_upgrade(c['id'])
            self.assertEqual(app.get(c['id']),c)

    def test_legacy_pin_preview_discloses_combat_and_preserves_existing_physical_receipts(self):
        from copy import deepcopy
        from characters_unlimited.rules import RuleArchive
        with tempfile.TemporaryDirectory() as directory:
            archive=RuleArchive.load()
            earlier=CharacterApplication(directory,die=lambda sides:4,rule_archive=RuleArchive(archive.definitions(),{**archive.active_versions(),'heroes-program-skills':'1.11.0'}))
            c=earlier.create(game='heroes-unlimited')
            c=earlier.select_education(c['id'],revision=0,method='choose',education_id='high-school')
            c=earlier.select_hero_secondary(c['id'],revision=c['revision'],selections=['body-building','running'])
            self.assertFalse(earlier.hero_program_view(c['id'])['combat']['supported'])
            receipts=deepcopy(c['physical_acquisitions'])
            app=CharacterApplication(directory,die=lambda sides:4)
            with self.assertRaises(ValueError):app.select_hero_secondary(c['id'],revision=c['revision'],selections=['hand-to-hand-basic'])
            preview=app.preview_rule_upgrade(c['id'])
            self.assertTrue(any(row['name']=='Heroes attacks' and row['before'] is None and row['after']==3 for row in preview['combat']))
            c=app.apply_rule_upgrade(c['id'],revision=c['revision'],token=preview['token'])['character']
            self.assertEqual(c['physical_acquisitions'],receipts)
            c=app.select_hero_secondary(c['id'],revision=c['revision'],selections=['body-building','running','hand-to-hand-basic'])
            self.assertEqual(app.hero_program_view(c['id'])['combat']['totals']['attacks']['value'],4)
            restored=app.import_character(app.export_character(c['id']))
            self.assertEqual(restored['physical_acquisitions'],c['physical_acquisitions'])
            self.assertEqual(app.hero_program_view(restored['id'])['combat'],app.hero_program_view(c['id'])['combat'])

    def test_editable_pdf_populates_basic_combat_and_unarmed_effects_without_a_percentage(self):
        from io import BytesIO
        from pypdf import PdfReader
        with tempfile.TemporaryDirectory() as directory:
            app=CharacterApplication(directory,die=lambda sides:4)
            c=app.create(game='heroes-unlimited')
            c=app.select_education(c['id'],revision=0,method='choose',education_id='high-school')
            c=app.set_attribute(c['id'],revision=c['revision'],attribute='PS',mode='fixed',value=20)
            c=app.select_hero_secondary(c['id'],revision=c['revision'],selections=['hand-to-hand-basic'])
            fields=PdfReader(BytesIO(app.export_pdf(c['id']))).get_fields()
            assert fields is not None
            self.assertEqual(fields['COMBAT_SKILL']['/V'],'Hand to Hand: Basic')
            self.assertEqual(fields['ATTACKS']['/V'],'4')
            self.assertEqual(fields['DAMAGE']['/V'],'5')
            self.assertNotIn('skills.hand-to-hand-basic.percentage',fields)
            text='\n'.join(str(row.get('/V','')) for row in fields.values())
            self.assertIn('Power kick: 2 x 2D4 + 5 S.D.C.; 2 actions',text)
            self.assertIn('pull punch: 2',text)

    def test_untrained_and_basic_attacks_attribute_bonuses_and_action_costs_do_not_stack(self):
        with tempfile.TemporaryDirectory() as directory:
            app=CharacterApplication(directory,die=lambda sides:4)
            c=app.create(game='heroes-unlimited')
            c=app.select_education(c['id'],revision=0,method='choose',education_id='high-school')
            view=app.hero_program_view(c['id'])['combat']
            self.assertEqual(view['totals']['attacks']['value'],3)
            self.assertEqual(view['parry_actions'],1)
            c=app.set_attribute(c['id'],revision=c['revision'],attribute='PS',mode='fixed',value=20)
            c=app.set_attribute(c['id'],revision=c['revision'],attribute='PP',mode='fixed',value=18)
            c=app.select_hero_secondary(c['id'],revision=c['revision'],selections=['hand-to-hand-basic','hand-to-hand-basic'])
            view=app.hero_program_view(c['id'])
            self.assertEqual(view['secondary']['used'],2)
            combat=view['combat']
            self.assertEqual(combat['training'],'Hand to Hand: Basic')
            self.assertEqual(combat['parry_actions'],0)
            self.assertEqual([combat['totals'][n]['value'] for n in ['attacks','initiative','strike','parry','dodge','damage','roll_with_impact','pull_punch']],[4,0,2,2,2,5,2,2])
            attacks={row['id']:row for row in combat['unarmed']}
            self.assertEqual(attacks['punch']['damage'],'1D4 + 5 S.D.C.')
            self.assertEqual(attacks['kick']['damage'],'2D4 + 5 S.D.C.')
            self.assertEqual(attacks['power-punch']['damage'],'2 x 1D4 + 5 S.D.C.')
            self.assertEqual(attacks['power-kick']['damage'],'2 x 2D4 + 5 S.D.C.')
            self.assertEqual(attacks['power-kick']['actions'],2)
            c=app.select_hero_secondary(c['id'],revision=c['revision'],selections=[])
            combat=app.hero_program_view(c['id'])['combat']
            self.assertEqual(combat['totals']['attacks']['value'],3)
            self.assertEqual(combat['parry_actions'],1)
