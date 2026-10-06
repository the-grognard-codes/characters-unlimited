"""Independently calculated RUE printed 233–235 and 295 class witnesses."""
from copy import deepcopy
from io import BytesIO
import tempfile
import unittest

from pypdf import PdfReader

from characters_unlimited.application import CharacterApplication


class CoalitionClassTests(unittest.TestCase):
    def no_roll(self, sides):
        self.fail('Retained class choices and fixed salary must not draw dice')

    def test_starting_attributes_required_skills_and_resources(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides: 3)
            for identity, ps, sdc, related, secondary, expected in [
                ('coalition-grunt', 11, 31, 7, 5, {
                    'native-language': 92, 'climbing': 45, 'military-etiquette': 50,
                    'hover-craft': 60, 'tanks-apcs': 50, 'radio-basic': 55,
                    'sensory-equipment': 40, 'weapon-systems': 50}),
                ('coalition-samas-pilot', 9, 21, 8, 4, {
                    'native-language': 94, 'math-basic': 55, 'military-etiquette': 50,
                    'radio-basic': 55, 'automobile': 75, 'hover-craft': 65,
                    'robots-power-armor': 71, 'sensory-equipment': 45, 'weapon-systems': 55})]:
                with self.subTest(identity=identity):
                    hero = app.create(character_class=identity)
                    self.assertEqual({key: hero['attributes'][key]['value'] for key in ('PS', 'PE', 'SPD')},
                                     {'PS': ps, 'PE': 10, 'SPD': 21})
                    rows = {row['id']: row for row in app.skill_view(hero['id'])['grants']}
                    self.assertEqual({key: rows[key]['percentage'] for key in expected}, expected)
                    self.assertNotIn('percentage', rows['robot-combat-basic'])
                    hero = app.generate_resources(hero['id'], revision=hero['revision'])
                    resources = app.resource_view(hero['id'])['resources']
                    self.assertEqual((resources['SDC']['value'], resources['HP']['value']), (sdc, 13))
                    self.assertEqual(app.skill_view(hero['id'])['remaining'],
                                     {'related': related, 'secondary': secondary})

    def test_higher_awards_xp_and_undo(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides: 3)
            for identity, xp, related, secondary in [('coalition-grunt', 325601, 11, 8),
                                                    ('coalition-samas-pilot', 289001, 16, 8)]:
                hero = app.create(character_class=identity)
                hero = app.generate_resources(hero['id'], revision=hero['revision'])
                hero = app.advance(hero['id'], revision=hero['revision'], method='level', value=15)
                self.assertEqual(hero['experience'], xp)
                self.assertEqual(app.skill_view(hero['id'])['remaining'], {'related': related, 'secondary': secondary})
                app.die = self.no_roll
                hero = app.undo_advancement(hero['id'], revision=hero['revision'])['character']
                self.assertEqual(hero['level'], 14)
                self.assertEqual(app.skill_view(hero['id'])['remaining']['secondary'], secondary - (identity == 'coalition-samas-pilot'))
                self.assertEqual(app.import_character(app.export_character(hero['id']))['advancement'], hero['advancement'])
                app.die = lambda sides: 3

    def test_shared_weapon_allowance_paid_upgrades_and_class_style_provenance(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides: 3)
            for identity, page in [('coalition-grunt', 233), ('coalition-samas-pilot', 234)]:
                hero = app.create(character_class=identity)
                for style, ancient, modern, expected in [
                    ('expert', ['knife'], [], 0), ('martial-arts', ['knife'], [], 2),
                    ('assassin', ['knife', 'sword'], [], 3),
                    ('expert', [], ['energy-pistol', 'energy-rifle', 'handguns'], 0)]:
                    hero = app.select_combat(hero['id'], revision=hero['revision'], choices={
                        'hand_to_hand': style, 'ancient': ancient, 'modern': modern})
                    view = app.combat_view(hero['id'])
                    self.assertEqual(view['related_cost'], expected)
                    chosen = next(row for row in view['catalog']['hand_to_hand'] if row['id'] == style)
                    self.assertEqual(chosen['source']['pages'][0], page)
                    self.assertEqual(chosen['source']['pdf_pages'][0], page + 3)
                app.die = self.no_roll
                self.assertEqual(app.import_character(app.export_character(hero['id']))['combat_choices'], hero['combat_choices'])
                app.die = lambda sides: 3

    def test_related_category_bonuses_include_source_domestic_penalty(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides: 3)
            for identity, expected in [('coalition-grunt', {'cook': 35, 'basic-electronics': 30,
                                                             'field-armorer': 55, 'airplane': 55}),
                                      ('coalition-samas-pilot', {'cook': 30, 'basic-electronics': 35,
                                                               'field-armorer': 50, 'airplane': 65})]:
                hero = app.create(character_class=identity)
                hero = app.select_skills(hero['id'], revision=hero['revision'], selections=[
                    {'skill_id': key, 'pool': 'related'} for key in expected])
                rows = {row['id']: row['percentage'] for row in app.skill_view(hero['id'])['selected']}
                self.assertEqual(rows, expected)
                hero = app.generate_resources(hero['id'], revision=hero['revision'])
                hero = app.advance(hero['id'], revision=hero['revision'], method='level', value=3)
                cook = next(row for row in app.skill_view(hero['id'])['selected'] if row['id'] == 'cook')
                self.assertEqual(cook['percentage'], expected['cook'] + 10)
                app.die = self.no_roll
                self.assertEqual(app.import_character(app.export_character(hero['id']))['skill_selections'], hero['skill_selections'])
                hero = app.select_skills(hero['id'], revision=hero['revision'], selections=[
                    *hero['skill_selections'], {'skill_id': 'cook', 'pool': 'secondary'}])
                cooks = [row for row in app.skill_view(hero['id'])['selected'] if row['id'] == 'cook']
                self.assertEqual([row['percentage'] for row in cooks], [55, 55])
                self.assertTrue(all(row['contributions']['class'] == 0 for row in cooks))
                app.die = lambda sides: 3

    def test_fixed_salary_issued_clip_grenades_and_editable_portable_output(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides: 3)
            for identity, salary in [('coalition-grunt', 1700), ('coalition-samas-pilot', 2000)]:
                hero = app.create(character_class=identity)
                app.die = self.no_roll
                hero = app.generate_starting_funds(hero['id'], revision=hero['revision'])
                self.assertEqual(hero['equipment']['credits'], salary)
                self.assertEqual(set(hero['starting_funds']), {'credits'})
                self.assertEqual(hero['starting_funds']['credits']['rolls'], [])
                hero = app.grant_starting_gear(hero['id'], revision=hero['revision'])
                self.assertEqual(len(hero['starting_gear']['grants']), 8)
                for group, selection in [('pistol', 'cs-c18'), ('rifle', 'cs-c12'),
                                         ('grenades', 'cs-grenade-fragmentation')]:
                    hero = app.grant_starting_group(hero['id'], revision=hero['revision'], group_id=group, selection=selection)
                items = {row['item_id']: row for row in hero['equipment']['items']}
                self.assertEqual(items['cs-pistol-e-clip']['quantity'], 4)
                self.assertEqual(items['cs-pistol-e-clip']['shots'], 10)
                self.assertEqual(items['cs-rifle-e-clip']['quantity'], 4)
                self.assertEqual(items['cs-rifle-e-clip']['shots'], 20)
                self.assertEqual(items['cs-grenade-fragmentation']['quantity'], 2)
                self.assertIsNone(items['cs-grenade-fragmentation']['shots'])
                inventory = deepcopy(hero['equipment'])
                next(row for row in inventory['items'] if row['item_id'] == 'cs-c12')['equipped'] = True
                hero = app.set_equipment(hero['id'], revision=hero['revision'], inventory=inventory)
                attack = next(row for row in app.equipment_view(hero['id'])['attacks'] if row['item_id'] == 'cs-c12')
                self.assertEqual(attack['damage'], '2D6 M.D.')
                before = deepcopy(hero)
                with self.assertRaises(ValueError):
                    app.grant_starting_group(hero['id'], revision=hero['revision'], group_id='grenades', selection='cs-grenade-fragmentation')
                self.assertEqual(app.get(hero['id']), before)
                self.assertEqual(app.import_character(app.export_character(hero['id']))['equipment'], hero['equipment'])
                fields = PdfReader(BytesIO(app.export_pdf(hero['id']))).get_fields()
                assert fields is not None
                text = ' '.join(str(row.get('/V', '')) for row in fields.values())
                self.assertIn('2D4 M.D.', text)
                self.assertIn('CS Fragmentation Grenade', text)
                self.assertIn('Alternate modes: 6D6 M.D. burst or 6D6 S.D.C. setting.', text)
                self.assertNotIn('None/None', text)
                app.die = lambda sides: 3

    def test_issued_armor_and_stored_samas_do_not_replace_human_attributes(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides: 3)
            hero = app.create(character_class='coalition-samas-pilot')
            hero = app.generate_resources(hero['id'], revision=hero['revision'])
            original_attributes = deepcopy(hero['attributes'])
            original_resources = app.resource_view(hero['id'])['resources']
            for group, selection in [('armor', 'cs-ca2'), ('samas', 'cs-samas'),
                                     ('transport', 'cs-military-hovercycle')]:
                hero = app.grant_starting_group(hero['id'], revision=hero['revision'], group_id=group, selection=selection)
            inventory = deepcopy(hero['equipment'])
            next(row for row in inventory['items'] if row['item_id'] == 'cs-ca2')['equipped'] = True
            samas = next(row for row in inventory['items'] if row['item_id'] == 'cs-samas')
            self.assertEqual((samas['location'], samas['equipped']), ('stored', False))
            hero = app.set_equipment(hero['id'], revision=hero['revision'], inventory=inventory)
            self.assertEqual(hero['attributes'], original_attributes)
            self.assertEqual(app.resource_view(hero['id'])['resources'], original_resources)
            view = app.equipment_view(hero['id'])
            self.assertEqual([row['item_id'] for row in view['armor']], ['cs-ca2'])
            self.assertEqual(view['armor'][0]['locations']['main_body'], 50)
            self.assertEqual(view['armor'][0]['movement_penalty'], -5)
            fields = PdfReader(BytesIO(app.export_pdf(hero['id']))).get_fields()
            assert fields is not None
            self.assertEqual(fields['COST']['/V'], '35000–45000')
            self.assertIn('Robot P.S. 30', ' '.join(str(row.get('/V', '')) for row in fields.values()))
