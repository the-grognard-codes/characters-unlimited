from copy import deepcopy
import tempfile
import unittest
from io import BytesIO

from pypdf import PdfReader
from characters_unlimited.application import CharacterApplication
from characters_unlimited.ability_paths import update_path
from characters_unlimited.rules import RuleArchive


class NaturalPsionicTests(unittest.TestCase):
    def test_accepted_source_conditions_and_metadata(self):
        pack = RuleArchive.load().active('rifts-natural-psionics')
        options = {row['id']: row for row in pack['catalog']['options']}
        self.assertIn('2 ISP into 1 PPE', options['restore-p-p-e']['description'])
        self.assertIn('14 ISP', options['restore-p-p-e']['description'])
        self.assertIn('combat bonuses are halved', options['stop-bleeding']['description'])
        self.assertIn('3D4 melee', options['nightvision']['description'])
        self.assertIn('24 hours', options['remote-viewing']['description'])
        self.assertIn('only once', options['object-read']['description'])
        self.assertIn('printed header instead says 2', options['total-recall']['description'])
        for row in options.values():
            params = {part['name']: part['text'] for part in row['parameters']}
            self.assertIn('Duration', params, row['name'])
            self.assertTrue(any(name.startswith(('I.S.P.', 'L.S.P.')) for name in params), row['name'])
            self.assertNotIn(chr(0x00c3), row['description'])
            self.assertNotIn('TLnr', row['description'])
            self.assertNotIn('kr or or or', row['description'])
        empathy = {part['name']: part['text'] for part in options['empathy']['parameters']}
        self.assertEqual(empathy['I.S.P.'], '4')

    def no_roll(self, sides):
        self.fail('Recorded potential and ISP must not reroll')

    def test_source_catalog_and_minor_selection_retention_portable_and_pdf(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides: 4)
            character = app.create('Minor psychic witness')
            app.die = lambda sides: 15 if sides == 100 else 4
            character = app.select_psionics(character['id'], revision=character['revision'], roll=True)
            app.die = self.no_roll
            character = app.select_psionics(character['id'], revision=character['revision'],
                categories=['Healing'], selections=['healing-touch', 'meditation'])
            view = app.psionic_view(character['id'])
            self.assertEqual(len(view['catalog']), 56)
            self.assertEqual(sum('Healing' in row['tags'] for row in view['catalog']), 15)
            self.assertEqual(sum('Physical' in row['tags'] for row in view['catalog']), 21)
            self.assertEqual(sum('Sensitive' in row['tags'] for row in view['catalog']), 24)
            self.assertEqual(view['resources']['ISP']['value'], 20)
            self.assertEqual(view['save_target'], 12)
            self.assertIn('0 choices remaining', view['guidance'][0])
            original = deepcopy(character['psionics']['resource_record'])
            character = app.select_psionics(character['id'], revision=character['revision'], enabled=False)
            self.assertEqual(app.psionic_view(character['id'])['resources'], {})
            self.assertEqual(app.psionic_view(character['id'])['save_target'], 15)
            character = app.select_psionics(character['id'], revision=character['revision'], enabled=True)
            self.assertEqual(character['psionics']['resource_record'], original)
            reopened = CharacterApplication(directory, die=self.no_roll)
            self.assertEqual(reopened.psionic_view(character['id'])['resources']['ISP']['value'], 20)
            bundle = app.export_character(character['id'])
            imported = app.import_character(bundle)
            self.assertEqual(app.psionic_view(imported['id'])['resources']['ISP']['value'], 20)
            fields = PdfReader(BytesIO(app.export_pdf(imported['id']))).get_fields()
            assert fields is not None
            values = ' '.join(str(row.get('/V', '')) for row in fields.values())
            self.assertIn('Healing Touch', values)
            self.assertIn('Inner Strength Points: 20', values)
            self.assertIn('save target 12', values)
            self.assertEqual(fields['ISP']['/V'], '20')
            self.assertEqual(fields['ISP_2']['/V'], '20')

    def test_major_growth_undo_and_replay_keep_every_level_roll(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides: 4)
            character = app.create()
            character = app.generate_resources(character['id'], revision=character['revision'])
            app.die = lambda sides: 5 if sides == 100 else 4
            character = app.select_psionics(character['id'], revision=character['revision'], roll=True)
            self.assertEqual(app.psionic_view(character['id'])['resources']['ISP']['value'], 28)
            character = app.select_psionics(character['id'], revision=character['revision'], mode='mixed',
                categories=['Healing', 'Sensitive'], selections=['healing-touch', 'deaden-pain', 'meditation',
                    'telepathy', 'see-aura', 'empathy'])
            self.assertIn('0 choices remaining', app.psionic_view(character['id'])['guidance'][0])
            character = app.advance(character['id'], revision=character['revision'], method='level', value=2)
            self.assertEqual(app.psionic_view(character['id'])['resources']['ISP']['value'], 33)
            character = app.undo_advancement(character['id'], revision=character['revision'])['character']
            self.assertEqual(app.psionic_view(character['id'])['resources']['ISP']['value'], 28)
            app.die = self.no_roll
            character = app.advance(character['id'], revision=character['revision'], method='level', value=2)
            self.assertEqual(app.psionic_view(character['id'])['resources']['ISP']['value'], 33)
            self.assertEqual(character['psionics']['gains']['2']['resource_gains']['ISP']['rolls'], [4])
            app.die = lambda sides: 4
            character = app.advance(character['id'], revision=character['revision'], method='level', value=4)
            self.assertEqual(app.psionic_view(character['id'])['resources']['ISP']['value'], 43)
            copy = app.import_character(app.export_character(character['id']))
            self.assertEqual(app.psionic_view(copy['id'])['resources']['ISP']['value'], 43)

    def test_effective_me_is_recorded_once_and_forged_source_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides: 4)
            character = app.create()
            character = app.set_attribute(character['id'], revision=character['revision'],
                attribute='ME', mode='fixed', value=24)
            app.die = lambda sides: 15 if sides == 100 else 4
            character = app.select_psionics(character['id'], revision=character['revision'], roll=True)
            self.assertEqual(app.psionic_view(character['id'])['resources']['ISP']['value'], 32)
            character = app.set_attribute(character['id'], revision=character['revision'],
                attribute='ME', mode='fixed', value=30)
            self.assertEqual(app.psionic_view(character['id'])['resources']['ISP']['value'], 32)
            bundle = app.export_character(character['id'])
            bundle['character']['psionics']['resource_record']['resource_attribute_snapshot']['ME']['explanation']['source']['book'] = 'Forged'
            with self.assertRaises(ValueError):
                app.import_character(bundle)

    def test_whole_profile_and_inactive_receipts_reject_before_dice(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides: 4)
            character = app.create()
            pack = app.rule_archive.active('rifts-natural-psionics')
            bad = deepcopy(pack)
            bad['paths'][2]['growth']['ISP']['formula']['count'] = True
            with self.assertRaises(ValueError):
                update_path(character, bad, None, self.no_roll, roll=True)
            bad = deepcopy(pack)
            bad['paths'][0]['growth'] = None
            with self.assertRaises(ValueError):
                update_path(character, bad, None, self.no_roll, roll=True)
            state = update_path(character, pack, None, lambda sides: 15 if sides == 100 else 4, roll=True)
            state['enabled'] = False
            invalid = {**state, 'abilities': None}
            with self.assertRaises(ValueError):
                update_path(character, pack, invalid, self.no_roll, enabled=True)
            state['resource_record']['resources']['ISP']['contributions'][1]['rolls'][0] = 7
            with self.assertRaises(ValueError):
                update_path(character, pack, state, self.no_roll, enabled=True)
            with self.assertRaises(ValueError):
                update_path(character, pack, None, self.no_roll, roll=True, categories=['Unknown'])
            hero = app.create(game='heroes-unlimited')
            app.die = self.no_roll
            with self.assertRaises(ValueError):
                app.select_psionics(hero['id'], revision=hero['revision'], roll=True)

    def test_nonpsychic_outcome_and_skip_preserve_exact_receipts(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides: 4)
            character = app.create()
            character = app.select_psionics(character['id'], revision=character['revision'], enabled=False)
            self.assertIsNone(character['psionics']['face'])
            app.die = lambda sides: 100
            character = app.select_psionics(character['id'], revision=character['revision'], roll=True)
            view = app.psionic_view(character['id'])
            self.assertEqual(view['path'], 'Not psychic')
            self.assertEqual(view['resources'], {})
            self.assertEqual(view['save_target'], 15)
            app.die = self.no_roll
            with self.assertRaises(ValueError):
                app.select_psionics(character['id'], revision=character['revision'], roll=True)
