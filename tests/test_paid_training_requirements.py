"""Paid training counts once within a source-owned initial skill minimum."""

from copy import deepcopy
from io import BytesIO
import tempfile
import unittest
from typing import Any, Callable

from pypdf import PdfReader
from characters_unlimited.application import CharacterApplication
from characters_unlimited.advancement import learning_key
from tests.test_owned_class_profiles import owned_pack, archive_with


SOURCE = {'book': 'Rifts - Ultimate Edition', 'pages': [88, 316],
          'section': 'City Rat initial Physical/Rogue choices and Physical training'}
STYLES = ['expert', 'martial-arts', 'assassin']


def requirement_fixture(mutation=None, *, paid=True):
    pack = owned_pack()
    profile = pack['class_profiles']['city-rat']
    requirement: dict[str, Any] = {'id': 'initial-physical-rogue', 'name': 'Initial Physical/Rogue choices',
                   'count': 3 if paid else 2, 'selector': {'any_of': [{'ids': ['climbing', 'prowl']}]},
                   'before_level': 2, 'source': deepcopy(SOURCE)}
    if paid:
        requirement['paid_hand_to_hand'] = list(STYLES)
    profile['pools']['related']['requirements'] = [requirement]
    if mutation:
        mutation(profile, requirement)
    return archive_with(pack)


def selections(*identities, pool='related'):
    return [{'skill_id': identity, 'pool': pool, 'specialty': ''} for identity in identities]


