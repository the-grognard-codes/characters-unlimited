from copy import deepcopy
import tempfile
import unittest
from characters_unlimited.application import CharacterApplication
from characters_unlimited.rules import RuleArchive

class RacialSourceProvenanceTests(unittest.TestCase):
    def test_racial_and_attribute_sources_replay_through_history_and_starting_resource_snapshot(self):
        installed=RuleArchive.load()
        core=installed.active('rifts-core')
        race=core['races'][0]
        source={'book':'Synthetic race fixture','section':'Default pool evidence','pages':[1]}
        override={'book':'Synthetic supplemental fixture','section':'P.E. pool evidence','pages':[2]}
        race['source']=source
        race['attribute_sources']={'PE':override}
        archive=RuleArchive([core if (row['id'],row['version'])==(core['id'],core['version']) else row
                            for row in installed.definitions()],installed.active_versions())
        with tempfile.TemporaryDirectory() as directory:
            app=CharacterApplication(directory,die=lambda sides:4,rule_archive=archive)
            hero=app.create()
            self.assertEqual(hero['attributes']['IQ']['explanation']['source'],source)
            self.assertEqual(hero['attributes']['PE']['explanation']['source'],override)
            hero=app.generate_resources(hero['id'],revision=hero['revision'])
            self.assertEqual(hero['resource_attribute_snapshot']['PE']['explanation']['source'],override)
            hero=app.reroll(hero['id'],revision=hero['revision'],attribute='PE')
            bundle=app.export_character(hero['id'])
            restored=app.import_character(bundle)
            self.assertEqual(restored['attributes'],hero['attributes'])
            self.assertEqual(restored['roll_history'],hero['roll_history'])
            self.assertEqual(restored['resource_attribute_snapshot'],hero['resource_attribute_snapshot'])
            for frame in ('current','history','snapshot'):
                with self.subTest(frame=frame):
                    bad=deepcopy(bundle)
                    character=bad['character']
                    records=(character['attributes'] if frame=='current' else
                             character['roll_history'][0]['attributes'] if frame=='history' else
                             character['resource_attribute_snapshot'])
                    records['PE']['explanation']['source']=deepcopy(source)
                    with self.assertRaises(ValueError):
                        app.import_character(bad)

    def test_legacy_fallback_and_override_without_race_default(self):
        installed = RuleArchive.load()
        core = installed.active('heroes-core')
        source = {'book': 'Synthetic supplement', 'section': 'M.E. table'}
        core['races'][0]['attribute_sources'] = {'ME': source}
        archive = RuleArchive([
            core if (row['id'], row['version']) == (core['id'], core['version']) else row
            for row in installed.definitions()
        ], installed.active_versions())
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides: 4, rule_archive=archive)
            hero = app.create(game='heroes-unlimited')
            self.assertEqual(hero['attributes']['IQ']['explanation']['source'], core['source'])
            self.assertEqual(hero['attributes']['ME']['explanation']['source'], source)
            restored = app.import_character(app.export_character(hero['id']))
            self.assertEqual(restored['attributes'], hero['attributes'])

    def test_invalid_source_definitions_reject_before_any_die(self):
        installed = RuleArchive.load()
        original = installed.active('rifts-core')
        cases = [
            {'source': None},
            {'source': {'book': 'Fixture'}},
            {'source': {'book': ' ', 'section': 'Table'}},
            {'source': {'book': 42, 'section': 'Table'}},
            {'attribute_sources': []},
            {'attribute_sources': {'unknown': {'book': 'Fixture', 'section': 'Table'}}},
            {'attribute_sources': {'SPD': {'book': 'Fixture', 'section': ''}}},
        ]
        for declaration in cases:
            with self.subTest(declaration=declaration):
                core = deepcopy(original)
                core['races'][0].update(declaration)
                archive = RuleArchive([
                    core if (row['id'], row['version']) == (core['id'], core['version']) else row
                    for row in installed.definitions()
                ], installed.active_versions())
                draws = []
                def die(sides):
                    draws.append(sides)
                    return 4
                with tempfile.TemporaryDirectory() as directory:
                    app = CharacterApplication(directory, die=die, rule_archive=archive)
                    with self.assertRaises(ValueError):
                        app.create()
                    self.assertEqual(draws, [])

