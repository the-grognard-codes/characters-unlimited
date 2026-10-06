"""Original Operator source values through retained public character workflows."""

from io import BytesIO
import tempfile
import unittest
from pypdf import PdfReader
from characters_unlimited.application import CharacterApplication
from characters_unlimited.rules import RuleArchive


class OperatorTests(unittest.TestCase):
    def test_both_lifestyles_have_source_attributes_resources_and_saves(self):
        with tempfile.TemporaryDirectory() as directory:
            app=CharacterApplication(directory,die=lambda sides:3)
            for identity in ['operator','operator-city']:
                hero=app.create(character_class=identity)
                self.assertEqual({k:hero['attributes'][k]['value'] for k in ['IQ','ME','PS','PP','PE']},
                    {'IQ':10,'ME':9,'PS':11,'PP':10,'PE':9})
                rows={r['id']:r for r in app.skill_view(hero['id'])['grants']}
                self.assertEqual({k:rows[k]['percentage'] for k in ['native-language','math-basic','electrical-engineer',
                    'mechanical-engineer','weapons-engineer','recognize-machine-quality']},
                    {'native-language':92,'math-basic':65,'electrical-engineer':55,
                     'mechanical-engineer':45,'weapons-engineer':40,'recognize-machine-quality':58})
                self.assertNotIn('literacy-native',rows)
                self.assertNotIn('cybernetic-medicine',rows)
                hero=app.generate_resources(hero['id'],revision=hero['revision'])
                resources=app.resource_view(hero['id'])['resources']
                self.assertEqual(resources['SDC']['value'],30)
                self.assertEqual(resources['SDC']['contributions'],{'general-base':18,'operator':12})
                self.assertEqual(resources['HP']['value'],12)
                combat=app.combat_view(hero['id'])
                self.assertEqual(combat['saving_bonuses']['fatigue']['value'],2)
                self.assertEqual(combat['saving_bonuses']['disease']['value'],2)
                self.assertEqual(combat['related_cost'],0)

    def test_three_distinct_pilot_grants_keep_required_learning_age_after_revision(self):
        with tempfile.TemporaryDirectory() as directory:
            app=CharacterApplication(directory,die=lambda sides:3)
            hero=app.create(character_class='operator')
            hero=app.generate_resources(hero['id'],revision=hero['revision'])
            hero=app.advance(hero['id'],revision=hero['revision'],method='level',value=3)
            for choices,remaining in [(['automobile','automobile','airplane'],1),
                    (['automobile','airplane','hover-craft'],0)]:
                hero=app.select_required_skills(hero['id'],revision=hero['revision'],choices={
                    'native_language':'English','other_languages':['Spanish'],'pilot':choices})
                view=app.skill_view(hero['id'])
                self.assertEqual(view['required_remaining']['pilot'],remaining)
            rows={r['id']:r for r in view['grants']}
            self.assertEqual(rows['automobile']['percentage'],79)
            self.assertEqual(rows['automobile']['learned_level'],1)
            self.assertEqual(rows['airplane']['percentage'],73)
            self.assertEqual(rows['native-language']['percentage'],92)
            self.assertEqual(rows['recognize-machine-quality']['percentage'],64)
            self.assertEqual(rows['other-language']['percentage'],76)
            self.assertEqual(view['remaining'],{'related':10,'secondary':4})
            imported=app.import_character(app.export_character(hero['id']))
            self.assertEqual(CharacterApplication(directory).skill_view(imported['id']),view)

    def test_additional_mechanical_minimum_and_source_category_exceptions(self):
        with tempfile.TemporaryDirectory() as directory:
            app=CharacterApplication(directory,die=lambda sides:3)
            hero=app.create(character_class='operator')
            for ids,remaining in [(['mechanical-engineer','weapons-engineer'],2),
                    (['basic-mechanics','basic-mechanics'],1),(['basic-mechanics','automotive-mechanics'],0)]:
                hero=app.select_skills(hero['id'],revision=hero['revision'],selections=[
                    {'skill_id':i,'pool':'related'} for i in ids])
                self.assertEqual(app.skill_view(hero['id'])['pool_requirements'][0]['remaining'],remaining)
            hero=app.select_skills(hero['id'],revision=hero['revision'],selections=[
                {'skill_id':i,'pool':'related'} for i in ['scuba','field-armorer','military-fortification','computer-hacking']])
            rows={r['id']:r for r in app.skill_view(hero['id'])['selected']}
            self.assertEqual({k:rows[k]['contributions']['class'] for k in rows},
                {'scuba':10,'field-armorer':10,'military-fortification':10,'computer-hacking':15})

    def test_fixed_blunt_basic_and_paid_training_grow_without_backdating_new_choices(self):
        with tempfile.TemporaryDirectory() as directory:
            app=CharacterApplication(directory,die=lambda sides:3)
            hero=app.create(character_class='operator')
            for style,cost in [('basic',0),('expert',1),('martial-arts',2),('assassin',2)]:
                hero=app.select_combat(hero['id'],revision=hero['revision'],choices={
                    'hand_to_hand':style,'ancient':[],'modern':['energy-pistol']})
                self.assertEqual(app.combat_view(hero['id'])['related_cost'],cost)
            hero=app.generate_resources(hero['id'],revision=hero['revision'])
            hero=app.advance(hero['id'],revision=hero['revision'],method='level',value=3)
            combat=app.combat_view(hero['id'])
            blunt=next(row for row in combat['melee'] if row['id']=='blunt')
            self.assertEqual(blunt['strike']['contributions']['weapon_proficiency'],2)
            self.assertEqual(blunt['parry']['contributions']['weapon_proficiency'],2)
            self.assertEqual(blunt['thrown']['contributions']['weapon_proficiency'],0)
            self.assertEqual(hero['experience'],3801)
            hero=app.advance(hero['id'],revision=hero['revision'],method='level',value=4)
            self.assertEqual(app.skill_view(hero['id'])['remaining']['secondary'],5)
            hero=app.undo_advancement(hero['id'],revision=hero['revision'])['character']
            self.assertEqual(hero['level'],3)

    def test_source_funds_original_kit_glove_dice_and_two_vehicle_receipts(self):
        with tempfile.TemporaryDirectory() as directory:
            app=CharacterApplication(directory,die=lambda sides:3)
            for identity,credits in [('operator',1500),('operator-city',12000)]:
                hero=app.create(character_class=identity)
                hero=app.select_required_skills(hero['id'],revision=hero['revision'],choices={
                    'native_language':'English','other_languages':['Spanish'],'pilot':['automobile','hover-craft','airplane']})
                hero=app.generate_starting_funds(hero['id'],revision=hero['revision'])
                self.assertEqual(hero['equipment']['credits'],credits)
                self.assertEqual(hero['starting_funds']['credits']['rolls'],[3]*(4 if identity=='operator-city' else 5))
                if identity=='operator':self.assertEqual(hero['starting_funds']['saleable_goods']['value'],9000)
                else:self.assertNotIn('saleable_goods',hero['starting_funds'])
                hero=app.grant_starting_gear(hero['id'],revision=hero['revision'])
                self.assertEqual(len(hero['starting_gear']['grants']),23)
                hero=app.select_combat(hero['id'],revision=hero['revision'],choices={
                    'hand_to_hand':'basic','ancient':[],'modern':['energy-pistol']})
                for group,item in [('armor','operator-buddy-plastic-man'),('large-wrench','operator-large-wrench'),
                        ('hammer','operator-hammer'),('small-knives','operator-small-knife'),
                        ('rope','operator-rope'),('goggles-gloves','operator-goggles'),
                        ('transport-1','operator-jeep'),('transport-2','operator-hover-truck'),('elective-weapon-1','wilks-320')]:
                    hero=app.grant_starting_group(hero['id'],revision=hero['revision'],group_id=group,selection=item)
                gloves=hero['starting_equipment_groups']['goggles-gloves']['grants'][1]
                self.assertEqual((gloves['quantity'],gloves['rolls']),(3,[3]))
                self.assertEqual(len(hero['starting_equipment_groups']),9)
                self.assertFalse(any(r['item_id']=='standard-e-clip' for r in hero['equipment']['items']))
                equipment=app.equipment_view(hero['id'])
                self.assertEqual(next(r for r in equipment['items'] if r['item_id']=='operator-rope')['weight_lbs'],10)
                imported=app.import_character(app.export_character(hero['id']))
                self.assertEqual(imported['starting_equipment_groups'],hero['starting_equipment_groups'])
                self.assertEqual(imported['equipment'],hero['equipment'])
                fields=PdfReader(BytesIO(app.export_pdf(hero['id']))).get_fields()
                assert fields is not None
                text=' '.join(str(r.get('/V','')) for r in fields.values())
                self.assertIn('Recognize Machine Quality',text)
                self.assertIn('doctor glove',text.lower())
                self.assertIn('Save vs fatigue: +2',text)

    def test_buddy_armor_and_blunt_tools_keep_exact_values_without_enhancing_purchases(self):
        with tempfile.TemporaryDirectory() as directory:
            app=CharacterApplication(directory,die=lambda sides:3)
            hero=app.create(character_class='operator')
            for group,item in [('armor','operator-buddy-plastic-man'),('large-wrench','operator-large-wrench'),('hammer','operator-hammer')]:
                hero=app.grant_starting_group(hero['id'],revision=hero['revision'],group_id=group,selection=item)
            inventory=hero['equipment']
            for possession in inventory['items']:possession['equipped']=True
            hero=app.set_equipment(hero['id'],revision=hero['revision'],inventory=inventory)
            view=app.equipment_view(hero['id'])
            self.assertEqual(view['armor'][0]['locations'],{'main_body':38.5,'helmet':33,'left_arm':16.5,
                'right_arm':16.5,'left_leg':24.2,'right_leg':24.2})
            self.assertEqual([r['base_damage'] for r in view['melee_attacks']],['2D6 S.D.C.','2D6 S.D.C.'])
            for attack in view['melee_attacks']:
                self.assertEqual(attack['strike']['contributions']['weapon_proficiency'],1)
                self.assertNotIn('knife',attack['guidance'].lower())
            hero=app.purchase_equipment(hero['id'],revision=hero['revision'],item_id='plastic-man')
            ordinary=next(r for r in app.equipment_view(hero['id'])['items'] if r['item_id']=='plastic-man')
            self.assertEqual(ordinary['locations']['main_body'],35)
            imported=app.import_character(app.export_character(hero['id']))
            self.assertEqual(app.equipment_view(imported['id'])['armor'],view['armor'])

    def test_unselected_bad_glove_formula_rejects_before_dice_and_receipts_reject_tampering(self):
        installed=RuleArchive.load();pack=installed.active('rifts-equipment')
        pack['class_profiles']['operator-city']['starting_groups']['groups']['goggles-gloves']['additional_grants']['operator-goggles'][0]['quantity_formula']['sides']=True
        archive=RuleArchive([pack if r['id']==pack['id'] and r['version']==pack['version'] else r
            for r in installed.definitions()],installed.active_versions())
        with tempfile.TemporaryDirectory() as directory:
            app=CharacterApplication(directory,rule_archive=archive,die=lambda n:self.fail('Preflight must reject before dice'))
            with self.assertRaises(ValueError):app.create()
        with tempfile.TemporaryDirectory() as directory:
            app=CharacterApplication(directory,die=lambda n:3)
            hero=app.create(character_class='operator')
            hero=app.grant_starting_group(hero['id'],revision=hero['revision'],group_id='goggles-gloves',selection='operator-goggles')
            portable=app.export_character(hero['id'])
            portable['character']['starting_equipment_groups']['goggles-gloves']['grants'][1]['quantity']=4
            with self.assertRaises(ValueError):app.import_character(portable)
            self.assertEqual(app.get(hero['id']),hero)

    def test_previous_cyber_doc_pins_preserve_training_and_exact_portable_state(self):
        installed=RuleArchive.load();active=installed.active_versions()
        active.update({'rifts-core':'1.6.0','rifts-domestic-skills':'2.27.0','rifts-equipment':'1.14.0'})
        with tempfile.TemporaryDirectory() as directory:
            old=CharacterApplication(directory,rule_archive=RuleArchive(installed.definitions(),active),die=lambda n:3)
            hero=old.create(character_class='cyber-doc')
            view=old.skill_view(hero['id'])
            current=CharacterApplication(directory)
            self.assertEqual(current.skill_view(hero['id']),view)
            imported=current.import_character(old.export_character(hero['id']))
            self.assertEqual(imported['additional_rule_packs'],hero['additional_rule_packs'])
            self.assertEqual(current.skill_view(imported['id']),view)
            fields=PdfReader(BytesIO(current.export_pdf(imported['id']))).get_fields()
            assert fields is not None
            self.assertIn('Save vs pain: +2',' '.join(str(r.get('/V','')) for r in fields.values()))
