import tempfile
import unittest

from characters_unlimited.application import CharacterApplication, SaveConflict
from characters_unlimited.rules import RuleArchive


class RequiredVagabondSkillWorkflowTests(unittest.TestCase):
    def test_required_choices_and_grants_include_class_and_skill_synergies(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides: 4)
            character = app.create()
            character = app.set_attribute(character['id'], revision=0, attribute='IQ', mode='fixed', value=16)
            character = app.select_required_skills(character['id'], revision=1, choices={
                'native_language': 'American', 'other_languages': ['Spanish', 'Dragonese'],
                'pilot': 'automobile', 'repair': 'general-repair'})
            view = app.skill_view(character['id'])
            grants = {skill['id']: skill for skill in view['grants']}
            self.assertEqual(grants['native-language']['percentage'], 90)
            self.assertEqual(grants['barter']['percentage'], 58)
            self.assertEqual(grants['identify-undercover']['percentage'], 62)
            self.assertEqual(grants['radio-basic']['percentage'], 52)
            self.assertEqual(grants['streetwise']['percentage'], 32)
            self.assertEqual(grants['automobile']['percentage'], 72)
            self.assertEqual(grants['general-repair']['percentage'], 47)
            self.assertEqual([skill['percentage'] for skill in view['grants'] if skill['id']=='other-language'], [67,67])
            self.assertEqual(view['required_remaining'], {'native_language':0,'other_languages':0,'pilot':0,'repair':0})
            self.assertEqual(grants['identify-undercover']['contributions']['streetwise'], 10)
            self.assertEqual(grants['identify-undercover']['contributions']['class_ability'], 10)
            self.assertEqual(CharacterApplication(directory).get(character['id'])['required_skill_choices'], character['required_skill_choices'])
            with tempfile.TemporaryDirectory() as other:
                imported = CharacterApplication(other).import_character(app.export_character(character['id']))
                self.assertEqual(imported['required_skill_choices'], character['required_skill_choices'])

    def test_horse_has_both_checks_and_language_guidance_retains_excess(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides: 4)
            character = app.create()
            saved = app.select_required_skills(character['id'], revision=0, choices={
                'native_language':'American', 'other_languages':[' American ', 'Spanish', ' spanish ', 'Dragonese', 'French', ''],
                'pilot':'motorcycle', 'repair':'horse-general'})
            view = app.skill_view(saved['id'])
            horse = next(skill for skill in view['grants'] if skill['id']=='horse-general')
            self.assertEqual(horse['percentage'], 45)
            self.assertEqual(horse['additional_checks'][0]['name'], 'Jumping and other special maneuvers')
            self.assertEqual(horse['additional_checks'][0]['percentage'], 25)
            self.assertEqual(sum(horse['additional_checks'][0]['contributions'].values()), 25)
            self.assertEqual(view['required_remaining']['other_languages'], -1)
            self.assertTrue(view['warnings'])
            self.assertEqual(len(saved['required_skill_choices']['other_languages']), 6)
            self.assertEqual([skill['specialty'] for skill in view['grants'] if skill['id'] == 'other-language'], ['Spanish', 'Dragonese', 'French'])
            self.assertEqual(next(skill for skill in view['grants'] if skill['id']=='motorcycle')['percentage'], 72)

    def test_invalid_or_stale_required_choice_cannot_replace_saved_work(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides: 4)
            character = app.create()
            with self.assertRaises(ValueError):
                app.select_required_skills(character['id'], revision=0, choices={'pilot':'jet'})
            self.assertEqual(app.get(character['id']), character)
            saved = app.select_required_skills(character['id'], revision=0, choices={'pilot':'automobile'})
            with self.assertRaises(SaveConflict):
                app.select_required_skills(character['id'], revision=0, choices={'pilot':'motorcycle'})
            self.assertEqual(app.get(character['id']), saved)

    def test_upgrade_previews_added_grants_without_mispairing_selected_skills(self):
        archive = RuleArchive.load()
        active = archive.active_versions()
        active['rifts-domestic-skills'] = '1.1.0'
        with tempfile.TemporaryDirectory() as directory:
            earlier = CharacterApplication(directory, die=lambda sides: 4, rule_archive=RuleArchive(archive.definitions(), active))
            character = earlier.create()
            earlier.select_skills(character['id'], revision=0, selections=[{'skill_id':'dance','pool':'domestic'}])
            preview = CharacterApplication(directory).preview_rule_upgrade(character['id'])
            dance = next(row for row in preview['skills'] if row['name']=='Dance')
            self.assertEqual((dance['before'], dance['after']), (45,45))
            barter = next(row for row in preview['skills'] if row['name']=='Barter')
            self.assertEqual((barter['before'], barter['after']), (None,56))
            self.assertEqual(preview['after_required_remaining']['other_languages'], 2)

    def test_upgrade_preview_includes_secondary_horsemanship_checks(self):
        archive = RuleArchive.load()
        corrected = archive.resolve('rifts-domestic-skills','1.2.0')
        corrected['version'] = '1.2.1'
        horse = next(item for item in corrected['required']['repair']['options'] if item['id']=='horse-general')
        horse['additional_checks'][0]['base'] = 30
        active = archive.active_versions()
        active['rifts-domestic-skills'] = '1.2.1'
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides: 4)
            character = app.create()
            app.select_required_skills(character['id'], revision=0, choices={'repair':'horse-general'})
            later = CharacterApplication(directory, rule_archive=RuleArchive([*archive.definitions(),corrected], active))
            preview = later.preview_rule_upgrade(character['id'])
            row = next(row for row in preview['skills'] if 'Jumping and other special maneuvers' in row['name'])
            self.assertEqual((row['before'],row['after']), (25,35))
