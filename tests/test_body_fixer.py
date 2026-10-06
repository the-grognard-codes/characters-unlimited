"""Original RUE87-88 Body Fixer values across public retained workflows."""

from copy import deepcopy
from io import BytesIO
import tempfile
import unittest
from pypdf import PdfReader
from characters_unlimited.application import CharacterApplication
from characters_unlimited.rules import RuleArchive


class BodyFixerTests(unittest.TestCase):
    def test_required_medical_checks_and_source_attributes(self):
        with tempfile.TemporaryDirectory() as directory:
            app=CharacterApplication(directory,die=lambda sides:3)
            for identity in ['body-fixer','body-fixer-city']:
                hero=app.create(character_class=identity)
                self.assertEqual({k:hero['attributes'][k]['value'] for k in ['IQ','MA','PS','PP','PE']},
                    {'IQ':9,'MA':10,'PS':10,'PP':10,'PE':11})  # Outdoorsmanship adds one more PE.
                rows={r['id']:r for r in app.skill_view(hero['id'])['grants']}
                doctor=rows['medical-doctor']
                self.assertEqual(doctor['uncapped_percentage'],100)
                self.assertEqual(doctor['percentage'],98)
                self.assertEqual([r['percentage'] for r in doctor['additional_checks']],[70,35])
                self.assertNotIn('Effect: Disease Diagnostic Specialist',doctor['additional_checks'][0]['contributions'])
                self.assertEqual(rows['literacy-native']['percentage'],70)
                self.assertEqual(rows['brewing-medicinal']['percentage'],45)
                self.assertEqual(app.combat_view(hero['id'])['fixed_proficiencies']['ancient'],['knife'])
                self.assertEqual(app.combat_view(hero['id'])['related_cost'],0)
                self.assertEqual(app.combat_view(hero['id'])['melee'][0]['strike']['value'],1)
                self.assertEqual(app.combat_view(hero['id'])['totals']['dodge']['value'],1)
                self.assertEqual(app.combat_view(hero['id'])['totals']['disarm']['value'],1)

    def test_required_physical_swap_duplicate_and_reselection_keep_original_rolls(self):
        with tempfile.TemporaryDirectory() as directory:
            app=CharacterApplication(directory,die=lambda sides:3)
            hero=app.create(character_class='body-fixer')
            hero=app.select_required_skills(hero['id'],revision=hero['revision'],choices={'physical':'athletics'})
            self.assertEqual(hero['attributes']['PS']['value'],11)
            receipts=deepcopy(hero['physical_acquisitions'])
            app.die=lambda sides:self.fail('Cached or constant Physical choices cannot reroll')
            hero=app.select_skills(hero['id'],revision=hero['revision'],selections=[{'skill_id':'athletics','pool':'related'}])
            self.assertEqual(hero['attributes']['PS']['value'],11)
            self.assertEqual(hero['physical_acquisitions'],receipts)
            hero=app.select_skills(hero['id'],revision=hero['revision'],selections=[])
            hero=app.select_required_skills(hero['id'],revision=hero['revision'],choices={'physical':'body-building'})
            self.assertEqual(hero['attributes']['PS']['value'],12)
            self.assertEqual(hero['attributes']['SPD']['value'],9)
            hero=app.select_required_skills(hero['id'],revision=hero['revision'],choices={'physical':'athletics'})
            self.assertEqual(hero['attributes']['PS']['value'],11)
            self.assertEqual(hero['attributes']['SPD']['value'],12)
            self.assertEqual(hero['physical_acquisitions']['athletics'],receipts['athletics'])
            self.assertIn('body-building',hero['physical_acquisitions'])
            self.assertEqual(CharacterApplication(directory).get(hero['id']),hero)
            imported=app.import_character(app.export_character(hero['id']))
            self.assertEqual(imported['physical_acquisitions'],hero['physical_acquisitions'])
            self.assertEqual(imported['attributes'],hero['attributes'])

    def test_stale_required_choice_does_not_acquire_new_dice_or_mutate_save(self):
        with tempfile.TemporaryDirectory() as directory:
            app=CharacterApplication(directory,die=lambda sides:3)
            hero=app.create(character_class='body-fixer')
            stale=hero['revision']
            hero=app.edit(hero['id'],revision=stale,notes='Retain this edit')
            app.die=lambda sides:self.fail('Stale required choice cannot draw dice')
            with self.assertRaises(ValueError):
                app.select_required_skills(hero['id'],revision=stale,choices={'physical':'athletics'})
            self.assertEqual(app.get(hero['id']),hero)

    def test_advancement_required_growth_category_minimum_and_undo(self):
        with tempfile.TemporaryDirectory() as directory:
            app=CharacterApplication(directory,die=lambda sides:3)
            hero=app.create(character_class='body-fixer')
            hero=app.select_required_skills(hero['id'],revision=hero['revision'],choices={'native_language':'English','physical':'body-building','pilot':'automobile'})
            hero=app.select_skills(hero['id'],revision=hero['revision'],selections=[
                {'skill_id':i,'pool':'related'} for i in ['medical-doctor','pathology','brewing-medicinal','first-aid','holistic-medicine','field-surgery']])
            self.assertEqual(app.skill_view(hero['id'])['pool_requirements'][0]['remaining'],0)
            rows={r['id']:r for r in app.skill_view(hero['id'])['selected']}
            self.assertEqual(rows['medical-doctor']['additional_checks'][0]['percentage'],70)
            self.assertEqual(rows['holistic-medicine']['percentage'],50)
            hero=app.generate_resources(hero['id'],revision=hero['revision'])
            self.assertEqual({k:r['value'] for k,r in app.resource_view(hero['id'])['resources'].items()}, {'SDC':41,'HP':14})
            original=deepcopy(hero['resources'])
            hero=app.advance(hero['id'],revision=hero['revision'],method='level',value=3)
            rows={r['id']:r for r in app.skill_view(hero['id'])['grants']}
            self.assertEqual(rows['literacy-native']['percentage'],80)
            self.assertEqual([r['percentage'] for r in rows['medical-doctor']['additional_checks']],[80,45])
            self.assertEqual(app.skill_view(hero['id'])['remaining'],{'related':7,'secondary':7})
            hero=app.undo_advancement(hero['id'],revision=hero['revision'])['character']
            self.assertEqual(hero['level'],2)
            hero=app.undo_advancement(hero['id'],revision=hero['revision'])['character']
            self.assertEqual(hero['level'],1)
            self.assertEqual(hero['resources'],original)

    def test_lifestyle_funds_and_full_source_inventory_replay(self):
        with tempfile.TemporaryDirectory() as directory:
            app=CharacterApplication(directory,die=lambda sides:3)
            for identity,credits in [('body-fixer',3000),('body-fixer-city',15000)]:
                hero=app.create(character_class=identity)
                hero=app.select_required_skills(hero['id'],revision=hero['revision'],choices={'pilot':'automobile'})
                hero=app.generate_starting_funds(hero['id'],revision=hero['revision'])
                self.assertEqual(hero['equipment']['credits'],credits)
                self.assertEqual('saleable_goods' in hero['starting_funds'],identity=='body-fixer')
                hero=app.grant_starting_gear(hero['id'],revision=hero['revision'])
                choices={'armor':'plastic-man','fixed-knife':'knife-large','medical-vibro-knife':'vibro-knife',
                    'body-fixer-irmss':'body-fixer-irmss','body-fixer-compu-drug':'body-fixer-compu-drug',
                    'body-fixer-laser-scalpel':'body-fixer-laser-scalpel','city-rat-rmk':'city-rat-rmk','transport':'body-fixer-jeep'}
                for group,item in choices.items():
                    hero=app.grant_starting_group(hero['id'],revision=hero['revision'],group_id=group,selection=item)
                self.assertFalse(any(r['id'].startswith('elective-weapon-') for r in app.equipment_view(hero['id'])['starting_groups']['groups']))
                self.assertEqual(sum(r['quantity'] for r in hero['equipment']['items'] if r['item_id']=='standard-e-clip'),2)
                imported=app.import_character(app.export_character(hero['id']))
                self.assertEqual(imported['starting_equipment_groups'],hero['starting_equipment_groups'])
                self.assertEqual(imported['equipment'],hero['equipment'])
                fields=PdfReader(BytesIO(app.export_pdf(hero['id']))).get_fields()
                assert fields is not None
                text=' '.join(str(r.get('/V','')) for r in fields.values())
                self.assertIn('[checks: primary]',text)
                self.assertIn('Wilks laser scalpel',text)

    def test_fixed_knife_and_each_extra_wp_have_separate_weapon_and_clip_receipts(self):
        with tempfile.TemporaryDirectory() as directory:
            app=CharacterApplication(directory,die=lambda sides:3)
            hero=app.create(character_class='body-fixer')
            hero=app.select_combat(hero['id'],revision=hero['revision'],choices={'ancient':['knife','sword'],'modern':['energy-pistol'],'hand_to_hand':'expert'})
            self.assertEqual(app.combat_view(hero['id'])['related_cost'],4)  # Expert2 + Sword1 + Energy Pistol1.
            groups={r['id']:r for r in app.equipment_view(hero['id'])['starting_groups']['groups']}
            self.assertIn('elective-weapon-2',groups)
            self.assertNotIn('elective-weapon-3',groups)
            for group,item in [('fixed-knife','knife-large'),('elective-weapon-1','vibro-saber'),('elective-weapon-2','wilks-320')]:
                hero=app.grant_starting_group(hero['id'],revision=hero['revision'],group_id=group,selection=item)
            self.assertEqual(sum(r['quantity'] for r in hero['equipment']['items'] if r['item_id']=='standard-e-clip'),6)
            receipts=deepcopy(hero['starting_equipment_groups'])
            hero=app.select_combat(hero['id'],revision=hero['revision'],choices={'ancient':[],'modern':[]})
            self.assertEqual(app.import_character(app.export_character(hero['id']))['starting_equipment_groups'],receipts)

    def test_malformed_unselected_physical_and_scoped_check_rules_reject_before_draws(self):
        # Warm the immutable content cache; a changed declaration with the same
        # version must still pass every unselected-owner preflight below.
        with tempfile.TemporaryDirectory() as directory:
            CharacterApplication(directory,die=lambda sides:3).create()
        for fault in ['physical','unknown-check','context-check','boolean-repeat']:
            installed=RuleArchive.load();pack=installed.active('rifts-equipment' if fault=='boolean-repeat' else 'rifts-domestic-skills')
            owner=pack['class_profiles']['body-fixer-city']
            if fault=='physical': owner['required']['groups'][2]['options'][0]['attributes']['PS']['bonus']=999
            elif fault=='boolean-repeat': owner['starting_groups']['groups']['elective-weapon']['repeat_for_proficiencies']=True
            else: owner['skill_effects'][0]['check_names']=['unknown' if fault=='unknown-check' else 'Animal treatment']
            archive=RuleArchive([pack if (r['id'],r['version'])==(pack['id'],pack['version']) else r for r in installed.definitions()],installed.active_versions())
            with tempfile.TemporaryDirectory() as directory:
                app=CharacterApplication(directory,rule_archive=archive,die=lambda sides:self.fail('No invalid-rule draws'))
                with self.assertRaises(ValueError): app.create(character_class='vagabond')
                self.assertEqual(app.list(),[])

    def test_repeated_owned_rule_resolution_returns_independent_declarations(self):
        with tempfile.TemporaryDirectory() as directory:
            app=CharacterApplication(directory,die=lambda sides:3)
            hero=app.create(character_class='body-fixer')
            rules=app.character_skill_pack(hero)
            rules['class_bonuses']['combat']['dodge']=999
            rules['class_profiles']['body-fixer-city']['required']['groups'].clear()
            fresh=app.character_skill_pack(hero)
            self.assertEqual(fresh['class_bonuses']['combat']['dodge'],1)
            self.assertEqual(len(fresh['class_profiles']['body-fixer-city']['required']['groups']),4)
            self.assertEqual(app.combat_view(hero['id'])['totals']['dodge']['value'],1)

    def test_scoped_additional_check_leaves_primary_and_legacy_effects_unchanged(self):
        installed=RuleArchive.load();pack=installed.active('rifts-domestic-skills')
        pack['class_profiles']['body-fixer']['skill_effects'][0]['check_names']=['Treatment']
        archive=RuleArchive([pack if (r['id'],r['version'])==(pack['id'],pack['version']) else r for r in installed.definitions()],installed.active_versions())
        with tempfile.TemporaryDirectory() as directory:
            app=CharacterApplication(directory,rule_archive=archive,die=lambda sides:3)
            hero=app.create(character_class='body-fixer')
            doctor=next(r for r in app.skill_view(hero['id'])['grants'] if r['id']=='medical-doctor')
            self.assertEqual(doctor['percentage'],80)
            self.assertEqual([r['percentage'] for r in doctor['additional_checks']],[90,55])


if __name__=='__main__':
    unittest.main()
