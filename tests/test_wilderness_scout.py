"""Original RUE pp.99–100 Scout grants through public saved workflows."""

from copy import deepcopy
import tempfile
import unittest
from characters_unlimited.application import CharacterApplication
from characters_unlimited.rules import RuleArchive


class WildernessScoutTests(unittest.TestCase):
    def test_source_grants_class_dice_and_actual_selected_training(self):
        with tempfile.TemporaryDirectory() as directory:
            app=CharacterApplication(directory,die=lambda sides:3)
            hero=app.create(character_class='wilderness-scout')
            self.assertEqual(hero['attributes']['PS']['value'],13)  # 3D6 + class D4 + Athletics 1
            self.assertEqual(hero['attributes']['PE']['value'],12)
            view=app.skill_view(hero['id'])
            grants={row['id']:row for row in view['grants']}
            for identifier,value in {'native-language':94,'cook':50,'fishing':55,'climbing':60,
                'horse-general':60,'identify-plants-fruit':45,'land-navigation':56,'prowl':42,
                'radio-basic':55,'track-trap-animals':45,'wilderness-survival':50,
                'trail-blazing':20,'cross-country-pacing':35,'cartography':40}.items():
                self.assertEqual(grants[identifier]['percentage'],value,identifier)
            self.assertNotIn('percentage',grants['hunting'])
            self.assertEqual(grants['climbing']['additional_checks'][0]['percentage'],50)
            self.assertEqual(grants['horse-general']['additional_checks'][0]['percentage'],40)
            self.assertEqual({r['id']:r['remaining'] for r in view['pool_requirements']},{'physical':2,'wilderness':1})
            hero=app.select_required_skills(hero['id'],revision=hero['revision'],choices={
                'native_language':'English','other_languages':['Spanish','French'],'pilot':'motorcycle'})
            self.assertEqual(next(r for r in app.skill_view(hero['id'])['grants'] if r['id']=='motorcycle')['percentage'],74)
            hero=app.select_skills(hero['id'],revision=hero['revision'],selections=[
                {'skill_id':s,'pool':'related'} for s in ['swimming','climbing','skin-prepare-hides','math-basic','holistic-medicine','rope-works']])
            selected={row['id']:row for row in app.skill_view(hero['id'])['selected']}
            self.assertEqual(selected['climbing']['percentage'],60)
            self.assertEqual(selected['math-basic']['percentage'],50)
            self.assertEqual(selected['holistic-medicine']['contributions']['class'],10)
            self.assertEqual(selected['holistic-medicine']['effect_contributions'][0]['value'],10)
            self.assertEqual(selected['holistic-medicine']['selection_cost'],2)
            self.assertEqual(selected['rope-works']['percentage'],45)
            self.assertEqual(next(r for r in app.skill_view(hero['id'])['pool_requirements'] if r['id']=='physical')['remaining'],1)
            hero=app.select_skills(hero['id'],revision=hero['revision'],selections=[
                *hero['skill_selections'],{'skill_id':'running','pool':'related'}])
            self.assertTrue(all(r['remaining']==0 for r in app.skill_view(hero['id'])['pool_requirements']))
            self.assertEqual(next(r for r in app.skill_view(hero['id'])['grants'] if r['id']=='cartography')['additional_checks'],[])

    def test_unselected_scout_attribute_rule_rejects_before_dice(self):
        installed=RuleArchive.load()
        core=installed.active('rifts-core')
        next(row for row in core['classes'] if row['id']=='wilderness-scout')['attribute_bonuses']['PE']['count']=True
        archive=RuleArchive([core if (row['id'],row['version'])==(core['id'],core['version'])
            else row for row in installed.definitions()],installed.active_versions())
        with tempfile.TemporaryDirectory() as directory:
            app=CharacterApplication(directory,rule_archive=archive,
                die=lambda sides:self.fail('Unselected class rules must validate before dice'))
            with self.assertRaises(ValueError):
                app.create(character_class='vagabond')
            self.assertEqual(app.list(),[])

    def test_source_progression_bonuses_resources_and_learning_dates(self):
        with tempfile.TemporaryDirectory() as directory:
            app=CharacterApplication(directory,die=lambda sides:3)
            hero=app.create(character_class='wilderness-scout',level=3)
            original=deepcopy(hero)
            combat=app.combat_view(hero['id'])
            self.assertEqual(combat['remaining']['proficiencies'],3)
            self.assertEqual(combat['totals']['initiative']['value'],1)
            self.assertEqual(combat['totals']['roll_with_impact']['value'],5)  # Basic 2 + Athletics 1 + Scout 2
            self.assertEqual(combat['saving_bonuses']['horror_factor']['value'],1)
            self.assertEqual(combat['saving_bonuses']['poison']['value'],2)
            self.assertEqual(combat['saving_bonuses']['coma_death']['value'],10)
            self.assertEqual(app.skill_view(hero['id'])['remaining']['related'],10)
            self.assertEqual(app.skill_view(hero['id'])['remaining']['secondary'],5)
            hero=app.select_skills(hero['id'],revision=hero['revision'],selections=[{'skill_id':'math-basic','pool':'related'}])
            self.assertEqual(next(r for r in app.skill_view(hero['id'])['selected'] if r['id']=='math-basic')['percentage'],50)
            hero=app.advance(hero['id'],revision=hero['revision'],method='level',value=4)
            self.assertEqual(app.combat_view(hero['id'])['saving_bonuses']['horror_factor']['value'],2)
            self.assertEqual(next(r for r in app.skill_view(hero['id'])['selected'] if r['id']=='math-basic')['percentage'],55)
            self.assertEqual(next(r for r in app.skill_view(hero['id'])['grants'] if r['id']=='cartography')['percentage'],55)
            restored=app.undo_advancement(hero['id'],revision=hero['revision'])['character']
            self.assertEqual(restored['resources'],original['resources'])
            self.assertEqual(app.combat_view(hero['id'])['saving_bonuses']['horror_factor']['value'],1)

    def test_starting_funds_kit_ammunition_condition_and_portability(self):
        with tempfile.TemporaryDirectory() as directory:
            app=CharacterApplication(directory,die=lambda sides:3)
            hero=app.create(character_class='wilderness-scout')
            hero=app.generate_starting_funds(hero['id'],revision=hero['revision'])
            self.assertEqual(hero['equipment']['credits'],900)
            self.assertEqual(hero['starting_funds']['saleable_goods']['value'],9000)
            hero=app.grant_starting_gear(hero['id'],revision=hero['revision'])
            self.assertEqual(len(hero['starting_gear']['grants']),26)
            hero=app.grant_starting_group(hero['id'],revision=hero['revision'],group_id='elective-weapon-1',selection='wilks-447')
            hero=app.grant_starting_group(hero['id'],revision=hero['revision'],group_id='transport',selection='scout-hovercycle')
            receipts=deepcopy(hero['starting_equipment_groups'])
            self.assertEqual(receipts['elective-weapon-1']['grants'][1]['quantity'],3)
            self.assertEqual(receipts['transport']['condition'],{'rolls':[3],'value':30})
            hero=app.set_equipment(hero['id'],revision=hero['revision'],inventory={'credits':12,'items':[]})
            app.die=lambda sides:self.fail('Portable receipts must never reroll')
            imported=app.import_character(app.export_character(hero['id']))
            self.assertEqual(imported['starting_equipment_groups'],receipts)
            self.assertEqual(imported['starting_gear'],hero['starting_gear'])
            self.assertEqual(CharacterApplication(directory).get(hero['id']),hero)

    def test_old_pins_remain_and_compatible_upgrade_preserves_original_class_receipts(self):
        with tempfile.TemporaryDirectory() as directory:
            archive=RuleArchive.load()
            old=RuleArchive(archive.definitions(),{**archive.active_versions(),'rifts-core':'1.2.0',
                'rifts-domestic-skills':'2.23.0','rifts-equipment':'1.10.0'})
            previous=CharacterApplication(directory,die=lambda sides:3,rule_archive=old)
            hero=previous.create()
            hero=previous.generate_starting_funds(hero['id'],revision=hero['revision'])
            hero=previous.grant_starting_gear(hero['id'],revision=hero['revision'])
            current=CharacterApplication(directory,die=lambda sides:self.fail('Compatible upgrades must not reroll'))
            self.assertEqual(current.get(hero['id'])['rules']['version'],'1.2.0')
            preview=current.preview_rule_upgrade(hero['id'])
            updated=current.apply_rule_upgrade(hero['id'],revision=hero['revision'],token=preview['token'])['character']
            for field in ['attributes','starting_funds','starting_gear','equipment']:
                self.assertEqual(updated[field],hero[field])
            self.assertEqual(updated['rules']['version'],'1.2.0')  # Core identity stays pinned; skill/equipment updates are explicit.
            self.assertEqual(updated['additional_rule_packs']['rifts-domestic-skills'],'2.30.0')

    def test_vibro_weapon_keeps_mega_damage_without_structural_strength_additions(self):
        with tempfile.TemporaryDirectory() as directory:
            app=CharacterApplication(directory,die=lambda sides:3)
            hero=app.create(character_class='wilderness-scout')
            hero=app.set_attribute(hero['id'],revision=hero['revision'],attribute='PS',mode='fixed',value=30)
            hero=app.grant_starting_group(hero['id'],revision=hero['revision'],group_id='vibro-blade',selection='vibro-knife')
            inventory=deepcopy(hero['equipment']);inventory['items'][0]['equipped']=True
            hero=app.set_equipment(hero['id'],revision=hero['revision'],inventory=inventory)
            attack=app.equipment_view(hero['id'])['melee_attacks'][0]
            self.assertEqual(attack['damage'],'1D6 M.D.')
            self.assertEqual(attack['damage_bonus']['value'],0)

    def test_starting_equipment_matches_actual_training_and_retains_mismatches_with_guidance(self):
        from io import BytesIO
        from pypdf import PdfReader
        with tempfile.TemporaryDirectory() as directory:
            app=CharacterApplication(directory,die=lambda sides:3)
            hero=app.create(character_class='wilderness-scout')
            hero=app.select_required_skills(hero['id'],revision=hero['revision'],choices={'pilot':'horse-general'})
            hero=app.select_combat(hero['id'],revision=hero['revision'],choices={
                'ancient':['sword'],'modern':['energy-pistol','energy-rifle']})
            hero=app.grant_starting_group(hero['id'],revision=hero['revision'],group_id='transport',selection='scout-horse-wagon')
            hero=app.grant_starting_group(hero['id'],revision=hero['revision'],group_id='elective-weapon-1',selection='vibro-saber')
            hero=app.grant_starting_group(hero['id'],revision=hero['revision'],group_id='elective-weapon-2',selection='wilks-320')
            hero=app.grant_starting_group(hero['id'],revision=hero['revision'],group_id='elective-weapon-3',selection='knife-large')
            view=app.equipment_view(hero['id'])
            groups={row['id']:row for row in view['starting_groups']['groups']}
            for group,option in [('transport','scout-horse-wagon'),('elective-weapon-1','vibro-saber'),('elective-weapon-2','wilks-320')]:
                self.assertTrue(groups[group]['option_requirements'][option][0]['satisfied'])
            self.assertFalse(groups['elective-weapon-3']['option_requirements']['knife-large'][0]['satisfied'])
            self.assertTrue(any('Weapon for elective W.P. 3' in note and 'retained' in note for note in view['warnings']))
            before=deepcopy(hero['starting_equipment_groups'])
            app.die=lambda sides:self.fail('Training guidance must not reroll retained equipment')
            restored=app.import_character(app.export_character(hero['id']))
            self.assertEqual(restored['starting_equipment_groups'],before)
            self.assertEqual(app.equipment_view(restored['id'])['warnings'],view['warnings'])
            fields=PdfReader(BytesIO(app.export_pdf(hero['id']))).get_fields()
            assert fields is not None
            self.assertIn('Training guidance:', ' '.join(str(row.get('/V','')) for row in fields.values()))

    def test_unselected_equipment_training_requirements_reject_before_dice(self):
        for change in ('unknown-training','unknown-option','bad-slot','unknown-catalog'):
            installed=RuleArchive.load()
            pack=installed.active('rifts-equipment')
            group=pack['class_profiles']['wilderness-scout']['starting_groups']['groups']['elective-weapon-1']
            if change=='unknown-training':
                group['option_requirements']['knife-large'][0]['selected_options']['selector']={'any_of':[{'ids':['missing']} ]}
            if change=='unknown-option':
                group['option_requirements']['missing']=group['option_requirements']['knife-large']
            if change=='bad-slot':
                group['proficiency_slot']=True
            if change=='unknown-catalog':
                group['option_requirements']['knife-large'][0]['selected_options']['catalog']='absent'
            archive=RuleArchive([pack if (row['id'],row['version'])==(pack['id'],pack['version'])
                else row for row in installed.definitions()],installed.active_versions())
            with self.subTest(change=change),tempfile.TemporaryDirectory() as directory:
                app=CharacterApplication(directory,rule_archive=archive,
                    die=lambda sides:self.fail('Unselected equipment requirements must reject before dice'))
                with self.assertRaises(ValueError):
                    app.create(character_class='vagabond')
                self.assertEqual(app.list(),[])
