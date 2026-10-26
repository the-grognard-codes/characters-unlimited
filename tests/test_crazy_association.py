"""Original RUE55-58 Human Association creation and retained-source witnesses."""

from copy import deepcopy
from io import BytesIO
import json
from pathlib import Path
import tempfile
import unittest

from pypdf import PdfReader
from characters_unlimited.application import CharacterApplication
from characters_unlimited.rules import RuleArchive
from tests.test_crazy import RELATED, SECONDARY, POWERS, GEAR_CHOICES, choices


ABILITY = 'rifts-crazy-association-psionics'
IDENTITIES = tuple('crazy-association-' + key for key in
                   ('daytime', 'nighttime', 'popeye', 'magic-object', 'power-words', 'solar'))
SOLAR = IDENTITIES[-1]
PARENTS = {'rifts-core': '1.21.0', 'rifts-domestic-skills': '2.42.0', 'rifts-equipment': '1.28.0'}
CANDIDATES = ('rifts-core-1.22.0.json', 'rifts-domestic-skills-2.43.0.json',
              'rifts-equipment-1.29.0.json', ABILITY + '-1.0.0.json')


def candidate_archive():
    installed = RuleArchive.load()
    folder = Path(__file__).resolve().parents[1] / 'characters_unlimited/packs'
    candidates = [json.loads((folder / name).read_text(encoding='utf-8')) for name in CANDIDATES]
    keys = {(p['id'], p['version']) for p in candidates}
    return RuleArchive([*[p for p in installed.definitions() if (p['id'], p['version']) not in keys], *candidates],
                       {**installed.active_versions(), **{p['id']: p['version'] for p in candidates}})


