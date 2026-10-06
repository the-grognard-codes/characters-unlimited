"""Public source witnesses for Cyber-Doc creation and surgery training."""

from io import BytesIO
import tempfile
import unittest
from pypdf import PdfReader
from characters_unlimited.application import CharacterApplication
from characters_unlimited.rules import RuleArchive


class CyberDocTests(unittest.TestCase):
    def test_both_source_profiles_have_their_own_attributes_checks_and_resources(self):
        with tempfile.TemporaryDirectory() as directory:
            app=CharacterApplication(directory,die=lambda sides:3)
            for identity in ['cyber-doc','cyber-doc-city']:
                hero=app.create(character_class=identity)
                self.assertEqual({k:hero['attributes'][k]['value'] for k in ['IQ','ME','PP','PE']},
                    {'IQ':9,'ME':10,'PP':11,'PE':9})
                rows={r['id']:r for r in app.skill_view(hero['id'])['grants']}
                self.assertEqual(rows['medical-doctor']['percentage'],60)
                self.assertEqual([r['percentage'] for r in rows['medical-doctor']['additional_checks']],[50,15])
                self.assertEqual(rows['cybernetic-medicine']['percentage'],50)
                self.assertEqual(rows['cybernetic-medicine']['additional_checks'][0]['percentage'],70)
                self.assertEqual(rows['literacy-native']['percentage'],80)
                self.assertEqual(rows['recognize-bionic-quality']['percentage'],60)
                self.assertEqual(app.combat_view(hero['id'])['related_cost'],0)
                self.assertEqual(app.combat_view(hero['id'])['melee'][0]['strike']['value'],1)
                hero=app.generate_resources(hero['id'],revision=hero['revision'])
                self.assertEqual({k:v['value'] for k,v in app.resource_view(hero['id'])['resources'].items()},
                    {'SDC':18,'HP':12})
                saves=app.combat_view(hero['id'])['saving_bonuses']
                self.assertEqual(saves['pain']['value'],2)
                self.assertEqual(saves['horror_factor']['value'],4)

    def test_category_bonus_exceptions_do_not_raise_general_doctor_training(self):
        with tempfile.TemporaryDirectory() as directory:
            app=CharacterApplication(directory,die=lambda sides:3)
            hero=app.create(character_class='cyber-doc')
            hero=app.select_skills(hero['id'],revision=hero['revision'],selections=[
                {'skill_id':i,'pool':'related'} for i in ['medical-doctor','bioware-mechanics']])
            view=app.skill_view(hero['id'])
            selected={r['id']:r for r in view['selected']}
            required={r['id']:r for r in view['grants']}
            self.assertEqual(selected['medical-doctor']['percentage'],60)
            self.assertEqual(required['medical-doctor']['percentage'],60)
            self.assertEqual(selected['medical-doctor']['contributions']['class'],0)
            self.assertEqual(selected['bioware-mechanics']['percentage'],45)
            self.assertEqual(selected['bioware-mechanics']['contributions']['class'],15)

    def test_bionic_upgrade_needs_both_trainings_and_preserves_required_learning_age(self):
        with tempfile.TemporaryDirectory() as directory:
            app=CharacterApplication(directory,die=lambda sides:3)
            hero=app.create(character_class='cyber-doc')
            hero=app.generate_resources(hero['id'],revision=hero['revision'])
            hero=app.advance(hero['id'],revision=hero['revision'],method='level',value=3)
            upgrade={'skill_id':'cybernetic-medicine-bionic-upgrade','pool':'related'}
            electrical={'skill_id':'electrical-engineer','pool':'related'}
            for selections,name,percentage in [([upgrade],'Surgery',80),
                    ([upgrade,electrical],'Surgery: bionic upgrade',90),
                    ([upgrade,upgrade,electrical],'Surgery: bionic upgrade',90),
                    ([electrical],'Surgery',80),([upgrade,electrical],'Surgery: bionic upgrade',90)]:
                hero=app.select_skills(hero['id'],revision=hero['revision'],selections=selections)
                row=next(r for r in app.skill_view(hero['id'])['grants'] if r['id']=='cybernetic-medicine')
                self.assertEqual(row['percentage'],60)
                self.assertEqual([(r['name'],r['percentage']) for r in row['additional_checks']],[(name,percentage)])
                self.assertEqual(row['learned_level'],1)
            imported=app.import_character(app.export_character(hero['id']))
            self.assertEqual(imported['learning_levels'],hero['learning_levels'])
            self.assertEqual(CharacterApplication(directory).skill_view(hero['id']),app.skill_view(imported['id']))
            hero=app.undo_advancement(hero['id'],revision=hero['revision'])['character']
            self.assertEqual(hero['level'],2)

    def test_two_additional_technical_choices_exclude_required_and_duplicate_copies(self):
        with tempfile.TemporaryDirectory() as directory:
            app=CharacterApplication(directory,die=lambda sides:3)
            hero=app.create(character_class='cyber-doc')
            for ids,remaining in [(['computer-operation','computer-operation'],2),
                    (['computer-programming','computer-programming'],1),
                    (['computer-programming','research'],0)]:
                hero=app.select_skills(hero['id'],revision=hero['revision'],selections=[
                    {'skill_id':i,'pool':'related'} for i in ids])
                self.assertEqual(app.skill_view(hero['id'])['pool_requirements'][0]['remaining'],remaining)

    def test_source_lifestyles_medical_kit_and_weapon_receipts_round_trip(self):
        with tempfile.TemporaryDirectory() as directory:
            app=CharacterApplication(directory,die=lambda sides:3)
            for identity,credits in [('cyber-doc',1800),('cyber-doc-city',12000)]:
                hero=app.create(character_class=identity)
                hero=app.select_required_skills(hero['id'],revision=hero['revision'],choices={
                    'native_language':'English','other_languages':['Spanish']})
                hero=app.generate_starting_funds(hero['id'],revision=hero['revision'])
                self.assertEqual(hero['equipment']['credits'],credits)
                if identity=='cyber-doc':self.assertEqual(hero['starting_funds']['saleable_goods']['value'],6000)
                else:self.assertNotIn('saleable_goods',hero['starting_funds'])
                hero=app.grant_starting_gear(hero['id'],revision=hero['revision'])
                self.assertEqual(next(r['quantity'] for r in hero['equipment']['items'] if r['item_id']=='cyber-doc-scalpel'),6)
                self.assertEqual(len(hero['starting_gear']['grants']),12)
                hero=app.select_combat(hero['id'],revision=hero['revision'],choices={
                    'modern':['energy-pistol'],'ancient':[],'hand_to_hand':'expert'})
                self.assertEqual(app.combat_view(hero['id'])['related_cost'],3)
                groups={'armor':'urban-warrior','fixed-knife':'knife-large','medical-vibro-knife':'vibro-knife',
                    'body-fixer-irmss':'body-fixer-irmss','body-fixer-compu-drug':'body-fixer-compu-drug',
                    'elective-weapon-1':'wilks-320'}
                for group,item in groups.items():
                    hero=app.grant_starting_group(hero['id'],revision=hero['revision'],group_id=group,selection=item)
                self.assertEqual(sum(r['quantity'] for r in hero['equipment']['items'] if r['item_id']=='standard-e-clip'),4)
                self.assertFalse(any(r['item_id'] in ['city-rat-rmk','body-fixer-laser-scalpel','body-fixer-jeep'] for r in hero['equipment']['items']))
                imported=app.import_character(app.export_character(hero['id']))
                self.assertEqual(imported['starting_equipment_groups'],hero['starting_equipment_groups'])
                self.assertEqual(imported['equipment'],hero['equipment'])
                fields=PdfReader(BytesIO(app.export_pdf(hero['id']))).get_fields()
                assert fields is not None
                text=' '.join(str(r.get('/V','')) for r in fields.values())
                self.assertIn('Cybernetic Medicine',text)
                self.assertIn('Surgery',text)
                self.assertIn('6',text)

    def test_malformed_unselected_bonus_exceptions_and_check_conditions_fail_before_dice(self):
        for fault in ['boolean-bonus','wrong-category','unknown-condition','empty-condition']:
            installed=RuleArchive.load();pack=installed.active('rifts-domestic-skills')
            if fault in ['boolean-bonus','wrong-category']:
                pack['class_profiles']['cyber-doc-city']['selection_rules']['related']['medical']['bonuses']={
                    'medical-doctor':True} if fault=='boolean-bonus' else {'body-building':10}
            else:
                row=next(r for r in pack['skills'] if r['id']=='cybernetic-medicine')
                row['additional_checks'][1]['requires_skills']=['missing'] if fault=='unknown-condition' else []
            archive=RuleArchive([pack if r['id']==pack['id'] and r['version']==pack['version'] else r
                for r in installed.definitions()],installed.active_versions())
            with tempfile.TemporaryDirectory() as directory:
                app=CharacterApplication(directory,rule_archive=archive,die=lambda sides:self.fail('Preflight must reject before drawing'))
                with self.assertRaises(ValueError):app.create()

    def test_previous_body_fixer_pins_keep_their_actual_old_views(self):
        installed=RuleArchive.load();active=installed.active_versions()
        active.update({'rifts-core':'1.5.0','rifts-domestic-skills':'2.26.0','rifts-equipment':'1.13.0'})
        with tempfile.TemporaryDirectory() as directory:
            old=CharacterApplication(directory,rule_archive=RuleArchive(installed.definitions(),active),die=lambda sides:3)
            hero=old.create(character_class='body-fixer')
            view=old.skill_view(hero['id'])
            current=CharacterApplication(directory)
            self.assertEqual(current.skill_view(hero['id']),view)
            imported=current.import_character(old.export_character(hero['id']))
            self.assertEqual(imported['additional_rule_packs'],hero['additional_rule_packs'])
            self.assertEqual(current.skill_view(imported['id']),view)
