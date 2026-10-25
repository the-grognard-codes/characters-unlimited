"""Source-owned wearer overrides affect projected armor, never stored possessions."""

from copy import deepcopy
import tempfile
import unittest
from typing import Any, Callable
from uuid import uuid4

from characters_unlimited.application import CharacterApplication
from characters_unlimited.rules import RuleArchive


SOURCE = {'book': 'Synthetic wearer fixture', 'section': 'Conditional armor penalties'}


def armor_archive(mutate: Callable[[dict[str, Any]], None] | None = None):
    archive = RuleArchive.load()
    pack = archive.active('rifts-equipment')
    armor = next(row for row in pack['items'] if row['id'] == 'plastic-man')
    armor.update(movement_penalty_by_class={'city-rat': -5}, movement_source=SOURCE)
    if mutate:
        mutate(armor)
    return RuleArchive([pack if row['id'] == pack['id'] and row['version'] == pack['version'] else row
                        for row in archive.definitions()], archive.active_versions())


def replace_field(field: str, value: Any) -> Callable[[dict[str, Any]], None]:
    def mutate(row: dict[str, Any]) -> None:
        row[field] = deepcopy(value)
    return mutate


class WearerArmorPenaltyTests(unittest.TestCase):
    def no_roll(self, sides):
        self.fail('Malformed inactive rules and exact reopening must not draw dice')

    def test_public_armor_projection_uses_wearer_override_and_retains_other_defaults(self):
        with tempfile.TemporaryDirectory() as directory:
            archive = armor_archive()
            app = CharacterApplication(directory, die=lambda sides: 4, rule_archive=archive)
            for identity, penalty in [('city-rat', -5), ('vagabond', -10)]:
                hero = app.create(character_class=identity)
                inventory = {'credits': 0, 'items': [{'id': str(uuid4()), 'item_id': 'plastic-man',
                    'quantity': 1, 'location': 'carried', 'equipped': True, 'shots': None}]}
                hero = app.set_equipment(hero['id'], revision=hero['revision'], inventory=inventory)
                view = app.equipment_view(hero['id'])
                self.assertEqual((view['armor'][0]['movement_penalty'], view['armor'][0]['prowl_penalty']),
                                 (penalty, penalty))
                self.assertEqual(view['armor'][0]['movement_source'], SOURCE)
                self.assertEqual(hero['equipment'], inventory)
                reopened = CharacterApplication(directory, die=self.no_roll, rule_archive=archive)
                imported = reopened.import_character(reopened.export_character(hero['id']))
                self.assertEqual(reopened.equipment_view(imported['id'])['armor'], view['armor'])
                self.assertNotIn('movement_penalty', imported['equipment']['items'][0])

    def test_malformed_unselected_override_rejects_before_dice_or_write(self):
        bad: list[Any] = [None, [], {}, {'': -5}, {'city-rat': True}, {'city-rat': 1},
                          {'city-rat': -101}, {'x' * 81: -5}]
        mutations = [replace_field('movement_penalty_by_class', value) for value in bad]
        mutations += [replace_field('movement_penalty', None), replace_field('prowl_penalty', -5),
                      replace_field('movement_source', {'book': 'Missing section'}),
                      replace_field('category', 'gear')]
        for mutate in mutations:
            with self.subTest(mutate=mutate), tempfile.TemporaryDirectory() as directory:
                app = CharacterApplication(directory, die=self.no_roll, rule_archive=armor_archive(mutate))
                with self.assertRaises(ValueError):
                    app.create(character_class='vagabond')
                self.assertEqual(app.list(), [])
