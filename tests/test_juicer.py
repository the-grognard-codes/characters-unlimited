"""Independent original RUE79-81/267/270/285/295/316-317 Juicer witnesses."""

from copy import deepcopy
from io import BytesIO
import json
from pathlib import Path
import tempfile
import unittest

from pypdf import PdfReader
from characters_unlimited.application import CharacterApplication
from characters_unlimited.rules import RuleArchive
from characters_unlimited.skill_choices import selection_policy


IDENTITY = 'juicer-classic'
CANDIDATES = ('rifts-core-1.20.0.json', 'rifts-domestic-skills-2.41.0.json', 'rifts-equipment-1.27.0.json')
PARENTS = {'rifts-core': '1.19.0', 'rifts-domestic-skills': '2.40.0', 'rifts-equipment': '1.26.0'}
RELATED = ('prowl', 'first-aid', 'math-basic', 'computer-operation', 'detect-ambush',
           'intelligence', 'camouflage', 'literacy-native')
GEAR_CHOICES = {'armor': 'juicer-assassin-plate', 'named-rifle': 'ja-11', 'pistol': 'wilks-320',
                'vibro-knife': 'vibro-knife', 'portable-irmss': 'body-fixer-irmss',
                'non-energy-weapon': 'knife-large', 'wp-knife': 'vibro-knife',
                'wp-energy-rifle': 'wilks-447', 'wp-energy-pistol': 'cs-c18',
                'wp-weapon-1': 'vibro-saber', 'wp-weapon-2': 'gaw-m16a2-20'}


def candidate_archive():
    installed = RuleArchive.load()
    folder = Path(__file__).resolve().parents[1] / 'characters_unlimited/packs'
    candidates = [json.loads((folder / filename).read_text(encoding='utf-8')) for filename in CANDIDATES]
    keys = {(pack['id'], pack['version']) for pack in candidates}
    return RuleArchive([*[pack for pack in installed.definitions() if (pack['id'], pack['version']) not in keys],
                        *candidates], {**installed.active_versions(), **{p['id']: p['version'] for p in candidates}})


def choices(identities, *, pool='related'):
    return [{'skill_id': identity, 'pool': pool, 'specialty': ''} for identity in identities]