class PaidTrainingRequirementTests(unittest.TestCase):
    def requirement(self, app, hero):
        return app.skill_view(hero['id'])['pool_requirements'][0]

    def test_one_distinct_style_credit_is_independent_of_its_slot_cost(self):
        for style, credit, slots in [('basic', 2, 8), ('expert', 3, 7),
                                      ('martial-arts', 3, 6), ('assassin', 3, 6)]:
            with self.subTest(style=style), tempfile.TemporaryDirectory() as directory:
                app = CharacterApplication(directory, die=lambda sides: 4,
                                           rule_archive=requirement_fixture())
                hero = app.create(character_class='city-rat')
                self.assertEqual(self.requirement(app, hero)['remaining'], 3)
                hero = app.select_skills(hero['id'], revision=hero['revision'],
                                         selections=selections('climbing', 'prowl'))
                hero = app.select_combat(hero['id'], revision=hero['revision'],
                                         choices={'hand_to_hand': style})
                view = app.skill_view(hero['id'])
                row = self.requirement(app, hero)
                self.assertEqual((row['credited'], row['remaining']), (credit, 3-credit))
                self.assertEqual(view['remaining']['related'], slots)
                self.assertEqual({item['id']: item['percentage'] for item in view['selected']},
                                 {'climbing': 45, 'prowl': 40})
                self.assertEqual(len(row['training_credits']), 0 if style == 'basic' else 1)
                if style != 'basic':
                    self.assertEqual(row['training_credits'][0]['id'], style)
                    self.assertEqual(row['training_credits'][0]['learned_level'], 1)
                    self.assertEqual(row['training_credits'][0]['source'], SOURCE)
                hero = app.generate_resources(hero['id'], revision=hero['revision'])
                resources = app.resource_view(hero['id'])['resources']
                self.assertEqual((resources['HP']['value'], resources['SDC']['value']), (17, 32))

    def test_paid_style_alone_is_one_choice_and_free_or_duplicate_choices_do_not_fill_it(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides: 4,
                                       rule_archive=requirement_fixture())
            hero = app.create(character_class='city-rat')
            self.assertEqual(self.requirement(app, hero)['credited'], 0)  # Free Running and Basic.
            hero = app.select_combat(hero['id'], revision=hero['revision'],
                                     choices={'hand_to_hand': 'martial-arts'})
            self.assertEqual((self.requirement(app, hero)['credited'],
                              app.skill_view(hero['id'])['remaining']['related']), (1, 8))
            hero = app.select_skills(hero['id'], revision=hero['revision'], selections=[
                *selections('climbing', 'climbing'), *selections('prowl', pool='secondary')])
            row = self.requirement(app, hero)
            self.assertEqual((row['credited'], row['remaining'], row['duplicates']), (2, 1, True))

    def test_paid_weapon_slots_do_not_credit_free_basic_training(self):
        def paid_weapons(profile, requirement):
            profile['combat']['additional_proficiency_cost'] = 1
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides: 4,
                                       rule_archive=requirement_fixture(paid_weapons))
            hero = app.create(character_class='city-rat')
            hero = app.select_combat(hero['id'], revision=hero['revision'], choices={
                'hand_to_hand': 'basic', 'ancient': ['knife', 'sword']})
            self.assertEqual(app.skill_view(hero['id'])['remaining']['related'], 9)
            self.assertEqual(self.requirement(app, hero)['credited'], 0)

    def test_acquisition_level_not_elapsed_age_controls_initial_credit_and_portable_replay(self):
        for learned in (1, 3):
            with self.subTest(learned=learned), tempfile.TemporaryDirectory() as directory, tempfile.TemporaryDirectory() as copied:
                archive = requirement_fixture()
                app = CharacterApplication(directory, die=lambda sides: 4, rule_archive=archive)
                hero = app.create(character_class='city-rat')
                hero = app.select_skills(hero['id'], revision=hero['revision'],
                                         selections=selections('climbing', 'prowl'))
                hero = app.generate_resources(hero['id'], revision=hero['revision'])
                hero = app.advance(hero['id'], revision=hero['revision'], method='level', value=3)
                hero = app.select_combat(hero['id'], revision=hero['revision'],
                                         choices={'hand_to_hand': 'expert'}, learned_level=learned)
                self.assertEqual(hero['learning_levels'][learning_key('hand', 'expert')], learned)
                row = self.requirement(app, hero)
                self.assertEqual(row['credited'], 3 if learned == 1 else 2)
                self.assertEqual(row['remaining'], 0 if learned == 1 else 1)
                before = deepcopy(app.get(hero['id']))
                def no_roll(sides):
                    self.fail('Requirement projection/reopen/import must not roll')
                app.die = no_roll
                self.assertEqual(self.requirement(app, hero), row)
                other = CharacterApplication(copied, die=no_roll, rule_archive=archive)
                restored = other.import_character(app.export_character(hero['id']))
                self.assertEqual(self.requirement(other, restored), row)
                reopened = CharacterApplication(directory, die=no_roll, rule_archive=archive)
                self.assertEqual(self.requirement(reopened, hero), row)
                self.assertEqual(app.get(hero['id']), before)

    def test_initial_record_survives_advance_undo_and_style_reselection(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides: 4,
                                       rule_archive=requirement_fixture())
            hero = app.create(character_class='city-rat')
            hero = app.select_skills(hero['id'], revision=hero['revision'],
                                     selections=selections('climbing', 'prowl'))
            hero = app.select_combat(hero['id'], revision=hero['revision'],
                                     choices={'hand_to_hand': 'expert'})
            hero = app.generate_resources(hero['id'], revision=hero['revision'])
            hero = app.advance(hero['id'], revision=hero['revision'], method='level', value=3)
            self.assertEqual(self.requirement(app, hero)['credited'], 3)
            hero = app.undo_advancement(hero['id'], revision=hero['revision'])['character']
            self.assertEqual(self.requirement(app, hero)['credited'], 3)
            hero = app.select_combat(hero['id'], revision=hero['revision'], choices={'hand_to_hand': 'basic'})
            self.assertEqual(self.requirement(app, hero)['credited'], 2)
            hero = app.select_combat(hero['id'], revision=hero['revision'], choices={'hand_to_hand': 'expert'})
            self.assertEqual(hero['learning_levels'][learning_key('hand', 'expert')], 1)
            self.assertEqual(self.requirement(app, hero)['credited'], 3)

    def test_malformed_unselected_training_or_impossible_capacity_rejects_before_dice(self):
        mutations: list[Callable[..., Any]] = [lambda p, r, value=value: r.update(paid_hand_to_hand=value)
                     for value in (None, [], True, ['expert', 'expert'], ['unknown'], ['basic'])]
        mutations += [lambda p, r: r.update(count=4),
                      lambda p, r: r.update(counting='distinct-specialties'),
                      lambda p, r: p['pools']['secondary'].update(requirements=p['pools']['related'].pop('requirements')),
                      lambda p, r: next(row for row in p['combat']['hand_to_hand'] if row['id'] == 'expert').update(cost=True),
                      lambda p, r: next(row for row in p['combat']['hand_to_hand'] if row['id'] == 'expert').update(cost=1001),
                      lambda p, r: next(row for row in p['combat']['hand_to_hand'] if row['id'] == 'expert').update(name=None),
                      lambda p, r: next(row for row in p['combat']['hand_to_hand'] if row['id'] == 'expert').pop('name')]
        for mutation in mutations:
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as directory:
                def no_roll(sides):
                    self.fail('Malformed inactive training must reject before dice')
                app = CharacterApplication(directory, die=no_roll,
                                           rule_archive=requirement_fixture(mutation))
                with self.assertRaises(ValueError):
                    app.create(character_class='vagabond')
                self.assertEqual(app.list(), [])

    def test_legacy_requirement_shape_has_no_training_fields(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides: 4,
                                       rule_archive=requirement_fixture(paid=False))
            hero = app.create(character_class='city-rat')
            hero = app.select_skills(hero['id'], revision=hero['revision'], selections=selections('climbing'))
            row = self.requirement(app, hero)
            self.assertEqual(row, {
                'id': 'initial-physical-rogue', 'name': 'Initial Physical/Rogue choices', 'count': 2,
                'selector': {'any_of': [{'ids': ['climbing', 'prowl']}]}, 'before_level': 2,
                'source': SOURCE, 'pool': 'related', 'eligible': ['climbing'], 'credited': 1,
                'remaining': 1, 'unresolved': [], 'outside': [], 'duplicates': False})

    def test_pdf_explains_distinct_credit_and_initial_cutoff_without_mutating_the_save(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides: 4,
                                       rule_archive=requirement_fixture())
            hero = app.create(character_class='city-rat')
            hero = app.select_skills(hero['id'], revision=hero['revision'],
                                     selections=selections('climbing', 'prowl'))
            hero = app.select_combat(hero['id'], revision=hero['revision'],
                                     choices={'hand_to_hand': 'martial-arts'})
            before = deepcopy(app.get(hero['id']))
            def no_roll(sides):
                self.fail('Exported requirement explanations must not roll')
            app.die = no_roll
            fields = PdfReader(BytesIO(app.export_pdf(hero['id']))).get_fields()
            assert fields is not None
            text = ' '.join(' '.join(str(field.get('/V', '')) for field in fields.values()).split())
            self.assertIn('3 qualifying related choices (minimum 3); 0 still required.', text)
            self.assertIn('counts as one choice (learned at level 1).', text)
            self.assertIn('Only choices learned before level 2 count.', text)
            self.assertEqual(app.get(hero['id']), before)


if __name__ == '__main__':
    unittest.main()
