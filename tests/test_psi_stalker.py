"""Independent source fixtures for RUE153-156/295 Psi-Stalker paths."""
from copy import deepcopy
import tempfile
import unittest

from characters_unlimited.application import CharacterApplication
from characters_unlimited.rules import RuleArchive
from characters_unlimited.skill_choices import selection_policy


PATHS = ('psi-stalker-civilized', 'psi-stalker-coalition', 'psi-stalker-wild')


class PsiStalkerTests(unittest.TestCase):
    archive = staticmethod(RuleArchive.load)

    def app(self, directory):
        return CharacterApplication(directory, die=lambda sides: 3, rule_archive=self.archive())

    def no_roll(self, sides):
        self.fail('Projection, reopen and exact portable replay must not draw dice')

    def test_exceptional_dice_use_natural_three_dice_before_constants_and_no_four_dice_explosion(self):
        with tempfile.TemporaryDirectory() as directory:
            app=self.app(directory)
            app.die=lambda sides:min(6,sides)
            hero=app.create(race='psi-stalker',character_class=PATHS[2])
            self.assertEqual({key:hero['attributes'][key]['base'] for key in ('IQ','ME','PS','PP','PE','SPD')},
                             {'IQ':30,'ME':35,'PS':30,'PP':30,'PE':24,'SPD':30})
            self.assertEqual(hero['attributes']['PS']['value'],32)
            self.assertEqual(hero['attributes']['PP']['value'],32)
            self.assertEqual(hero['attributes']['ME']['bonus_rolls'],[6,6])
            self.assertEqual(hero['attributes']['PE']['bonus_rolls'],[])
            self.assertEqual(hero['attributes']['SPD']['bonus_rolls'],[])

    def test_racial_attributes_resources_psychic_reserve_and_scoped_saving_bonuses(self):
        for path in PATHS:
            with self.subTest(path=path), tempfile.TemporaryDirectory() as directory:
                wild = path.endswith('wild')
                app = self.app(directory)
                hero = app.create(race='psi-stalker', character_class=path)
                expected = {'IQ':9,'ME':14,'MA':9,'PS':11,'PP':11 if wild else 9,
                            'PE':12 if wild else 13,'PB':9,'SPD':18 if wild else 30}
                self.assertEqual({key:row['value'] for key,row in hero['attributes'].items()}, expected)
                self.assertEqual(hero['attributes']['PS']['base'], 9)
                self.assertEqual(hero['attributes']['SPD']['base'], 18)
                hero = app.generate_resources(hero['id'], revision=hero['revision'])
                resources = app.resource_view(hero['id'])['resources']
                self.assertEqual({key:resources[key]['value'] for key in ('HP','SDC','PPE')},
                                 {'HP':19 if wild else 20,'SDC':28 if wild else 41,'PPE':6})
                saves = app.combat_view(hero['id'])['saving_bonuses']
                self.assertEqual({key:saves[key]['value'] for key in ('magic','mind_control','mind_altering_drugs','possession','horror_factor')},
                                 {'magic':3,'mind_control':5,'mind_altering_drugs':5,'possession':3,'horror_factor':6})
                self.assertEqual(saves['drugs']['value'],0)
                self.assertEqual(saves['psionics']['value'],0)
                self.assertEqual(app.combat_view(hero['id'])['class_bonuses']['perception']['value'],5 if wild else 4)
                psychic = app.psionic_view(hero['id'])['effective']
                self.assertEqual(psychic['save_target'],6)
                self.assertEqual(psychic['resources']['ISP']['value'],54)  # ME14 +30 die +10 level1.

    def test_skill_percentages_animal_empathy_and_intelligence_apply_once(self):
        for path in (PATHS[0],PATHS[2]):
            with self.subTest(path=path), tempfile.TemporaryDirectory() as directory:
                app=self.app(directory); hero=app.create(race='psi-stalker',character_class=path)
                wild=path.endswith('wild')
                view=app.skill_view(hero['id']); grants={row['id']:row for row in view['grants']}
                expected={'native-language':90 if wild else 96,'climbing':45,'prowl':35}
                expected.update({'detect-ambush':35,'escape-artist':35,'land-navigation':46,'tracking':35,
                    'wilderness-survival':60,'horse-cowboy':91,'horse-exotic':60} if wild else
                    {'hover-craft':60,'sensory-equipment':40,'radio-basic':55,'weapon-systems':50})
                self.assertEqual({key:grants[key]['percentage'] for key in expected},expected)
                choices=[{'skill_id':'language-other','pool':'language','specialty':'Spanish'}]
                choices += [{'skill_id':'animal-husbandry','pool':'secondary','specialty':''}]
                if not wild:
                    choices += [{'skill_id':'tame-wild-horse','pool':'related','specialty':''},
                                {'skill_id':'breed-dogs','pool':'related','specialty':''}]
                hero=app.select_skills(hero['id'],revision=hero['revision'],selections=choices)
                selected={row['id']:row for row in app.skill_view(hero['id'])['selected']}
                self.assertEqual(selected['language-other']['percentage'],75 if wild else 70)
                self.assertEqual(selected['animal-husbandry']['percentage'],50)  #35+15 domestic animal empathy.
                if not wild:
                    self.assertEqual(selected['tame-wild-horse']['percentage'],40)  #20+5 OCC+15 empathy.
                    self.assertEqual(selected['breed-dogs']['percentage'],60)  #40+5 OCC+15 empathy.
                hero=app.set_attribute(hero['id'],revision=hero['revision'],attribute='IQ',mode='fixed',value=18)
                self.assertEqual(next(row for row in app.skill_view(hero['id'])['selected'] if row['id']=='language-other')['percentage'],79 if wild else 74)

    def test_six_sensitive_choices_distinct_inherent_senses_and_exact_no_dice_portability(self):
        archive=self.archive()
        powers=[row for row in archive.active('rifts-psi-stalker-psionics')['catalog']['options'] if row['category']=='Sensitive']
        selected=[row['id'] for row in powers[:6]]
        self.assertEqual(len(selected),6)
        for path in PATHS:
            with self.subTest(path=path),tempfile.TemporaryDirectory() as directory,tempfile.TemporaryDirectory() as copied:
                app=self.app(directory); hero=app.create(race='psi-stalker',character_class=path)
                hero=app.select_class_psionics(hero['id'],revision=hero['revision'],selections=selected)
                view=app.psionic_view(hero['id'])['effective']
                self.assertEqual(len(view['abilities']),8)
                by_id={row['id']:row for row in view['abilities']}
                self.assertEqual(set(by_id),{*selected,'psi-stalker-sense-psychic-magic','psi-stalker-sense-supernatural'})
                scent={row['id']:row['value'] for row in by_id['psi-stalker-sense-psychic-magic']['parameters']}
                self.assertEqual((scent['specific-scent'],scent['active-energy'],scent['recognition']),(20,65,25))
                self.assertEqual(scent['active-range'],600)
                senses={row['id']:row['value'] for row in by_id['psi-stalker-sense-supernatural']['parameters']}
                self.assertEqual((senses['detection'],senses['disguised'],senses['powerful']),(45,35,73))
                guidance=' '.join(app.character_skill_pack(hero)['path_guidance'])
                self.assertIn('Sense Psychic/Magic Energy',guidance)
                self.assertIn('Sense Supernatural Beings',guidance)
                app.die=self.no_roll
                exported=app.export_character(hero['id'])
                reopened=CharacterApplication(directory,die=self.no_roll,rule_archive=archive)
                self.assertEqual(reopened.get(hero['id']),hero)
                target=CharacterApplication(copied,die=self.no_roll,rule_archive=archive)
                restored=target.import_character(exported)
                ignore={'id','revision','updated_at','copied_from'}
                self.assertEqual({k:v for k,v in restored.items() if k not in ignore},
                                 {k:v for k,v in hero.items() if k not in ignore})
                self.assertEqual(target.psionic_view(restored['id'])['effective'],view)

    def test_xp_skill_awards_paid_training_and_retained_advancement_undo(self):
        for path in (PATHS[0],PATHS[2]):
            with self.subTest(path=path),tempfile.TemporaryDirectory() as directory:
                app=self.app(directory); hero=app.create(race='psi-stalker',character_class=path)
                receipt=deepcopy(hero['numeric_acquisitions'])
                hero=app.generate_resources(hero['id'],revision=hero['revision'])
                hero=app.advance(hero['id'],revision=hero['revision'],method='xp',value=2050)
                self.assertEqual(hero['level'],1)
                hero=app.advance(hero['id'],revision=hero['revision'],method='xp',value=2051)
                self.assertEqual(hero['level'],2)
                self.assertEqual(app.skill_view(hero['id'])['remaining']['related'],4 if path.endswith('wild') else 5)
                hero=app.advance(hero['id'],revision=hero['revision'],method='xp',value=16501)
                self.assertEqual(hero['level'],5)
                remaining=app.skill_view(hero['id'])['remaining']
                self.assertEqual((remaining['related'],remaining['secondary']),(5 if path.endswith('wild') else 6,12))
                for hand,cost in [('expert',0),('martial-arts',2),('assassin',2)]:
                    hero=app.select_combat(hero['id'],revision=hero['revision'],choices={'hand_to_hand':hand,'ancient':[],'modern':[]})
                    self.assertEqual(app.combat_view(hero['id'])['related_cost'],cost)
                self.assertEqual(app.psionic_view(hero['id'])['effective']['resources']['ISP']['value'],94)
                app.die=self.no_roll
                hero=app.undo_advancement(hero['id'],revision=hero['revision'])['character']
                hero=app.advance(hero['id'],revision=hero['revision'],method='level',value=5)
                self.assertEqual(hero['numeric_acquisitions'],receipt)
                self.assertEqual(app.psionic_view(hero['id'])['effective']['resources']['ISP']['value'],94)
                app.export_character(hero['id'])

    def test_equipment_variants_funds_weapon_pools_and_retained_clips(self):
        for path,credits in [(PATHS[0],1800),(PATHS[1],1700),(PATHS[2],0)]:
            with self.subTest(path=path),tempfile.TemporaryDirectory() as directory:
                app=self.app(directory); hero=app.create(race='psi-stalker',character_class=path)
                hero=app.generate_starting_funds(hero['id'],revision=hero['revision'])
                self.assertEqual(hero['equipment']['credits'],credits)
                hero=app.grant_starting_gear(hero['id'],revision=hero['revision'])
                if path==PATHS[1]:
                    for key,item in [('neural-mace','psi-stalker-neural-mace'),('fist-spikes','psi-stalker-fist-spikes'),('vibro-knife','vibro-knife')]:
                        hero=app.grant_starting_group(hero['id'],revision=hero['revision'],group_id=key,selection=item)
                else:
                    choices={'hand_to_hand':'expert','ancient':['knife','sword']+(['spear'] if path.endswith('wild') else []),
                             'modern':['energy-pistol','energy-rifle'] if path.endswith('wild') else []}
                    hero=app.select_combat(hero['id'],revision=hero['revision'],choices=choices)
                    weapons=['knife-large','vibro-saber']+(['psi-stalker-wood-spear','wilks-320','wilks-447'] if path.endswith('wild') else [])
                    for slot,item in enumerate(weapons,1):
                        hero=app.grant_starting_group(hero['id'],revision=hero['revision'],group_id='wp-weapon-'+str(slot),selection=item)
                    if path==PATHS[0]:
                        for key,item in [('pistol','wilks-320'),('rifle','wilks-447')]:
                            hero=app.grant_starting_group(hero['id'],revision=hero['revision'],group_id=key,selection=item)
                    else:
                        hero=app.grant_starting_group(hero['id'],revision=hero['revision'],group_id='transport',selection='psi-stalker-horse')
                        for key,item in [('blade-1','knife-large'),('blade-2','vibro-knife')]:
                            hero=app.grant_starting_group(hero['id'],revision=hero['revision'],group_id=key,selection=item)
                        self.assertEqual(sum(row['quantity'] for row in hero['equipment']['items'] if row['item_id']=='vibro-knife'),1)
                    self.assertEqual(sum(row['quantity'] for row in hero['equipment']['items'] if row['item_id']=='standard-e-clip'),0)
                    hero=app.grant_starting_group(hero['id'],revision=hero['revision'],group_id='spare-clips',selection='standard-e-clip')
                    self.assertEqual(sum(row['quantity'] for row in hero['equipment']['items'] if row['item_id']=='standard-e-clip'),4)
                    grants=hero['starting_equipment_groups']['spare-clips']['grants']
                    self.assertEqual([row['rolls'] for row in grants if 'rolls' in row],[[3]])
                app.die=self.no_roll
                restored=app.import_character(app.export_character(hero['id']))
                self.assertEqual(restored['equipment'],hero['equipment'])

    def test_wild_conventional_ammunition_is_one_retained_allowance_and_reloads_exact_weapon(self):
        for weapon,training in [('gaw-m16a2-20','rifles'),('wi-gl8-shotgun','shotgun'),
                ('gaw-smg-30','submachine-gun'),('magnum-revolver','handguns'),
                ('gaw-light-mg-200','heavy-military'),('nautyll-harpoon-20','harpoon-spear-gun')]:
            with self.subTest(weapon=weapon),tempfile.TemporaryDirectory() as directory:
                app=self.app(directory); hero=app.create(race='psi-stalker',character_class=PATHS[2])
                hero=app.select_combat(hero['id'],revision=hero['revision'],choices={'hand_to_hand':'expert','ancient':[],'modern':[training]})
                hero=app.grant_starting_group(hero['id'],revision=hero['revision'],group_id='wp-weapon-1',selection=weapon)
                ammo='psi-stalker-ammo-'+weapon
                hero=app.grant_starting_group(hero['id'],revision=hero['revision'],group_id='spare-clips',selection=ammo)
                self.assertEqual(sum(row['quantity'] for row in hero['equipment']['items'] if row['item_id']==ammo),4)
                inventory=deepcopy(hero['equipment'])
                gun=next(row for row in inventory['items'] if row['item_id']==weapon)
                clip=next(row for row in inventory['items'] if row['item_id']==ammo and row['quantity']==1)
                capacity=clip['shots']; gun['shots']=0
                app.die=self.no_roll
                hero=app.set_equipment(hero['id'],revision=hero['revision'],inventory=inventory)
                hero=app.reload_weapon(hero['id'],revision=hero['revision'],weapon_possession_id=gun['id'],clip_possession_id=clip['id'])
                self.assertEqual(next(row['shots'] for row in hero['equipment']['items'] if row['id']==gun['id']),capacity)
                self.assertEqual(next(row['shots'] for row in hero['equipment']['items'] if row['id']==clip['id']),0)
                self.assertEqual(app.import_character(app.export_character(hero['id']))['equipment'],hero['equipment'])

    def test_pairing_and_distinct_related_restrictions_preserve_humans(self):
        archive=self.archive(); pack=archive.active('rifts-domestic-skills'); catalog={r['id']:r for r in pack['skills']}
        for path in PATHS:
            ids=[row['id'] for row in pack['class_profiles'][path]['combat']['ancient']]
            self.assertEqual(ids,['knife','sword','blunt','spear'])
        for path,skill,allowed,bonus in [(PATHS[0],'tame-wild-horse',True,5),(PATHS[2],'tame-wild-horse',False,0),
                (PATHS[2],'holistic-medicine',True,5),(PATHS[0],'holistic-medicine',False,0),
                (PATHS[2],'tanks-apcs',False,0),(PATHS[0],'computer-operation',False,0)]:
            policy=selection_policy(catalog[skill],'related',{**pack,**pack['class_profiles'][path]})
            self.assertEqual((policy['allowed'],policy['bonus']),(allowed,bonus))
        with tempfile.TemporaryDirectory() as directory:
            app=self.app(directory); app.die=self.no_roll
            with self.assertRaises(ValueError):
                app.create(race='human',character_class=PATHS[0])
            with self.assertRaises(ValueError):
                app.create(race='psi-stalker',character_class='vagabond')
            self.assertEqual(app.list(),[])
            app.die=lambda sides:3
            hero=app.create(race='psi-stalker',character_class=PATHS[2])
            hero=app.select_combat(hero['id'],revision=hero['revision'],choices={'hand_to_hand':'expert','ancient':['blunt'],'modern':[]})
            self.assertEqual([row['id'] for row in app.combat_view(hero['id'])['melee']],['blunt'])
        old=archive.resolve('rifts-core','1.16.0')
        self.assertEqual(archive.active('rifts-core')['classes'][:len(old['classes'])],old['classes'])
        self.assertEqual(archive.active('rifts-core')['creation_profiles'][0],old['creation_profiles'][0])
        old_skills=archive.resolve('rifts-domestic-skills','2.37.0')
        self.assertEqual(pack['skills'],old_skills['skills'])
        for identity,profile in old_skills['class_profiles'].items():
            self.assertEqual(pack['class_profiles'][identity],profile)
        previous=archive.resolve('rifts-equipment','1.24.0')
        current=archive.active('rifts-equipment')
        self.assertEqual(current['items'][:len(previous['items'])],previous['items'])
        for identity,profile in previous['class_profiles'].items():
            self.assertEqual(current['class_profiles'][identity],profile)
