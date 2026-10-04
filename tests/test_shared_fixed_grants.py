from copy import deepcopy
from io import BytesIO
import tempfile
import unittest
from pypdf import PdfReader
from characters_unlimited.application import CharacterApplication
from characters_unlimited.rules import RuleArchive

class SharedFixedGrantTests(unittest.TestCase):
    def test_program_selector_grants_percentile_and_physical_skills_once_with_retained_dice(self):
        installed=RuleArchive.load()
        pack=installed.active('heroes-program-skills')
        program=next(row for row in pack['programs'] if row['id']=='computer')
        program.pop('skill_ids')
        program['skill_grants']=['computer-operation', {'selector':{'any_of':[{'tags_any':['synthetic-grant']}]}}, 'boxing']
        for row in pack['skills']:
            if row['id'] in ('computer-operation','boxing'):
                row['tags']=['synthetic-grant']
        archive=RuleArchive([pack if (row['id'],row['version'])==(pack['id'],pack['version']) else row
                            for row in installed.definitions()], installed.active_versions())
        with tempfile.TemporaryDirectory() as directory:
            app=CharacterApplication(directory, die=lambda sides:4,rule_archive=archive)
            hero=app.create(game='heroes-unlimited')
            hero=app.select_education(hero['id'],revision=hero['revision'],method='choose',education_id='high-school')
            hero=app.select_hero_programs(hero['id'],revision=hero['revision'],selections=[{'slot':0,'program':'computer'}])
            view=app.hero_program_view(hero['id'])
            projected=next(row for row in view['catalog'] if row['id']=='computer')
            self.assertEqual(projected['skill_ids'],['computer-operation','boxing'])
            self.assertNotIn('skill_grants',projected)
            self.assertIn('computer-operation',[row['id'] for row in view['skills']])
            receipt=deepcopy(hero['physical_acquisitions']['boxing'])
            self.assertEqual(len([row for row in app.hero_program_view(hero['id'])['physical']['selected'] if row['id']=='boxing']),1)
            app.die=lambda sides:self.fail('Retained grant must not reroll')
            hero=app.select_hero_programs(hero['id'],revision=hero['revision'],selections=[])
            hero=app.select_hero_programs(hero['id'],revision=hero['revision'],selections=[{'slot':0,'program':'computer'}])
            self.assertEqual(hero['physical_acquisitions']['boxing'],receipt)
            restored=app.import_character(app.export_character(hero['id']))
            self.assertEqual(restored['physical_acquisitions'],hero['physical_acquisitions'])
            fields=PdfReader(BytesIO(app.export_pdf(hero['id']))).get_fields()
            assert fields is not None
            self.assertIn('Boxing','\n'.join(str(row.get('/V','')) for row in fields.values()))

    def test_rifts_selector_grants_acquire_once_and_remain_on_optional_backtracking(self):
        installed=RuleArchive.load()
        pack=installed.active('rifts-domestic-skills')
        pack['physical_grants']=[{'selector':{'any_of':[{'tags_any':['synthetic-running']}]}}, 'running']
        next(row for row in pack['skills'] if row['id']=='running')['tags']=['synthetic-running']
        archive=RuleArchive([pack if (row['id'],row['version'])==(pack['id'],pack['version']) else row
                            for row in installed.definitions()],installed.active_versions())
        with tempfile.TemporaryDirectory() as directory:
            app=CharacterApplication(directory,die=lambda sides:2,rule_archive=archive)
            hero=app.create()
            receipt=deepcopy(hero['physical_acquisitions']['running'])
            grants=[row['id'] for row in app.skill_view(hero['id'])['grants']]
            self.assertEqual(grants.count('running'),1)
            app.die=lambda sides:self.fail('Retained grant must not reroll')
            hero=app.select_skills(hero['id'],revision=hero['revision'],selections=[{'skill_id':'running','pool':'related'}])
            hero=app.select_skills(hero['id'],revision=hero['revision'],selections=[])
            self.assertEqual(hero['physical_acquisitions']['running'],receipt)
            self.assertEqual(app.import_character(app.export_character(hero['id']))['physical_acquisitions'],hero['physical_acquisitions'])

    def test_invalid_unselected_program_grants_reject_empty_save_atomically_without_dice(self):
        mutations=[
            lambda row:row.update(skill_grants=['unknown-grant']),
            lambda row:row.update(skill_grants=[{'selector':{'any_of':[{'ids':['unknown-grant']}]}}]),
            lambda row:row.update(skill_grants=[{'script':'execute'}]),
            lambda row:row.update(skill_grants=True),
            lambda row:row.update(skill_grants=[],skill_ids=[]),
        ]
        for mutation in mutations:
            with self.subTest(mutation=mutation),tempfile.TemporaryDirectory() as directory:
                installed=RuleArchive.load()
                app=CharacterApplication(directory,die=lambda sides:4,rule_archive=installed)
                hero=app.create(game='heroes-unlimited')
                hero=app.select_education(hero['id'],revision=hero['revision'],method='choose',education_id='high-school')
                before=deepcopy(app.get(hero['id']))
                pack=installed.active('heroes-program-skills')
                program=next(row for row in pack['programs'] if row['id']=='computer')
                program.pop('skill_ids')
                mutation(program)
                app.rule_archive=RuleArchive([pack if (row['id'],row['version'])==(pack['id'],pack['version']) else row
                                              for row in installed.definitions()],installed.active_versions())
                app.die=lambda sides:self.fail('Malformed grant must not draw dice')
                with self.assertRaises(ValueError):
                    app.select_hero_programs(hero['id'],revision=hero['revision'],selections=[])
                app.rule_archive=installed
                self.assertEqual(app.get(hero['id']),before)
