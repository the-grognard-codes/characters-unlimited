"""Declarative selectors exercised through existing character program choices."""
from copy import deepcopy
from io import BytesIO
from pypdf import PdfReader
import tempfile
import unittest
from characters_unlimited.application import CharacterApplication
from characters_unlimited.rules import RuleArchive

class SharedOptionSelectorTests(unittest.TestCase):
    def test_categories_tags_and_exclusions_compile_to_program_choices_and_reopen(self):
        installed = RuleArchive.load()
        skills = installed.active('heroes-program-skills')
        repair = next(row for row in skills['skills'] if row['id'] == 'computer-repair')
        repair['tags'] = ['field-tech']  # Synthetic import-contract metadata.
        program = next(row for row in skills['programs'] if row['id'] == 'computer')
        group = program['choice_groups'][0]
        group.pop('skill_ids')
        group.update(count=2, selection_costs={'computer-repair': 2}, selector={
            'any_of': [{'categories': ['Communications']}, {'tags_any': ['field-tech']}],
            'exclude_ids': ['radio-satellite']})
        definitions = [skills if (row['id'], row['version']) == (skills['id'], skills['version'])
                       else row for row in installed.definitions()]
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides: 4,
                rule_archive=RuleArchive(definitions, installed.active_versions()))
            hero = app.create(game='heroes-unlimited')
            hero = app.select_education(hero['id'], revision=0, method='choose', education_id='high-school')
            choices = ['radio-basic', 'computer-repair', 'computer-repair', 'radio-satellite', 'boxing']
            hero = app.select_hero_programs(hero['id'], revision=hero['revision'], selections=[
                {'slot': 0, 'program': 'computer', 'choices': {'repair-radio': choices}}])
            view = app.hero_program_view(hero['id'])
            projected = view['program_choices'][0]['groups'][0]
            self.assertEqual((projected['credited'], projected['remaining']), (3, -1))
            self.assertIn('radio-basic', projected['skill_ids'])
            self.assertIn('computer-repair', projected['skill_ids'])
            self.assertNotIn('radio-satellite', projected['skill_ids'])
            self.assertNotIn('boxing', projected['skill_ids'])
            rows = {row['id']: row for row in view['skills']}
            self.assertEqual(rows['radio-basic']['contributions']['education'], 5)
            self.assertEqual(rows['computer-repair']['contributions']['education'], 5)
            self.assertEqual(rows['radio-satellite']['contributions']['education'], 0)
            self.assertNotIn('boxing', hero.get('physical_acquisitions', {}))
            fields = PdfReader(BytesIO(app.export_pdf(hero['id']))).get_fields()
            assert fields is not None
            text = ' '.join(' '.join(str(row.get('/V', '')) for row in fields.values()).split())
            self.assertIn('3 selections used / 2 allowed / -1 remaining', text)
            self.assertTrue(all(not row.get('/Ff', 0) & 1 for row in fields.values()))
            restored = app.import_character(app.export_character(hero['id']))
            self.assertEqual(restored['hero_program_selections'], hero['hero_program_selections'])
            self.assertEqual(app.hero_program_view(restored['id'])['program_choices'], view['program_choices'])

    def test_malformed_power_category_rejects_before_acquisition_and_save(self):
        installed = RuleArchive.load()
        powers = installed.active('heroes-super-abilities')
        powers['powers'][0]['category'] = True
        definitions = [powers if (row['id'], row['version']) == (powers['id'], powers['version'])
                       else row for row in installed.definitions()]
        with tempfile.TemporaryDirectory() as directory:
            original = CharacterApplication(directory, die=lambda sides: 4)
            hero = original.create(game='heroes-unlimited')
            app = CharacterApplication(directory, die=lambda sides: self.fail('Invalid metadata rolled dice'),
                rule_archive=RuleArchive(definitions, installed.active_versions()))
            before = deepcopy(app.get(hero['id']))
            with self.assertRaises(ValueError):
                app.select_hero_powers(hero['id'], revision=hero['revision'],
                    selections=['extraordinary-mental-affinity'])
            self.assertEqual(app.get(hero['id']), before)

    def test_invalid_selector_syntax_and_missing_references_reject_atomically(self):
        selectors = [
            {'any_of': [{'ids': ['missing']}]},
            {'any_of': [{'tags_any': [True]}]},
            {'any_of': [{'python': 'grant_everything()'}]},
            {'any_of': []},
            {'any_of': [{'categories': ['Communications']}], 'exclude_ids': ['missing']},
        ]
        for selector in selectors:
            with self.subTest(selector=selector), tempfile.TemporaryDirectory() as directory:
                installed = RuleArchive.load()
                skills = installed.active('heroes-program-skills')
                program = next(row for row in skills['programs'] if row['id'] == 'computer')
                group = program['choice_groups'][0]
                group.pop('skill_ids')
                group['selector'] = selector
                original = CharacterApplication(directory, die=lambda sides: 4)
                hero = original.create(game='heroes-unlimited')
                hero = original.select_education(hero['id'], revision=0, method='choose', education_id='high-school')
                definitions = [skills if (row['id'], row['version']) == (skills['id'], skills['version'])
                               else row for row in installed.definitions()]
                app = CharacterApplication(directory, die=lambda sides: self.fail('Invalid selector rolled dice'),
                    rule_archive=RuleArchive(definitions, installed.active_versions()))
                before = deepcopy(app.get(hero['id']))
                with self.assertRaises(ValueError):
                    app.select_hero_programs(hero['id'], revision=hero['revision'],
                        selections=[{'slot': 0, 'program': 'computer'}])
                self.assertEqual(app.get(hero['id']), before)

    def test_invalid_unselected_program_selector_rejects_empty_save(self):
        installed = RuleArchive.load()
        skills = installed.active('heroes-program-skills')
        program = next(row for row in skills['programs'] if row['id'] == 'computer')
        group = program['choice_groups'][0]
        group.pop('skill_ids')
        group['selector'] = {'any_of': [{'ids': ['missing']}]}
        definitions = [skills if (row['id'], row['version']) == (skills['id'], skills['version'])
                       else row for row in installed.definitions()]
        with tempfile.TemporaryDirectory() as directory:
            original = CharacterApplication(directory, die=lambda sides: 4)
            hero = original.create(game='heroes-unlimited')
            hero = original.select_education(hero['id'], revision=0, method='choose', education_id='high-school')
            app = CharacterApplication(directory, die=lambda sides: self.fail('Invalid selector rolled dice'),
                rule_archive=RuleArchive(definitions, installed.active_versions()))
            before = deepcopy(app.get(hero['id']))
            with self.assertRaises(ValueError):
                app.select_hero_programs(hero['id'], revision=hero['revision'], selections=[])
            self.assertEqual(app.get(hero['id']), before)
