"""Public opt-in strength descriptions preserve normal paths and retained saves."""

from copy import deepcopy
from io import BytesIO
import tempfile
import unittest
from typing import Any, Callable
from uuid import uuid4

from pypdf import PdfReader
from characters_unlimited.application import CharacterApplication
from tests.test_owned_class_profiles import owned_pack, archive_with


SOURCE = {'book': 'Synthetic strength fixture', 'section': 'Descriptive strength ownership'}
DESCRIPTION = {'name': 'Enhanced fixture strength',
               'text': 'Use the source strength table. Power attacks use two actions; damage is descriptive.',
               'source': SOURCE}


def strength_fixture(mutate: Callable[[dict[str, Any]], None] | None = None, *, described=True):
    pack = owned_pack()
    rules = pack['class_profiles']['city-rat']['combat']
    if described:
        rules.update(strength_type='enhanced-fixture', strength_description=deepcopy(DESCRIPTION))
    if mutate:
        mutate(rules)
    return archive_with(pack)


def replace_rule(field: str, value: Any) -> Callable[[dict[str, Any]], None]:
    def mutate(rules: dict[str, Any]) -> None:
        rules[field] = deepcopy(value)
    return mutate


class DescriptiveStrengthTests(unittest.TestCase):
    def no_roll(self, sides):
        self.fail('Read/replay or malformed inactive declarations must not draw dice')

    def test_strength_edits_never_present_normal_damage_as_an_enhanced_result(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides: 4, rule_archive=strength_fixture())
            hero = app.create(character_class='city-rat')
            for score in (22, 24, 31, 51):
                hero = app.set_attribute(hero['id'], revision=hero['revision'],
                                         attribute='PS', mode='fixed', value=score)
                view = app.combat_view(hero['id'])
                self.assertIsNone(view['totals']['damage']['value'])
                self.assertEqual(view['strength'], {'type': 'enhanced-fixture', **DESCRIPTION})
                self.assertNotIn('normal_strength', view['totals']['damage']['contributions'])
                self.assertTrue(view['unarmed'])
                self.assertTrue(all('descriptive' in row['damage'].lower() for row in view['unarmed']))
                self.assertTrue(any(DESCRIPTION['text'] in note for note in view['notes']))
                self.assertFalse(any('normal-human strength bonus' in note for note in view['notes']))
                self.assertNotIn('strength_type', hero)  # Projection owns the source rule, not duplicate save state.

    def test_equipment_keeps_source_md_and_does_not_cite_normal_human_damage(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides: 4, rule_archive=strength_fixture())
            hero = app.create(character_class='city-rat')
            hero = app.set_attribute(hero['id'], revision=hero['revision'], attribute='PS', mode='fixed', value=27)
            hero = app.set_equipment(hero['id'], revision=hero['revision'], inventory={'credits': 0, 'items': [
                {'id': str(uuid4()), 'item_id': identity, 'quantity': 1,
                 'location': 'carried', 'equipped': True, 'shots': None}
                for identity in ('knife-large', 'vibro-knife')]})
            rows = {row['item_id']: row for row in app.equipment_view(hero['id'])['melee_attacks']}
            self.assertIn('enhanced-strength', rows['knife-large']['damage'].lower())
            self.assertIsNone(rows['knife-large']['damage_bonus']['value'])
            self.assertIn(SOURCE, rows['knife-large']['damage_bonus']['sources'])
            self.assertFalse(any(source.get('section') == 'Normal human strength damage'
                                 for source in rows['knife-large']['damage_bonus']['sources']))
            self.assertEqual(rows['vibro-knife']['damage'], '1D6 M.D.')
            self.assertEqual(rows['vibro-knife']['damage_bonus']['value'], 0)

    def test_malformed_inactive_strength_rejects_before_dice_or_save(self):
        mutations: list[Callable[[dict[str, Any]], None]] = [
            replace_rule('strength_type', value)
            for value in (None, True, '', 'x' * 81, 'normal-human')]
        bad_descriptions: list[Any] = [None, [], {}, {**DESCRIPTION, 'extra': True},
                                      {**DESCRIPTION, 'name': ''}, {**DESCRIPTION, 'text': 'x' * 8001},
                                      {**DESCRIPTION, 'source': {'book': 'Missing section'}}]
        mutations += [replace_rule('strength_description', value) for value in bad_descriptions]
        mutations.append(lambda rules: rules.pop('strength_description'))
        for mutate in mutations:
            with self.subTest(mutate=mutate), tempfile.TemporaryDirectory() as directory:
                app = CharacterApplication(directory, die=self.no_roll, rule_archive=strength_fixture(mutate))
                with self.assertRaises(ValueError):
                    app.create(character_class='vagabond')
                self.assertEqual(app.list(), [])

    def test_advance_undo_reopen_portable_and_pdf_reuse_source_projection_without_dice(self):
        with tempfile.TemporaryDirectory() as directory:
            archive = strength_fixture()
            app = CharacterApplication(directory, die=lambda sides: 4, rule_archive=archive)
            hero = app.create(character_class='city-rat')
            hero = app.generate_resources(hero['id'], revision=hero['revision'])
            hero = app.advance(hero['id'], revision=hero['revision'], method='level', value=3)
            expected = app.combat_view(hero['id'])
            app.die = self.no_roll
            hero = app.undo_advancement(hero['id'], revision=hero['revision'])['character']
            hero = app.advance(hero['id'], revision=hero['revision'], method='level', value=3)
            self.assertEqual(app.combat_view(hero['id']), expected)
            reopened = CharacterApplication(directory, die=self.no_roll, rule_archive=archive)
            imported = reopened.import_character(reopened.export_character(hero['id']))
            self.assertEqual(reopened.combat_view(hero['id']), expected)
            self.assertEqual(reopened.combat_view(imported['id']), expected)
            fields = PdfReader(BytesIO(reopened.export_pdf(imported['id']))).get_fields()
            self.assertIsNotNone(fields)
            text = ' '.join(str(row.get('/V', '')) for row in (fields or {}).values())
            self.assertIn(DESCRIPTION['name'], text)
            self.assertIn('damage is descriptive', text)

    def test_other_profile_keeps_exact_legacy_views_and_save_shape(self):
        with tempfile.TemporaryDirectory() as baseline_dir, tempfile.TemporaryDirectory() as candidate_dir:
            baseline = CharacterApplication(baseline_dir, die=lambda sides: 4,
                                            rule_archive=strength_fixture(described=False))
            candidate = CharacterApplication(candidate_dir, die=lambda sides: 4, rule_archive=strength_fixture())
            old = baseline.create(character_class='vagabond')
            new = candidate.create(character_class='vagabond')
            for method in ('combat_view', 'skill_view', 'resource_view', 'equipment_view'):
                self.assertEqual(getattr(candidate, method)(new['id']), getattr(baseline, method)(old['id']))
            self.assertEqual(set(new), set(old))
            self.assertNotIn('strength', candidate.combat_view(new['id']))
            self.assertNotIn('strength_description', new)