class JuicerTests(unittest.TestCase):
    def app(self, directory):
        return CharacterApplication(directory, die=lambda sides: 4, rule_archive=candidate_archive())

    def no_roll(self, sides):
        self.fail('Exact source replay must not draw dice')

    def complete(self, app, hero):
        hero = app.select_required_skills(hero['id'], revision=hero['revision'], choices={'native_language': 'American'})
        hero = app.select_skills(hero['id'], revision=hero['revision'], selections=[
            *choices(RELATED), *choices(('cook', 'dance'), pool='secondary'),
            {'skill_id': 'language-other', 'pool': 'language', 'specialty': 'Spanish'},
            {'skill_id': 'language-other', 'pool': 'language', 'specialty': 'Chinese'},
            *choices(('motorcycle', 'hovercycle'), pool='pilot')])
        return app.select_combat(hero['id'], revision=hero['revision'],
            choices={'hand_to_hand': 'expert', 'ancient': ['sword'], 'modern': ['rifles']})

    def test_source_attributes_resources_required_percentages_and_class_bonuses(self):
        with tempfile.TemporaryDirectory() as directory:
            app = self.app(directory)
            hero = app.create(character_class=IDENTITY)
            self.assertEqual({key: row['value'] for key, row in hero['attributes'].items()},
                {'IQ': 12, 'ME': 12, 'MA': 12, 'PS': 22, 'PP': 13, 'PE': 22, 'PB': 12, 'SPD': 108})
            hero = app.generate_resources(hero['id'], revision=hero['revision'])
            resources = app.resource_view(hero['id'])['resources']
            self.assertEqual({key: row['value'] for key, row in resources.items()}, {'HP': 66, 'SDC': 428})
            grants = {row['id']: row for row in app.skill_view(hero['id'])['grants']}
            expected = {'native-language': 92, 'acrobatics': 75, 'climbing': 75, 'land-navigation': 41,
                        'radio-basic': 55, 'recognize-weapon-quality': 35, 'swimming': 60, 'wilderness-survival': 35}
            self.assertEqual({key: grants[key]['percentage'] for key in expected}, expected)
            combat = app.combat_view(hero['id'])
            self.assertEqual({key: combat['totals'][key]['value'] for key in
                ('attacks', 'initiative', 'disarm', 'pull_punch', 'roll_with_impact', 'dodge')},
                {'attacks': 6, 'initiative': 4, 'disarm': 2, 'pull_punch': 4, 'roll_with_impact': 7, 'dodge': 0})
            saves = {identity: row['value'] for identity, row in combat['saving_bonuses'].items()}
            self.assertEqual({key: saves[key] for key in ('psionics', 'mind_control', 'poison', 'drugs', 'coma_death')},
                             {'psionics': 4, 'mind_control': 6, 'poison': 12, 'drugs': 12, 'coma_death': 34})
            self.assertIsNone(combat['totals']['damage']['value'])
            self.assertEqual(combat['strength']['type'], 'augmented')
            self.assertTrue(all('descriptive' in row['damage'] for row in combat['unarmed']))
            self.assertNotIn('strength_type', hero)

    def test_complete_named_pools_wp_and_source_style_costs(self):
        with tempfile.TemporaryDirectory() as directory:
            app = self.app(directory)
            hero = self.complete(app, app.create(character_class=IDENTITY))
            view = app.skill_view(hero['id'])
            self.assertEqual(view['remaining'], {'language': 0, 'pilot': 0, 'related': 0, 'secondary': 0})
            self.assertFalse(view['warnings'])
            selected = {row['id']: row['percentage'] for row in view['selected']}
            self.assertEqual({key: selected[key] for key in ('prowl', 'first-aid', 'math-basic', 'computer-operation',
                                                            'language-other', 'motorcycle', 'hovercycle')},
                {'prowl': 45, 'first-aid': 45, 'math-basic': 45, 'computer-operation': 40,
                 'language-other': 60, 'motorcycle': 70, 'hovercycle': 80})
            combat = app.combat_view(hero['id'])
            self.assertEqual({family: combat['fixed_proficiencies'][family] for family in ('ancient', 'modern')},
                             {'ancient': ['knife'], 'modern': ['energy-rifle', 'energy-pistol']})
            self.assertEqual(combat['fixed_proficiencies']['source']['pages'], [81])
            for style, cost in [('expert', 0), ('martial-arts', 1), ('assassin', 1)]:
                hero = app.select_combat(hero['id'], revision=hero['revision'],
                    choices={'hand_to_hand': style, 'ancient': ['sword'], 'modern': ['rifles']})
                self.assertEqual(app.combat_view(hero['id'])['related_cost'], cost)
                self.assertEqual(app.skill_view(hero['id'])['remaining']['related'], -cost)
            with self.assertRaises(ValueError):
                app.select_combat(hero['id'], revision=hero['revision'], choices={'hand_to_hand': 'basic'})

    def test_source_category_rules_and_honor_system_retention(self):
        with tempfile.TemporaryDirectory() as directory:
            app = self.app(directory)
            hero = app.create(character_class=IDENTITY)
            pack = app.character_skill_pack(hero)
            catalog = {row['id']: row for row in pack['skills']}
            for identity, allowed, bonus in [('branding', False, 0), ('trick-riding', True, 0),
                ('biology', False, 0), ('math-advanced', True, 0), ('aircraft-mechanics', False, 0),
                ('basic-mechanics', True, 0), ('basic-electronics', True, 0), ('forgery', False, 0),
                ('intelligence', True, 5), ('camouflage', True, 10), ('combat-helicopter', True, 5),
                ('motorcycle', True, 0), ('prowl', True, 15), ('gambling-standard', True, 2)]:
                policy = selection_policy(catalog[identity], 'related', pack)
                self.assertEqual((policy['allowed'], policy['bonus']), (allowed, bonus), identity)
            hero = app.select_skills(hero['id'], revision=hero['revision'], selections=choices(('biology', 'branding')))
            view = app.skill_view(hero['id'])
            self.assertEqual(len(hero['skill_selections']), 2)
            self.assertEqual(view['remaining']['related'], 6)
            self.assertGreaterEqual(len(view['warnings']), 2)

    def test_human_path_has_no_prevalence_roll_and_other_race_pairings_reject_before_dice(self):
        with tempfile.TemporaryDirectory() as directory:
            app = self.app(directory)
            calls: list[int] = []
            def die(sides):
                calls.append(sides)
                return 4
            app.die = die
            app.create(character_class=IDENTITY)
            self.assertNotIn(100, calls)
            app.die = self.no_roll
            for race in ('psi-stalker', 'dog-boy'):
                with self.assertRaises(ValueError):
                    app.create(race=race, character_class=IDENTITY)
            self.assertEqual(len(app.list()), 1)

    def test_progression_xp_awards_retained_undo_and_exact_portability(self):
        with tempfile.TemporaryDirectory() as directory, tempfile.TemporaryDirectory() as target:
            app = self.app(directory)
            hero = self.complete(app, app.create(character_class=IDENTITY))
            hero = app.generate_resources(hero['id'], revision=hero['revision'])
            hero = app.advance(hero['id'], revision=hero['revision'], method='xp', value=4281)
            self.assertEqual(hero['level'], 3)
            self.assertEqual(app.resource_view(hero['id'])['resources']['HP']['value'], 74)
            view = app.skill_view(hero['id'])
            self.assertEqual(view['remaining'], {'language': 0, 'pilot': 0, 'related': 1, 'secondary': 2})
            grants = {row['id']: row['percentage'] for row in view['grants'] if 'percentage' in row}
            self.assertEqual((grants['acrobatics'], grants['climbing'], grants['land-navigation']), (85, 85, 49))
            expected = {method: getattr(app, method)(hero['id']) for method in
                        ('skill_view', 'combat_view', 'resource_view', 'equipment_view')}
            app.die = self.no_roll
            hero = app.undo_advancement(hero['id'], revision=hero['revision'])['character']
            hero = app.advance(hero['id'], revision=hero['revision'], method='level', value=3)
            for method, value in expected.items():
                self.assertEqual(getattr(app, method)(hero['id']), value)
            restored_app = CharacterApplication(target, die=self.no_roll, rule_archive=candidate_archive())
            imported = restored_app.import_character(app.export_character(hero['id']))
            for method, value in expected.items():
                self.assertEqual(getattr(restored_app, method)(imported['id']), value)
            self.assertEqual(CharacterApplication(directory, die=self.no_roll, rule_archive=candidate_archive()).get(hero['id']), hero)
            app.die = lambda sides: 4
            hero = app.advance(hero['id'], revision=hero['revision'], method='xp', value=341601)
            self.assertEqual(hero['level'], 15)
            self.assertEqual(app.resource_view(hero['id'])['resources']['HP']['value'], 122)
            self.assertEqual(app.skill_view(hero['id'])['remaining'],
                             {'language': 0, 'pilot': 0, 'related': 5, 'secondary': 10})

    def test_source_funds_fixed_kit_wp_weapons_clip_quantities_and_descriptive_rifle(self):
        with tempfile.TemporaryDirectory() as directory:
            app = self.app(directory)
            hero = self.complete(app, app.create(character_class=IDENTITY))
            calls = []
            def die(sides):
                calls.append(sides)
                return 4
            app.die = die
            hero = app.generate_starting_funds(hero['id'], revision=hero['revision'])
            self.assertEqual(calls, [6] * 8)
            self.assertEqual({key: row['value'] for key, row in hero['starting_funds'].items()},
                             {'credits': 1600, 'saleable_goods': 1600})
            self.assertEqual(hero['equipment']['credits'], 1600)
            calls.clear()
            hero = app.grant_starting_gear(hero['id'], revision=hero['revision'])
            for group_id, selection in GEAR_CHOICES.items():
                hero = app.grant_starting_group(hero['id'], revision=hero['revision'],
                                                group_id=group_id, selection=selection)
            self.assertEqual(calls, [4] * 4)
            receipts = hero['starting_equipment_groups']
            for key, clip in [('named-rifle', 'ja-11-short-eclip'), ('pistol', 'standard-e-clip')]:
                grant = next(row for row in receipts[key]['grants'] if row['item_id'] == clip)
                self.assertEqual((grant['quantity'], grant['rolls']), (8, [4, 4]))
            self.assertEqual(set(receipts), set(GEAR_CHOICES))
            self.assertFalse(any('vehicle' in key or 'transport' in key for key in receipts))
            inventory = deepcopy(hero['equipment'])
            for possession in inventory['items']:
                possession['equipped'] = possession['item_id'] in ('juicer-assassin-plate', 'ja-11')
            hero = app.set_equipment(hero['id'], revision=hero['revision'], inventory=inventory)
            view = app.equipment_view(hero['id'])
            armor = view['armor'][0]
            self.assertEqual((armor['locations']['main_body'], armor['weight_lbs'], armor['movement_penalty'], armor['prowl_penalty']),
                             (45, 14, -5, -5))
            self.assertFalse(armor['environmental'])
            self.assertFalse(any(row['item_id'] == 'ja-11' for row in view['attacks']))
            rifle = next(row for row in view['items'] if row['item_id'] == 'ja-11')
            self.assertIsNone(rifle['shots'])
            self.assertIn('aimed-only', rifle['description'])
            app.die = self.no_roll
            with self.assertRaises(ValueError):
                app.grant_starting_group(hero['id'], revision=hero['revision'], group_id='named-rifle', selection='ja-11')
            self.assertEqual(app.get(hero['id']), hero)
            imported = app.import_character(app.export_character(hero['id']))
            self.assertEqual(app.equipment_view(imported['id']), view)
            fields = PdfReader(BytesIO(app.export_pdf(imported['id']))).get_fields() or {}
            text = ' '.join(str(row.get('/V', '')) for row in fields.values())
            self.assertIn('Augmented Strength', text)
            self.assertIn('JA-11', text)
            self.assertIn('descriptive', text)

    def test_automatic_physical_receipts_do_not_duplicate_and_optional_effects_use_existing_floor(self):
        with tempfile.TemporaryDirectory() as directory:
            app = self.app(directory)
            hero = app.create(character_class=IDENTITY)
            hero = app.generate_resources(hero['id'], revision=hero['revision'])
            before = deepcopy(hero['physical_acquisitions'])
            app.die = self.no_roll
            hero = app.select_skills(hero['id'], revision=hero['revision'], selections=choices(('acrobatics', 'running')))
            self.assertEqual(hero['physical_acquisitions'], before)
            self.assertEqual((hero['attributes']['PE']['value'], hero['attributes']['SPD']['value']), (22, 108))
            hero = app.select_skills(hero['id'], revision=hero['revision'], selections=choices(('body-building',)))
            self.assertEqual(hero['attributes']['PS']['value'], 23)
            resources = app.resource_view(hero['id'])['resources']
            self.assertEqual((resources['HP']['value'], resources['SDC']['value']), (66, 438))

    def test_parent_definitions_preserve_every_unrelated_field_through_production_decoder(self):
        archive = candidate_archive()
        for identity, old_version in PARENTS.items():
            before = archive.resolve(identity, old_version)
            after = archive.active(identity)
            expected = deepcopy(before)
            expected['version'] = after['version']
            if identity == 'rifts-core':
                self.assertEqual(after['classes'][:-1], before['classes'])
                self.assertEqual(after['classes'][-1]['id'], IDENTITY)
                expected['classes'].append(after['classes'][-1])
                old_human = next(row for row in expected['creation_profiles'] if row['race'] == 'human')
                old_human['classes'].append(IDENTITY)
                old_human['source']['pages'] = sorted(set(old_human['source']['pages']) | {79, 80, 81})
                old_human['source']['pdf_pages'] = [page + 3 for page in old_human['source']['pages']]
            else:
                expected['class_profiles'][IDENTITY] = after['class_profiles'][IDENTITY]
                if identity == 'rifts-equipment':
                    self.assertEqual(after['items'][:len(before['items'])], before['items'])
                    expected['items'] += after['items'][len(before['items']):]
            self.assertEqual(after, expected, identity)

    def test_older_city_rat_vagabond_and_dog_boy_public_outputs_keep_exact_pins(self):
        installed = RuleArchive.load()
        baseline = RuleArchive(installed.definitions(), {**installed.active_versions(), **PARENTS})
        for race, identity in [('human', 'city-rat'), ('human', 'vagabond'), ('dog-boy', 'dog-boy-coalition-disarm')]:
            with self.subTest(path=identity), tempfile.TemporaryDirectory() as directory, tempfile.TemporaryDirectory() as target:
                old = CharacterApplication(directory, die=lambda sides: 4, rule_archive=baseline)
                hero = old.create(race=race, character_class=identity)
                hero = old.generate_resources(hero['id'], revision=hero['revision'])
                hero = old.set_equipment(hero['id'], revision=hero['revision'], inventory={'credits': 0, 'items': []})
                expected = {method: getattr(old, method)(hero['id']) for method in
                            ('skill_view', 'combat_view', 'resource_view', 'equipment_view')}
                new = CharacterApplication(target, die=self.no_roll, rule_archive=candidate_archive())
                imported = new.import_character(old.export_character(hero['id']))
                self.assertEqual(imported['rules'], hero['rules'])
                self.assertEqual(imported['additional_rule_packs'], hero['additional_rule_packs'])
                for method, value in expected.items():
                    self.assertEqual(getattr(new, method)(imported['id']), value)
