from copy import deepcopy
from io import BytesIO
import tempfile
import unittest

from pypdf import PdfReader

from characters_unlimited.ability_paths import compile_paths, project_path, update_path
from characters_unlimited.application import CharacterApplication
from characters_unlimited.attribute_modifiers import ATTRIBUTE_NAMES
from characters_unlimited.rules import RuleArchive


SOURCE = {'book': 'Synthetic learning witness', 'section': 'Known and elective awards'}


def learning_pack():
    pack = RuleArchive.load().active('rifts-operator-psionics')
    pack['version'] = 'learning-witness'
    pack['format'] = 'ability-paths-v3'
    pack['catalog']['version'] = 'learning-witness'
    definitions = pack['catalog']['options']
    next(row for row in definitions if row['id'] == 'total-recall')['tags'] = ['Sensitive', 'Physical']
    for path in pack['paths']:
        path['known_abilities'] = ['sense-time'] if path['resources'] else []
        path['allowances'] = {'class': {'count': 0, 'minimum_categories': 0, 'maximum_categories': 4,
            'awards': [
                {'id': 'physical', 'name': 'Initial Physical', 'source': SOURCE, 'level': 1,
                 'count': 1, 'categories': ['Physical']},
                {'id': 'sensitive', 'name': 'Initial Sensitive', 'source': SOURCE, 'level': 1,
                 'count': 1, 'categories': ['Sensitive']},
                {'id': 'super', 'name': 'Later Super', 'source': SOURCE, 'level': 3,
                 'count': 1, 'categories': ['Super']}]}}
    return pack


def archive_with(pack):
    installed = RuleArchive.load()
    core = installed.active('rifts-core')
    for row in core['classes']:
        if row.get('ability_path', {}).get('id') == pack['id']:
            row['ability_path']['version'] = pack['version']
    definitions = [core if (row['id'], row['version']) == (core['id'], core['version']) else row
                   for row in installed.definitions()]
    return RuleArchive([*definitions, pack], installed.active_versions())