class CrazyAssociationTests(unittest.TestCase):
    def app(self, directory):
        return CharacterApplication(directory, die=lambda sides: 4, rule_archive=candidate_archive())

    def no_roll(self, sides):
        self.fail('Retained source values must not draw dice')

    def complete(self, app, hero):
        hero = app.select_required_skills(hero['id'], revision=hero['revision'], choices={'native_language': 'American'})
        hero = app.select_skills(hero['id'], revision=hero['revision'], selections=[
            *choices(RELATED), *choices(SECONDARY, 'secondary'),
            {'skill_id': 'language-other', 'pool': 'language', 'specialty': 'Spanish'}])
        hero = app.select_combat(hero['id'], revision=hero['revision'], choices={
            'hand_to_hand': 'martial-arts', 'ancient': ['knife', 'sword'], 'modern': ['energy-pistol', 'rifles']})
        return app.select_class_psionics(hero['id'], revision=hero['revision'], selections=list(POWERS))

    def test_all_six_empowered_source_attributes_reserves_perception_and_conditions(self):
        phrases = [('indoors or in darkness',), ('dusk until dawn',),
                   ('Character Notes', 'Pumpkin Seeds', 'Spinach', 'three hours'),
                   ('Character Notes', 'not actually magical', '3D6 weeks'),
                   ('Character Notes', '24 hours', 'repeating'), ('even Secondary Skills', 'Perception remains unchanged')]
        with tempfile.TemporaryDirectory() as directory:
            app = self.app(directory)
            for identity, expected_phrases in zip(IDENTITIES, phrases):
                with self.subTest(identity=identity):
                    hero = app.create(character_class=identity)
                    hero = app.generate_resources(hero['id'], revision=hero['revision'])
                    self.assertEqual({k: r['value'] for k, r in hero['attributes'].items()},
                        {'IQ': 12, 'ME': 12, 'MA': 12, 'PS': 22, 'PP': 17, 'PE': 18, 'PB': 12, 'SPD': 28})
                    resources = app.resource_view(hero['id'])['resources']
                    self.assertEqual({k: r['value'] for k, r in resources.items()},
                                     {'HP': 42, 'SDC': 158 if identity == SOLAR else 148, 'PPE': 24})
                    combat = app.combat_view(hero['id'])
                    self.assertEqual(combat['class_bonuses']['perception']['value'], 4 if identity == SOLAR else 3)
                    self.assertEqual(combat['totals']['attacks']['value'], 5)
                    self.assertIsNone(combat['totals']['damage']['value'])
                    self.assertEqual(app.psionic_view(hero['id'])['effective']['resources']['ISP']['value'], 36)
                    guidance = ' '.join(app.skill_view(hero['id'])['path_guidance'])
                    self.assertIn('empowered', guidance)
                    self.assertNotIn('Frenzy', guidance)
                    for phrase in expected_phrases:
                        self.assertIn(phrase, guidance)
                    if identity == SOLAR:
                        self.assertEqual(resources['SDC']['contributions']['solar-full-sun'], 10)
                        self.assertEqual(resources['SDC']['rolls']['solar-full-sun'], [])

    def test_complete_solar_training_includes_secondary_additional_checks_and_caps(self):
        with tempfile.TemporaryDirectory() as directory:
            app = self.app(directory)
            hero = self.complete(app, app.create(character_class=SOLAR))
            view = app.skill_view(hero['id'])
            self.assertEqual(view['remaining'], {'language': 0, 'related': 0, 'secondary': 0})
            self.assertFalse(view['warnings'])
            selected = {r['id']: r for r in view['selected']}
            expected = dict(zip(RELATED, (50, 80, 80, 55, 40, 50, 50)))
            expected.update(zip(SECONDARY, (45, 45, 45, 50, 40, 40)))
            expected['language-other'] = 70
            self.assertEqual({k: selected[k]['percentage'] for k in expected}, expected)
            self.assertEqual(selected['computer-repair']['additional_checks'][0]['percentage'], 45)
            grants = {r['id']: r for r in view['grants']}
            required = {'native-language': 98, 'climbing': 70, 'dance': 50, 'detect-ambush': 45,
                'detect-concealment': 45, 'electronic-countermeasures': 45, 'escape-artist': 45,
                'gymnastics': 75, 'land-navigation': 51, 'prowl': 55, 'radio-basic': 60,
                'streetwise': 35, 'tailing': 55, 'swimming': 75}
            self.assertEqual({k: grants[k]['percentage'] for k in required}, required)
            gym = {r['name']: r['percentage'] for r in grants['gymnastics']['additional_checks']}
            self.assertEqual({k: gym[k] for k in ('Parallel bars and rings', 'Back flip', 'Climb rope and rappel')},
                             {'Parallel bars and rings': 85, 'Back flip': 95, 'Climb rope and rappel': 85})
            self.assertEqual(grants['climbing']['additional_checks'][0]['percentage'], 60)
            hero = app.select_skills(hero['id'], revision=hero['revision'], selections=[
                *choices(('art', 'forgery')), *choices(('sewing',), 'secondary')])
            self.assertEqual({r['id']: r['percentage'] for r in app.skill_view(hero['id'])['selected']},
                             {'art': 50, 'forgery': 55, 'sewing': 55})

    def test_shared_three_psychic_award_has_no_extra_trait_budget_or_frenzy(self):
        with tempfile.TemporaryDirectory() as directory:
            app = self.app(directory)
            hero = app.create(character_class=SOLAR)
            reserve = deepcopy(hero['class_psionics']['resource_record'])
            app.die = self.no_roll
            hero = app.select_class_psionics(hero['id'], revision=hero['revision'], selections=list(POWERS))
            view = app.psionic_view(hero['id'])['class_entitlement']
            self.assertEqual(len(view['catalog']), 42)
            self.assertEqual(set(view['known_abilities']),
                             {'crazy-enhanced-senses', 'crazy-bio-regeneration', 'crazy-association-empowered'})
            awards = view['learning_awards']['awards']
            self.assertEqual([(r['id'], r['count'], r['remaining']) for r in awards], [('initial-psychic', 3, 0)])
            self.assertFalse(any(r['id'].startswith('crazy-frenzy-') for r in view['catalog']))
            self.assertEqual(hero['class_psionics']['resource_record'], reserve)
            before = app.get(hero['id'])
            for excluded in ('astral-projection', 'ectoplasm', 'object-read', 'telekinesis', 'crazy-frenzy-anger'):
                with self.assertRaises(ValueError):
                    app.select_class_psionics(hero['id'], revision=hero['revision'], selections=[excluded])
                self.assertEqual(app.get(hero['id']), before)
            app.die = lambda sides: 15 if sides == 100 else 4
            hero = app.select_psionics(hero['id'], revision=hero['revision'], roll=True)
            app.die = self.no_roll
            hero = app.select_psionics(hero['id'], revision=hero['revision'], enabled=True,
                mode='single', categories=['Sensitive'], selections=['sense-time', 'total-recall'])
            self.assertEqual(app.psionic_view(hero['id'])['effective']['resources']['ISP']['value'], 36)

    def test_food_object_and_phrase_notes_duplicate_reopen_import_and_editable_pdf(self):
        details = [('popeye', 'Chosen food: Pumpkin Seeds and ginger tea.'),
                   ('magic-object', 'Chosen focus: a blue stone with a silver spiral.'),
                   ('power-words', 'Chosen phrase: Solen kai, wake the sun!')]
        with tempfile.TemporaryDirectory() as directory, tempfile.TemporaryDirectory() as target:
            app = self.app(directory)
            receiving = self.app(target)
            for key, note in details:
                with self.subTest(key=key):
                    hero = app.create(character_class='crazy-association-' + key)
                    hero = app.edit(hero['id'], revision=hero['revision'], notes=note)
                    duplicate = app.duplicate(hero['id'])
                    self.assertEqual(duplicate['notes'], note)
                    app.die = self.no_roll
                    reopened = self.app(directory)
                    receiving.die = self.no_roll
                    imported = receiving.import_character(reopened.export_character(hero['id']))
                    self.assertEqual((imported['notes'], imported['character_class']), (note, hero['character_class']))
                    fields = PdfReader(BytesIO(receiving.export_pdf(imported['id']))).get_fields() or {}
                    text = ' '.join(str(r.get('/V', '')) for r in fields.values())
                    self.assertIn(note, text)
                    self.assertIn('Character Notes', text)
                    self.assertIn('empowered condition', text)
                    app.die = lambda sides: 4

    def test_retained_learning_resources_undo_replay_and_exact_portable_views(self):
        with tempfile.TemporaryDirectory() as directory, tempfile.TemporaryDirectory() as target:
            app = self.app(directory)
            hero = self.complete(app, app.create(character_class=SOLAR))
            hero = app.generate_resources(hero['id'], revision=hero['revision'])
            hero = app.advance(hero['id'], revision=hero['revision'], method='xp', value=4281)
            self.assertEqual(app.resource_view(hero['id'])['resources']['HP']['value'], 50)
            self.assertEqual(app.psionic_view(hero['id'])['effective']['resources']['ISP']['value'], 44)
            self.assertEqual(app.skill_view(hero['id'])['remaining'], {'language': 0, 'related': 2, 'secondary': 1})
            app.die = self.no_roll
            selected = deepcopy(hero['skill_selections'])
            hero = app.select_skills(hero['id'], revision=hero['revision'], selections=[r for r in selected if r['skill_id'] != 'art'])
            hero = app.select_skills(hero['id'], revision=hero['revision'], selections=selected)
            view = app.skill_view(hero['id'])
            self.assertEqual(next(r for r in view['selected'] if r['id'] == 'art')['percentage'], 60)
            gym = next(r for r in view['grants'] if r['id'] == 'gymnastics')
            self.assertEqual(next(r for r in gym['additional_checks'] if r['name'] == 'Back flip')['percentage'], 98)
            methods = ('skill_view', 'combat_view', 'resource_view', 'equipment_view', 'psionic_view')
            expected = {method: getattr(app, method)(hero['id']) for method in methods}
            hero = app.undo_advancement(hero['id'], revision=hero['revision'])['character']
            hero = app.advance(hero['id'], revision=hero['revision'], method='xp', value=4281)
            receiving = self.app(target)
            receiving.die = self.no_roll
            imported = receiving.import_character(app.export_character(hero['id']))
            self.assertEqual(imported['class_psionics'], hero['class_psionics'])
            for method, value in expected.items():
                self.assertEqual(getattr(receiving, method)(imported['id']), value)

    def test_solar_level_fifteen_retains_source_roll_milestones(self):
        with tempfile.TemporaryDirectory() as directory:
            app = self.app(directory)
            hero = app.create(character_class=SOLAR)
            hero = app.generate_resources(hero['id'], revision=hero['revision'])
            hero = app.advance(hero['id'], revision=hero['revision'], method='xp', value=341601)
            self.assertEqual(hero['level'], 15)
            self.assertEqual({k: r['value'] for k, r in app.resource_view(hero['id'])['resources'].items()},
                             {'HP': 98, 'SDC': 158, 'PPE': 24})
            self.assertEqual(app.psionic_view(hero['id'])['effective']['resources']['ISP']['value'], 92)
            self.assertEqual(app.combat_view(hero['id'])['totals']['roll_with_impact']['contributions']['O.C.C.'], 12)

    def test_shared_kit_funds_quantities_and_every_association_armor_wearer(self):
        with tempfile.TemporaryDirectory() as directory:
            app = self.app(directory)
            hero = self.complete(app, app.create(character_class=SOLAR))
            hero = app.generate_starting_funds(hero['id'], revision=hero['revision'])
            hero = app.grant_starting_gear(hero['id'], revision=hero['revision'])
            for group, item in GEAR_CHOICES.items():
                hero = app.grant_starting_group(hero['id'], revision=hero['revision'], group_id=group, selection=item)
            view = app.equipment_view(hero['id'])
            self.assertEqual(view['inventory']['credits'], 800)
            self.assertEqual(hero['starting_funds']['saleable_goods']['value'], 4000)
            self.assertEqual(len(hero['starting_equipment_groups']), 8)
            self.assertEqual(sum(r['quantity'] for r in view['items'] if r['item_id'] == 'standard-e-clip'), 8)
            self.assertEqual(sum(r['quantity'] for r in view['items'] if r['item_id'] == 'knife-large'), 5)
            self.assertFalse(any(r['category'] == 'vehicle' for r in view['items']))
            for identity in IDENTITIES:
                current = hero if identity == SOLAR else app.create(character_class=identity)
                if identity != SOLAR:
                    current = app.grant_starting_group(current['id'], revision=current['revision'], group_id='armor', selection='juicer-assassin-plate')
                inventory = deepcopy(current['equipment'])
                for item in inventory['items']:
                    item['equipped'] = item['item_id'] == 'juicer-assassin-plate'
                current = app.set_equipment(current['id'], revision=current['revision'], inventory=inventory)
                armor = app.equipment_view(current['id'])['armor'][0]
                self.assertEqual((armor['movement_penalty'], armor['prowl_penalty']), (-5, -5))

    def test_invalid_unselected_profiles_dependencies_and_races_reject_before_dice(self):
        for kind in ('missing-reference', 'solar-selector', 'solar-constant', 'psychic-award'):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as directory:
                archive = candidate_archive()
                definitions = archive.definitions()
                skills = next(p for p in definitions if (p['id'], p['version']) == ('rifts-domestic-skills', '2.43.0'))
                if kind == 'missing-reference':
                    skills['class_profiles'][IDENTITIES[0]]['combat']['catalog_ref'] = 'missing'
                elif kind == 'solar-selector':
                    skills['class_profiles'][SOLAR]['skill_effects'][-1]['selector'] = {'any_of': [{'ids': ['missing']}]}
                elif kind == 'solar-constant':
                    next(r for r in skills['class_profiles'][SOLAR]['resources']['definitions'] if r['id'] == 'SDC')['contributions'][-1]['formula']['bonus'] = True
                else:
                    next(p for p in definitions if p['id'] == ABILITY)['paths'][0]['allowances']['class']['awards'][0]['categories'] = ['Unknown']
                app = CharacterApplication(directory, die=self.no_roll, rule_archive=RuleArchive(definitions, archive.active_versions()))
                with self.assertRaises(ValueError):
                    app.create(character_class='vagabond')
                self.assertFalse(app.list())
        with tempfile.TemporaryDirectory() as directory:
            app = self.app(directory)
            app.die = self.no_roll
            for race in ('psi-stalker', 'dog-boy'):
                with self.assertRaises(ValueError):
                    app.create(race=race, character_class=SOLAR)

    def test_bad_unselected_equipment_owner_preserves_saved_character(self):
        with tempfile.TemporaryDirectory() as directory:
            app = self.app(directory)
            hero = app.create(character_class=SOLAR)
            archive = candidate_archive()
            definitions = archive.definitions()
            equipment = next(p for p in definitions if (p['id'], p['version']) == ('rifts-equipment', '1.29.0'))
            equipment['class_profiles'][IDENTITIES[0]]['starting_groups']['values']['character_class'] = 'other'
            app.rule_archive = RuleArchive(definitions, archive.active_versions())
            app.die = self.no_roll
            with self.assertRaises(ValueError):
                app.grant_starting_group(hero['id'], revision=hero['revision'], group_id='knives', selection='knife-large')
            self.assertEqual(app.get(hero['id']), hero)

    def test_whole_parents_preserved_with_only_new_owners_shared_records_and_wearers(self):
        archive = candidate_archive()
        for identity, version in PARENTS.items():
            before = archive.resolve(identity, version)
            after = archive.active(identity)
            expected = deepcopy(before)
            expected['version'] = after['version']
            if identity == 'rifts-core':
                self.assertEqual(after['classes'][:len(before['classes'])], before['classes'])
                self.assertEqual([r['id'] for r in after['classes'][len(before['classes']):]], list(IDENTITIES))
                expected['classes'].extend(after['classes'][len(before['classes']):])
                human = next(r for r in expected['creation_profiles'] if r['race'] == 'human')
                human['classes'].extend(IDENTITIES)
                human['source']['pages'] = sorted(set(human['source']['pages']) | {55, 56, 57, 58})
                human['source']['pdf_pages'] = [p + 3 for p in human['source']['pages']]
            else:
                for owner in IDENTITIES:
                    expected['class_profiles'][owner] = after['class_profiles'][owner]
                self.assertEqual(set(after.get('profile_catalogs', {})) - set(before.get('profile_catalogs', {})),
                    {'crazy-association-combat'} if identity == 'rifts-domestic-skills' else
                    {'crazy-association-starting-funds', 'crazy-association-starting-gear', 'crazy-association-starting-groups'})
                expected['profile_catalogs'] = {**before.get('profile_catalogs', {}), **after['profile_catalogs']}
                if identity == 'rifts-domestic-skills':
                    self.assertEqual(after['profile_catalogs']['crazy-association-combat']['value'], before['class_profiles']['crazy-frenzy']['combat'])
                else:
                    armor = next(r for r in expected['items'] if r['id'] == 'juicer-assassin-plate')
                    armor['movement_penalty_by_class'].update({owner: -5 for owner in IDENTITIES})
            self.assertEqual(after, expected, identity)

    def test_archived_frenzy_keeps_exact_public_outputs_and_has_no_association_dependency(self):
        installed = RuleArchive.load()
        previous = RuleArchive(installed.definitions(), {**installed.active_versions(), **PARENTS})
        with tempfile.TemporaryDirectory() as directory, tempfile.TemporaryDirectory() as target:
            origin = CharacterApplication(directory, die=lambda sides: 4, rule_archive=previous)
            hero = origin.create(character_class='crazy-frenzy')
            hero = origin.generate_resources(hero['id'], revision=hero['revision'])
            hero = origin.set_equipment(hero['id'], revision=hero['revision'], inventory={'credits': 0, 'items': []})
            methods = ('skill_view', 'combat_view', 'resource_view', 'equipment_view', 'psionic_view')
            expected = {method: getattr(origin, method)(hero['id']) for method in methods}
            bundle = origin.export_character(hero['id'])
            self.assertNotIn(ABILITY, {p['id'] for p in bundle['rule_packs']})
            receiving = self.app(target)
            receiving.die = self.no_roll
            imported = receiving.import_character(bundle)
            self.assertEqual(imported['rules'], hero['rules'])
            self.assertEqual(imported['additional_rule_packs'], hero['additional_rule_packs'])
            for method, value in expected.items():
                self.assertEqual(getattr(receiving, method)(imported['id']), value)
