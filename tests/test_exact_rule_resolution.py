import copy
import tempfile
import unittest
from collections import Counter
from unittest.mock import patch

from characters_unlimited.application import CharacterApplication
from characters_unlimited.portability import pinned_packs
from characters_unlimited.rules import RuleArchive


def no_dice(sides):
    raise AssertionError('Exact rule resolution and replay must not draw dice')


def fixture():
    core = {'id': 'rifts-core', 'version': '1', 'game': 'rifts', 'classes': [
        {'id': name, 'ability_path': {'id': 'inactive-path', 'version': '1'}}
        for name in ('unused-one', 'unused-two')]}
    packs = [core, {'id': 'skills', 'version': '1'}, {'id': 'skills', 'version': '2'},
             {'id': 'inactive-path', 'version': '1'}, {'id': 'unrelated', 'version': '1'}]
    before = {'rules': {'id': 'rifts-core', 'version': '1'},
              'additional_rule_packs': {'skills': '1'}}
    character = {**copy.deepcopy(before), 'additional_rule_packs': {'skills': '2'},
                 'advancement': {'before': copy.deepcopy(before)},
                 'later_advancements': [{'before': copy.deepcopy(before)} for _ in range(13)]}
    return packs, character


class ExactRuleResolutionTests(unittest.TestCase):
    def test_public_reopen_views_mutation_and_portability_do_not_expand_the_archive(self):
        archive = RuleArchive.load()
        with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
            source = CharacterApplication(first, die=lambda sides: 3, rule_archive=archive)
            target = CharacterApplication(second, rule_archive=archive)
            characters = [source.create(game=game) for game in ('rifts', 'heroes-unlimited')]
            source.die = no_dice
            target.die = no_dice
            bundles = [source.export_character(character['id']) for character in characters]
            skill_view = source.skill_view(characters[0]['id'])
            with patch.object(archive, 'definitions', side_effect=AssertionError('Unrelated archive decoded')):
                for character, bundle in zip(characters, bundles):
                    with self.subTest(game=character['game']):
                        self.assertEqual(source.get(character['id']), character)
                        self.assertEqual(source.export_character(character['id']), bundle)
                        restored = target.import_character(bundle)
                        ignored = {'id', 'revision', 'updated_at', 'copied_from'}
                        self.assertEqual({k: v for k, v in restored.items() if k not in ignored},
                                         {k: v for k, v in character.items() if k not in ignored})
                self.assertEqual(source.skill_view(characters[0]['id']), skill_view)
                selected = source.select_skills(characters[0]['id'], revision=0,
                                               selections=[{'skill_id': 'dance', 'pool': 'domestic'}])
                self.assertEqual(selected['revision'], 1)
                self.assertEqual(source.export_character(selected['id'])['character'], selected)

    def test_one_lookup_and_copy_per_exact_definition_across_all_history_frames(self):
        packs, character = fixture()
        archive = RuleArchive(packs, {})
        with patch.object(archive, 'resolve', wraps=archive.resolve) as resolving:
            with patch('characters_unlimited.portability.deepcopy', wraps=copy.deepcopy) as copying:
                result = pinned_packs(character, resolve=resolving)
        self.assertEqual(result, pinned_packs(character, packs))
        self.assertEqual([(p['id'], p['version']) for p in result],
                         [('skills', '2'), ('rifts-core', '1'), ('inactive-path', '1'), ('skills', '1')])
        self.assertEqual(Counter(call.args for call in resolving.call_args_list),
                         Counter({(p['id'], p['version']): 1 for p in result}))
        self.assertEqual(copying.call_count, len(result))
        result[0]['name'] = 'Caller mutation'
        self.assertNotIn('name', pinned_packs(character, resolve=archive.resolve)[0])

    def test_conflicting_missing_and_malformed_pins_reject_for_both_adapters(self):
        packs, character = fixture()
        cases = []
        invalid_versions: list[object] = [[], {}, None, 3]
        for value in invalid_versions:
            invalid = copy.deepcopy(character)
            invalid['additional_rule_packs']['skills'] = value
            cases.append(invalid)
            invalid = copy.deepcopy(character)
            invalid['rules']['version'] = value
            cases.append(invalid)
        for identifier, version in (('rifts-core', 'different'), ('inactive-path', 'different'), ('missing', '1')):
            invalid = copy.deepcopy(character)
            invalid['additional_rule_packs'][identifier] = version
            cases.append(invalid)
        archive = RuleArchive(packs, {})
        for invalid in cases:
            for options in ({'packs': packs}, {'resolve': archive.resolve}):
                with self.subTest(invalid=invalid, resolver='resolve' in options), self.assertRaises(ValueError):
                    pinned_packs(invalid, **options)
        missing = RuleArchive([pack for pack in packs if pack['id'] != 'inactive-path'], {})
        with self.assertRaisesRegex(ValueError, 'Unsupported rule version'):
            pinned_packs(character, resolve=missing.resolve)

    def test_history_validation_and_current_only_collection_are_preserved(self):
        packs, character = fixture()
        archive = RuleArchive(packs, {})
        character['later_advancements'][-1]['before']['later_advancements'] = []
        for options in ({'packs': packs}, {'resolve': archive.resolve}):
            with self.assertRaisesRegex(ValueError, 'flat'):
                pinned_packs(character, **options)
            current = pinned_packs(character, include_history=False, **options)
            self.assertNotIn(('skills', '1'), [(p['id'], p['version']) for p in current])
        character['later_advancements'] = []
        character['advancement']['before']['advancement'] = {}
        with self.assertRaisesRegex(ValueError, 'flat initial'):
            pinned_packs(character, resolve=archive.resolve)

    def test_cached_current_pins_do_not_hide_missing_or_malformed_historical_pins(self):
        packs, character = fixture()
        archive = RuleArchive(packs, {})
        invalid_versions: list[object] = ['missing', [], {}]
        for version in invalid_versions:
            invalid = copy.deepcopy(character)
            invalid['later_advancements'][-1]['before']['additional_rule_packs']['skills'] = version
            for options in ({'packs': packs}, {'resolve': archive.resolve}):
                with self.subTest(version=version, resolver='resolve' in options), self.assertRaises(ValueError):
                    pinned_packs(invalid, **options)

    def test_resolver_identity_must_match_the_requested_exact_pin(self):
        _, character = fixture()
        invalid_definitions: list[object] = [None, [], {'id': 'other', 'version': '1'},
                                           {'id': 'rifts-core', 'version': 'latest'}]
        for returned in invalid_definitions:
            with self.subTest(returned=returned), self.assertRaises(ValueError):
                pinned_packs(character, resolve=lambda identifier, version: returned)

    def test_list_adapter_keeps_first_match_and_requires_one_lookup_source(self):
        packs, character = fixture()
        first = {**packs[2], 'name': 'First accepted match'}
        ordered = [first, *packs]
        self.assertEqual(pinned_packs(character, ordered)[0], first)
        with self.assertRaises(ValueError):
            pinned_packs(character)
        with self.assertRaises(ValueError):
            pinned_packs(character, packs, resolve=RuleArchive(packs, {}).resolve)

    def test_legacy_application_fallback_is_local_to_reopen(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides: 3)
            character = app.create()
            del character['additional_rule_packs']['rifts-domestic-skills']
            app.store.put(character)
            with patch.object(app.rule_archive, 'definitions', side_effect=AssertionError('Archive expanded')):
                reopened = app.get(character['id'])
            self.assertEqual(reopened['additional_rule_packs']['rifts-domestic-skills'], '1.0.0')
            self.assertEqual(app.store.get(character['id']), character)
