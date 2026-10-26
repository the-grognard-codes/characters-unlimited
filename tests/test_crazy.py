"""Original RUE55-57/267-268/285/295/316-317 Human Frenzy witnesses."""

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


IDENTITY = 'crazy-frenzy'
ABILITY = 'rifts-crazy-frenzy-psionics'
CANDIDATES = ('rifts-core-1.21.0.json', 'rifts-domestic-skills-2.42.0.json',
              'rifts-equipment-1.28.0.json', 'rifts-crazy-frenzy-psionics-1.0.0.json')
PARENTS = {'rifts-core': '1.20.0', 'rifts-domestic-skills': '2.41.0', 'rifts-equipment': '1.27.0'}
RELATED = ('art', 'demolitions', 'demolitions-disposal', 'pick-locks', 'palming', 'pick-pockets', 'math-basic')
SECONDARY = ('literacy-native', 'computer-repair', 'basic-electronics', 'first-aid', 'cook', 'housekeeping')
POWERS = ('mind-block', 'sense-evil', 'telepathy')
TRIGGERS = tuple('crazy-frenzy-' + key for key in ('frustration', 'anger', 'pain', 'sorrow', 'tension-anxiety'))
GEAR_CHOICES = {'armor': 'juicer-assassin-plate', 'hatchet': 'crazy-hatchet', 'knives': 'knife-large',
                'ancient-1': 'knife-large', 'ancient-2': 'vibro-saber', 'vibro-knife': 'vibro-knife',
                'pistol': 'wilks-320', 'rifle': 'wilks-447'}


def candidate_archive():
    installed = RuleArchive.load()
    folder = Path(__file__).resolve().parents[1] / 'characters_unlimited/packs'
    candidates = [json.loads((folder / filename).read_text(encoding='utf-8')) for filename in CANDIDATES]
    keys = {(pack['id'], pack['version']) for pack in candidates}
    return RuleArchive([*[pack for pack in installed.definitions() if (pack['id'], pack['version']) not in keys],
                        *candidates], {**installed.active_versions(), **{p['id']: p['version'] for p in candidates}})


def choices(identities, pool='related'):
    return [{'skill_id': identity, 'pool': pool, 'specialty': ''} for identity in identities]


