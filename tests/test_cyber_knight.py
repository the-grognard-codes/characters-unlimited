"""Source-backed Human Cyber-Knight paths, training ages and owned possessions."""
from copy import deepcopy
from typing import Any
import tempfile
import unittest
from characters_unlimited.application import CharacterApplication
from characters_unlimited.rules import RuleArchive


class CyberKnightTests(unittest.TestCase):
    archive = staticmethod(RuleArchive.load)

    def no_roll(self, sides):
        self.fail('Retained class choices and portable replay must not reroll')

    def test_required_swimming_has_one_calculated_browser_receipt(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides: 3, rule_archive=self.archive())
            hero = app.create(character_class='cyber-knight-minor')
            app.die = self.no_roll
            view = app.skill_view(hero['id'])
            swimming = [row for row in view['grants'] if row['id'] == 'swimming']
            self.assertEqual(len(swimming), 1)
            self.assertEqual(swimming[0]['percentage'], 60)
            self.assertIsInstance(swimming[0]['activities'], list)
            self.assertEqual(swimming[0]['activities'][0]['yards_per_melee'],
                             3 * hero['attributes']['PS']['value'])
            self.assertEqual(swimming[0]['activities'][0]['minutes'],
                             hero['attributes']['PE']['value'])
            self.assertIn('effects', swimming[0])

    def test_parent_declarations_are_preserved_exactly(self):
        archive = self.archive()
        core = archive.active('rifts-core')
        old_core = archive.resolve('rifts-core','1.14.0')
        self.assertEqual(core['classes'][:-4],old_core['classes'])
        for identifier,version,new_items in [('rifts-domestic-skills','2.35.0',1),
                                               ('rifts-equipment','1.22.0',18)]:
            current = archive.active(identifier)
            previous = archive.resolve(identifier,version)
            field = 'skills' if identifier=='rifts-domestic-skills' else 'items'
            self.assertEqual(current[field][:-new_items],previous[field])
            for identity,profile in previous['class_profiles'].items():
                self.assertEqual(current['class_profiles'][identity],profile)

    def test_fixed_science_lore_synergy_and_other_language_percentages(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory,die=lambda sides:3,rule_archive=self.archive())
            hero = app.create(character_class='cyber-knight-major')
            grants = {row['id']:row for row in app.skill_view(hero['id'])['grants'] if 'percentage' in row}
            self.assertEqual([grants[key]['percentage'] for key in
                              ('anthropology','lore-demons-monsters','paramedic')],[45,50,50])
            app.die = self.no_roll
            hero = app.select_skills(hero['id'],revision=hero['revision'],selections=[
                {'skill_id':'language-other','pool':'other-languages','specialty':name} for name in ('Spanish','French')])
            self.assertEqual([row['percentage'] for row in app.skill_view(hero['id'])['selected']],[80,80])

    def test_source_psychic_choices_retained_growth_and_master_super_award(self):
        for path,initial,count,gain in [('non-psychic',12,0,3),('minor',21,3,3),
                                       ('major',30,6,3),('master',40,8,6)]:
            with self.subTest(path=path),tempfile.TemporaryDirectory() as directory,tempfile.TemporaryDirectory() as copied:
                archive = self.archive()
                app = CharacterApplication(directory,die=lambda sides:3,rule_archive=archive)
                hero = app.create(character_class='cyber-knight-'+path)
                dependency = archive.active('rifts-cyber-knight-'+path+'-psionics')
                fixed = set(dependency['paths'][0]['known_abilities'])
                choices = [row['id'] for row in dependency['catalog']['options']
                           if row['id'] not in fixed and row['category']!='Super'][:count]
                app.die = self.no_roll
                hero = app.select_class_psionics(hero['id'],revision=hero['revision'],selections=choices)
                view = app.psionic_view(hero['id'])
                self.assertEqual(view['class_entitlement']['selection_group']['remaining'],0)
                self.assertEqual(view['effective']['resources']['ISP']['value'],initial)
                self.assertEqual(len(hero['class_psionics']['abilities']['selections']),3+count)
                app.die = lambda sides:3
                hero = app.generate_resources(hero['id'],revision=hero['revision'])
                hero = app.advance(hero['id'],revision=hero['revision'],method='level',value=2)
                self.assertEqual(app.psionic_view(hero['id'])['effective']['resources']['ISP']['value'],initial+gain)
                if path=='master':
                    self.assertEqual(app.psionic_view(hero['id'])['class_entitlement']['selection_group']['remaining'],1)
                    choices.append(next(row['id'] for row in dependency['catalog']['options'] if row['category']=='Super'))
                    app.die = self.no_roll
                    hero = app.select_class_psionics(hero['id'],revision=hero['revision'],selections=choices)
                    self.assertEqual(app.psionic_view(hero['id'])['class_entitlement']['selection_group']['remaining'],0)
                other = CharacterApplication(copied,die=self.no_roll,rule_archive=archive)
                restored = other.import_character(app.export_character(hero['id']))
                self.assertEqual(restored['class_psionics'],hero['class_psionics'])
                self.assertEqual(other.psionic_view(restored['id']),app.psionic_view(hero['id']))

    def test_source_skills_resources_weapon_awards_and_exact_portable_paths(self):
        archive = self.archive()
        for path, isp in [('non-psychic',12),('minor',21),('major',30),('master',40)]:
            with tempfile.TemporaryDirectory() as directory,tempfile.TemporaryDirectory() as copied:
                app = CharacterApplication(directory,die=lambda sides:3,rule_archive=archive)
                hero = app.create(character_class='cyber-knight-'+path)
                hero = app.generate_resources(hero['id'],revision=hero['revision'])
                attributes = {key:row['value'] for key,row in hero['attributes'].items()}
                assert [attributes[key] for key in ('ME','PS','PP','PE')] == [12,16,13,14],attributes
                resources = app.resource_view(hero['id'])['resources']
                assert [resources[key]['value'] for key in ('SDC','HP','PPE')] == [64,17,18],resources
                assert app.psionic_view(hero['id'])['effective']['resources']['ISP']['value'] == isp
                combat = app.combat_view(hero['id'])
                assert combat['totals']['attacks']['value'] == 5,combat['totals']['attacks']
                assert combat['class_bonuses']['perception']['value'] == (5 if path=='non-psychic' else 3)
                view = app.skill_view(hero['id'])
                grants = {row['id']:row for row in view['grants'] if 'percentage' in row}
                assert [grants[key]['percentage'] for key in ('native-language','dragonese-language','literacy-native',
                    'horse-cyber-knight','land-navigation','climbing','gymnastics','swimming')] == [96,96,60,70,48,55,55,60],grants
                app.die = self.no_roll
                choices: dict[str, Any] = {'ancient':['knife','sword','blunt'],'modern':['handguns','energy-pistol','energy-rifle','rifles'],
                           'hand_to_hand':'martial-arts'}
                hero = app.select_combat(hero['id'],revision=hero['revision'],choices=choices)
                assert app.combat_view(hero['id'])['related_cost'] == 3
                selections = [{'skill_id':'language-other','pool':'other-languages','specialty':language}
                              for language in ('Spanish','French')]
                selections += [{'skill_id':key,'pool':'related','specialty':''} for key in ('athletics','running','trick-riding')]
                # Physical acquisition dice are deliberate; ordinary language/riding projections are deterministic.
                app.die = lambda sides:3
                hero = app.select_skills(hero['id'],revision=hero['revision'],selections=selections)
                view = app.skill_view(hero['id'])
                selected = {row['id']:row for row in view['selected']}
                assert selected['trick-riding']['percentage'] == 70,selected
                assert [view['remaining'][key] for key in ('related','secondary','other-languages')] == [6,6,0],view['remaining']
                assert all(row['remaining']==0 for row in view['pool_requirements'])
                hero = app.advance(hero['id'],revision=hero['revision'],method='level',value=5)
                combat = app.combat_view(hero['id'])
                assert combat['related_cost']==3 and combat['remaining']['weapon_awards']==3
                shield = next(row for row in combat['melee'] if row['id']=='shield')
                # Shield acquired at class two is training level four at class five: +2 parry, +1 strike.
                assert shield['parry']['contributions']['weapon_proficiency']==2,shield
                app.die = self.no_roll
                later = deepcopy(choices)
                later['modern'] += ['shotgun','submachine-gun','heavy-military']
                hero = app.select_combat(hero['id'],revision=hero['revision'],choices=later)
                assert app.combat_view(hero['id'])['related_cost']==3
                assert app.combat_view(hero['id'])['remaining']['weapon_awards']==0
                other = CharacterApplication(copied,die=self.no_roll,rule_archive=archive)
                restored = other.import_character(app.export_character(hero['id']))
                assert other.skill_view(restored['id'])==app.skill_view(hero['id'])
                assert other.combat_view(restored['id'])==app.combat_view(hero['id'])
                assert CharacterApplication(directory,die=self.no_roll,rule_archive=archive).get(hero['id'])==hero

    def test_source_equipment_funds_and_partial_armor_portability(self):
        archive = self.archive()
        with tempfile.TemporaryDirectory() as directory,tempfile.TemporaryDirectory() as copied:
            app = CharacterApplication(directory,die=lambda sides:3,rule_archive=archive)
            hero = app.create(character_class='cyber-knight-minor')
            hero = app.generate_resources(hero['id'],revision=hero['revision'])
            hero = app.generate_starting_funds(hero['id'],revision=hero['revision'])
            assert hero['equipment']['credits']==600
            hero = app.grant_starting_gear(hero['id'],revision=hero['revision'])
            for key,item in [('heavy-armor','cs-ca1'),('light-armor','plastic-man'),('knife','knife-large'),
                             ('ancient-weapon','vibro-saber'),('pistol','cs-c18'),('rifle','cs-c10'),
                             ('cross-and-stakes','cyber-knight-wooden-cross'),('spare-clips','cs-rifle-e-clip')]:
                hero = app.grant_starting_group(hero['id'],revision=hero['revision'],group_id=key,selection=item)
            inventory = {row['item_id']:row for row in hero['equipment']['items']}
            assert inventory['cyber-knight-wooden-stake']['quantity']==6
            assert inventory['cs-rifle-e-clip']['quantity']==3
            assert 'cs-pistol-e-clip' not in inventory and 'standard-e-clip' not in inventory
            assert inventory['cyber-knight-canteen']['quantity']==2
            assert inventory['knife-large']['quantity']==1
            assert 'optional-second-knife' not in hero['starting_equipment_groups']
            view = app.equipment_view(hero['id'])
            assert all(row.get('id')!='cyber-knight-cyber-armor' for row in view['armor'])
            cyber = next(row for row in view['catalog'] if row['id']=='cyber-knight-cyber-armor')
            assert cyber['weight_lbs'] is None and cyber['cost_credits'] is None and cyber['category']=='gear'
            assert 'thigh15' in cyber['description'] and 'cannot be reused or transferred' in cyber['description']
            assert not any('glitter-boy' in key or 'motorcycle' in key for key in inventory)
            changed = deepcopy(hero['equipment'])
            next(row for row in changed['items'] if row['item_id']=='cyber-knight-cyber-armor')['equipped']=True
            app.die = self.no_roll
            hero = app.set_equipment(hero['id'],revision=hero['revision'],inventory=changed)
            assert all(row.get('id')!='cyber-knight-cyber-armor' for row in app.equipment_view(hero['id'])['armor'])
            try:
                app.grant_starting_group(hero['id'],revision=hero['revision'],group_id='cross-and-stakes',selection='cyber-knight-wooden-cross')
            except ValueError as error:
                assert 'already been granted' in str(error)
            else:
                raise AssertionError('Starting cross/stakes cannot be issued twice')
            assert next(row for row in hero['equipment']['items'] if row['item_id']=='cyber-knight-wooden-stake')['quantity']==6
            other = CharacterApplication(copied,die=self.no_roll,rule_archive=archive)
            restored = other.import_character(app.export_character(hero['id']))
            assert restored['starting_funds']==hero['starting_funds']
            assert restored['starting_equipment_groups']==hero['starting_equipment_groups']
            assert restored['equipment']==hero['equipment']
            assert CharacterApplication(directory,die=self.no_roll,rule_archive=archive).get(hero['id'])==hero
