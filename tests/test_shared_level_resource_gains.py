from copy import deepcopy
from io import BytesIO
from pypdf import PdfReader
import tempfile
import unittest
from characters_unlimited.application import CharacterApplication
from characters_unlimited.rules import RuleArchive
from characters_unlimited.recorded_formulas import MAX_INTEGER

SOURCE = {'book': 'Synthetic progression fixture', 'section': 'Additional resource growth', 'pages': [1]}


def fixture_archive(*changed):
    installed = RuleArchive.load()
    replacements = {(row['id'], row['version']): row for row in changed}
    return RuleArchive([replacements.get((row['id'], row['version']), row)
                        for row in installed.definitions()], {**installed.active_versions(), **{row['id']:row['version'] for row in changed}})


class SharedLevelResourceGainTests(unittest.TestCase):
    def test_rifts_ppe_growth_ignores_house_options_and_survives_undo_replay(self):
        pack = RuleArchive.load().resolve('rifts-domestic-skills', '2.23.0')
        pack['resources']['definitions'].append({'id': 'PPE', 'name': 'Synthetic P.P.E.', 'contributions': [
            {'id': 'initial', 'formula': {'count': 0, 'sides': 0, 'bonus': 10}, 'source': SOURCE}]})
        pack['advancement']['resource_gains'] = {'PPE': {
            'formula': {'count': 2, 'sides': 6, 'constant': 1, 'multiplier': 2}, 'source': SOURCE}}
        pack['higher_advancement']['resource_gains'] = {'PPE': {
            'formula': {'count': 0, 'sides': 0, 'constant': 3}, 'source': SOURCE}}
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides: 4, rule_archive=fixture_archive(pack))
            hero = app.create(generation={'reroll_ones': True, 'extra_die': True})
            hero = app.generate_resources(hero['id'], revision=hero['revision'])
            app.die = lambda sides: 1
            hero = app.advance(hero['id'], revision=hero['revision'], method='level', value=3)
            self.assertEqual(app.resource_view(hero['id'])['resources']['PPE']['value'], 19)
            self.assertEqual(hero['advancement']['resource_gains']['PPE']['rolls'], [1, 1])
            self.assertEqual(hero['later_advancements'][0]['resource_gains']['PPE']['value'], 3)
            bundle = app.export_character(hero['id'])
            reopened = app.import_character(bundle)
            restored = app.undo_advancement(reopened['id'], revision=reopened['revision'])['character']
            app.die = lambda sides: self.fail('Retained level gain must not reroll')
            replay = app.advance(restored['id'], revision=restored['revision'], method='level', value=3)
            self.assertEqual(app.resource_view(replay['id'])['resources']['PPE']['value'], 19)
            fixed = app.set_resource(replay['id'], revision=replay['revision'], resource='PPE', mode='fixed', value=99)
            self.assertEqual(app.resource_view(fixed['id'])['resources']['PPE']['value'], 99)
            for key in ('value', 'source', 'rolls'):
                bad = deepcopy(bundle)
                receipt = bad['character']['advancement']['resource_gains']['PPE']
                receipt[key] = {'value': 99, 'source': {'book': 'Forged', 'section': 'Wrong'}, 'rolls': [6, 6]}[key]
                with self.subTest(key=key), self.assertRaises(ValueError):
                    app.import_character(bad)

    def test_heroes_ppe_uses_the_same_initial_and_later_gain_records(self):
        installed = RuleArchive.load()
        initial = installed.active('heroes-advancement')
        later = installed.active('heroes-higher-advancement')
        initial['resource_gains'] = {'PPE': {'formula': {'count': 1, 'sides': 4, 'constant': 2}, 'source': SOURCE}}
        later['resource_gains'] = {'PPE': {'formula': {'count': 2, 'sides': 4, 'constant': 1, 'multiplier': 2}, 'source': SOURCE}}
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides: 4, rule_archive=fixture_archive(initial, later))
            hero = app.create(game='heroes-unlimited')
            hero = app.generate_resources(hero['id'], revision=hero['revision'])
            hero = app.advance(hero['id'], revision=hero['revision'], method='level', value=3)
            self.assertEqual(app.resource_view(hero['id'])['resources']['PPE']['value'], 48)
            self.assertEqual(hero['advancement']['resource_gains']['PPE']['value'], 6)
            self.assertEqual(hero['later_advancements'][0]['resource_gains']['PPE']['value'], 18)
            restored = app.import_character(app.export_character(hero['id']))
            self.assertEqual(restored['later_advancements'], hero['later_advancements'])
            fields = PdfReader(BytesIO(app.export_pdf(hero['id']))).get_fields()
            assert fields is not None
            self.assertEqual(fields['PPE']['/V'], '48')
            rolled_back = app.undo_advancement(restored['id'], revision=restored['revision'])['character']
            rolled_back = app.undo_advancement(rolled_back['id'], revision=rolled_back['revision'])['character']
            app.die = lambda sides: self.fail('Retained first and later gains must not reroll')
            replay = app.advance(rolled_back['id'], revision=rolled_back['revision'], method='level', value=3)
            self.assertEqual(app.resource_view(replay['id'])['resources']['PPE']['value'], 48)

    def test_combined_resource_overflow_rejects_advancement_without_saving(self):
        from characters_unlimited.recorded_formulas import MAX_INTEGER
        pack = RuleArchive.load().resolve('rifts-domestic-skills', '2.23.0')
        pack['advancement']['resource_gains'] = {'HP': {
            'formula': {'count': 0, 'sides': 0, 'constant': MAX_INTEGER}, 'source': SOURCE}}
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides: 4, rule_archive=fixture_archive(pack))
            hero = app.create()
            hero = app.generate_resources(hero['id'], revision=hero['revision'])
            with self.assertRaises(ValueError):
                app.advance(hero['id'], revision=hero['revision'], method='level', value=2)
            self.assertEqual(app.get(hero['id']), hero)

    def test_invalid_later_gain_definitions_preflight_before_all_advancement_dice(self):
        installed = RuleArchive.load()
        invalids: list[dict] = [
            {'MISSING': {'formula': {'count': 1, 'sides': 6}, 'source': SOURCE}},
            {'HP': {'formula': {'count': 1001, 'sides': 6}, 'source': SOURCE}},
            {'HP': {'formula': {'count': 1, 'sides': 6}, 'source': {}}},
            {'HP': {'formula': {'count': 0, 'sides': 0, 'constant': MAX_INTEGER, 'multiplier': 2}, 'source': SOURCE}},
        ]
        for definitions in invalids:
            with self.subTest(definitions=definitions), tempfile.TemporaryDirectory() as directory:
                pack = installed.resolve('rifts-domestic-skills', '2.23.0')
                pack['higher_advancement']['resource_gains'] = definitions
                draws = []
                app = CharacterApplication(directory, die=lambda sides: 4, rule_archive=fixture_archive(pack))
                hero = app.create()
                hero = app.generate_resources(hero['id'], revision=hero['revision'])
                def die(sides):
                    draws.append(sides)
                    return 4
                app.die = die
                with self.assertRaises(ValueError):
                    app.advance(hero['id'], revision=hero['revision'], method='level', value=3)
                self.assertEqual(draws, [])
                self.assertEqual(app.get(hero['id']), hero)

    def test_nondefault_class_does_not_inherit_additional_default_class_growth(self):
        pack = RuleArchive.load().resolve('rifts-domestic-skills', '2.23.0')
        pack['higher_advancement']['resource_gains'] = {'HP': {
            'formula': {'count': 0, 'sides': 0, 'constant': 7}, 'source': SOURCE}}
        pack['class_profiles']['city-rat'].pop('higher_advancement')
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides: 4, rule_archive=fixture_archive(pack))
            hero = app.create(character_class='city-rat')
            hero = app.generate_resources(hero['id'], revision=hero['revision'])
            hero = app.advance(hero['id'], revision=hero['revision'], method='level', value=3)
            self.assertFalse('resource_gains' in hero['later_advancements'][0])

    def test_section_only_source_survives_both_editable_pdf_exports(self):
        installed = RuleArchive.load()
        source = {'book': 'Synthetic progression fixture', 'section': 'Section-only resource evidence'}
        for game, pack_id in [('rifts', 'rifts-domestic-skills'), ('heroes-unlimited', 'heroes-advancement')]:
            with self.subTest(game=game), tempfile.TemporaryDirectory() as directory:
                pack = installed.resolve(pack_id, '2.23.0') if game == 'rifts' else installed.active(pack_id)
                rules = pack['advancement'] if game == 'rifts' else pack
                rules['resource_gains'] = {'HP': {
                    'formula': {'count': 0, 'sides': 0, 'constant': 3}, 'source': source}}
                app = CharacterApplication(directory, die=lambda sides: 4, rule_archive=fixture_archive(pack))
                hero = app.create(game=game)
                hero = app.generate_resources(hero['id'], revision=hero['revision'])
                hero = app.advance(hero['id'], revision=hero['revision'], method='level', value=2)
                pdf = PdfReader(BytesIO(app.export_pdf(hero['id'])))
                fields = pdf.get_fields()
                assert fields is not None
                key = 'HIT POINTS' if game == 'rifts' else 'HP'
                self.assertEqual(fields[key]['/V'], str(app.resource_view(hero['id'])['resources']['HP']['value']))
                exported = '\n'.join(str(field.get('/V', '')) for field in fields.values())
                self.assertIn('Section-only resource evidence', ' '.join(exported.split()))

    def test_starting_contribution_label_cannot_be_overwritten_by_level_growth(self):
        pack = RuleArchive.load().resolve('rifts-domestic-skills', '2.23.0')
        hp = next(row for row in pack['resources']['definitions'] if row['id'] == 'HP')
        hp['contributions'].append({'id': 'Additional level 2', 'formula': {
            'count': 0, 'sides': 0, 'bonus': 7}, 'source': SOURCE})
        pack['advancement']['resource_gains'] = {'HP': {
            'formula': {'count': 0, 'sides': 0, 'constant': 3}, 'source': SOURCE}}
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides: 4, rule_archive=fixture_archive(pack))
            hero = app.create()
            hero = app.generate_resources(hero['id'], revision=hero['revision'])
            starting = app.resource_view(hero['id'])['resources']['HP']['value']
            hero = app.advance(hero['id'], revision=hero['revision'], method='level', value=2)
            view = app.resource_view(hero['id'])['resources']['HP']
            self.assertEqual(view['value'], starting + 4 + 3)
            self.assertEqual(view['contributions']['Additional level 2'], 7)
            self.assertIn(3, view['contributions'].values())
