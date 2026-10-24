"""Independent original RUE145–148/295 standard Dog Boy witnesses."""
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest

from characters_unlimited.application import CharacterApplication
from characters_unlimited.rules import RuleArchive
from characters_unlimited.skill_choices import selection_policy


PATHS = ('dog-boy-coalition-disarm', 'dog-boy-coalition-pull-punch')
CANDIDATES = ('rifts-core-1.18.0.json', 'rifts-domestic-skills-2.39.0.json',
              'rifts-equipment-1.26.0.json', 'rifts-dog-boy-psionics-1.0.0.json')


def candidate_archive(mutate=None):
    """Exercise explicit candidates before default activation, and exact pins after."""
    archive = RuleArchive.load()
    folder = Path(__file__).resolve().parents[1] / 'characters_unlimited/packs'
    candidates = [json.loads((folder / filename).read_text(encoding='utf-8')) for filename in CANDIDATES]
    if mutate:
        mutate(candidates)
    keys = {(p['id'], p['version']) for p in candidates}
    return RuleArchive([*[p for p in archive.definitions() if (p['id'], p['version']) not in keys], *candidates],
                       {**archive.active_versions(), **{p['id']: p['version'] for p in candidates}})


class DogBoyTests(unittest.TestCase):
    def app(self, directory):
        return CharacterApplication(directory, die=lambda sides: 3, rule_archive=candidate_archive())

    def no_roll(self, sides):
        self.fail('Exact read/replay must not draw dice')

    def test_source_attributes_resources_scoped_saves_and_alternative_combat_bonus(self):
        for path in PATHS:
            with self.subTest(path=path), tempfile.TemporaryDirectory() as directory:
                app = self.app(directory)
                hero = app.create(race='dog-boy', character_class=path)
                self.assertEqual({key: row['value'] for key, row in hero['attributes'].items()},
                    {'IQ': 9, 'ME': 9, 'MA': 9, 'PS': 12, 'PP': 9, 'PE': 13, 'PB': 9, 'SPD': 27})
                self.assertEqual(hero['attributes']['PE']['base'], 9)
                hero = app.generate_resources(hero['id'], revision=hero['revision'])
                resources = app.resource_view(hero['id'])['resources']
                self.assertEqual({key: row['value'] for key, row in resources.items()}, {'HP': 16, 'SDC': 35, 'PPE': 9})
                combat = app.combat_view(hero['id'])
                saves = combat['saving_bonuses']
                self.assertEqual({key: saves[key]['value'] for key in ('psionics', 'mind_control', 'illusions', 'possession', 'curses', 'disease')},
                                 dict.fromkeys(('psionics', 'mind_control', 'illusions', 'possession', 'curses', 'disease'), 2))
                self.assertEqual((saves['magic']['value'], saves['drugs']['value']), (0, 0))
                self.assertEqual(combat['class_bonuses']['perception']['value'], 5)
                selected = 'disarm' if path.endswith('disarm') else 'pull_punch'
                other = 'pull_punch' if selected == 'disarm' else 'disarm'
                self.assertEqual(combat['totals'][selected]['contributions']['O.C.C.'], 2)
                self.assertNotIn('O.C.C.', combat['totals'][other]['contributions'])
                self.assertEqual(combat['totals']['parry']['value'], 1)
                psychic = app.psionic_view(hero['id'])['effective']
                self.assertEqual(psychic['save_target'], 10)
                self.assertEqual(psychic['resources']['ISP']['value'], 39)

    def test_skills_source_percentages_restrictions_fixed_weapons_and_paid_training(self):
        with tempfile.TemporaryDirectory() as directory:
            app = self.app(directory)
            hero = app.create(race='dog-boy')
            view = app.skill_view(hero['id'])
            grants = {row['id']: row for row in view['grants']}
            expected = {'native-language': 88, 'climbing': 50, 'intelligence': 38, 'land-navigation': 46,
                        'hover-craft': 60, 'radio-basic': 55, 'sensory-equipment': 40, 'wilderness-survival': 40}
            self.assertEqual({key: grants[key]['percentage'] for key in expected}, expected)
            self.assertEqual((view['remaining']['related'], view['remaining']['secondary']), (5, 6))
            hero = app.select_skills(hero['id'], revision=hero['revision'], selections=[
                {'skill_id': 'language-other', 'pool': 'language', 'specialty': 'Spanish'},
                {'skill_id': 'motorcycle', 'pool': 'related', 'specialty': ''}])
            rows = {row['id']: row for row in app.skill_view(hero['id'])['selected']}
            self.assertEqual(rows['language-other']['percentage'], 55)
            self.assertEqual(rows['motorcycle']['percentage'], 65)
            for hand, cost in [('expert', 0), ('martial-arts', 2), ('assassin', 2)]:
                hero = app.select_combat(hero['id'], revision=hero['revision'],
                    choices={'hand_to_hand': hand, 'ancient': ['knife'], 'modern': []})
                self.assertEqual(app.combat_view(hero['id'])['related_cost'], cost)
            combat = app.combat_view(hero['id'])
            self.assertEqual(combat['fixed_proficiencies']['modern'], ['energy-pistol', 'energy-rifle'])
            knife = next(row for row in combat['melee'] if row['id'] == 'knife')
            self.assertEqual(knife['parry']['contributions']['O.C.C.'], 1)
            pack = app.character_skill_pack(hero)
            for family, identity in [('related', 'acrobatics'), ('related', 'prowl'), ('related', 'computer-operation'),
                                     ('related', 'literacy-native'), ('secondary', 'literacy-other')]:
                definition = next(row for row in pack['skills'] if row['id'] == identity)
                self.assertFalse(selection_policy(definition, family, pack)['allowed'])
            hero = app.select_skills(hero['id'], revision=hero['revision'], selections=[
                {'skill_id': 'prowl', 'pool': 'related', 'specialty': ''}])
            self.assertTrue(app.skill_view(hero['id'])['warnings'])  # Honor-system choices remain visible.

    def test_fixed_and_elective_psychics_distinct_inherent_senses_and_exact_replay(self):
        with tempfile.TemporaryDirectory() as directory, tempfile.TemporaryDirectory() as target:
            app = self.app(directory)
            hero = app.create(race='dog-boy')
            hero = app.select_class_psionics(hero['id'], revision=hero['revision'], selections=['telepathy'])
            psychic = app.psionic_view(hero['id'])['effective']
            abilities = {row['id']: row for row in psychic['abilities']}
            self.assertEqual(set(abilities), {'sense-evil', 'sense-magic', 'sixth-sense', 'empathy', 'telepathy',
                'dog-boy-energy', 'dog-boy-psychic-scent', 'dog-boy-supernatural', 'dog-boy-physical-senses'})
            self.assertIn('reception only', abilities['empathy']['description'])
            energy = {row['id']: row['value'] for row in abilities['dog-boy-energy']['parameters']}
            self.assertEqual(energy, {'tracking': 45, 'active-range': 450, 'passive-range': 55})
            scent = {row['id']: row['value'] for row in abilities['dog-boy-psychic-scent']['parameters']}
            self.assertEqual(scent, {'general': 14, 'specific': 10, 'range': 55})
            hero = app.select_class_psionics(hero['id'], revision=hero['revision'], selections=['telepathy', 'total-recall'])
            self.assertEqual(app.psionic_view(hero['id'])['class_entitlement']['selection_group']['remaining'], -1)
            hero = app.select_class_psionics(hero['id'], revision=hero['revision'], selections=['telepathy'])
            psychic = app.psionic_view(hero['id'])['effective']
            app.die = self.no_roll
            bundle = app.export_character(hero['id'])
            restored_app = CharacterApplication(target, rule_archive=candidate_archive(), die=self.no_roll)
            restored = restored_app.import_character(bundle)
            self.assertEqual(restored_app.psionic_view(restored['id'])['effective'], psychic)
            self.assertEqual(CharacterApplication(directory, rule_archive=candidate_archive(), die=self.no_roll).get(hero['id']), hero)

    def test_source_kit_pairs_four_rifle_spares_and_one_time_snares(self):
        for index, path in enumerate(PATHS):
            with self.subTest(path=path), tempfile.TemporaryDirectory() as directory:
                app = self.app(directory)
                hero = app.create(race='dog-boy', character_class=path)
                hero = app.generate_starting_funds(hero['id'], revision=hero['revision'], choices={'credits': 250})
                self.assertEqual(hero['equipment']['credits'], 500)
                hero = app.grant_starting_gear(hero['id'], revision=hero['revision'])
                options = {'armor': 'dog-boy-armor-light' if not index else 'dog-boy-armor-heavy',
                    'survival-knife': 'cs-survival-knife', 'close-combat': 'vibro-knife' if not index else 'dog-boy-vibro-claws',
                    'pistol': 'cs-c18', 'rifle': 'cs-c10' if not index else 'cs-c12',
                    'spare-clips': 'cs-rifle-e-clip', 'snares': 'dog-boy-snare'}
                calls = []
                def die(sides):
                    calls.append(sides)
                    return 4
                app.die = die
                for group_id, selection in options.items():
                    hero = app.grant_starting_group(hero['id'], revision=hero['revision'], group_id=group_id, selection=selection)
                self.assertEqual(calls, [6])
                receipts = deepcopy(hero['starting_equipment_groups'])
                self.assertEqual(receipts['close-combat']['grants'][0]['quantity'], 2)
                self.assertEqual(receipts['spare-clips']['grants'][0]['quantity'], 4)
                self.assertEqual(receipts['snares']['grants'][0]['quantity'], 4)
                self.assertEqual(receipts['snares']['grants'][0]['rolls'], [4])
                inventory = deepcopy(hero['equipment'])
                next(row for row in inventory['items'] if row['item_id'] == options['armor'])['equipped'] = True
                hero = app.set_equipment(hero['id'], revision=hero['revision'], inventory=inventory)
                view = app.equipment_view(hero['id'])
                self.assertEqual(view['armor'][0]['locations']['main_body'], 30 if not index else 50)
                self.assertFalse(view['armor'][0]['environmental'])
                self.assertEqual(view['armor'][0]['movement_penalty'], 0 if not index else None)
                self.assertFalse(any(row['item_id'] == 'cs-pistol-e-clip' for row in hero['equipment']['items']))
                hero = app.set_equipment(hero['id'], revision=hero['revision'], inventory={'credits': 1, 'items': []})
                app.die = self.no_roll
                self.assertEqual(app.import_character(app.export_character(hero['id']))['starting_equipment_groups'], receipts)
                with self.assertRaises(ValueError):
                    app.grant_starting_group(hero['id'], revision=hero['revision'], group_id='snares', selection='dog-boy-snare')

    def test_xp_awards_and_original_dice_survive_undo_and_replay(self):
        with tempfile.TemporaryDirectory() as directory:
            app = self.app(directory)
            hero = app.create(race='dog-boy')
            hero = app.generate_resources(hero['id'], revision=hero['revision'])
            hero = app.advance(hero['id'], revision=hero['revision'], method='xp', value=1950)
            self.assertEqual(hero['level'], 1)
            hero = app.advance(hero['id'], revision=hero['revision'], method='xp', value=1951)
            self.assertEqual(hero['level'], 2)
            self.assertEqual(app.psionic_view(hero['id'])['effective']['resources']['ISP']['value'], 49)
            self.assertEqual(app.skill_view(hero['id'])['remaining']['secondary'], 8)
            hero = app.advance(hero['id'], revision=hero['revision'], method='xp', value=17601)
            self.assertEqual(hero['level'], 5)
            self.assertEqual(app.psionic_view(hero['id'])['effective']['resources']['ISP']['value'], 79)
            self.assertEqual(app.resource_view(hero['id'])['resources']['HP']['value'], 28)
            view = app.skill_view(hero['id'])
            self.assertEqual((view['remaining']['related'], view['remaining']['secondary']), (6, 10))
            resources = deepcopy(hero['resources'])
            app.die = self.no_roll
            hero = app.undo_advancement(hero['id'], revision=hero['revision'])['character']
            hero = app.advance(hero['id'], revision=hero['revision'], method='level', value=5)
            self.assertEqual(hero['resources'], resources)
            self.assertEqual(app.psionic_view(hero['id'])['effective']['resources']['ISP']['value'], 79)
            app.export_character(hero['id'])

    def test_inactive_saving_definitions_preflight_and_pairings_preserve_existing_paths(self):
        mutations = [lambda rules: rules.update(saving_definitions=[{'id': 'magic', 'name': 'Duplicate', 'source': rules['source']}]),
                     lambda rules: rules.update(saving_definitions=[{'id': 'curses', 'name': '', 'source': {}}]),
                     lambda rules: rules.update(saving_definitions='curses')]
        for mutation in mutations:
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as directory:
                def mutate(packs):
                    mutation(packs[1]['class_profiles'][PATHS[1]]['class_bonuses'])
                app = CharacterApplication(directory, rule_archive=candidate_archive(mutate), die=self.no_roll)
                with self.assertRaises(ValueError):
                    app.create()
        with tempfile.TemporaryDirectory() as directory:
            app = self.app(directory)
            for race, path in [('human', PATHS[0]), ('dog-boy', 'vagabond'), ('psi-stalker', PATHS[1])]:
                with self.assertRaises(ValueError):
                    app.create(race=race, character_class=path)
            for race, path in [('human', 'vagabond'), ('psi-stalker', 'psi-stalker-wild')]:
                hero = app.create(race=race, character_class=path)
                self.assertNotIn('curses', app.combat_view(hero['id'])['saving_bonuses'])
