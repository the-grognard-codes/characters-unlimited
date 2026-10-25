"""Source-grounded Human pilot workflows, RUE84-85/271-274/295."""
from copy import deepcopy
import tempfile
import unittest

from characters_unlimited.advancement import learning_key
from characters_unlimited.application import CharacterApplication
from characters_unlimited.rules import RuleArchive
from characters_unlimited.skill_choices import selection_policy


def choice(skill, pool, specialty=''):
    return {'skill_id':skill,'pool':pool,'specialty':specialty}


class RobotPilotTests(unittest.TestCase):
    archive = staticmethod(RuleArchive.load)

    def app(self, directory):
        return CharacterApplication(directory,die=lambda sides:3,rule_archive=self.archive())

    def no_roll(self, sides):
        self.fail('Reopen, selection and portable replay must retain recorded dice')

    def test_common_and_distinct_mos_percentages_resources_and_pilot_is_human(self):
        for path,expected in [('power-armor',{'math-advanced':60,'navigation':55,'robots-power-armor':76}),
            ('robot',{'land-navigation':48,'robots-power-armor':66,'tanks-apcs':36,'tracked-construction':60,'weapon-systems':55})]:
            with self.subTest(path=path),tempfile.TemporaryDirectory() as directory:
                app=self.app(directory)
                hero=app.create(character_class='robot-pilot-'+path)
                grants={r['id']:r for r in app.skill_view(hero['id'])['grants']}
                expected.update({'native-language':94,'math-basic':65,'climbing':45,'computer-operation':50,
                    'military-etiquette':50,'radio-basic':55,'sensory-equipment':45})
                self.assertEqual({k:grants[k]['percentage'] for k in expected},expected)
                self.assertNotIn('percentage',grants['combat-driving'])
                self.assertEqual([r['id'] for r in app.skill_view(hero['id'])['grants']].count('climbing'),1)
                hero=app.generate_resources(hero['id'],revision=hero['revision'])
                resources=app.resource_view(hero['id'])['resources']
                # 18 fallback +10 Body Building +3 Running; PE9 +1 Running +3 HP die.
                self.assertEqual((resources['SDC']['value'],resources['HP']['value']),(31,13))
                self.assertEqual(hero['attributes']['PS']['value'],11)
                self.assertEqual(app.combat_view(hero['id'])['related_cost'],0)

    def test_alternative_training_synergy_and_separate_bonus_pools(self):
        with tempfile.TemporaryDirectory() as directory:
            app=self.app(directory); hero=app.create(character_class='robot-pilot-power-armor')
            rows=[choice('language-other','common-language','Spanish'),choice('automobile','common-pilot'),
                choice('basic-mechanics','mechanics-acrobatics'),choice('jet-fighter','combat-aircraft'),choice('hovercycle','mos-pilot')]
            hero=app.select_skills(hero['id'],revision=hero['revision'],selections=rows)
            view=app.skill_view(hero['id']); selected={r['id']:r for r in view['selected']}
            self.assertEqual([selected[k]['percentage'] for k in ('language-other','automobile','basic-mechanics','jet-fighter','hovercycle')],
                             [70,75,45,55,82])
            self.assertEqual([view['remaining'][k] for k in ('common-language','common-pilot','mechanics-acrobatics','combat-aircraft','mos-pilot')],[0]*5)
            rows[2]=choice('acrobatics','mechanics-acrobatics')
            hero=app.select_skills(hero['id'],revision=hero['revision'],selections=rows)
            grants={r['id']:r for r in app.skill_view(hero['id'])['grants']}
            self.assertEqual(grants['climbing']['percentage'],60)
            self.assertNotIn('basic-mechanics',{r['id'] for r in app.skill_view(hero['id'])['selected']})
            hero=app.set_attribute(hero['id'],revision=hero['revision'],attribute='IQ',mode='fixed',value=18)
            self.assertEqual(next(r for r in app.skill_view(hero['id'])['selected'] if r['id']=='language-other')['percentage'],74)

    def test_awards_xp_boundaries_and_training_costs(self):
        with tempfile.TemporaryDirectory() as directory:
            app=self.app(directory); hero=app.create(character_class='robot-pilot-robot')
            hero=app.generate_resources(hero['id'],revision=hero['revision'])
            hero=app.advance(hero['id'],revision=hero['revision'],method='xp',value=4201)
            self.assertEqual(hero['level'],3)
            self.assertEqual({k:app.skill_view(hero['id'])['remaining'][k] for k in ('related','secondary','elite-models')},
                             {'related':6,'secondary':2,'elite-models':3})
            hero=app.advance(hero['id'],revision=hero['revision'],method='xp',value=8401)
            self.assertEqual(hero['level'],4)
            self.assertEqual(app.skill_view(hero['id'])['remaining']['secondary'],4)
            for hand,cost in [('expert',0),('martial-arts',1),('commando',2),('assassin',2)]:
                hero=app.select_combat(hero['id'],revision=hero['revision'],choices={'hand_to_hand':hand,'ancient':['sword'],'modern':['shotgun']})
                self.assertEqual(app.combat_view(hero['id'])['related_cost'],cost)
            hero=app.advance(hero['id'],revision=hero['revision'],method='level',value=12)
            view=app.skill_view(hero['id'])
            self.assertEqual((view['remaining']['related'],view['remaining']['secondary'],view['remaining']['elite-models']),(8,8,6))

    def test_elite_specialties_keep_initial_and_later_ages_with_exact_portability(self):
        for path,skill,names in [('power-armor','power-armor-combat-elite',['NG-X9 Samson','Flying Titan','NG Red Hawk']),
                                 ('robot','robot-vehicle-combat-elite',['Titan Combat','Titan Exploration','NG Hunter'])]:
            with self.subTest(path=path),tempfile.TemporaryDirectory() as directory,tempfile.TemporaryDirectory() as copied:
                app=self.app(directory); hero=app.create(character_class='robot-pilot-'+path)
                hero=app.generate_resources(hero['id'],revision=hero['revision'])
                hero=app.advance(hero['id'],revision=hero['revision'],method='level',value=3)
                app.die=self.no_roll
                hero=app.select_skills(hero['id'],revision=hero['revision'],selections=[choice(skill,'elite-models',name) for name in names])
                self.assertEqual([hero['learning_levels'][learning_key('skill',skill,name)] for name in names],[1,1,3])
                view=app.skill_view(hero['id'])
                self.assertEqual(view['remaining']['elite-models'],0)
                self.assertTrue(all('percentage' not in r for r in view['selected']))
                self.assertFalse(any('Two distinct initial' in w for w in view['warnings']))
                restored=CharacterApplication(copied,die=self.no_roll,rule_archive=self.archive()).import_character(app.export_character(hero['id']))
                ignored={'id','revision','updated_at','copied_from'}
                self.assertEqual({k:v for k,v in restored.items() if k not in ignored},{k:v for k,v in hero.items() if k not in ignored})
                self.assertEqual(CharacterApplication(directory,die=self.no_roll,rule_archive=self.archive()).get(hero['id']),hero)

    def test_equipment_vehicle_separation_random_clips_and_retained_receipts(self):
        for path,group_id,item in [('power-armor','samson','ng-x9-samson'),('robot','robot','tr-001-titan-combat')]:
            with self.subTest(path=path),tempfile.TemporaryDirectory() as directory,tempfile.TemporaryDirectory() as copied:
                app=self.app(directory); hero=app.create(character_class='robot-pilot-'+path)
                hero=app.generate_starting_funds(hero['id'],revision=hero['revision'])
                self.assertEqual(hero['equipment']['credits'],300)
                hero=app.grant_starting_gear(hero['id'],revision=hero['revision'])
                for key,selected in [(group_id,item),('pistol','wilks-320'),('rifle','wilks-447'),
                    ('gyro-compass','pilot-gyro-compass'),('clock-calendar','pilot-clock-calendar')]:
                    hero=app.grant_starting_group(hero['id'],revision=hero['revision'],group_id=key,selection=selected)
                inv=hero['equipment']['items']
                self.assertEqual(sum(r['quantity'] for r in inv if r['item_id']=='standard-e-clip'),10)
                self.assertEqual(sum(r['quantity'] for r in inv if r['item_id']=='pilot-merc-signal-flare'),4)
                vehicle=next(r for r in inv if r['item_id']==item)
                self.assertEqual((vehicle['location'],vehicle['equipped']),('stored',False))
                edited=deepcopy(hero['equipment']); next(r for r in edited['items'] if r['item_id']==item).update(location='carried',equipped=True)
                hero=app.set_equipment(hero['id'],revision=hero['revision'],inventory=edited)
                self.assertEqual(app.equipment_view(hero['id'])['armor'],[])
                self.assertEqual(hero['attributes']['PS']['value'],11)
                app.die=self.no_roll
                with self.assertRaisesRegex(ValueError,'already been granted'):
                    app.grant_starting_group(hero['id'],revision=hero['revision'],group_id='pistol',selection='wilks-320')
                hero=app.get(hero['id'])
                self.assertEqual(sum(r['quantity'] for r in hero['equipment']['items'] if r['item_id']=='standard-e-clip'),10)
                restored=CharacterApplication(copied,die=self.no_roll,rule_archive=self.archive()).import_character(app.export_character(hero['id']))
                self.assertEqual(restored['equipment'],hero['equipment'])

    def test_related_category_exclusions_and_parent_identity_preservation(self):
        archive=self.archive(); pack=archive.active('rifts-domestic-skills')
        profile={**pack,**pack['class_profiles']['robot-pilot-robot']}; catalog={r['id']:r for r in pack['skills']}
        for key,allowed,bonus in [('naval-history',False,0),('warship',False,0),('horse-general',False,0),
                                 ('aircraft-mechanics',True,5),('astronomy-navigation',True,15),('wilderness-survival',True,0),('seduction',True,0)]:
            rule=selection_policy(catalog[key],'related',profile)
            self.assertEqual((rule['allowed'],rule['bonus']),(allowed,bonus),key)
        old=archive.resolve('rifts-domestic-skills','2.36.0')
        pilot_pack=archive.resolve('rifts-domestic-skills','2.37.0')
        self.assertEqual(pack['skills'][:-2],old['skills'])
        for identity,before in old['class_profiles'].items():
            expected=deepcopy(before)
            for rules in expected['selection_rules'].values():
                pilot=rules.get('pilot',{})
                if pilot.get('allow')=='any':
                    pilot['exclude']=list(dict.fromkeys([*pilot.get('exclude',[]),'power-armor-combat-elite','robot-vehicle-combat-elite']))
            self.assertEqual(pilot_pack['class_profiles'][identity],expected)
        for identity in ('robot-pilot-power-armor','robot-pilot-robot'):
            self.assertEqual(pack['class_profiles'][identity],pilot_pack['class_profiles'][identity])
        self.assertEqual(archive.resolve('rifts-core','1.16.0')['classes'][:-2],archive.resolve('rifts-core','1.15.0')['classes'])

    def test_conventional_sidearm_does_not_invent_energy_clips(self):
        with tempfile.TemporaryDirectory() as directory:
            app = self.app(directory)
            hero = app.create(character_class='robot-pilot-robot')
            app.die = self.no_roll
            hero = app.grant_starting_group(hero['id'], revision=hero['revision'],
                                           group_id='pistol', selection='magnum-revolver')
            self.assertEqual([(row['item_id'], row['quantity']) for row in hero['equipment']['items']],
                             [('magnum-revolver', 1)])