class AbilityLearningTests(unittest.TestCase):
    def no_roll(self, sides):
        self.fail('Recorded acquisitions must not reroll')

    def context(self, level=1):
        return {'game': 'rifts', 'level': level,
                'attributes': {key: {'base': 10, 'value': 10, 'effects': []} for key in ATTRIBUTE_NAMES}}

    def test_source_class_strike_and_pull_bonus_project_once_to_saved_weapon_choices(self):
        installed = RuleArchive.load()
        skills = installed.active('rifts-domestic-skills')
        skills['version'] = 'source-bonus-witness'
        profile = skills['class_profiles']['operator']
        profile['class_bonuses']['combat'] = {'strike': 1, 'pull_punch': 2}
        active = installed.active_versions()
        active[skills['id']] = skills['version']
        archive = RuleArchive([*installed.definitions(), skills], active)
        with tempfile.TemporaryDirectory() as original, tempfile.TemporaryDirectory() as modified:
            old = CharacterApplication(original, die=lambda sides: 4)
            new = CharacterApplication(modified, die=lambda sides: 4, rule_archive=archive)
            before = old.create(character_class='operator')
            after = new.create(character_class='operator')
            choices = {'hand_to_hand': 'basic', 'ancient': ['knife'], 'modern': ['energy-pistol']}
            before = old.select_combat(before['id'], revision=before['revision'], choices=choices)
            after = new.select_combat(after['id'], revision=after['revision'], choices=choices)
            baseline, result = old.combat_view(before['id']), new.combat_view(after['id'])
            self.assertEqual(result['totals']['strike']['value'], baseline['totals']['strike']['value'] + 1)
            self.assertEqual(result['totals']['pull_punch']['value'], baseline['totals']['pull_punch']['value'] + 2)
            for expected, actual in zip(baseline['melee'], result['melee']):
                for stat in ('strike', 'thrown'):
                    self.assertEqual(actual[stat]['value'], expected[stat]['value'] + 1)
                    self.assertEqual(actual[stat]['contributions']['O.C.C.'], 1)
            for expected, actual in zip(baseline['shooting'], result['shooting']):
                for context in ('single', 'burst', 'wild'):
                    self.assertEqual(actual[context]['value'], expected[context]['value'] + 1)
                self.assertEqual(actual['aimed']['value'],
                                 None if expected['aimed']['value'] is None else expected['aimed']['value'] + 1)
            new.die = self.no_roll
            imported = new.import_character(new.export_character(after['id']))
            self.assertEqual(new.combat_view(imported['id']), result)

    def test_known_grants_do_not_consume_awards_or_disappear_on_selection(self):
        pack = learning_pack()
        state = update_path(self.context(), pack, None, lambda sides: 2)
        self.assertEqual(state['abilities']['selections'], ['sense-time'])
        state = update_path(self.context(), pack, state, self.no_roll,
                            selections=['total-recall', 'resist-fatigue'])
        view = project_path(self.context(), pack, state)
        self.assertEqual(view['known_abilities'], ['sense-time'])
        self.assertEqual(len(view['abilities']), 3)
        self.assertEqual(view['learning_awards']['remaining'], 0)
        self.assertEqual(view['selection_group']['credited'], 2)
        # A greedy allocator that gives Total Recall the first Physical slot
        # fails to allocate Resist Fatigue. Maximum exclusive credit uses both.
        self.assertEqual([row['credited'] for row in view['learning_awards']['awards']], [1, 1])
        state = update_path(self.context(), pack, state, self.no_roll, selections=[])
        self.assertEqual(state['abilities']['selections'], ['sense-time'])
        state = update_path(self.context(), pack, state, self.no_roll, selections=['total-recall'])
        self.assertEqual(state['learning_levels']['total-recall'], 1)

    def test_first_learning_level_survives_removal_advancement_and_reselection(self):
        pack = learning_pack()
        definition = next(row for row in pack['catalog']['options'] if row['id'] == 'telemechanics')
        definition['requirements'] = [{'id': 'tier', 'name': 'Later tier', 'source': SOURCE, 'minimum_level': 3}]
        state = update_path(self.context(), pack, None, lambda sides: 2, selections=['telemechanics'])
        later = update_path(self.context(3), pack, state, lambda sides: 2)
        view = project_path(self.context(3), pack, later)
        self.assertEqual(view['learning_awards']['unallocated'], {'telemechanics': 1})
        self.assertTrue(any('source minimum learning level 3' in row for row in view['guidance']))
        removed = update_path(self.context(3), pack, later, self.no_roll, selections=[])
        selected = update_path(self.context(3), pack, removed, self.no_roll, selections=['telemechanics'])
        self.assertEqual(selected['learning_levels']['telemechanics'], 1)
        fresh = update_path(self.context(3), pack, None, lambda sides: 2, selections=['telemechanics'])
        self.assertEqual(fresh['learning_levels']['telemechanics'], 3)
        self.assertEqual(project_path(self.context(3), pack, fresh)['learning_awards']['unallocated'], {})

    def test_duplicate_electives_and_malformed_inactive_awards_reject_before_dice(self):
        pack = learning_pack()
        with self.assertRaises(ValueError):
            update_path(self.context(), pack, None, self.no_roll, selections=['telemechanics', 'telemechanics'])
        mutations = [
            lambda value: value['paths'][0]['known_abilities'].append('unknown'),
            lambda value: value['paths'][0]['allowances']['class']['awards'][0].update(level=True),
            lambda value: value['paths'][0]['allowances']['class']['awards'][0].update(categories=['Alien']),
            lambda value: value['paths'][0]['allowances']['class']['awards'][0].update(count=1001),
            lambda value: value['paths'][1]['allowances']['class'].update(costs={'sense-time': 2}),
            lambda value: value['paths'][0]['allowances']['class'].update(costs={'total-recall': 2}),
        ]
        for mutate in mutations:
            bad = deepcopy(pack)
            mutate(bad)
            with self.subTest(bad=bad['paths'][0]), tempfile.TemporaryDirectory() as directory:
                app = CharacterApplication(directory, die=self.no_roll, rule_archive=archive_with(bad))
                with self.assertRaises(ValueError):
                    app.create(character_class='operator')
                with self.assertRaises(ValueError):
                    app.catalog()
                self.assertEqual(app.list(), [])

    def test_learning_corruption_and_missing_known_grants_reject(self):
        pack = learning_pack()
        state = update_path(self.context(), pack, None, lambda sides: 2, selections=['total-recall'])
        for mutate in (lambda row: row['learning_levels'].update({'total-recall': True}),
                       lambda row: row['learning_levels'].update({'total-recall': 2}),
                       lambda row: row['learning_levels'].pop('total-recall'),
                       lambda row: row['learning_levels'].update({'sense-time': 2}),
                       lambda row: row['abilities']['selections'].remove('sense-time')):
            bad = deepcopy(state)
            mutate(bad)
            with self.assertRaises(ValueError):
                update_path(self.context(), pack, bad, self.no_roll)
            with self.assertRaises(ValueError):
                project_path(self.context(), pack, bad)

    def test_public_undo_portable_reopen_and_editable_pdf_retain_learning(self):
        archive = archive_with(learning_pack())
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides: 2, rule_archive=archive)
            hero = app.create(character_class='psi-operator')
            hero = app.generate_resources(hero['id'], revision=hero['revision'])
            hero = app.advance(hero['id'], revision=hero['revision'], method='level', value=3)
            hero = app.select_class_psionics(hero['id'], revision=hero['revision'], selections=['telemechanics'])
            self.assertEqual(hero['class_psionics']['learning_levels']['telemechanics'], 3)
            app.die = self.no_roll
            hero = app.undo_advancement(hero['id'], revision=hero['revision'])['character']
            self.assertEqual(hero['class_psionics']['learning_levels']['telemechanics'], 3)
            self.assertNotIn('telemechanics', hero['class_psionics']['abilities']['selections'])
            with self.assertRaisesRegex(ValueError, 'after the current level'):
                app.select_class_psionics(hero['id'], revision=hero['revision'], selections=['telemechanics'])
            undo_bundle = app.export_character(hero['id'])
            app.import_character(undo_bundle)
            damaged = deepcopy(undo_bundle)
            damaged['character']['class_psionics']['abilities']['selections'].append('telemechanics')
            with self.assertRaisesRegex(ValueError, 'after the current level'):
                app.import_character(damaged)
            hero = app.advance(hero['id'], revision=hero['revision'], method='level', value=3)
            hero = app.select_class_psionics(hero['id'], revision=hero['revision'], selections=['telemechanics'])
            bundle = app.export_character(hero['id'])
            imported = app.import_character(bundle)
            self.assertEqual(imported['class_psionics'], hero['class_psionics'])
            reopened = CharacterApplication(directory, die=self.no_roll, rule_archive=archive)
            self.assertEqual(reopened.psionic_view(imported['id']), app.psionic_view(hero['id']))
            fields = PdfReader(BytesIO(app.export_pdf(hero['id']))).get_fields()
            assert fields is not None
            values = ' '.join(str(row.get('/V', '')) for row in fields.values())
            self.assertIn('Learned at level 3', values)
            self.assertIn('Always known class grant', values)
            damaged = deepcopy(bundle)
            damaged['character']['class_psionics']['learning_levels']['sense-time'] = 2
            with self.assertRaises(ValueError):
                app.import_character(damaged)
            damaged = deepcopy(bundle)
            damaged['character']['class_psionics']['learning_levels']['telemechanics'] = 1
            with self.assertRaisesRegex(ValueError, 'retained advancement history'):
                app.import_character(damaged)
            self.assertEqual(app.get(hero['id']), hero)

    def test_future_cached_selection_rejects_before_new_resource_dice(self):
        pack = learning_pack()
        state = update_path(self.context(3), pack, None, lambda sides: 2, selections=['telemechanics'])
        state = update_path(self.context(3), pack, state, self.no_roll, selections=[])
        # The retained receipt is valid after undo; selecting it early is not.
        project_path(self.context(), pack, state)
        with self.assertRaisesRegex(ValueError, 'after the current level'):
            update_path(self.context(2), pack, state, self.no_roll, selections=['telemechanics'])

    def test_weighted_single_category_choice_uses_saved_and_new_awards_once(self):
        pack = learning_pack()
        for path in pack['paths']:
            allowance = path['allowances']['class']
            allowance['awards'] = [
                {'id': 'initial', 'name': 'Initial choices', 'source': SOURCE, 'level': 1,
                 'count': 3, 'categories': ['Super']},
                {'id': 'later', 'name': 'Later choice', 'source': SOURCE, 'level': 3,
                 'count': 1, 'categories': ['Super']}]
            allowance['costs'] = {'electrokinesis': 2}
        state = update_path(self.context(), pack, None, lambda sides: 2,
                            selections=['telemechanics', 'telemechanic-paralysis'])
        self.assertEqual(project_path(self.context(), pack, state)['learning_awards']['remaining'], 1)
        state = update_path(self.context(3), pack, state, lambda sides: 2,
                            selections=['telemechanics', 'telemechanic-paralysis', 'electrokinesis'])
        result = project_path(self.context(3), pack, state)['learning_awards']
        self.assertEqual([row['credited'] for row in result['awards']], [3, 1])
        self.assertEqual((result['credited'], result['remaining'], result['unallocated']), (4, 0, {}))


if __name__ == '__main__':
    unittest.main()
