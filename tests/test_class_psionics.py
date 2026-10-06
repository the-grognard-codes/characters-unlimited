import tempfile
import unittest
import json
import threading
from copy import deepcopy
from io import BytesIO
from pypdf import PdfReader
from characters_unlimited.application import CharacterApplication
from characters_unlimited.rules import RuleArchive
from characters_unlimited.server import create_server
from urllib.request import Request, urlopen
from urllib.error import HTTPError


class ClassPsionicTests(unittest.TestCase):
    def no_roll(self, sides):
        self.fail('Retained psychic receipts must not reroll')

    def test_class_power_endpoint_is_protected_revision_checked_and_saved(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides: 2)
            hero = app.create(character_class='psi-operator')
            app.die = self.no_roll
            server = create_server(app)
            worker = threading.Thread(target=server.serve_forever, daemon=True)
            worker.start()
            try:
                base = f'http://127.0.0.1:{server.server_port}'
                with urlopen(base+'/api/bootstrap', timeout=5) as response:
                    token = json.load(response)['token']
                path = base+'/api/characters/'+hero['id']+'/class-psionics'
                body = json.dumps({'revision': 0, 'selections': ['telemechanics', 'total-recall', 'sense-time']}).encode()
                with self.assertRaises(HTTPError) as denied:
                    urlopen(Request(path, data=body), timeout=5)
                self.assertEqual(denied.exception.code, 403)
                denied.exception.close()
                headers = {'Content-Type': 'application/json', 'X-Session-Token': token, 'Origin': base}
                with urlopen(Request(path, data=body, headers=headers), timeout=5) as response:
                    saved = json.load(response)
                self.assertEqual(saved['revision'], 1)
                with self.assertRaises(HTTPError) as stale:
                    urlopen(Request(path, data=body, headers=headers), timeout=5)
                self.assertEqual(stale.exception.code, 409)
                stale.exception.close()
                with urlopen(base+'/api/characters/'+hero['id']+'/psionics', timeout=5) as response:
                    view = json.load(response)
                self.assertEqual(view['class_entitlement']['selection_group']['remaining'], 0)
                self.assertEqual(view['effective']['resources']['ISP']['value'], 14)
                self.assertEqual(app.get(hero['id']), saved)
            finally:
                server.shutdown(); server.server_close(); worker.join()

    def test_fixed_major_both_lifestyles_preserve_source_allowances_and_no_percentile(self):
        for identity in ('psi-operator', 'psi-operator-city'):
            with self.subTest(identity=identity), tempfile.TemporaryDirectory() as directory:
                calls = []
                def die(sides):
                    calls.append(sides)
                    return 2
                app = CharacterApplication(directory, die=die)
                hero = app.create(character_class=identity)
                self.assertNotIn(100, calls)
                self.assertIsNone(hero['class_psionics']['face'])
                view = app.psionic_view(hero['id'])
                self.assertEqual(len(view['class_entitlement']['catalog']), 11)
                self.assertEqual(view['effective']['resources']['ISP']['value'], 14)
                self.assertEqual(view['effective']['save_target'], 12)
                self.assertEqual(app.skill_view(hero['id'])['remaining'], {'related': 4, 'secondary': 4})
                app.die = self.no_roll
                hero = app.select_class_psionics(hero['id'], revision=hero['revision'],
                    selections=['telemechanics', 'total-recall', 'sense-time'])
                projected = app.psionic_view(hero['id'])['class_entitlement']
                self.assertEqual(projected['selection_group']['remaining'], 0)
                self.assertFalse(any('categories with no' in note for note in projected['guidance']))
                recall = next(row for row in projected['abilities'] if row['id'] == 'total-recall')
                self.assertEqual(next(row['text'] for row in recall['parameters'] if row['name'] == 'I.S.P.'), 'I.S.P.: 2')
                original = deepcopy(hero['class_psionics'])
                reopened = CharacterApplication(directory, die=self.no_roll)
                imported = reopened.import_character(app.export_character(hero['id']))
                self.assertEqual(imported['class_psionics'], original)

    def test_weighted_excess_and_prerequisites_remain_guidance_with_retained_choices(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides: 2)
            hero = app.create(character_class='psi-operator')
            app.die = self.no_roll
            hero = app.select_class_psionics(hero['id'], revision=hero['revision'], selections=['telemechanic-paralysis'])
            view = app.psionic_view(hero['id'])['class_entitlement']
            self.assertEqual(view['selection_group']['credited'], 2)
            self.assertFalse(view['abilities'][0]['requirements'][0]['satisfied'])
            chosen = ['telemechanic-paralysis', 'telemechanics', 'electrokinesis']
            hero = app.select_class_psionics(hero['id'], revision=hero['revision'], selections=chosen)
            view = app.psionic_view(hero['id'])['class_entitlement']
            self.assertEqual(view['selection_group']['remaining'], -2)
            self.assertTrue(view['abilities'][0]['requirements'][0]['satisfied'])
            acquired = deepcopy(hero['class_psionics']['abilities']['acquisitions'])
            hero = app.select_class_psionics(hero['id'], revision=hero['revision'], selections=[])
            hero = app.select_class_psionics(hero['id'], revision=hero['revision'], selections=chosen)
            self.assertEqual(hero['class_psionics']['abilities']['acquisitions'], acquired)

    def test_natural_none_minor_major_and_skip_never_replace_or_double_the_class_reserve(self):
        for face, natural_isp in ((80, None), (15, 10), (1, 14)):
            with self.subTest(face=face), tempfile.TemporaryDirectory() as directory:
                app = CharacterApplication(directory, die=lambda sides: 2)
                hero = app.create(character_class='psi-operator')
                source = deepcopy(hero['class_psionics']['resource_record'])
                app.die = lambda sides: face if sides == 100 else 2
                hero = app.select_psionics(hero['id'], revision=hero['revision'], roll=True)
                view = app.psionic_view(hero['id'])
                self.assertEqual(view['resources'].get('ISP', {}).get('value'), natural_isp)
                self.assertEqual(view['effective']['resources']['ISP']['value'], 14)
                self.assertEqual(view['effective']['save_target'], 12)
                self.assertEqual(hero['class_psionics']['resource_record'], source)
                app.die = self.no_roll
                hero = app.select_psionics(hero['id'], revision=hero['revision'], enabled=False)
                self.assertEqual(app.psionic_view(hero['id'])['effective']['resources']['ISP']['value'], 14)

    def test_growth_halved_skill_awards_and_undo_replay_retain_every_die(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides: 2)
            hero = app.create(character_class='psi-operator')
            hero = app.generate_resources(hero['id'], revision=hero['revision'])
            hero = app.advance(hero['id'], revision=hero['revision'], method='level', value=4)
            self.assertEqual(app.psionic_view(hero['id'])['effective']['resources']['ISP']['value'], 23)
            self.assertEqual(app.psionic_view(hero['id'])['class_entitlement']['selection_group']['remaining'], 4)
            self.assertEqual(app.skill_view(hero['id'])['remaining'], {'related': 5, 'secondary': 5})
            gains = deepcopy(hero['class_psionics']['gains'])
            hero = app.select_class_psionics(hero['id'], revision=hero['revision'], selections=['electrokinesis'])
            result = app.undo_advancement(hero['id'], revision=hero['revision'])
            hero = result['character']
            self.assertEqual(hero['level'], 3)
            self.assertEqual(hero['class_psionics']['gains'], gains)
            self.assertEqual(hero['class_psionics']['abilities']['selections'], [])
            app.die = self.no_roll
            hero = app.advance(hero['id'], revision=hero['revision'], method='level', value=4)
            self.assertEqual(hero['class_psionics']['gains'], gains)
            self.assertEqual(app.psionic_view(hero['id'])['effective']['resources']['ISP']['value'], 23)
            imported = app.import_character(app.export_character(hero['id']))
            self.assertEqual(imported['class_psionics'], hero['class_psionics'])

    def test_both_power_origins_and_authoritative_isp_survive_editable_pdf(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides: 2)
            hero = app.create(character_class='psi-operator')
            hero = app.select_class_psionics(hero['id'], revision=hero['revision'], selections=['object-read'])
            app.die = lambda sides: 15 if sides == 100 else 2
            hero = app.select_psionics(hero['id'], revision=hero['revision'], roll=True)
            hero = app.select_psionics(hero['id'], revision=hero['revision'], categories=['Sensitive'], selections=['object-read'])
            view = app.psionic_view(hero['id'])
            self.assertEqual([row['id'] for row in view['effective']['abilities']], ['object-read', 'object-read'])
            self.assertIn('limited to', view['effective']['abilities'][0]['description'])
            self.assertNotIn('Class grant is limited', view['effective']['abilities'][1]['description'])
            fields = PdfReader(BytesIO(app.export_pdf(hero['id']))).get_fields()
            assert fields is not None
            self.assertEqual(fields['ISP']['/V'], '14')
            notes = ' '.join(str(row.get('/V', '')) for row in fields.values())
            self.assertIn('Class psychic powers: Major class psychic', notes)
            self.assertIn('Natural psionics: Minor psychic', notes)
            self.assertIn('not added again', notes)

    def test_explicit_null_inactive_binding_rejects_before_dice_or_save(self):
        installed = RuleArchive.load()
        bad = installed.active('rifts-core')
        next(row for row in bad['classes'] if row['id'] == 'psi-operator')['ability_path'] = None
        archive = RuleArchive([bad if row['id'] == bad['id'] and row['version'] == bad['version'] else row
                               for row in installed.definitions()], installed.active_versions())
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=self.no_roll, rule_archive=archive)
            with self.assertRaisesRegex(ValueError, 'exact source dependency identities'):
                app.create(character_class='operator')
            self.assertEqual(app.list(), [])
            with self.assertRaisesRegex(ValueError, 'exact source dependency identities'):
                app.catalog()

    def test_unselected_fixed_dependencies_reject_before_dice_and_import_tampering_cannot_write(self):
        installed = RuleArchive.load()
        bad = installed.active('rifts-operator-psionics')
        bad['paths'][1]['allowances']['class']['milestones']['4'] = True
        archive = RuleArchive([bad if row['id'] == bad['id'] and row['version'] == bad['version'] else row
                               for row in installed.definitions()], installed.active_versions())
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=self.no_roll, rule_archive=archive)
            with self.assertRaises(ValueError):
                app.create(character_class='operator')
            self.assertEqual(app.list(), [])
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides: 2)
            hero = app.create(character_class='psi-operator')
            bundle = app.export_character(hero['id'])
            bundle['character']['class_psionics']['face'] = 1
            with self.assertRaises(ValueError):
                app.import_character(bundle)
            bundle = app.export_character(hero['id'])
            bundle['character']['class_psionics']['resource_record']['resource_attribute_snapshot']['ME']['explanation']['source']['book'] = 'Forged'
            with self.assertRaises(ValueError):
                app.import_character(bundle)
            self.assertEqual(app.get(hero['id']), hero)

    def test_old_operator_and_natural_pins_keep_their_exact_public_state(self):
        installed = RuleArchive.load()
        active = installed.active_versions()
        active.update({'rifts-core': '1.7.0', 'rifts-domestic-skills': '2.28.0', 'rifts-equipment': '1.15.0'})
        with tempfile.TemporaryDirectory() as directory:
            old = CharacterApplication(directory, die=lambda sides: 2,
                                       rule_archive=RuleArchive(installed.definitions(), active))
            hero = old.create(character_class='operator')
            old.die = lambda sides: 15 if sides == 100 else 2
            hero = old.select_psionics(hero['id'], revision=hero['revision'], roll=True)
            expected = old.psionic_view(hero['id'])
            new = CharacterApplication(directory, die=self.no_roll)
            self.assertEqual(new.psionic_view(hero['id']), expected)
            self.assertNotIn('class_psionics', hero)
            imported = new.import_character(old.export_character(hero['id']))
            self.assertEqual(new.psionic_view(imported['id']), expected)


if __name__ == '__main__':
    unittest.main()
