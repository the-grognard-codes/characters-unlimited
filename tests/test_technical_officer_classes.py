"""Independent Human Technical Officer source witnesses, RUE printed236–237/295."""
import tempfile
import unittest

from characters_unlimited.application import CharacterApplication
from characters_unlimited.advancement import learning_key
from characters_unlimited.rules import RuleArchive


class TechnicalOfficerTests(unittest.TestCase):
    archive = staticmethod(RuleArchive.load)
    paths = ('communications','electrician','mechanic','robotics','technician','medic')

    def app(self, directory):
        return CharacterApplication(directory,die=lambda sides:3,rule_archive=self.archive())

    def no_roll(self, sides):
        self.fail('Recorded training, fixed pay, equipment and import must not roll')

    def test_source_common_mos_totals_and_resources(self):
        archive = self.archive()
        # Weapons followed the six-path acceptance; keep that historical boundary.
        unfinished = 'coalition-technical-officer-weapons'
        core = archive.resolve('rifts-core','1.11.0')
        self.assertNotIn(unfinished,{row['id'] for row in core['classes']})
        self.assertFalse(any(unfinished in row['classes'] for row in core['creation_profiles']))
        for pack,version in (('rifts-domestic-skills','2.32.0'),('rifts-equipment','1.19.0')):
            self.assertNotIn(unfinished,archive.resolve(pack,version)['class_profiles'])
        expected = {
            'communications':{'radio-basic':70,'basic-electronics':40,'cryptography':35,'tv-video':35},
            'electrician':{'computer-operation':60,'math-advanced':55,'electrical-engineer':50},
            'mechanic':{'computer-operation':55,'automotive-mechanics':55,'locksmith':40,'basic-mechanics':50},
            'robotics':{'robots-power-armor':71,'robot-electronics':50,'robot-mechanics':35,'vehicle-armorer':35},
            'technician':{'general-repair':50,'research':50,'sensory-equipment':45},
            'medic':{'biology':45,'field-surgery':45,'medical-doctor':65,'paramedic':55},
        }
        with tempfile.TemporaryDirectory() as directory:
            app = self.app(directory)
            for path, values in expected.items():
                with self.subTest(path=path):
                    hero = app.create(character_class='coalition-technical-officer-'+path)
                    rows = {row['id']:row for row in app.skill_view(hero['id'])['grants']}
                    self.assertEqual({key:rows[key]['percentage'] for key in values},values)
                    self.assertEqual([rows[key]['percentage'] for key in
                        ('native-language','literacy-native','math-basic','military-etiquette')],[98,60,75,55])
                    hero = app.generate_resources(hero['id'],revision=hero['revision'])
                    resources = app.resource_view(hero['id'])['resources']
                    self.assertEqual((resources['SDC']['value'],resources['HP']['value']),(21,13))
                    self.assertNotIn('robot-combat-basic',rows)

    def test_initial_specialties_and_fixed_overlap_do_not_certify_missing_choices(self):
        with tempfile.TemporaryDirectory() as directory:
            app = self.app(directory)
            hero = app.create(character_class='coalition-technical-officer-communications',level=3)
            app.die = self.no_roll
            for choice in ({'skill_id':'language-other','pool':'mos','specialty':''},
                           {'skill_id':'radio-basic','pool':'mos'}):
                hero = app.select_skills(hero['id'],revision=hero['revision'],selections=[choice])
                self.assertEqual(app.skill_view(hero['id'])['pool_requirements'][0]['remaining'],1)
            choices = [{'skill_id':'language-other','pool':'mos','specialty':'Spanish'},
                       {'skill_id':'language-other','pool':'related','specialty':'French'}]
            hero = app.select_skills(hero['id'],revision=hero['revision'],selections=choices)
            view = app.skill_view(hero['id'])
            self.assertEqual([row['percentage'] for row in view['selected']],[66,55])
            self.assertEqual(view['pool_requirements'][0]['remaining'],0)
            self.assertEqual([hero['learning_levels'][learning_key('skill','language-other',name)]
                              for name in ('Spanish','French')],[1,3])
            levels = hero['learning_levels']
            hero = app.select_skills(hero['id'],revision=hero['revision'],selections=[])
            hero = app.select_skills(hero['id'],revision=hero['revision'],selections=choices,learned_level=3)
            self.assertEqual(hero['learning_levels'],levels)
            imported = app.import_character(app.export_character(hero['id']))
            self.assertEqual(app.skill_view(imported['id'])['selected'],app.skill_view(hero['id'])['selected'])
            self.assertEqual(self.app(directory).get(hero['id']),hero)

    def test_technician_choices_credit_distinct_specialties_without_extra_grants(self):
        with tempfile.TemporaryDirectory() as directory:
            app = self.app(directory)
            hero = app.create(character_class='coalition-technical-officer-technician')
            choices = [{'skill_id':'history-pre','pool':'mos','specialty':name}
                       for name in ('North America','Europe')]
            choices.extend([{'skill_id':'chemistry','pool':'mos'},
                            {'skill_id':'photography','pool':'mos'},
                            {'skill_id':'botany','pool':'related'}])
            app.die = self.no_roll
            hero = app.select_skills(hero['id'],revision=hero['revision'],selections=choices)
            view = app.skill_view(hero['id'])
            self.assertEqual((view['remaining']['mos'],view['pool_requirements'][0]['remaining']),(0,0))
            self.assertFalse(view['pool_requirements'][0]['duplicates'])
            self.assertEqual(next(row['percentage'] for row in view['selected'] if row['id']=='photography'),50)
            self.assertEqual(next(row['percentage'] for row in view['selected'] if row['id']=='chemistry'),45)
            self.assertEqual(next(row['percentage'] for row in view['selected'] if row['id']=='botany'),25)
            self.assertEqual(view['remaining']['related'],2)

    def test_paid_expert_paramedic_and_additional_weapons_use_related_choices(self):
        with tempfile.TemporaryDirectory() as directory:
            app = self.app(directory)
            hero = app.create(character_class='coalition-technical-officer-medic')
            app.die = self.no_roll
            hero = app.select_combat(hero['id'],revision=hero['revision'],choices={
                'hand_to_hand':'expert','ancient':[],'modern':[]})
            self.assertEqual(app.skill_view(hero['id'])['remaining']['related'],2)
            hero = app.select_skills(hero['id'],revision=hero['revision'],selections=[
                {'skill_id':'paramedic','pool':'related'}])
            self.assertEqual(app.skill_view(hero['id'])['remaining']['related'],0)
            hero = app.select_combat(hero['id'],revision=hero['revision'],choices={
                'hand_to_hand':'expert','ancient':['knife'],'modern':['energy-pistol','energy-rifle']})
            self.assertEqual(app.skill_view(hero['id'])['remaining']['related'],-1)
            view = app.combat_view(hero['id'])
            self.assertEqual({row['id'] for row in view['catalog']['hand_to_hand']},{'basic','expert'})
            self.assertEqual(view['fixed_proficiencies']['modern'],['energy-pistol','energy-rifle'])

    def test_fixed_salary_all_issued_groups_and_elective_weapon_receipts_reopen(self):
        with tempfile.TemporaryDirectory() as directory:
            app = self.app(directory)
            hero = app.create(character_class='coalition-technical-officer-robotics')
            app.die = self.no_roll
            hero = app.generate_starting_funds(hero['id'],revision=hero['revision'])
            self.assertEqual(hero['equipment']['credits'],2000)
            self.assertEqual(hero['starting_funds']['credits']['rolls'],[])
            hero = app.grant_starting_gear(hero['id'],revision=hero['revision'])
            self.assertEqual(len(hero['starting_gear']['grants']),8)
            hero = app.select_combat(hero['id'],revision=hero['revision'],choices={
                'hand_to_hand':'basic','ancient':['knife','sword'],'modern':[]})
            for group, item in [('armor','cs-ca2'),('pistol','cs-c18'),('rifle','cs-c12'),
                ('grenades','cs-grenade-fragmentation'),('survival-knife','cs-survival-knife'),
                ('non-energy-weapon','magnum-revolver'),('pocket-computer','cs-technical-officer-pocket-computer'),
                ('mos-toolkit','cs-technical-officer-mos-toolkit'),('elective-weapon-1','vibro-knife'),
                ('elective-weapon-2','vibro-saber')]:
                hero = app.grant_starting_group(hero['id'],revision=hero['revision'],group_id=group,selection=item)
            inventory = {row['item_id']:row for row in hero['equipment']['items']}
            self.assertEqual(inventory['cs-pistol-e-clip']['quantity'],4)
            self.assertEqual(inventory['cs-rifle-e-clip']['quantity'],4)
            self.assertEqual(inventory['cs-grenade-fragmentation']['quantity'],2)
            self.assertFalse(any('samas' in key for key in inventory))
            original = hero['starting_equipment_groups']
            hero = app.select_combat(hero['id'],revision=hero['revision'],choices={
                'hand_to_hand':'basic','ancient':[],'modern':[]})
            self.assertEqual(hero['starting_equipment_groups'],original)
            imported = app.import_character(app.export_character(hero['id']))
            self.assertEqual(imported['starting_equipment_groups'],original)
            self.assertEqual(self.app(directory).get(hero['id']),hero)

    def test_source_xp_awards_through_fifteen_and_exact_undo(self):
        with tempfile.TemporaryDirectory() as directory:
            app = self.app(directory)
            hero = app.create(character_class='coalition-technical-officer-electrician')
            hero = app.generate_resources(hero['id'],revision=hero['revision'])
            hero = app.advance(hero['id'],revision=hero['revision'],method='level',value=15)
            self.assertEqual(hero['experience'],329961)
            self.assertEqual(app.skill_view(hero['id'])['remaining'],{'related':9,'secondary':6,'mos':1})
            app.die = self.no_roll
            hero = app.undo_advancement(hero['id'],revision=hero['revision'])['character']
            self.assertEqual((hero['level'],hero['experience']),(14,279961))
            self.assertEqual(app.skill_view(hero['id'])['remaining']['related'],8)
            self.assertEqual(app.import_character(app.export_character(hero['id']))['advancement'],hero['advancement'])
