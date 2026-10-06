"""RUE printed93-96 scholarly paths with independently calculated normal skills."""

from copy import deepcopy
from io import BytesIO
import tempfile
import unittest
from pypdf import PdfReader
from characters_unlimited.application import CharacterApplication
from characters_unlimited.rules import RuleArchive


class ScholarlyClassTests(unittest.TestCase):
    def test_owned_source_attributes_required_skills_and_private_checks(self):
        cases = {
            'rogue-scholar': {'IQ':10, 'MA':11, 'native-language':98, 'math-basic':70,
                'literacy-native':90, 'computer-operation':60, 'computer-programming':45,
                'creative-writing':40, 'find-contraband':41, 'history-pre':59, 'history-post':60,
                'research':70, 'recognize-authenticity':58, 'professional-restoration':58},
            'rogue-scientist': {'IQ':11, 'MA':9, 'native-language':96, 'math-basic':75,
                'math-advanced':75, 'astronomy-navigation':60, 'basic-electronics':50,
                'automobile':70, 'radio-basic':55, 'recycle':50, 'salvage':55, 'scientific-authenticity':57}}
        with tempfile.TemporaryDirectory() as directory:
            app=CharacterApplication(directory,die=lambda sides:3)
            for identity,expected in cases.items():
                with self.subTest(identity=identity):
                    hero=app.create(character_class=identity)
                    rows={row['id']:row for row in app.skill_view(hero['id'])['grants']}
                    for identifier,value in expected.items():
                        actual=hero['attributes'][identifier]['value'] if identifier in ('IQ','MA') else rows[identifier]['percentage']
                        self.assertEqual(actual,value,identifier)
                    self.assertNotIn('eyeball',rows)
                    self.assertNotIn('cartography',rows)
                    self.assertEqual(app.combat_view(hero['id'])['choices']['hand_to_hand'],'none')
                    self.assertEqual(app.combat_view(hero['id'])['totals']['attacks']['value'],1)

    def test_language_literacy_choices_reopen_and_keep_native_specialties_distinct(self):
        with tempfile.TemporaryDirectory() as directory:
            app=CharacterApplication(directory,die=lambda sides:3)
            for identity,spoken,literate in [('rogue-scholar',75,60),('rogue-scientist',70,65)]:
                hero=app.create(character_class=identity)
                choices={'native_language':'English','other_languages':['Spanish','French'],
                         'literacies':['Spanish','German','Latin']}
                if identity=='rogue-scientist':
                    choices['other_languages']=['Spanish','French','German'];choices['literacies']=['English','Spanish']
                else:
                    choices['pilot']='hover-craft'
                hero=app.select_required_skills(hero['id'],revision=hero['revision'],choices=choices)
                view=app.skill_view(hero['id'])
                self.assertEqual({row['percentage'] for row in view['grants'] if row['id']=='other-language'},{spoken})
                self.assertEqual({row['percentage'] for row in view['grants'] if row['id']=='literacy-other'},{literate})
                self.assertEqual(CharacterApplication(directory).get(hero['id']),hero)
                imported=app.import_character(app.export_character(hero['id']))
                self.assertEqual(imported['required_skill_choices'],hero['required_skill_choices'])

    def test_normal_ability_bonuses_and_category_minima_use_actual_optional_training(self):
        with tempfile.TemporaryDirectory() as directory:
            app=CharacterApplication(directory,die=lambda sides:3)
            scholar=app.create(character_class='rogue-scholar')
            scholar=app.select_skills(scholar['id'],revision=scholar['revision'],selections=[
                {'skill_id':identifier,'pool':'related'} for identifier in ['art','calligraphy','photography','computer-hacking','research']])
            view=app.skill_view(scholar['id']);rows={r['id']:r for r in view['selected']}
            self.assertEqual(rows['art']['percentage'],60)  # 35+Technical15+Restoration10
            self.assertEqual(rows['computer-hacking']['percentage'],30)  # 20+10
            self.assertEqual(view['pool_requirements'][0]['remaining'],1)  # automatic Research does not fill it
            scientist=app.create(character_class='rogue-scientist')
            ids=['anthropology','chemistry-analytical','cryptography','jury-rig','brewing-basic','brewing-medicinal',
                 'math-basic','biology','first-aid','holistic-medicine','art']
            scientist=app.select_skills(scientist['id'],revision=scientist['revision'],selections=[
                {'skill_id':identifier,'pool':'related'} for identifier in ids])
            view=app.skill_view(scientist['id']);rows={r['id']:r for r in view['selected']}
            self.assertEqual(rows['anthropology']['percentage'],60)  # 30+Science20+Analyze10
            self.assertEqual(rows['jury-rig']['percentage'],70)  # 25+Technical15+Analyze10+Hypothesize20
            self.assertEqual(rows['cryptography']['percentage'],50)  # 25+Communications15+Analyze10
            minima={r['id']:r['remaining'] for r in view['pool_requirements']}
            self.assertEqual(minima,{'science':0,'medical':0,'technical':0})
            self.assertEqual(rows['math-basic']['percentage'],75)  # required30 is applied once

    def test_scholar_military_submersibles_remain_ineligible_honor_guidance(self):
        with tempfile.TemporaryDirectory() as directory:
            app=CharacterApplication(directory,die=lambda sides:3)
            hero=app.create(character_class='rogue-scholar')
            hero=app.select_skills(hero['id'],revision=hero['revision'],selections=[
                {'skill_id':'submersible','pool':'related'}])
            view=app.skill_view(hero['id']);row=view['selected'][0]
            self.assertTrue(any('Submersibles' in warning for warning in view['warnings']))
            self.assertEqual(row['contributions']['class'],0)

    def test_fixed_training_does_not_create_an_extra_repeat_slot(self):
        installed=RuleArchive.load();skills=installed.active('rifts-domestic-skills')
        skills['class_profiles']['rogue-scientist']['combat']['fixed_proficiencies']=deepcopy(
            skills['class_profiles']['wilderness-scout']['combat']['fixed_proficiencies'])
        archive=RuleArchive([skills if (p['id'],p['version'])==(skills['id'],skills['version']) else p
            for p in installed.definitions()],installed.active_versions())
        with tempfile.TemporaryDirectory() as directory:
            app=CharacterApplication(directory,rule_archive=archive,die=lambda sides:3)
            hero=app.create(character_class='rogue-scientist')
            hero=app.select_combat(hero['id'],revision=hero['revision'],choices={
                'ancient':['knife','sword'],'modern':['energy-pistol']})
            weapons=[g for g in app.equipment_view(hero['id'])['starting_groups']['groups']
                if g['id'].startswith('elective-weapon-')]
            self.assertEqual(len(weapons),2)
            self.assertTrue(weapons[0]['option_requirements']['vibro-saber'][0]['satisfied'])
            with self.assertRaises(ValueError):
                app.grant_starting_group(hero['id'],revision=hero['revision'],group_id='elective-weapon-3',selection='wilks-320')

    def test_optional_handguns_receive_a_matching_source_weapon_without_extra_clips(self):
        with tempfile.TemporaryDirectory() as directory:
            app=CharacterApplication(directory,die=lambda sides:3)
            hero=app.create(character_class='rogue-scientist')
            hero=app.select_combat(hero['id'],revision=hero['revision'],choices={
                'modern':['energy-pistol','handguns']})
            hero=app.grant_starting_group(hero['id'],revision=hero['revision'],group_id='elective-weapon-2',selection='magnum-revolver')
            group=next(g for g in app.equipment_view(hero['id'])['starting_groups']['groups']
                if g['id']=='elective-weapon-2')
            self.assertTrue(group['option_requirements']['magnum-revolver'][0]['satisfied'])
            self.assertEqual(hero['equipment']['items'][0]['shots'],6)
            self.assertEqual(len(hero['equipment']['items']),1)
            self.assertEqual(app.combat_view(hero['id'])['related_cost'],1)
            self.assertEqual(app.import_character(app.export_character(hero['id']))['starting_equipment_groups'],hero['starting_equipment_groups'])

    def test_paid_hand_training_and_additional_distinct_weapons_use_related_allowance(self):
        with tempfile.TemporaryDirectory() as directory:
            app=CharacterApplication(directory,die=lambda sides:3)
            for identity,total,ancient,martial_cost in [('rogue-scholar',11,['sword'],4),('rogue-scientist',15,[],3)]:
                hero=app.create(character_class=identity)
                hero=app.select_combat(hero['id'],revision=hero['revision'],choices={'hand_to_hand':'martial-arts',
                    'ancient':ancient,'modern':['energy-pistol','energy-rifle','energy-rifle']})
                view=app.combat_view(hero['id'])
                self.assertEqual(view['related_cost'],martial_cost+1)
                self.assertEqual(app.skill_view(hero['id'])['remaining']['related'],total-martial_cost-1)
                hero=app.select_combat(hero['id'],revision=hero['revision'],choices={'ancient':['sword','knife'],'modern':['energy-rifle']})
                self.assertEqual(app.combat_view(hero['id'])['related_cost'],1 if identity=='rogue-scholar' else 2)

    def test_two_skill_awards_source_xp_and_learning_dates_survive_advancement_undo(self):
        with tempfile.TemporaryDirectory() as directory:
            app=CharacterApplication(directory,die=lambda sides:3)
            for identity,total,secondary,private in [('rogue-scholar',11,3,'recognize-authenticity'),
                    ('rogue-scientist',15,4,'scientific-authenticity')]:
                hero=app.create(character_class=identity,level=3)
                view=app.skill_view(hero['id'])
                self.assertEqual(view['remaining']['related'],total+2)
                self.assertEqual(view['remaining']['secondary'],secondary+1)
                self.assertEqual(hero['experience'],4001)
                before=deepcopy(hero)
                hero=app.select_skills(hero['id'],revision=hero['revision'],selections=[{'skill_id':'art','pool':'related'}])
                first=next(r['percentage'] for r in app.skill_view(hero['id'])['selected'] if r['id']=='art')
                hero=app.advance(hero['id'],revision=hero['revision'],method='level',value=6)
                self.assertEqual(app.skill_view(hero['id'])['remaining']['related'],total+4-1)
                self.assertEqual(next(r['percentage'] for r in app.skill_view(hero['id'])['selected'] if r['id']=='art'),first+15)
                hero=app.undo_advancement(hero['id'],revision=hero['revision'])['character']
                self.assertEqual(hero['level'],5)
                self.assertEqual(app.skill_view(hero['id'])['remaining']['related'],total+2-1)
                self.assertEqual(hero['resources'],before['resources'])

    def test_original_funds_fixed_kit_matching_equipment_and_optional_jars_replay(self):
        with tempfile.TemporaryDirectory() as directory:
            app=CharacterApplication(directory,die=lambda sides:3)
            for identity,credits,ancient,weapon in [('rogue-scholar',600,['sword'],'vibro-saber'),
                    ('rogue-scientist',3000,[],'wilks-320')]:
                hero=app.create(character_class=identity)
                hero=app.generate_starting_funds(hero['id'],revision=hero['revision'])
                self.assertEqual(hero['equipment']['credits'],credits)
                self.assertEqual(hero['starting_funds']['saleable_goods']['value'],9000)
                hero=app.grant_starting_gear(hero['id'],revision=hero['revision'])
                hero=app.select_combat(hero['id'],revision=hero['revision'],choices={'ancient':ancient,'modern':['energy-pistol']})
                hero=app.grant_starting_group(hero['id'],revision=hero['revision'],group_id='elective-weapon-1',selection=weapon)
                if identity=='rogue-scholar':
                    hero=app.select_required_skills(hero['id'],revision=hero['revision'],choices={'pilot':'hover-craft'})
                    hero=app.grant_starting_group(hero['id'],revision=hero['revision'],group_id='transport',selection='rogue-scholar-hover-truck')
                else:
                    self.assertEqual(len(hero['starting_equipment_groups']['elective-weapon-1']['grants']),1)
                    hero=app.grant_starting_group(hero['id'],revision=hero['revision'],group_id='specimen-kit',selection='rogue-scientist-specimen-kit')
                    self.assertEqual(hero['starting_equipment_groups']['specimen-kit']['grants'][1]['quantity'],3)
                receipt=deepcopy(hero['starting_equipment_groups'])
                imported=app.import_character(app.export_character(hero['id']))
                self.assertEqual(imported['starting_equipment_groups'],receipt)
                fields=PdfReader(BytesIO(app.export_pdf(hero['id']))).get_fields()
                assert fields is not None
                text=' '.join(str(row.get('/V','')) for row in fields.values())
                self.assertIn('Training matched:',text)
                self.assertIn('No Hand to Hand Combat Skill',text)
                self.assertIn('O.C.C. guidance:',text)
                self.assertIn('Find Contraband+20',text)

    def test_malformed_unselected_awards_and_proficiency_allowances_reject_before_dice(self):
        for field in ('related_per_award','proficiency_counts','additional_proficiency_cost','required_proficiencies'):
            installed=RuleArchive.load();pack=installed.active('rifts-domestic-skills')
            owner=pack['class_profiles']['rogue-scientist']
            if field=='related_per_award': owner['higher_advancement'][field]=True
            elif field=='proficiency_counts': owner['combat'][field]['ancient']=-1
            elif field=='required_proficiencies': owner['combat'][field]['modern']=['unreviewed-weapon']
            else: owner['combat'][field]=True
            archive=RuleArchive([pack if (r['id'],r['version'])==(pack['id'],pack['version']) else r
                for r in installed.definitions()],installed.active_versions())
            with tempfile.TemporaryDirectory() as directory:
                app=CharacterApplication(directory,rule_archive=archive,die=lambda sides:self.fail('No preflight draws'))
                with self.assertRaises(ValueError): app.create(character_class='vagabond')
                self.assertEqual(app.list(),[])

    def test_every_distinct_proficiency_gets_equipment_and_old_slots_survive_removal(self):
        with tempfile.TemporaryDirectory() as directory:
            app=CharacterApplication(directory,die=lambda sides:3)
            hero=app.create(character_class='rogue-scientist')
            hero=app.select_combat(hero['id'],revision=hero['revision'],choices={
                'ancient':['sword','knife','knife'],'modern':['energy-pistol','energy-rifle']})
            groups=app.equipment_view(hero['id'])['starting_groups']['groups']
            weapons=[r for r in groups if r['id'].startswith('elective-weapon-')]
            self.assertEqual(len(weapons),4)
            hero=app.grant_starting_group(hero['id'],revision=hero['revision'],group_id='spare-clips',selection='standard-e-clip')
            clips=[row for row in hero['equipment']['items'] if row['item_id']=='standard-e-clip']
            self.assertEqual(sum(row['quantity'] for row in clips),2)
            self.assertEqual(app.combat_view(hero['id'])['remaining'],{'ancient':0,'modern':0})
            hero=app.grant_starting_group(hero['id'],revision=hero['revision'],group_id='elective-weapon-4',selection='wilks-447')
            receipt=deepcopy(hero['starting_equipment_groups'])
            hero=app.select_combat(hero['id'],revision=hero['revision'],choices={'ancient':[],'modern':['energy-pistol']})
            app.die=lambda sides:self.fail('Retained slots must not reroll')
            imported=app.import_character(app.export_character(hero['id']))
            self.assertEqual(imported['starting_equipment_groups'],receipt)
            groups={r['id']:r for r in app.equipment_view(imported['id'])['starting_groups']['groups']}
            self.assertTrue(groups['elective-weapon-4']['generated'])
            self.assertFalse(groups['elective-weapon-4']['option_requirements']['wilks-447'][0]['satisfied'])

    def test_unselected_repeated_equipment_rule_rejects_before_dice(self):
        installed=RuleArchive.load();pack=installed.active('rifts-equipment')
        pack['class_profiles']['rogue-scientist']['starting_groups']['groups']['elective-weapon']['repeat_for_proficiencies']=True
        archive=RuleArchive([pack if (r['id'],r['version'])==(pack['id'],pack['version']) else r
            for r in installed.definitions()],installed.active_versions())
        with tempfile.TemporaryDirectory() as directory:
            app=CharacterApplication(directory,rule_archive=archive,die=lambda sides:self.fail('No invalid-rule draws'))
            with self.assertRaises(ValueError): app.create()
            self.assertEqual(app.list(),[])

    def test_future_repeat_slot_collision_rejects_unselected_owner_before_dice(self):
        installed=RuleArchive.load();pack=installed.active('rifts-equipment')
        groups=pack['class_profiles']['rogue-scientist']['starting_groups']['groups']
        groups['elective-weapon-3']=deepcopy(groups['armor'])
        archive=RuleArchive([pack if (r['id'],r['version'])==(pack['id'],pack['version']) else r
            for r in installed.definitions()],installed.active_versions())
        with tempfile.TemporaryDirectory() as directory:
            app=CharacterApplication(directory,rule_archive=archive,die=lambda sides:self.fail('No preflight draws'))
            with self.assertRaisesRegex(ValueError,'identities collide'): app.create(character_class='vagabond')
            self.assertEqual(app.list(),[])
