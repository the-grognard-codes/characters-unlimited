import tempfile
import unittest
from pathlib import Path
import shutil
from unittest.mock import patch

from characters_unlimited.application import CharacterApplication, SaveConflict
from characters_unlimited.rules import RuleArchive


class HeroesProgramUpgradeWorkflowTests(unittest.TestCase):
    def test_high_school_business_is_retained_without_an_unsupported_scholastic_bonus(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides: 4)
            hero = app.create(game='heroes-unlimited')
            hero = app.select_education(hero['id'], revision=0, method='choose', education_id='high-school')
            hero = app.set_attribute(hero['id'], revision=hero['revision'], attribute='IQ', mode='fixed', value=16)
            choices = [{'slot':0, 'program':'business'}]
            hero = app.select_hero_programs(hero['id'], revision=hero['revision'], selections=choices)
            view = app.hero_program_view(hero['id'])
            research = next(skill for skill in view['skills'] if skill['id']=='research')
            self.assertEqual(research['percentage'], 52)
            self.assertEqual(research['contributions']['education'], 0)
            self.assertEqual(view['selections'], choices)
            self.assertTrue(any('eligible' in warning for warning in view['warnings']))
            self.assertEqual(hero['additional_rule_packs']['heroes-program-skills'], '1.5.0')
            imported = app.import_character(app.export_character(hero['id']))
            self.assertEqual(imported['hero_program_selections'], choices)
            self.assertEqual(app.hero_program_view(imported['id'])['skills'], view['skills'])

    def test_legacy_program_preview_is_read_only_and_apply_preserves_other_exact_pins(self):
        with tempfile.TemporaryDirectory() as directory:
            archive = RuleArchive.load()
            legacy = RuleArchive(archive.definitions(), {**archive.active_versions(), 'heroes-program-skills':'1.0.0'})
            earlier = CharacterApplication(directory, die=lambda sides: 4, rule_archive=legacy)
            hero = earlier.create(game='heroes-unlimited')
            hero = earlier.select_education(hero['id'], revision=0, method='choose', education_id='high-school')
            hero = earlier.set_attribute(hero['id'], revision=hero['revision'], attribute='IQ', mode='fixed', value=16)
            hero = earlier.select_hero_programs(hero['id'], revision=hero['revision'], selections=[{'slot':0,'program':'business'}])
            current = CharacterApplication(directory)
            preview = current.preview_rule_upgrade(hero['id'])
            self.assertEqual(preview['changes'], [{'pack_id':'heroes-program-skills','from':'1.0.0','to':'1.5.0'}])
            research = next(skill for skill in preview['skills'] if skill['name']=='Research')
            self.assertEqual((research['before'], research['after']), (57,52))
            self.assertEqual(preview['combat'], [])
            self.assertEqual(current.get(hero['id']), hero)
            imported_earlier = current.import_character(current.export_character(hero['id']))
            self.assertEqual(imported_earlier['additional_rule_packs']['heroes-program-skills'], '1.0.0')
            result = current.apply_rule_upgrade(hero['id'], revision=hero['revision'], token=preview['token'])
            updated = result['character']
            self.assertEqual(updated['additional_rule_packs'], {**hero['additional_rule_packs'],'heroes-program-skills':'1.5.0'})
            self.assertEqual(updated['attributes'], hero['attributes'])
            self.assertEqual(updated['education'], hero['education'])
            self.assertEqual(updated['hero_program_selections'], hero['hero_program_selections'])
            self.assertEqual(next(skill for skill in current.hero_program_view(hero['id'])['skills'] if skill['id']=='research')['percentage'],52)
            with tempfile.TemporaryDirectory() as restored:
                shutil.copyfile(result['backup']['path'], Path(restored)/'characters.sqlite3')
                self.assertEqual(CharacterApplication(restored).get(hero['id']), hero)

    def test_tampered_stale_and_failed_heroes_updates_preserve_the_saved_rules(self):
        with tempfile.TemporaryDirectory() as directory:
            archive = RuleArchive.load()
            legacy = RuleArchive(archive.definitions(), {**archive.active_versions(), 'heroes-program-skills':'1.0.0'})
            earlier = CharacterApplication(directory, die=lambda sides:4, rule_archive=legacy)
            hero = earlier.create(game='heroes-unlimited')
            hero = earlier.select_education(hero['id'], revision=0, method='choose', education_id='high-school')
            hero = earlier.select_hero_programs(hero['id'], revision=hero['revision'], selections=[{'slot':0,'program':'business'}])
            current = CharacterApplication(directory)
            preview = current.preview_rule_upgrade(hero['id'])
            with self.assertRaises(ValueError):
                current.apply_rule_upgrade(hero['id'], revision=hero['revision'], token='tampered')
            with patch.object(current, 'backup', side_effect=OSError('Backup unavailable')):
                with self.assertRaises(OSError):
                    current.apply_rule_upgrade(hero['id'], revision=hero['revision'], token=preview['token'])
            self.assertEqual(current.get(hero['id']), hero)
            changed = current.edit(hero['id'], revision=hero['revision'], notes='More character work')
            with self.assertRaises(SaveConflict):
                current.apply_rule_upgrade(hero['id'], revision=hero['revision'], token=preview['token'])
            with self.assertRaises(ValueError):
                current.apply_rule_upgrade(hero['id'], revision=changed['revision'], token=preview['token'])
            self.assertEqual(current.get(hero['id']), changed)


if __name__ == '__main__':
    unittest.main()
