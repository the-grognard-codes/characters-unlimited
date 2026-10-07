import tempfile
import unittest
from copy import deepcopy
from io import BytesIO

from pypdf import PdfReader
from characters_unlimited.application import CharacterApplication
from characters_unlimited.storage import SaveConflict
from characters_unlimited.rules import RuleArchive


class AdvancementWorkflowTests(unittest.TestCase):
    def test_first_vagabond_level_preserves_starting_pe_and_advances_existing_skills(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides: 4)
            hero = app.create()
            hero = app.select_skills(hero['id'], revision=0, selections=[
                {'skill_id': 'swimming', 'pool': 'secondary'}])
            hero = app.generate_resources(hero['id'], revision=hero['revision'])
            hero = app.set_attribute(hero['id'], revision=hero['revision'], attribute='PE', mode='fixed', value=30)
            calls = []
            def gain(sides):
                calls.append(sides)
                return 1
            app.die = gain
            hero = app.advance(hero['id'], revision=hero['revision'], method='xp', value=1876)
            self.assertEqual(hero['level'], 2)
            self.assertEqual(calls, [6])
            self.assertEqual(app.resource_view(hero['id'])['resources']['HP']['value'], 19)
            self.assertEqual(app.resource_view(hero['id'])['resources']['SDC']['value'], 38)
            skills = app.skill_view(hero['id'])
            self.assertEqual(next(s for s in skills['selected'] if s['id'] == 'swimming')['percentage'], 55)
            self.assertEqual(next(s for s in skills['grants'] if s['id'] == 'cook')['percentage'], 55)
            self.assertEqual(next(s for s in skills['grants'] if s['id'] == 'eyeball')['percentage'], 59)
            self.assertEqual(app.combat_view(hero['id'])['totals']['parry']['value'], 2)
            copy = app.import_character(app.export_character(hero['id']))
            self.assertEqual(app.resource_view(copy['id']), app.resource_view(hero['id']))
            self.assertEqual(CharacterApplication(directory).skill_view(hero['id']), skills)
            fields = PdfReader(BytesIO(app.export_pdf(hero['id']))).get_fields()
            assert fields is not None
            self.assertEqual(fields['HIT POINTS']['/V'], '19')

    def test_late_skills_and_complete_undo_replay_keep_recorded_dice_and_recover_edits(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides: 4)
            hero = app.create(name='Before')
            hero = app.generate_resources(hero['id'], revision=0)
            before = deepcopy(hero)
            hero = app.advance(hero['id'], revision=hero['revision'], method='level', value=2)
            hero = app.select_skills(hero['id'], revision=hero['revision'], selections=[
                {'skill_id': 'swimming', 'pool': 'secondary'}])
            self.assertEqual(app.skill_view(hero['id'])['selected'][0]['percentage'], 50)
            hero = app.edit(hero['id'], revision=hero['revision'], name='After', notes='Keep this recovery copy')
            with self.assertRaises(SaveConflict):
                app.undo_advancement(hero['id'], revision=0)
            result = app.undo_advancement(hero['id'], revision=hero['revision'])
            restored = result['character']
            self.assertEqual(restored['name'], 'Before')
            self.assertEqual(restored['notes'], '')
            self.assertEqual(restored['level'], 1)
            self.assertNotIn('skill_selections', restored)
            self.assertEqual(restored['attributes'], before['attributes'])
            self.assertEqual(restored['resources'], before['resources'])
            recovery = app.get(result['recovery']['id'])
            self.assertEqual(recovery['name'], 'After')
            self.assertEqual(recovery['notes'], 'Keep this recovery copy')
            copied = app.import_character(app.export_character(restored['id']))
            app.die = lambda sides: self.fail('Replay must reuse recorded advancement die')
            replayed = app.advance(copied['id'], revision=copied['revision'], method='level', value=2)
            self.assertEqual(app.resource_view(replayed['id'])['resources']['HP']['value'], 22)
            self.assertEqual(replayed['id'], copied['id'])

    def test_rejects_inconsistent_history_and_keeps_historic_rule_pins_for_undo(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides: 4)
            hero = app.create()
            hero = app.generate_resources(hero['id'], revision=0)
            hero = app.advance(hero['id'], revision=hero['revision'], method='level', value=2)
            bundle = app.export_character(hero['id'])
            for mutation in ('missing', 'die', 'source', 'snapshot', 'learning', 'nested'):
                bad = deepcopy(bundle)
                character = bad['character']
                if mutation == 'missing':
                    del character['advancement']
                elif mutation == 'die':
                    character['advancement']['hp_roll'] = True
                elif mutation == 'source':
                    character['advancement']['source']['pages'] = [1]
                elif mutation == 'snapshot':
                    character['advancement']['before']['resources']['HP']['contributions'][0]['value'] = 999
                elif mutation == 'learning':
                    character['learning_levels']['["weapon", "unknown", ""]'] = 1
                else:
                    character['advancement']['before']['advancement'] = {}
                with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                    app.import_character(bad)
            archive = RuleArchive.load()
            correction = archive.active('rifts-domestic-skills')
            correction['version'] = '99.2.0'
            next(s for s in correction['skills'] if s['id'] == 'cook')['base'] += 1
            for profile in correction.get('class_profiles', {}).values():
                for grant in profile.get('required', {}).get('grants', []):
                    if grant.get('catalog_skill_id', grant.get('id')) == 'cook':
                        grant['base'] += 1
            newer = CharacterApplication(directory, rule_archive=RuleArchive([*archive.definitions(), correction],
                {**archive.active_versions(), 'rifts-domestic-skills': '99.2.0'}))
            preview = newer.preview_rule_upgrade(hero['id'])
            hero = newer.apply_rule_upgrade(hero['id'], revision=hero['revision'], token=preview['token'])['character']
            portable = newer.export_character(hero['id'])
            versions = {p['version'] for p in portable['rule_packs'] if p['id'] == 'rifts-domestic-skills'}
            self.assertEqual(versions, {'2.34.0', '99.2.0'})
            copy = newer.import_character(portable)
            restored = newer.undo_advancement(copy['id'], revision=copy['revision'])['character']
            self.assertEqual(restored['additional_rule_packs']['rifts-domestic-skills'], '2.34.0')

    def test_all_current_training_styles_and_proficiencies_use_the_original_level_two_tables(self):
        # Expected values are read from printed pp. 327, 347-348, and 360.
        for style, expected in [('basic', (4, 0, 0, 2, 2, 2)),
                                ('expert', (4, 0, 0, 3, 3, 3)),
                                ('martial-arts', (4, 0, 2, 3, 3, 3)),
                                ('assassin', (5, 1, 2, 0, 0, 0))]:
            with self.subTest(style=style), tempfile.TemporaryDirectory() as directory:
                app = CharacterApplication(directory, die=lambda sides: 4)
                hero = app.create()
                hero = app.select_combat(hero['id'], revision=0, choices={
                    'hand_to_hand': style, 'ancient': ['knife', 'sword'],
                    'modern': ['handguns', 'energy-pistol', 'energy-rifle']})
                hero = app.generate_resources(hero['id'], revision=hero['revision'])
                hero = app.advance(hero['id'], revision=hero['revision'], method='level', value=2)
                combat = app.combat_view(hero['id'])
                self.assertEqual(tuple(combat['totals'][stat]['value'] for stat in
                    ('attacks', 'initiative', 'strike', 'parry', 'dodge', 'pull_punch')), expected)
                self.assertEqual([w['single']['value'] for w in combat['shooting']], [1, 1, 1])
                self.assertEqual([w['strike']['contributions']['weapon_proficiency'] for w in combat['melee']], [1, 1])
                self.assertEqual([w['parry']['contributions']['weapon_proficiency'] for w in combat['melee']], [1, 1])
                if style == 'martial-arts':
                    karate = next(m for m in combat['unarmed'] if m['id'] == 'karate-punch')
                    self.assertEqual(karate['damage'], '2D4 S.D.C.')
                    self.assertEqual(next(m for m in combat['unarmed'] if m['id'] == 'martial-backhand')['damage'], '1D6 S.D.C.')
                    self.assertEqual(next(m for m in combat['unarmed'] if m['id'] == 'power-karate-punch')['actions'], 2)
                    fields = PdfReader(BytesIO(app.export_pdf(hero['id']))).get_fields()
                    assert fields is not None
                    self.assertIn('Karate punch', ' '.join(str(f.get('/V', '')) for f in fields.values()))
                hero = app.select_combat(hero['id'], revision=hero['revision'], choices={
                    'hand_to_hand': 'expert' if style == 'basic' else style})
                if style == 'basic':
                    self.assertEqual(app.combat_view(hero['id'])['totals']['parry']['value'], 0)

    def test_xp_without_level_gain_creation_at_two_and_rejected_requests_do_not_lose_state(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides: 4)
            hero = app.create(level=2)
            self.assertEqual(hero['level'], 2)
            self.assertEqual(app.resource_view(hero['id'])['resources']['HP']['value'], 22)
            initial = app.create()
            initial = app.advance(initial['id'], revision=0, method='xp', value=1875)
            self.assertEqual(initial['level'], 1)
            self.assertEqual(initial['experience'], 1875)
            self.assertNotIn('resources', initial)
            for method, value in [('xp', -1), ('xp', 3751), ('level', 3), ('level', True)]:
                with self.subTest(method=method, value=value), self.assertRaises(ValueError):
                    app.advance(initial['id'], revision=initial['revision'], method=method, value=value)
                self.assertEqual(app.get(initial['id']), initial)
            app.die = lambda sides: self.fail('Changing XP within level two cannot roll a gain')
            updated = app.advance(hero['id'], revision=hero['revision'], method='xp', value=3750)
            self.assertEqual(updated['experience'], 3750)
            self.assertEqual(app.resource_view(hero['id'])['resources']['HP']['value'], 22)
            with self.assertRaises(ValueError):
                app.advance(updated['id'], revision=updated['revision'], method='xp', value=0)

    def test_invalid_gain_old_pins_manual_resources_and_learned_level_choices_preserve_history(self):
        with tempfile.TemporaryDirectory() as directory:
            archive = RuleArchive.load()
            old = CharacterApplication(directory, die=lambda sides: 4, rule_archive=RuleArchive(
                archive.definitions(), {**archive.active_versions(), 'rifts-domestic-skills': '2.4.0'}))
            hero = old.create()
            hero = old.generate_resources(hero['id'], revision=0)
            app = CharacterApplication(directory, die=lambda sides: 4)
            with self.assertRaises(ValueError):
                app.advance(hero['id'], revision=hero['revision'], method='level', value=2)
            preview = app.preview_rule_upgrade(hero['id'])
            hero = app.apply_rule_upgrade(hero['id'], revision=hero['revision'], token=preview['token'])['character']
            hero = app.set_resource(hero['id'], revision=hero['revision'], resource='HP', mode='fixed', value=100)
            before = deepcopy(hero)
            for face in (0, 7, True):
                app.die = lambda sides: face
                with self.assertRaises(ValueError):
                    app.advance(hero['id'], revision=hero['revision'], method='level', value=2)
                self.assertEqual(app.get(hero['id']), before)
            app.die = lambda sides: 1
            hero = app.advance(hero['id'], revision=hero['revision'], method='level', value=2)
            self.assertEqual(app.resource_view(hero['id'])['resources']['HP']['value'], 100)
            hero = app.set_resource(hero['id'], revision=hero['revision'], resource='HP', mode='adjustment', value=5)
            self.assertEqual(app.resource_view(hero['id'])['resources']['HP']['value'], 24)
            selection = [{'skill_id': 'instrument', 'pool': 'secondary', 'specialty': ' Bass  Guitar '}]
            hero = app.select_skills(hero['id'], revision=hero['revision'], selections=selection, learned_level=1)
            self.assertEqual(app.skill_view(hero['id'])['selected'][0]['contributions']['advancement'], 5)
            hero = app.select_skills(hero['id'], revision=hero['revision'], selections=[])
            selection[0]['specialty'] = 'bass guitar'
            hero = app.select_skills(hero['id'], revision=hero['revision'], selections=selection)
            self.assertEqual(app.skill_view(hero['id'])['selected'][0]['contributions']['advancement'], 5)
            portable = app.export_character(hero['id'])
            del portable['character']['learning_levels']['["skill", "instrument", "bass guitar"]']
            with self.assertRaises(ValueError):
                app.import_character(portable)
