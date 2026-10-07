"""Independent Human Merc Soldier witnesses, original RUE82–83/295."""
from copy import deepcopy
import tempfile
import unittest
from characters_unlimited.application import CharacterApplication
from characters_unlimited.rules import RuleArchive
from characters_unlimited.skill_choices import selection_policy


class MercSoldierTests(unittest.TestCase):
    archive = staticmethod(RuleArchive.load)
    paths = ('communications','eod','grunt','scout','heavy-weapons-wp',
             'heavy-weapons-demolitions','transportation','medic')

    def app(self,directory):
        return CharacterApplication(directory,die=lambda sides:3,rule_archive=self.archive())

    def no_roll(self,sides):
        self.fail('Retained source training, equipment and portable replay must not roll')

    def choices(self,path):
        result = [{'skill_id':'language-other','pool':'common-language','specialty':'Spanish'}]
        optional = {
            'communications':[('optic-systems','mos',''),('language-other','mos','French'),('tv-video','mos','')],
            'grunt':[('swimming','mos',''),('automobile','mos','')],
            'heavy-weapons-demolitions':[('demolitions','mos',''),('demolitions-disposal','mos','')],
            'transportation':[('automobile','vehicle-pairs',''),('hover-craft','vehicle-pairs',''),
                ('combat-driving','mechanics-driving',''),('airplane','extra-pilot','')],
            'medic':[('chemistry','mos',''),('brewing-medicinal','mos','')],
        }
        result += [{'skill_id':key,'pool':pool,'specialty':specialty}
                   for key,pool,specialty in optional.get(path,[])]
        return result

    def combat(self,path):
        return {'hand_to_hand':'basic',
                'ancient':['sword'] if path in ('grunt','heavy-weapons-wp') else [],
                'modern':['shotgun'] if path in ('grunt','heavy-weapons-wp') else []}

    def test_source_common_mos_percentages_fixed_physical_and_minimum_guidance(self):
        expected = {
            'communications':{'computer-operation':60,'radio-basic':65,'electronic-countermeasures':45,'sensory-equipment':50},
            'eod':{'basic-electronics':50,'basic-mechanics':45,'demolitions':75,'demolitions-disposal':80,'demolitions-underwater':66,'trap-mine-detection':30},
            'grunt':{'land-navigation':41},
            'scout':{'detect-ambush':45,'detect-concealment':35,'intelligence':47,'land-navigation':50,'prowl':35,'tailing':50,'wilderness-survival':40},
            'heavy-weapons-wp':{'recognize-weapon-quality':45,'weapon-systems':50},
            'heavy-weapons-demolitions':{'recognize-weapon-quality':45,'weapon-systems':50},
            'transportation':{'navigation':50,'tanks-apcs':46,'truck':50},
            'medic':{'biology':45,'field-surgery':45,'medical-doctor':65,'sewing':50},
        }
        for path,percentages in expected.items():
            with self.subTest(path=path),tempfile.TemporaryDirectory() as directory:
                app = self.app(directory)
                hero = app.create(character_class='merc-soldier-'+path)
                grants = {row['id']:row for row in app.skill_view(hero['id'])['grants']}
                self.assertEqual({key:grants[key]['percentage'] for key in percentages},percentages)
                self.assertEqual([grants[key]['percentage'] for key in
                    ('native-language','climbing','math-basic','military-etiquette','sign-language')],[95,50,50,45,30])
                self.assertEqual(grants['sign-language']['specialty'],'Military')
                hero = app.generate_resources(hero['id'],revision=hero['revision'])
                resources = app.resource_view(hero['id'])['resources']
                self.assertEqual((resources['SDC']['value'],resources['HP']['value']),
                                 (30,15) if path == 'grunt' else (24,13))
                if path == 'scout':
                    self.assertNotIn('electronic-countermeasures',grants)
                    self.assertNotIn('basic-electronics',grants)

    def test_initial_pool_bonus_separation_and_exclusive_heavy_alternatives(self):
        for path in self.paths:
            with self.subTest(path=path),tempfile.TemporaryDirectory() as directory:
                app = self.app(directory)
                hero = app.create(character_class='merc-soldier-'+path)
                selections = self.choices(path)
                selections += [{'skill_id':key,'pool':'related','specialty':''}
                               for key in ('cook','gardening','housekeeping','dance')]
                selections += [{'skill_id':key,'pool':'secondary','specialty':''} for key in ('fishing','photography')]
                hero = app.select_skills(hero['id'],revision=hero['revision'],selections=selections)
                hero = app.select_combat(hero['id'],revision=hero['revision'],choices=self.combat(path))
                view = app.skill_view(hero['id'])
                self.assertTrue(all(count == 0 for count in view['remaining'].values()),view['remaining'])
                self.assertTrue(all(row['remaining'] == 0 for row in view['pool_requirements']))
                self.assertEqual(view['warnings'],[])
                self.assertEqual(app.combat_view(hero['id'])['related_cost'],0)
                selected = {(row['id'],row.get('specialty','')):row for row in view['selected']}
                self.assertEqual(selected['language-other','Spanish']['percentage'],60)
                if path == 'communications':
                    self.assertEqual(selected['language-other','French']['percentage'],65)
                    self.assertEqual(selected['optic-systems','']['percentage'],44)
                    self.assertEqual(selected['tv-video','']['percentage'],40)
                if path == 'transportation':
                    self.assertEqual([selected[key,'']['percentage'] for key in ('automobile','hover-craft','airplane')],[80,65,60])
                    self.assertIsNone(selected['combat-driving',''].get('percentage'))
                if path == 'medic':
                    self.assertEqual(selected['brewing-medicinal','']['percentage'],30)
                if path == 'heavy-weapons-demolitions':
                    self.assertEqual([selected[key,'']['percentage'] for key in ('demolitions','demolitions-disposal')],[65,65])
                    self.assertEqual(hero['combat_choices']['modern'],[])

    def test_source_issue_recorded_random_clips_armor_funds_and_exact_portability(self):
        for path in ('communications','eod','grunt','heavy-weapons-wp','heavy-weapons-demolitions','transportation'):
            with self.subTest(path=path),tempfile.TemporaryDirectory() as directory,tempfile.TemporaryDirectory() as copied:
                app = self.app(directory)
                hero = app.create(character_class='merc-soldier-'+path)
                hero = app.generate_resources(hero['id'],revision=hero['revision'])
                hero = app.select_skills(hero['id'],revision=hero['revision'],selections=self.choices(path))
                hero = app.select_combat(hero['id'],revision=hero['revision'],choices=self.combat(path))
                hero = app.generate_starting_funds(hero['id'],revision=hero['revision'])
                hero = app.grant_starting_gear(hero['id'],revision=hero['revision'])
                groups = app.equipment_view(hero['id'])['starting_groups']['groups']
                for group in groups:
                    if group['id'] == 'dress-uniform':
                        continue  # This witness is not part of a large company/army.
                    selected = ('vibro-saber' if group['id'] == 'elective-weapon-1' else
                                'wi-gl8-shotgun' if group['id'] == 'elective-weapon-2' else group['options'][0])
                    hero = app.grant_starting_group(hero['id'],revision=hero['revision'],
                                                    group_id=group['id'],selection=selected)
                app.die = self.no_roll
                inventory = {row['item_id']:row for row in hero['equipment']['items']}
                self.assertEqual(hero['equipment']['credits'],600)
                self.assertEqual([inventory[key]['quantity'] for key in
                    ('merc-canteen','merc-smoke-grenade','merc-signal-flare')],[2,2,3])
                self.assertNotIn('merc-dress-uniform',inventory)
                self.assertFalse(any('motorcycle' in key or 'glitter-boy' in key for key in inventory))
                equipment = app.equipment_view(hero['id'])
                catalog = {row['id']:row for row in equipment['catalog']}
                ammunition = [row for key,row in inventory.items() if catalog[key]['category'] == 'ammunition']
                self.assertGreaterEqual(len(ammunition),2)
                self.assertTrue(all(row['quantity'] == 6 for row in ammunition))
                self.assertTrue(all(row['shots'] == catalog[row['item_id']]['capacity'] for row in ammunition))
                armor = catalog['gladiator']
                self.assertEqual((armor['weight_lbs'],armor['cost_credits'],armor['movement_penalty']),(21,38000,-10))
                self.assertEqual([armor['locations'][key] for key in ('main_body','helmet','left_arm','left_leg')],[70,45,25,45])
                edit = deepcopy(hero['equipment'])
                next(row for row in edit['items'] if row['item_id'] == 'gladiator')['equipped'] = True
                hero = app.set_equipment(hero['id'],revision=hero['revision'],inventory=edit)
                self.assertTrue(any(row['item_id'] == 'gladiator' for row in app.equipment_view(hero['id'])['armor']))
                other = CharacterApplication(copied,die=self.no_roll,rule_archive=self.archive())
                restored = other.import_character(app.export_character(hero['id']))
                ignored = {'id','revision','updated_at','copied_from'}
                self.assertEqual({key:value for key,value in restored.items() if key not in ignored},
                                 {key:value for key,value in hero.items() if key not in ignored})
                self.assertEqual(self.app(directory).get(hero['id']),hero)

    def test_source_award_boundaries_fixed_specialties_and_later_learning(self):
        with tempfile.TemporaryDirectory() as directory:
            app = self.app(directory)
            hero = app.create(character_class='merc-soldier-communications')
            hero = app.generate_resources(hero['id'],revision=hero['revision'])
            hero = app.select_skills(hero['id'],revision=hero['revision'],selections=self.choices('communications'))
            hero = app.advance(hero['id'],revision=hero['revision'],method='xp',value=3861)
            self.assertEqual(hero['level'],3)
            view = app.skill_view(hero['id'])
            self.assertEqual((view['remaining']['related'],view['remaining']['secondary']),(5,2))
            self.assertEqual(next(row for row in view['grants'] if row['id'] == 'sign-language')['percentage'],40)
            selections = self.choices('communications')+[
                {'skill_id':'cook','pool':'related','specialty':''},
                {'skill_id':'photography','pool':'secondary','specialty':''}]
            hero = app.select_skills(hero['id'],revision=hero['revision'],selections=selections)
            acquired = {row['id']:row for row in app.skill_view(hero['id'])['selected']}
            self.assertEqual((acquired['cook']['percentage'],acquired['photography']['percentage']),(35,35))
            hero = app.advance(hero['id'],revision=hero['revision'],method='xp',value=7721)
            self.assertEqual(app.skill_view(hero['id'])['remaining']['secondary'],3)
            hero = app.advance(hero['id'],revision=hero['revision'],method='xp',value=340000)
            self.assertEqual(hero['level'],15)
            self.assertEqual((app.skill_view(hero['id'])['remaining']['related'],
                              app.skill_view(hero['id'])['remaining']['secondary']),(8,7))
            app.die = self.no_roll
            before = deepcopy(hero)
            with self.assertRaises(ValueError):
                app.advance(hero['id'],revision=hero['revision'],method='xp',value=340001)
            self.assertEqual(app.get(hero['id']),before)
            duplicate = [{'skill_id':'language-other','pool':'common-language','specialty':'American'}]
            hero = app.select_skills(hero['id'],revision=hero['revision'],selections=duplicate)
            self.assertTrue(any('already granted' in note for note in app.skill_view(hero['id'])['warnings']))

    def test_invalid_inactive_fixed_specialty_clip_formulas_and_secondary_training(self):
        original = self.archive()
        for kind in ('specialty','projection','quantity','training'):
            with self.subTest(kind=kind),tempfile.TemporaryDirectory() as directory:
                definitions = deepcopy(original.definitions())
                if kind in ('specialty','projection','training'):
                    pack = next(row for row in definitions if row['id'] == 'rifts-domestic-skills'
                                and row['version'] == original.active_versions()[row['id']])
                    if kind == 'specialty':
                        pack['class_profiles']['merc-soldier-scout']['required']['grants'][0]['specialty'] = True
                    elif kind == 'projection':
                        pack['class_profiles']['merc-soldier-scout']['required']['fixed_specialties'] = 1
                    else:
                        next(row for row in pack['skills'] if row['id'] == 'combat-driving')['base'] = 25
                else:
                    pack = next(row for row in definitions if row['id'] == 'rifts-equipment'
                                and row['version'] == original.active_versions()[row['id']])
                    group = pack['class_profiles']['merc-soldier-scout']['starting_groups']['groups']['pistol']
                    next(iter(group['additional_grants'].values()))[0]['quantity_formula']['constant'] = -5
                app = CharacterApplication(directory,die=self.no_roll,
                    rule_archive=RuleArchive(definitions,original.active_versions()))
                with self.assertRaises(ValueError):
                    app.create(character_class='vagabond')
                self.assertEqual(app.list(),[])
        with tempfile.TemporaryDirectory() as directory:
            app = self.app(directory)
            hero = app.create(character_class='merc-soldier-transportation')
            hero = app.select_skills(hero['id'],revision=hero['revision'],selections=[
                {'skill_id':'combat-driving','pool':'secondary','specialty':''}])
            self.assertTrue(any('not available' in note for note in app.skill_view(hero['id'])['warnings']))

    def test_new_training_does_not_expand_inherited_pilot_choices(self):
        archive = self.archive()
        newer = archive.resolve('rifts-domestic-skills','2.35.0')
        older = archive.resolve('rifts-domestic-skills','2.34.0')
        training = next(row for row in newer['skills'] if row['id'] == 'combat-driving')
        for identity,old_profile in older['class_profiles'].items():
            profile = newer['class_profiles'][identity]
            for pool in old_profile['selection_rules']:
                with self.subTest(identity=identity,pool=pool):
                    self.assertFalse(selection_policy(training,pool,profile)['allowed'])
                    for definition in older['skills']:
                        self.assertEqual(selection_policy(definition,pool,profile),
                                         selection_policy(definition,pool,old_profile))

    def test_medic_unqualified_brewing_credits_one_variant_at_source_bonus(self):
        with tempfile.TemporaryDirectory() as directory:
            app = self.app(directory)
            hero = app.create(character_class='merc-soldier-medic')
            for variant in ('brewing-basic','brewing-medicinal'):
                selections = self.choices('medic')
                next(row for row in selections if row['skill_id'] == 'brewing-medicinal')['skill_id'] = variant
                hero = app.select_skills(hero['id'],revision=hero['revision'],selections=selections)
                view = app.skill_view(hero['id'])
                brewing = [row for row in view['selected'] if row['id'].startswith('brewing-')]
                self.assertEqual([(row['id'],row['percentage']) for row in brewing],[(variant,30)])
                requirement = next(row for row in view['pool_requirements'] if row['id'] == 'brewing')
                self.assertEqual((requirement['count'],requirement['credited'],requirement['remaining']),(1,1,0))
                self.assertEqual(view['remaining']['mos'],0)
                self.assertEqual(view['warnings'],[])
            hero = app.select_skills(hero['id'],revision=hero['revision'],selections=self.choices('medic')+[
                {'skill_id':'brewing-basic','pool':'mos','specialty':''}])
            view = app.skill_view(hero['id'])
            self.assertTrue(view['warnings'])
            self.assertEqual(view['remaining']['mos'],-1)