class CrazyTests(unittest.TestCase):
    def app(self, directory):
        return CharacterApplication(directory, die=lambda sides: 4, rule_archive=candidate_archive())

    def no_roll(self, sides):
        self.fail('Retained source receipts must not draw dice')

    def complete(self, app, hero):
        hero = app.select_required_skills(hero['id'], revision=hero['revision'], choices={'native_language': 'American'})
        hero = app.select_skills(hero['id'], revision=hero['revision'], selections=[
            *choices(RELATED), *choices(SECONDARY, 'secondary'),
            {'skill_id': 'language-other', 'pool': 'language', 'specialty': 'Spanish'}])
        hero = app.select_combat(hero['id'], revision=hero['revision'], choices={
            'hand_to_hand': 'martial-arts', 'ancient': ['knife', 'sword'], 'modern': ['energy-pistol', 'rifles']})
        return app.select_class_psionics(hero['id'], revision=hero['revision'], selections=[*POWERS, TRIGGERS[0]])

    def test_independent_source_attributes_reserves_required_checks_and_saves(self):
        with tempfile.TemporaryDirectory() as directory:
            app = self.app(directory)
            calls = []
            def die(sides):
                calls.append(sides)
                return 4
            app.die = die
            hero = app.create(character_class=IDENTITY)
            self.assertNotIn(100, calls)
            hero = app.generate_resources(hero['id'], revision=hero['revision'])
            self.assertEqual({key: row['value'] for key, row in hero['attributes'].items()},
                {'IQ': 12, 'ME': 12, 'MA': 12, 'PS': 22, 'PP': 17, 'PE': 18, 'PB': 12, 'SPD': 28})
            self.assertEqual({key: row['value'] for key, row in app.resource_view(hero['id'])['resources'].items()},
                             {'HP': 42, 'SDC': 148, 'PPE': 24})
            psychic = app.psionic_view(hero['id'])
            self.assertEqual(psychic['effective']['resources']['ISP']['value'], 36)
            self.assertEqual(psychic['effective']['save_target'], 12)
            grants = {row['id']: row for row in app.skill_view(hero['id'])['grants']}
            expected = {'native-language': 95, 'climbing': 65, 'dance': 45, 'detect-ambush': 40,
                'detect-concealment': 40, 'electronic-countermeasures': 40, 'escape-artist': 40,
                'gymnastics': 70, 'land-navigation': 46, 'prowl': 50, 'radio-basic': 55,
                'streetwise': 30, 'tailing': 50, 'swimming': 70}
            self.assertEqual({key: grants[key]['percentage'] for key in expected}, expected)
            gym = {row['name']: row['percentage'] for row in grants['gymnastics']['additional_checks']}
            self.assertEqual({key: gym[key] for key in ('Parallel bars and rings', 'Back flip', 'Climb rope and rappel')},
                             {'Parallel bars and rings': 80, 'Back flip': 90, 'Climb rope and rappel': 80})
            self.assertEqual(grants['climbing']['additional_checks'][0]['percentage'], 55)
            combat = app.combat_view(hero['id'])
            self.assertEqual({key: combat['totals'][key]['value'] for key in
                ('attacks', 'initiative', 'roll_with_impact', 'pull_punch', 'disarm', 'strike', 'parry', 'dodge')},
                {'attacks': 5, 'initiative': 2, 'roll_with_impact': 9, 'pull_punch': 3, 'disarm': 0,
                 'strike': 1, 'parry': 1, 'dodge': 1})
            saves = {key: row['value'] for key, row in combat['saving_bonuses'].items()}
            self.assertEqual({key: saves[key] for key in ('psionics', 'possession', 'mind_control', 'poison', 'drugs', 'disease', 'coma_death', 'magic')},
                {'psionics': 2, 'possession': 2, 'mind_control': 6, 'poison': 6, 'drugs': 6, 'disease': 6, 'coma_death': 21, 'magic': 2})
            self.assertIsNone(combat['totals']['damage']['value'])
            self.assertEqual(combat['strength']['type'], 'augmented')
            self.assertTrue(all('descriptive' in row['damage'] for row in combat['unarmed']))

    def test_complete_source_training_and_delicate_touch_in_secondary_and_synergies(self):
        with tempfile.TemporaryDirectory() as directory:
            app = self.app(directory)
            hero = self.complete(app, app.create(character_class=IDENTITY))
            view = app.skill_view(hero['id'])
            self.assertEqual(view['remaining'], {'language': 0, 'related': 0, 'secondary': 0})
            self.assertFalse(view['warnings'])
            selected = {row['id']: row for row in view['selected']}
            expected = dict(zip(RELATED, (45, 75, 75, 50, 35, 45, 45)))
            expected.update(zip(SECONDARY, (40, 40, 40, 45, 35, 35)))
            expected['language-other'] = 65
            self.assertEqual({key: selected[key]['percentage'] for key in expected}, expected)
            self.assertEqual(selected['computer-repair']['additional_checks'][0]['percentage'], 40)
            hero = app.select_skills(hero['id'], revision=hero['revision'], selections=[
                *choices(('art', 'forgery')), *choices(('sewing',), 'secondary')])
            selected = {row['id']: row['percentage'] for row in app.skill_view(hero['id'])['selected']}
            self.assertEqual(selected, {'art': 45, 'forgery': 50, 'sewing': 50})

    def test_disjoint_psychic_and_trigger_awards_all_five_choices_and_exclusions(self):
        with tempfile.TemporaryDirectory() as directory:
            app = self.app(directory)
            hero = app.create(character_class=IDENTITY)
            view = app.psionic_view(hero['id'])['class_entitlement']
            catalog = {row['id']: row for row in view['catalog']}
            self.assertFalse(set(catalog) & {'astral-projection', 'ectoplasm', 'object-read', 'telekinesis'})
            self.assertEqual(catalog['meditation']['tags'], ['Physical', 'Sensitive'])
            self.assertEqual(catalog['resist-fatigue']['tags'], ['Physical'])
            self.assertEqual(set(view['known_abilities']), {'crazy-enhanced-senses', 'crazy-bio-regeneration'})
            app.die = self.no_roll
            reserve = deepcopy(hero['class_psionics']['resource_record'])
            for trigger in TRIGGERS:
                hero = app.select_class_psionics(hero['id'], revision=hero['revision'], selections=[*POWERS, trigger])
                view = app.psionic_view(hero['id'])['class_entitlement']
                self.assertEqual(view['selection_group']['remaining'], 0)
                awards = {row['id']: row for row in view['learning_awards']['awards']}
                self.assertEqual(awards['initial-psychic']['remaining'], 0)
                self.assertEqual(awards['initial-frenzy']['remaining'], 0)
                self.assertIn('Character trait, not a psychic power; no ISP cost', catalog[trigger]['description'])
                self.assertEqual(hero['class_psionics']['resource_record'], reserve)
            hero = app.select_class_psionics(hero['id'], revision=hero['revision'], selections=list(TRIGGERS[:4]))
            view = app.psionic_view(hero['id'])['class_entitlement']
            awards = {row['id']: row for row in view['learning_awards']['awards']}
            self.assertEqual(awards['initial-psychic']['remaining'], 3)
            self.assertTrue(view['guidance'])
            before = app.get(hero['id'])
            for excluded in ('astral-projection', 'ectoplasm', 'object-read', 'telekinesis'):
                with self.assertRaises(ValueError):
                    app.select_class_psionics(hero['id'], revision=hero['revision'], selections=[excluded])
                self.assertEqual(app.get(hero['id']), before)

    def test_category_restrictions_family_wps_and_source_style_costs(self):
        with tempfile.TemporaryDirectory() as directory:
            app = self.app(directory)
            hero = self.complete(app, app.create(character_class=IDENTITY))
            pack = app.character_skill_pack(hero)
            catalog = {row['id']: row for row in pack['skills']}
            for identity, allowed, bonus in [('branding', False, 0), ('basic-electronics', False, 0),
                ('automotive-mechanics', True, 0), ('locksmith', True, 0), ('basic-mechanics', False, 0),
                ('first-aid', True, 10), ('paramedic', True, 10), ('medical-doctor', False, 0),
                ('forgery', True, 10), ('camouflage', True, 5), ('motorcycle', True, 5),
                ('navigation', True, 0), ('prowl', True, 5), ('astronomy-navigation', True, 0), ('biology', False, 0)]:
                policy = selection_policy(catalog[identity], 'related', pack)
                self.assertEqual((policy['allowed'], policy['bonus']), (allowed, bonus), identity)
            for style, cost in [('martial-arts', 0), ('assassin', 0), ('commando', 2)]:
                hero = app.select_combat(hero['id'], revision=hero['revision'], choices={
                    'hand_to_hand': style, 'ancient': ['knife', 'sword'], 'modern': ['energy-pistol', 'rifles']})
                self.assertEqual(app.combat_view(hero['id'])['related_cost'], cost)
                self.assertEqual(app.skill_view(hero['id'])['remaining']['related'], -cost)
            hero = app.select_combat(hero['id'], revision=hero['revision'], choices={
                'hand_to_hand': 'martial-arts', 'ancient': ['knife', 'sword', 'blunt'], 'modern': ['energy-pistol', 'rifles']})
            self.assertEqual(app.combat_view(hero['id'])['related_cost'], 1)
            for style in ('basic', 'expert'):
                with self.assertRaises(ValueError):
                    app.select_combat(hero['id'], revision=hero['revision'], choices={'hand_to_hand': style})
            hero = app.select_skills(hero['id'], revision=hero['revision'], selections=choices(('biology', 'branding')))
            self.assertEqual(len(hero['skill_selections']), 2)
            self.assertGreaterEqual(len(app.skill_view(hero['id'])['warnings']), 2)

    def test_initial_gear_source_quantities_independent_funds_and_crazy_armor(self):
        with tempfile.TemporaryDirectory() as directory:
            app = self.app(directory)
            hero = self.complete(app, app.create(character_class=IDENTITY))
            hero = app.generate_starting_funds(hero['id'], revision=hero['revision'])
            hero = app.grant_starting_gear(hero['id'], revision=hero['revision'])
            for group, option in GEAR_CHOICES.items():
                hero = app.grant_starting_group(hero['id'], revision=hero['revision'], group_id=group, selection=option)
            inventory = deepcopy(hero['equipment'])
            for possession in inventory['items']:
                possession['equipped'] = possession['item_id'] == 'juicer-assassin-plate'
            hero = app.set_equipment(hero['id'], revision=hero['revision'], inventory=inventory)
            view = app.equipment_view(hero['id'])
            self.assertEqual(view['inventory']['credits'], 800)
            self.assertEqual(hero['starting_funds']['saleable_goods']['value'], 4000)
            items = view['items']
            self.assertEqual(sum(row['quantity'] for row in items if row['item_id'] == 'knife-large'), 5)
            self.assertEqual(sum(row['quantity'] for row in items if row['item_id'] == 'standard-e-clip'), 8)
            self.assertEqual(sum(row['quantity'] for row in items if row['item_id'] == 'crazy-canteen'), 2)
            self.assertFalse(any(row['category'] == 'vehicle' for row in items))
            self.assertEqual(len(hero['starting_equipment_groups']), 8)
            armor = view['armor'][0]
            self.assertEqual((armor['locations']['main_body'], armor['movement_penalty'], armor['prowl_penalty']),
                             (45, -5, -5))
            self.assertEqual(hero['starting_equipment_groups']['knives']['grants'][0]['rolls'], [4])
            for key in ('pistol', 'rifle'):
                spare = hero['starting_equipment_groups'][key]['grants'][1]
                self.assertEqual((spare['quantity'], spare['rolls']), (4, []))
            app.die = self.no_roll
            for group, option in GEAR_CHOICES.items():
                with self.assertRaises(ValueError):
                    app.grant_starting_group(hero['id'], revision=hero['revision'], group_id=group, selection=option)
            imported = app.import_character(app.export_character(hero['id']))
            self.assertEqual(app.equipment_view(imported['id']), view)

    def test_growth_source_awards_retained_undo_reopen_and_portability(self):
        with tempfile.TemporaryDirectory() as directory, tempfile.TemporaryDirectory() as target:
            app = self.app(directory)
            hero = self.complete(app, app.create(character_class=IDENTITY))
            hero = app.generate_resources(hero['id'], revision=hero['revision'])
            receipts = deepcopy(hero['physical_acquisitions'])
            hero = app.advance(hero['id'], revision=hero['revision'], method='xp', value=4281)
            self.assertEqual(hero['level'], 3)
            self.assertEqual(app.resource_view(hero['id'])['resources']['HP']['value'], 50)
            self.assertEqual(app.psionic_view(hero['id'])['effective']['resources']['ISP']['value'], 44)
            self.assertEqual(app.skill_view(hero['id'])['remaining'], {'language': 0, 'related': 2, 'secondary': 1})
            expected = {method: getattr(app, method)(hero['id']) for method in
                        ('skill_view', 'combat_view', 'resource_view', 'equipment_view', 'psionic_view')}
            app.die = self.no_roll
            hero = app.undo_advancement(hero['id'], revision=hero['revision'])['character']
            hero = app.advance(hero['id'], revision=hero['revision'], method='xp', value=4281)
            self.assertEqual(hero['physical_acquisitions'], receipts)
            reopened = CharacterApplication(directory, die=self.no_roll, rule_archive=candidate_archive())
            receiving = CharacterApplication(target, die=self.no_roll, rule_archive=candidate_archive())
            imported = receiving.import_character(reopened.export_character(hero['id']))
            self.assertEqual(imported['class_psionics'], hero['class_psionics'])
            for method, value in expected.items():
                self.assertEqual(getattr(receiving, method)(imported['id']), value)

    def test_level_fifteen_and_class_roll_milestones(self):
        with tempfile.TemporaryDirectory() as directory:
            app = self.app(directory)
            hero = app.create(character_class=IDENTITY)
            hero = app.generate_resources(hero['id'], revision=hero['revision'])
            hero = app.advance(hero['id'], revision=hero['revision'], method='xp', value=341601)
            self.assertEqual(hero['level'], 15)
            self.assertEqual({key: row['value'] for key, row in app.resource_view(hero['id'])['resources'].items()},
                             {'HP': 98, 'SDC': 148, 'PPE': 24})
            self.assertEqual(app.psionic_view(hero['id'])['effective']['resources']['ISP']['value'], 92)
            contributions = app.combat_view(hero['id'])['totals']['roll_with_impact']['contributions']
            self.assertEqual(contributions['O.C.C.'], 12)

    def test_natural_psionics_add_powers_without_replacing_or_summing_class_isp(self):
        with tempfile.TemporaryDirectory() as directory:
            app = self.app(directory)
            hero = app.create(character_class=IDENTITY)
            original = deepcopy(hero['class_psionics']['resource_record'])
            app.die = lambda sides: 15 if sides == 100 else 4
            hero = app.select_psionics(hero['id'], revision=hero['revision'], roll=True)
            app.die = self.no_roll
            hero = app.select_psionics(hero['id'], revision=hero['revision'], enabled=True,
                mode='single', categories=['Sensitive'], selections=['sense-time', 'total-recall'])
            view = app.psionic_view(hero['id'])
            self.assertEqual(view['effective']['resources']['ISP']['value'], 36)
            self.assertEqual(hero['class_psionics']['resource_record'], original)
            self.assertTrue({'sense-time', 'total-recall'} <= {row['id'] for row in view['effective']['abilities']})
            hero = app.select_psionics(hero['id'], revision=hero['revision'], enabled=False)
            self.assertEqual(app.psionic_view(hero['id'])['effective']['resources']['ISP']['value'], 36)

    def test_unsupported_pairings_and_malformed_inactive_dependency_reject_before_dice(self):
        with tempfile.TemporaryDirectory() as directory:
            app = self.app(directory)
            app.die = self.no_roll
            for race in ('psi-stalker', 'dog-boy'):
                with self.assertRaises(ValueError):
                    app.create(race=race, character_class=IDENTITY)
            archive = candidate_archive()
            definitions = archive.definitions()
            for row in definitions:
                if row['id'] == ABILITY:
                    row['paths'][0]['allowances']['class']['awards'][1]['categories'] = ['Unknown']
            broken = RuleArchive(definitions, archive.active_versions())
            app = CharacterApplication(directory, die=self.no_roll, rule_archive=broken)
            with self.assertRaises(ValueError):
                app.create(character_class='vagabond')
            self.assertFalse(app.list())

    def test_temporary_trait_and_inherent_guidance_survive_editable_pdf_without_changing_base(self):
        with tempfile.TemporaryDirectory() as directory:
            app = self.app(directory)
            hero = self.complete(app, app.create(character_class=IDENTITY))
            hero = app.generate_resources(hero['id'], revision=hero['revision'])
            fields = PdfReader(BytesIO(app.export_pdf(hero['id']))).get_fields() or {}
            text = ' '.join(str(row.get('/V', '')) for row in fields.values())
            for phrase in ('Frenzy: Intense Frustration', 'not a psychic power', '+30SDC', 'twice normal',
                           'Crazy Bio-Regeneration', 'helpless', 'Augmented Strength'):
                self.assertIn(phrase, text)
            self.assertEqual(app.resource_view(hero['id'])['resources']['SDC']['value'], 148)
            self.assertEqual(app.combat_view(hero['id'])['totals']['attacks']['value'], 5)

    def test_whole_parents_preserved_except_new_owner_and_explicit_armor_wearer(self):
        archive = candidate_archive()
        for identity, version in PARENTS.items():
            before = archive.resolve(identity, version)
            after = archive.active(identity)
            expected = deepcopy(before)
            expected['version'] = after['version']
            if identity == 'rifts-core':
                self.assertEqual(after['classes'][:-1], before['classes'])
                expected['classes'].append(after['classes'][-1])
                human = next(row for row in expected['creation_profiles'] if row['race'] == 'human')
                human['classes'].append(IDENTITY)
                human['source']['pages'] = sorted(set(human['source']['pages']) | {55, 56, 57})
                human['source']['pdf_pages'] = [page + 3 for page in human['source']['pages']]
            else:
                expected['class_profiles'][IDENTITY] = after['class_profiles'][IDENTITY]
                if identity == 'rifts-equipment':
                    armor = next(row for row in expected['items'] if row['id'] == 'juicer-assassin-plate')
                    armor['movement_penalty_by_class'][IDENTITY] = -5
                    armor['protection_notes'][0] = 'Non-environmental. Source penalty is5% for a Juicer or Crazy and10% for others; wearer-aware rules preserve that distinction.'
                    expected['items'] += after['items'][len(before['items']):]
            self.assertEqual(after, expected, identity)

    def test_older_juicer_and_cyber_knight_outputs_keep_exact_pins(self):
        installed = RuleArchive.load()
        baseline = RuleArchive(installed.definitions(), {**installed.active_versions(), **PARENTS})
        for identity in ('juicer-classic', 'cyber-knight-minor'):
            with self.subTest(identity=identity), tempfile.TemporaryDirectory() as directory, tempfile.TemporaryDirectory() as target:
                old = CharacterApplication(directory, die=lambda sides: 4, rule_archive=baseline)
                hero = old.create(character_class=identity)
                hero = old.generate_resources(hero['id'], revision=hero['revision'])
                hero = old.set_equipment(hero['id'], revision=hero['revision'], inventory={'credits': 0, 'items': []})
                expected = {method: getattr(old, method)(hero['id']) for method in
                            ('skill_view', 'combat_view', 'resource_view', 'equipment_view', 'psionic_view')}
                new = CharacterApplication(target, die=self.no_roll, rule_archive=candidate_archive())
                imported = new.import_character(old.export_character(hero['id']))
                self.assertEqual(imported['rules'], hero['rules'])
                self.assertEqual(imported['additional_rule_packs'], hero['additional_rule_packs'])
                for method, value in expected.items():
                    self.assertEqual(getattr(new, method)(imported['id']), value)
