"""Inactive-source runner activates these fixtures before official publication."""
from copy import deepcopy
import tempfile
import unittest
from characters_unlimited.application import CharacterApplication
from characters_unlimited.rules import RuleArchive


class GlitterBoyTests(unittest.TestCase):
    archive=staticmethod(RuleArchive.load)

    def app(self,directory):
        return CharacterApplication(directory,die=lambda sides:3,rule_archive=self.archive())

    def no_roll(self,sides):
        self.fail('Retained choices, source ownership and portability must not reroll')

    def test_independent_source_grants_initial_languages_pilot_and_lineage_resources(self):
        for identity,sdc in (('glitter-boy',18),('glitter-boy-family',38)):
            with self.subTest(identity=identity), tempfile.TemporaryDirectory() as directory:
                app=self.app(directory)
                hero=app.create(character_class=identity)
                hero=app.set_attribute(hero['id'],revision=hero['revision'],attribute='PP',mode='fixed',value=10)
                hero=app.generate_resources(hero['id'],revision=hero['revision'])
                resources=app.resource_view(hero['id'])['resources']
                self.assertEqual(resources['SDC']['value'],sdc)
                self.assertEqual(resources['HP']['value'],12)
                view=app.skill_view(hero['id'])
                grants={row['id']:row.get('percentage') for row in view['grants']}
                self.assertEqual([grants[key] for key in ('native-language','basic-electronics','basic-mechanics',
                    'general-repair','land-navigation','radio-basic','sensory-equipment','weapon-systems')],
                    [95,40,45,45,42,55,40,50])
                self.assertEqual([view['remaining'][pool] for pool in ('mos','related','secondary')],[3,7,2])
                app.die=self.no_roll
                choices=[]
                for skill,specialty in (('language-other','Spanish'),('language-other','French'),('robots-power-armor','')):
                    choices.append({'skill_id':skill,'pool':'mos','specialty':specialty})
                    hero=app.select_skills(hero['id'],revision=hero['revision'],selections=choices)
                view=app.skill_view(hero['id'])
                self.assertEqual(view['remaining']['mos'],0)
                self.assertTrue(all(row['remaining']==0 for row in view['pool_requirements']))
                self.assertEqual([row['percentage'] for row in view['selected']],[70,70,56])
                self.assertEqual(view['warnings'],[])
                shooting={row['id']:row for row in app.combat_view(hero['id'])['shooting']}
                self.assertTrue(all(shooting[key]['trained'] for key in ('energy-pistol','energy-rifle','heavy-mega-damage')))

    def test_variable_awards_medical_limit_and_style_weapon_costs(self):
        with tempfile.TemporaryDirectory() as directory:
            app=self.app(directory)
            hero=app.create(character_class='glitter-boy')
            hero=app.generate_resources(hero['id'],revision=hero['revision'])
            hero=app.advance(hero['id'],revision=hero['revision'],method='xp',value=4301)
            view=app.skill_view(hero['id'])
            self.assertEqual(hero['level'],3)
            self.assertEqual([view['remaining'][pool] for pool in ('related','secondary')],[9,4])
            hero=app.advance(hero['id'],revision=hero['revision'],method='xp',value=35701)
            view=app.skill_view(hero['id'])
            self.assertEqual(hero['level'],7)
            self.assertEqual([view['remaining'][pool] for pool in ('related','secondary')],[10,6])
            app.die=self.no_roll
            hero=app.select_combat(hero['id'],revision=hero['revision'],choices={
                'hand_to_hand':'martial-arts','ancient':['knife'],'modern':[]})
            self.assertEqual(app.combat_view(hero['id'])['related_cost'],3)
            hero=app.select_skills(hero['id'],revision=hero['revision'],selections=[
                {'skill_id':skill,'pool':'related','specialty':''} for skill in ('first-aid','paramedic')])
            view=app.skill_view(hero['id'])
            self.assertEqual(view['remaining']['related'],4)
            self.assertTrue(any('choose at most 1' in warning for warning in view['warnings']))
            self.assertEqual(len(hero['skill_selections']),2)

    def test_source_funds_complete_stored_armor_and_exact_no_roll_portability(self):
        with tempfile.TemporaryDirectory() as directory, tempfile.TemporaryDirectory() as copied:
            app=self.app(directory)
            hero=app.create(character_class='glitter-boy-family')
            hero=app.generate_resources(hero['id'],revision=hero['revision'])
            hero=app.generate_starting_funds(hero['id'],revision=hero['revision'])
            self.assertEqual(hero['equipment']['credits'],1200)
            hero=app.grant_starting_gear(hero['id'],revision=hero['revision'])
            app.die=self.no_roll
            hero=app.grant_starting_group(hero['id'],revision=hero['revision'],group_id='glitter-boy',selection='usa-g10-glitter-boy')
            vehicle=next(row for row in hero['equipment']['items'] if row['item_id']=='usa-g10-glitter-boy')
            self.assertEqual((vehicle['location'],vehicle['equipped']),('stored',False))
            self.assertEqual(hero['attributes']['PS']['value'],9)
            self.assertEqual(app.resource_view(hero['id'])['resources']['SDC']['value'],38)
            view=app.equipment_view(hero['id'])
            self.assertEqual(view['armor'],[])
            model=next(row for row in view['catalog'] if row['id']=='usa-g10-glitter-boy')
            self.assertIsNone(model['cost_credits'])
            self.assertEqual(model['category'],'gear')
            self.assertIsNone(model['weight_lbs'])
            self.assertIn('main body 770',model['description'])
            self.assertIn('1000-shot',model['description'])
            inventory_edit=deepcopy(hero['equipment'])
            moved=next(row for row in inventory_edit['items'] if row['item_id']=='usa-g10-glitter-boy')
            moved.update(location='carried',equipped=True)
            hero=app.set_equipment(hero['id'],revision=hero['revision'],inventory=inventory_edit)
            edited=app.equipment_view(hero['id'])
            self.assertEqual(edited['armor'],[])
            self.assertEqual(edited['carried_weight_lbs'],0)
            self.assertEqual(app.resource_view(hero['id'])['resources']['SDC']['value'],38)
            inventory={row['item_id']:row for row in hero['equipment']['items']}
            self.assertEqual([inventory[key]['quantity'] for key in ('gb-fatigues','gb-signal-flare','gb-smoke-grenade')],[2,6,2])
            other=CharacterApplication(copied,die=self.no_roll,rule_archive=self.archive())
            restored=other.import_character(app.export_character(hero['id']))
            ignored={'id','revision','updated_at','copied_from'}
            self.assertEqual({key:value for key,value in restored.items() if key not in ignored},
                             {key:value for key,value in hero.items() if key not in ignored})

    def test_invalid_inactive_variable_awards_and_category_limits_reject_before_dice(self):
        original=self.archive()
        invalid_cases: tuple[tuple[str,object],...]=(
            ('related_award_counts',{'3':True}),('related_award_counts',{'3':0}),
            ('related_award_counts',{'03':2}),('related_award_counts',{'4':2}),
            ('related_award_counts',[]),('max_choices',True),('max_choices',1.0),
            ('max_choices',-1),('max_choices',1001),('max_choices',None))
        for field,invalid in invalid_cases:
            with self.subTest(field=field,invalid=invalid), tempfile.TemporaryDirectory() as directory:
                definitions=deepcopy(original.definitions())
                version=original.active_versions()['rifts-domestic-skills']
                pack=next(row for row in definitions if row['id']=='rifts-domestic-skills' and row['version']==version)
                profile=pack['class_profiles']['glitter-boy']
                if field=='max_choices':
                    profile['selection_rules']['related']['medical'][field]=invalid
                else:
                    profile['higher_advancement'][field]=invalid
                app=CharacterApplication(directory,die=self.no_roll,
                    rule_archive=RuleArchive(definitions,original.active_versions()))
                with self.assertRaises(ValueError):
                    app.create(character_class='vagabond')
                self.assertEqual(app.list(),[])
